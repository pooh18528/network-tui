import asyncio
import csv
import socket
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from textual.app import App, ComposeResult, SystemCommand
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Static, Input, Button, Label
from textual.binding import Binding
from textual import on, work
from textual.events import Click, Key
from textual.screen import ModalScreen
from textual.reactive import reactive

from rich.text import Text
from rich.markup import escape as escape_markup

from .scanner import get_network_infos, scan_network
from .models import Device, NetworkInfo
from .lang import t, load_lang, save_lang
from .utils import mask_ip, mask_mac, mask_text

VERSION = "v2.5"


def _short(text: str, max_len: int, placeholder: str = "-") -> str:
    """ตัดข้อความยาวให้พอดีคอลัมน์ (กันตารางล้นจอ)"""
    s = (text or "").strip() or placeholder
    if len(s) <= max_len:
        return s
    if max_len <= 2:
        return s[:max_len]
    return s[:max_len - 1] + "…"


# ความกว้างคอลัมน์: คอลัมน์เล็ก fix ตายตัว, 3 คอลัมน์กลางปรับตามเนื้อหา/จอ
# จอกว้างมาก → ตารางกระชับตามเนื้อหา + แผงรายละเอียดขวา (ไม่ยืดคอลัมน์จนโล่ง)
# จอกลาง → ยืด 3 คอลัมน์กลางให้เต็ม / จอแคบ → ซ่อนคอลัมน์ไม่สำคัญก่อน
FIXED_COL_WIDTHS = {"#": 3, "IP": 17, "MAC": 19, "ประเภท": 9, "สถานะ": 9, "Ping": 8}
FLEX_COLS = ("ยี่ห้อ", "ชื่อเครื่อง", "รุ่น")
FLEX_MIN = {"ยี่ห้อ": 12, "ชื่อเครื่อง": 8, "รุ่น": 12}
FLEX_MAX = {"ยี่ห้อ": 26, "ชื่อเครื่อง": 20, "รุ่น": 40}
# เพดานตอนโหมดกระชับ (ตามความยาวเนื้อหาจริง ไม่ยืดเกินนี้)
SNUG_MAX = {"ยี่ห้อ": 30, "ชื่อเครื่อง": 24, "รุ่น": 60}
DETAIL_MIN_WIDTH = 38  # แผงขวาต้องกว้างอย่างน้อยเท่านี้ถึงจะโชว์
# ลำดับความสำคัญต่ำ → ถูกซ่อนก่อนเมื่อจอแคบ (CORE ห้ามซ่อนเด็ดขาด)
HIDE_PRIORITY = ("MAC", "ประเภท", "Ping", "ชื่อเครื่อง", "ยี่ห้อ")
CORE_COLS = ("#", "IP", "รุ่น", "สถานะ")
COL_ORDER = ("#", "IP", "MAC", "ยี่ห้อ", "ชื่อเครื่อง", "รุ่น", "ประเภท", "สถานะ", "Ping")
# ชื่อคอลัมน์ภายใน (ID) -> key ข้อความตามภาษา (None = ใช้ชื่อเดิมทั้ง 2 ภาษา)
COL_LABEL_KEY = {
    "#": None, "IP": None, "MAC": None,
    "ยี่ห้อ": "col_vendor", "ชื่อเครื่อง": "col_hostname", "รุ่น": "col_model",
    "ประเภท": "col_type", "สถานะ": "col_status", "Ping": None,
}


CSS = """
Screen {
    background: #0b0f1f;
}

Header {
    background: #1a1f3a;
    color: #7dd3fc;
}

/* แถบบนสุดแบบกำหนดเอง 3 ส่วน (แทน Header ที่ว่างโล่ง) */
#appbar {
    height: 1;
    background: #1a1f3a;
    color: #7dd3fc;
    padding: 0 1;
    layout: horizontal;
}

#appbar_left {
    width: 1fr;
    color: #38bdf8;
}

#appbar_left:hover {
    background: #232c52;
    text-style: bold;
}

#appbar_center {
    width: auto;
    color: #7dd3fc;
    text-style: bold;
}

#appbar_right {
    width: 1fr;
    height: 1;
    layout: horizontal;
}

#appbar_status {
    width: 1fr;
    color: #94a3b8;
    text-align: right;
}

#appbar_quit {
    width: auto;
    color: #f87171;
    text-style: bold;
    padding: 0 1;
}

#appbar_quit:hover {
    background: #7f1d1d;
    color: #ffffff;
}

#topbar {
    height: auto;
    min-height: 3;
    background: #141a33;
    border-bottom: solid #2a3050;
    padding: 0 1;
    layout: horizontal;
}

#topbar_info {
    color: #cbd5e1;
    height: auto;
    width: 1fr;
}

#topbar_right {
    color: #94a3b8;
    height: auto;
    width: auto;
    text-align: right;
}

#table_container {
    height: 1fr;
    min-height: 5;
    background: #0f142b;
    margin: 0;
    padding: 0;
}

#main {
    height: 1fr;
    min-height: 5;
    layout: horizontal;
}

#detail {
    width: 1fr;
    min-width: 30;
    height: 1fr;
    background: #101736;
    border-left: solid #2a3050;
    padding: 0 1;
    color: #cbd5e1;
    display: none;
}

#detail_title {
    color: #7dd3fc;
    text-style: bold;
    height: 1;
    margin-bottom: 1;
}

#detail_body {
    color: #cbd5e1;
    height: auto;
}

DataTable {
    background: #0f142b;
    scrollbar-color: #2a3050;
    scrollbar-background: #0f142b;
}

DataTable > .datatable--header {
    background: #1e293b;
    color: #38bdf8;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #2b4a7f;
}

DataTable > .datatable--even-row {
    background: #0f142b;
}

DataTable > .datatable--odd-row {
    background: #111834;
}

#statusbar {
    height: 1;
    background: #141a33;
    border-top: solid #2a3050;
    padding: 0 1;
    color: #94a3b8;
}

#status_left {
    width: 1fr;
}

#status_right {
    width: auto;
    color: #22d3ee;
}

#helpbar {
    height: 1;
    background: #0b0f1f;
    color: #7c8aa5;
    text-align: center;
    padding: 0 1;
}
"""


def get_alias_path() -> Path:
    # อยู่ข้างๆ โฟลเดอร์ Network-tui
    return Path(__file__).parent.parent / "aliases.json"


def load_alias_raw() -> dict:
    p = get_alias_path()
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except:
        pass
    return {}


def save_alias(mac: str, name: str, model: str):
    """บันทึก alias ลง aliases.json — mac คือ MAC จริง, name/model คือที่ผู้ใช้กรอก"""
    from .utils import normalize_mac
    p = get_alias_path()
    data = load_alias_raw()
    # เก็บ comment keys ไว้
    nm = normalize_mac(mac)
    if not name and not model:
        # ลบออก
        if nm in data:
            del data[nm]
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    # อัปเดตหรือสร้างใหม่
    entry = data.get(nm, {})
    if isinstance(entry, str):
        entry = {"name": entry}
    if name:
        entry["name"] = name
    if model:
        entry["model"] = model
    # ถ้าไม่ได้ระบุ model แต่มีชื่อ ให้เดา vendor เดิม
    data[nm] = entry
    # เขียนกลับ (เก็บ comment ไว้ข้างบน)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class NetworkTUI(App):
    CSS = CSS
    TITLE = "Network-TUI  🌐  Network Scanner"
    SUB_TITLE = f"{VERSION} • English / ไทย (L)"

    BINDINGS = [
        Binding("r,f5", "scan", "สแกนใหม่/Scan (R)"),
        Binding("q", "quit", "ออก/Quit (Q)"),
        Binding("f,slash", "filter", "กรอง/Filter (F)"),
        Binding("s", "sort", "เรียง/Sort (S)"),
        Binding("S", "sort_reverse", "กลับด้าน/Reverse (Shift+S)"),
        Binding("e", "export", "Export CSV (E)"),
        Binding("i", "change_interface", "เปลี่ยนวง/Switch (I)"),
        Binding("n,enter", "alias", "ตั้งชื่อ/Rename (N)"),
        Binding("p", "mask", "ปกปิด/Privacy (P)"),
        Binding("l", "toggle_lang", "ภาษา/Lang (L)"),
        Binding("question_mark", "help", "ช่วยเหลือ/Help (?)"),
    ]

    devices: reactive[List[Device]] = reactive([])
    network_info: reactive[Optional[NetworkInfo]] = reactive(None)
    filter_text: reactive[str] = reactive("")
    is_scanning: reactive[bool] = reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lang = load_lang()
        from .lang import set_current
        set_current(self.lang)
        self._all_devices: List[Device] = []
        self._sort_key = "ip"
        self._sort_reverse = False
        self._infos: List[NetworkInfo] = []
        self._current_iface_index = 0
        self._scan_count = 0
        self._col_keys = {}
        self._col_w = {**FIXED_COL_WIDTHS, **FLEX_MIN}
        self._visible = list(COL_ORDER)
        self._was_narrow = False
        self._content_w = dict(FLEX_MIN)  # ความกว้างตามเนื้อหาจริง (วัดจากข้อมูล)
        self._detail_cursor = -1  # แถวที่แผงรายละเอียดกำลังโชว์ (กันวาดซ้ำ)
        self._detail_on = False  # แผงขวาเปิดอยู่ไหม
        self.mask_mode = False  # โหมดปกปิด IP/MAC/ชื่อ (กด P) — session-only ไม่จำลงไฟล์

    def get_system_commands(self, screen):
        """เพิ่มคำสั่งใน command palette (Ctrl+P) — สลับภาษาโดยไม่ต้องจำปุ่ม L"""
        yield from super().get_system_commands(screen)
        yield SystemCommand(
            "Switch language / สลับภาษา",
            "Toggle Thai ⇄ English (same as L)",
            self.action_toggle_lang,
        )

    def col_label(self, name: str) -> str:
        """ชื่อคอลัมน์ตามภาษา (name = ID ภายใน)"""
        key = COL_LABEL_KEY.get(name)
        return t(key, self.lang) if key else name

    def refresh_column_labels(self) -> None:
        try:
            table = self.query_one("#device_table", DataTable)
            for name, key in self._col_keys.items():
                try:
                    table.columns[key].label = Text(self.col_label(name))
                except Exception:
                    pass
            table.refresh()
        except Exception:
            pass

    def action_mask(self):
        """P — สลับโหมดปกปิด IP/MAC/ชื่อเครื่อง (สำหรับแคปจอแชร์)"""
        self.mask_mode = not self.mask_mode
        self.notify(t("mask_on" if self.mask_mode else "mask_off", self.lang), timeout=3)
        self.update_topbar()
        self.update_detail()
        self.update_table()

    def _mi(self, s):
        return mask_ip(s) if self.mask_mode else s

    def _mm(self, s):
        return mask_mac(s) if self.mask_mode else s

    def _mt(self, s):
        return mask_text(s) if self.mask_mode else s

    def action_toggle_lang(self):
        """L — สลับภาษา ไทย/English ทันที (รวมชื่อรุ่นที่เดาไว้ โดยไม่แตะชื่อที่ผู้ใช้ตั้งเอง)"""
        try:
            self._do_toggle_lang()
        except Exception as e:
            try:
                self.notify(f"Language switch failed: {e}", severity="error", timeout=5)
            except Exception:
                pass

    def _do_toggle_lang(self):
        from .lang import other
        self.lang = other(self.lang)
        save_lang(self.lang)
        from .lang import set_current
        set_current(self.lang)
        # แปลชื่อรุ่นอัตโนมัติในหน่วยความจำทันที — ข้ามเครื่องที่มี alias (ของผู้ใช้ ห้ามแตะ)
        try:
            from .scanner import load_aliases
            from .oui import guess_model, guess_device_type
            from .utils import normalize_mac
            alias_map = load_aliases()
            for d in self._all_devices:
                try:
                    if d.mac and normalize_mac(d.mac) in alias_map:
                        continue
                    host = "" if d.hostname in ("-", "") else d.hostname
                    d.model = guess_model(host, d.vendor, d.mac or "", d.ttl, lang=self.lang)
                    d.device_type = guess_device_type(d.vendor, d.model, d.hostname)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.query_one("#helpbar", Static).update(t("helpbar", self.lang))
            self.query_one("#detail_title", Static).update(t("detail_title", self.lang))
        except Exception:
            pass
        self.refresh_column_labels()
        self.update_table()  # วาดใหม่ + วัดความกว้างตามภาษาใหม่
        self.update_topbar()
        self.update_detail()
        self.notify(t("lang_switched", self.lang), timeout=3)

    def compose(self) -> ComposeResult:
        with Horizontal(id="appbar"):
            globe = Static("", id="appbar_left")
            globe.tooltip = "Commands / คำสั่ง (click 🌐)"
            yield globe
            yield Static(f"Network-TUI · Scanner {VERSION}", id="appbar_center")
            with Horizontal(id="appbar_right"):
                yield Static("", id="appbar_status")
                quit_btn = Static("", id="appbar_quit")
                quit_btn.tooltip = "Quit / ออก"
                yield quit_btn

        with Horizontal(id="topbar"):
            yield Static(t("loading", self.lang), id="topbar_info")
            yield Static("", id="topbar_right")

        with Horizontal(id="main"):
            with Container(id="table_container"):
                yield DataTable(id="device_table", zebra_stripes=True, cursor_type="row", show_cursor=True)
            with Vertical(id="detail"):
                yield Static(t("detail_title", self.lang), id="detail_title")
                yield Static(t("detail_loading", self.lang), id="detail_body")

        with Horizontal(id="statusbar"):
            yield Static(t("state_ready", self.lang), id="status_left")
            yield Static("", id="status_right")

        yield Static(t("helpbar", self.lang), id="helpbar")

    def on_mount(self):
        table = self.query_one("#device_table", DataTable)
        # หัวสั้นประหยัดที่ — 3 คอลัมน์กลางจะยืด-หดตามจอผ่าน _fit_columns()
        for name in COL_ORDER:
            key = table.add_column(self.col_label(name), width=self._col_w.get(name, 12))
            self._col_keys[name] = key
        self._visible = list(COL_ORDER)
        table.cursor_type = "row"
        self._fit_columns()
        self.set_interval(0.5, self._auto_fit)
        self.set_interval(1.0, self._tick_clock)
        self._infos = get_network_infos()
        if self._infos:
            self.network_info = self._infos[0]
        else:
            self.network_info = NetworkInfo(
                interface="Unknown",
                local_ip="192.168.1.100",
                netmask="255.255.255.0",
                cidr="192.168.1.0/24",
                gateway="192.168.1.1",
            )
        self.update_topbar()
        self.update_appbar()
        try:
            self.notify(f"Network-TUI {VERSION} · {'ไทย' if self.lang == 'th' else 'English'} · L=สลับภาษา/Lang", timeout=4)
        except Exception:
            pass
        self.action_scan()

    def get_selected_device(self) -> Optional[Device]:
        table = self.query_one("#device_table", DataTable)
        if not self.devices:
            return None
        try:
            row = table.cursor_row
            if row is None or row < 0 or row >= len(self.devices):
                # cursor อยู่นอกช่วง (เช่น หลังกรอง/เรียงใหม่) — ใช้แถวแรก
                row = 0
            return self.devices[row]
        except Exception:
            pass
        # fallback: ถ้าไม่มี cursor ให้เอาตัวแรก
        if self.devices:
            return self.devices[0]
        return None

    def _min_total(self, visible) -> int:
        """ความกว้างขั้นต่ำ (รวม padding) ของชุดคอลัมน์ที่ระบุ"""
        vis = list(visible)
        fixed = sum(FIXED_COL_WIDTHS.get(c, 0) for c in vis)
        flex = sum(FLEX_MIN.get(c, 0) for c in vis)
        return fixed + flex + 2 * len(vis)

    def _measure_content(self, devices) -> None:
        """วัดความยาวเนื้อหาจริง (สำหรับโหมดกระชับ) — มีข้อมูลค่อยอัปเดต กันตารางหดตอนสแกน"""
        if not devices:
            return
        for name, attr, cap in (("ยี่ห้อ", "vendor", SNUG_MAX["ยี่ห้อ"]),
                                ("ชื่อเครื่อง", "hostname", SNUG_MAX["ชื่อเครื่อง"]),
                                ("รุ่น", "model", SNUG_MAX["รุ่น"])):
            m = 0
            for d in devices:
                try:
                    t = getattr(d, attr, "") or ""
                    # +2 เผื่อ 🔒/marker ท้ายข้อความ
                    m = max(m, len(t) + 2)
                except Exception:
                    pass
            self._content_w[name] = max(FLEX_MIN[name], min(cap, m))

    def _snug_widths(self, visible):
        """ความกว้างกระชับตามเนื้อหา (ไม่ยืดเกินจำเป็น)"""
        widths = {}
        for c in visible:
            if c in FLEX_COLS:
                widths[c] = max(FLEX_MIN[c], min(SNUG_MAX[c], self._content_w.get(c, FLEX_MIN[c])))
        return widths

    def _snug_total(self, visible) -> int:
        vis = list(visible)
        fixed = sum(FIXED_COL_WIDTHS.get(c, 0) for c in vis)
        flex = sum(self._snug_widths(vis).values())
        return fixed + flex + 2 * len(vis)

    def _stretch_widths(self, visible, avail):
        """ยืด 3 คอลัมน์กลางให้เต็ม avail (โหมดไม่มีแผงขวา)"""
        flex_here = [c for c in FLEX_COLS if c in visible]
        widths = {c: FLEX_MIN[c] for c in flex_here}
        room = avail - 2 * len(visible) - sum(FIXED_COL_WIDTHS.get(c, 0) for c in visible)
        remaining = room - sum(widths.values())
        if remaining > 0 and flex_here:
            for name in flex_here:
                if remaining <= 0:
                    break
                can = FLEX_MAX[name] - widths[name]
                if can > 0:
                    add = min(can, remaining)
                    widths[name] += add
                    remaining -= add
            if "รุ่น" in widths:
                widths["รุ่น"] += remaining  # เศษทั้งหมดให้รุ่น → เต็มขวาเสมอ
        elif remaining < 0 and "รุ่น" in widths:
            widths["รุ่น"] = max(8, widths["รุ่น"] + remaining)
        return widths

    def _layout_for_width(self, avail: int):
        """(เดิม) เลือกคอลัมน์+ยืดเต็ม — ใช้เฉพาะโหมดไม่มีแผงขวา"""
        visible = list(COL_ORDER)
        for drop in HIDE_PRIORITY:
            if self._min_total(visible) <= avail:
                break
            if drop in visible and drop not in CORE_COLS:
                visible.remove(drop)
        return visible, self._stretch_widths(visible, avail)

    def _rebuild_columns(self, table, visible, widths) -> None:
        """สร้างคอลัมน์ใหม่ตาม visible (คงลำดับเดิม) + รีเซ็ต scroll แนวนอนไปซ้ายสุด"""
        for key in list(table.columns.keys()):
            try:
                table.remove_column(key)
            except Exception:
                pass
        self._col_keys = {}
        for name in visible:
            w = widths.get(name, self._col_w.get(name, FIXED_COL_WIDTHS.get(name, 12)))
            self._col_keys[name] = table.add_column(self.col_label(name), width=w)
        self._visible = list(visible)
        self._col_w.update(widths)
        try:
            table.scroll_to(x=0, animate=False)
        except Exception:
            try:
                table.scroll_to(x=0)
            except Exception:
                pass

    def _set_detail_visible(self, show: bool, table_width: int = 0) -> bool:
        """เปิด/ปิดแผงรายละเอียดขวา (+ล็อกความกว้าง container ตาราง) — คืน True ถ้าเปลี่ยน"""
        if show == getattr(self, "_detail_on", False):
            return False
        self._detail_on = show
        try:
            detail = self.query_one("#detail", Vertical)
            container = self.query_one("#table_container", Container)
            detail.styles.display = "block" if show else "none"
            container.styles.width = table_width if show and table_width > 0 else "1fr"
        except Exception:
            pass
        return True

    def _fit_columns(self, allow_rebuild=True) -> str:
        """จัดเลย์เอาต์ตารางตามความกว้างจอ:
        - จอกว้าง: ตารางกระชับตามเนื้อหา + แผงรายละเอียดขวา
        - จอกลาง: ยืดคอลัมน์เต็มจอ / จอแคบ: ซ่อนคอลัมน์ไม่สำคัญก่อน

        คืน 'rebuilt' | 'resized' | 'needs_rebuild' | 'none'
        """
        if not self._col_keys:
            return "none"
        try:
            table = self.query_one("#device_table", DataTable)
        except Exception:
            return "none"
        try:
            scr_w = self.screen.size.width
        except Exception:
            return "none"
        if scr_w <= 0:
            return "none"
        # จอแคบผิดปกติ (< 50 คอลัมน์): เตือนครั้งเดียวตอนเข้าโหมดนี้
        narrow = scr_w < 50
        if narrow and not self._was_narrow:
            try:
                self.notify(t("narrow_tiny", self.lang, w=scr_w), timeout=5)
            except Exception:
                pass
        self._was_narrow = narrow

        # 1. เลือกชุดคอลัมน์: ใช้เกณฑ์ขั้นต่ำ (min) — อย่าใช้ snug (เดี๋ยวซ่อนเกินจำเป็น)
        visible = list(COL_ORDER)
        for drop in HIDE_PRIORITY:
            if self._min_total(visible) <= scr_w:
                break
            if drop in visible and drop not in CORE_COLS:
                visible.remove(drop)

        # 2. จอกว้างพอ → โหมดแผงขวา (ตารางกระชับ, ที่เหลือให้แผงรายละเอียด)
        full_set = len(visible) == len(COL_ORDER)
        snug = self._snug_widths(visible)
        snug_total = (sum(FIXED_COL_WIDTHS.get(c, 0) for c in visible)
                      + sum(snug.values()) + 2 * len(visible))
        detail_mode = full_set and (snug_total + DETAIL_MIN_WIDTH <= scr_w)

        if detail_mode:
            widths = snug
        else:
            # โหมดเต็มจอ: ตารางใช้ทั้งจอ (แผงขวาซ่อน) → ยืด flex เต็ม viewport ตาราง
            try:
                tbl_vw = table.scrollable_content_region.width
                avail = tbl_vw if tbl_vw and tbl_vw > 0 else scr_w
            except Exception:
                avail = scr_w
            _vis2, widths = self._layout_for_width(avail)
            # _layout_for_width อาจซ่อนเพิ่มถ้า viewport แคบกว่า screen (เช่น มี scrollbar)
            if len(_vis2) < len(visible):
                visible = _vis2

        if visible != list(getattr(self, "_visible", [])):
            if not allow_rebuild:
                return "needs_rebuild"
            before = set(getattr(self, "_visible", list(COL_ORDER)))
            self._rebuild_columns(table, visible, widths)
            hidden = [c for c in COL_ORDER if c in before and c not in visible]
            if hidden:
                try:
                    names = ', '.join(self.col_label(c) for c in hidden)
                    self.notify(t("narrow_hidden", self.lang, cols=names), timeout=4)
                except Exception:
                    pass
            self._set_detail_visible(detail_mode, snug_total if detail_mode else 0)
            try:
                table.refresh(layout=True)
            except Exception:
                pass
            return "rebuilt"

        # ชุดเดิม: ปรับความกว้าง + เปิด/ปิดแผงขวา
        changed = self._set_detail_visible(detail_mode, snug_total if detail_mode else 0)
        for name, w in widths.items():
            key = self._col_keys.get(name)
            if key is None:
                continue
            try:
                col = table.columns[key]  # Column metadata (get_column() คืนค่า cells ไม่ใช่ metadata)
            except Exception:
                continue
            if col.width != w:
                col.width = w
                changed = True
            self._col_w[name] = w
        if detail_mode:
            # ล็อก container ให้เท่าตารางจริง (กันยืด)
            try:
                total = (sum(FIXED_COL_WIDTHS.get(c, 0) for c in self._visible)
                         + sum(self._col_w.get(c, 0) for c in self._visible if c in FLEX_COLS)
                         + 2 * len(self._visible))
                container = self.query_one("#table_container", Container)
                container.styles.width = total
            except Exception:
                pass
        if changed:
            try:
                table.refresh(layout=True)
            except Exception:
                pass
            return "resized"
        return "none"

    def _auto_fit(self):
        """เช็กขนาดจอเป็นระยะ — ถ้าความกว้าง/ชุดคอลัมน์เปลี่ยน วาดแถวใหม่ให้ข้อความพอดี"""
        try:
            if self._fit_columns(allow_rebuild=False) in ("resized", "needs_rebuild"):
                self.update_table()
                return
        except Exception:
            pass
        # cursor ย้ายแถว (↑/↓) → อัปเดตแผงรายละเอียดขวาตาม (ถ้าเปิดอยู่)
        try:
            if getattr(self, "_detail_on", False) and self.devices:
                table = self.query_one("#device_table", DataTable)
                crow = table.cursor_row or 0
                if crow != getattr(self, "_detail_cursor", -1):
                    self.update_detail()
        except Exception:
            pass

    def _detail_markup(self, dev: Optional[Device]) -> str:
        """ข้อความในแผงรายละเอียดขวา (escape แล้วทุกฟิลด์)"""
        lg = self.lang

        def _hist_first(d: Device) -> str:
            try:
                from .history import get_entry
                v = (get_entry(d.mac or "") or {}).get("first_seen", "")
                return v.replace("T", " ")[:16] if v else "-"
            except Exception:
                return "-"

        def _hist_last(d: Device) -> str:
            try:
                from .history import get_entry
                v = (get_entry(d.mac or "") or {}).get("last_seen", "")
                return v.replace("T", " ")[:16] if v else "-"
            except Exception:
                return "-"

        if dev is None:
            if getattr(self, "is_scanning", False):
                return t("detail_scanning", lg)
            return t("detail_none", lg)
        mark = ""
        if dev.is_gateway:
            mark = " 🌐 Router"
        elif dev.is_self:
            mark = " ⭐ YOU" if lg == "en" else " ⭐ เครื่องนี้"
        lock = " 🔒" if getattr(dev, "is_randomized", False) else ""
        g = lambda s: escape_markup(str(s or "-"))
        show_ip = self._mi(dev.ip)
        show_mac = self._mm(dev.mac)
        show_host = self._mt(dev.hostname)
        lines = [
            f"[bold cyan]🔍 {g(show_ip)}[/]{mark}",
            "",
            f"[yellow]IP[/]          {g(show_ip)}",
            f"[yellow]MAC[/]         {g(show_mac)}{lock}",
            f"[yellow]{t('detail_vendor', lg)}[/]       {g(dev.vendor)}",
            f"[yellow]{t('detail_hostname', lg)}[/]  {g(show_host)}",
            f"[yellow]{t('detail_model', lg)}[/]         {g(dev.model)}",
            f"[yellow]{t('detail_type', lg)}[/]      {g(dev.device_type)}",
            f"[yellow]{t('detail_status', lg)}[/]       {'🟢 online' if dev.status == 'online' else '🔴 offline'}",
            f"[yellow]Ping[/]        {g(dev.latency_label())}",
            f"[yellow]{t('detail_iface', lg)}[/]   {g(dev.interface)}",
            f"[yellow]{t('detail_first', lg)}[/]  {g(_hist_first(dev))}",
            f"[yellow]{t('detail_last', lg)}[/]   {g(_hist_last(dev))}",
            "",
            f"[dim]{t('detail_hint', lg)}[/]",
        ]
        if getattr(dev, "is_randomized", False):
            lines.append(f"[yellow]{t('detail_private', lg)}[/]")
        return "\n".join(lines)

    def update_detail(self) -> None:
        """วาดแผงรายละเอียดตามแถวที่เลือกอยู่"""
        try:
            body = self.query_one("#detail_body", Static)
        except Exception:
            return
        try:
            dev = self.get_selected_device()
            crow = None
            try:
                crow = self.query_one("#device_table", DataTable).cursor_row
            except Exception:
                pass
            body.update(Text.from_markup(self._detail_markup(dev)))
            self._detail_cursor = crow if crow is not None else -1
        except Exception:
            pass

    def _hidden_suffix(self) -> str:
        """บอกจำนวนคอลัมน์ที่ซ่อนเพราะจอแคบ"""
        try:
            hidden = len(COL_ORDER) - len(self._visible)
        except Exception:
            hidden = 0
        if hidden <= 0:
            return ""
        return f" · -{hidden}col" if self.lang == "en" else f" · ซ่อน {hidden}"

    def update_appbar(self) -> None:
        """แถบบนสุด 3 ส่วน: ซ้ายเน็ตเวิร์ก กลางชื่อแอป ขวาสถานะ+นาฬิกา+ปุ่มออก"""
        try:
            info = self.network_info
            rest = ""
            if info and info.local_ip:
                rest = f"{info.interface or ''} · {info.cidr or info.local_ip}".strip(" ·")
            left = f"🌐 {rest}" if rest else "🌐"
            self.query_one("#appbar_left", Static).update(escape_markup(left))
        except Exception:
            pass
        try:
            if self.is_scanning:
                st = t("state_scanning", self.lang)
            else:
                st = t("state_ready", self.lang)
            clock = datetime.now().strftime("%H:%M:%S")
            self.query_one("#appbar_status", Static).update(f"{st} · {clock}")
        except Exception:
            pass
        try:
            quit_label = "✕ Quit" if self.lang == "en" else "✕ ออก"
            self.query_one("#appbar_quit", Static).update(quit_label)
        except Exception:
            pass

    @on(Click, "#appbar_quit")
    def _click_quit_button(self) -> None:
        """คลิกปุ่ม ✕ มุมขวาบน → ออกจากแอปทันที (เหมือนกด Q)"""
        try:
            self.exit()
        except Exception:
            pass

    def on_key(self, event: Key) -> None:
        """Esc ปิดแผง HelpPanel (sidebar แบบ dock ที่ Esc ธรรมดาปิดไม่ได้)
        ถ้าเป็น modal เปิดอยู่ให้ modal จัดการเอง ไม่แย่ง"""
        try:
            if event.key != "escape":
                return
            if isinstance(self.screen, ModalScreen):
                return
            if self.screen.query("HelpPanel"):
                event.prevent_default()
                event.stop()
                self.action_hide_help_panel()
        except Exception:
            pass

    def _tick_clock(self) -> None:
        """อัปเดตนาฬิกา + สถานะทุกวินาที (ไม่แตะตาราง)"""
        try:
            self.update_appbar()
        except Exception:
            pass

    def update_topbar(self):
        info = self.network_info
        if not info:
            return
        try:
            hostname = socket.gethostname()
        except Exception:
            hostname = "-"

        gw_text = escape_markup(info.gateway or "-")
        iface_text = escape_markup(info.interface or "-")
        cidr_text = escape_markup(info.cidr or f"{info.local_ip}/24")
        host_esc = escape_markup(_short(self._mt(hostname), 24))
        ip_esc = escape_markup(self._mi(info.local_ip))

        online = sum(1 for d in self._all_devices if d.status == "online") if self._all_devices else 0
        total = len(self._all_devices)

        private_count = sum(1 for d in self._all_devices if getattr(d, 'is_randomized', False))
        # นับที่ตั้งชื่อแล้ว
        named = sum(1 for d in self._all_devices if d.hostname and d.hostname not in ("-", "") and not d.is_self and not d.is_gateway)
        state = f'[yellow]{t("state_scanning", self.lang)}[/]' if self.is_scanning else f'[green]{t("state_ready", self.lang)}[/]'
        # แถบบนแยกซ้าย/ขวา — ซ้ายข้อมูลเครื่อง ขวาสถานะ+นาฬิกา (เต็มความกว้างจอ ไม่มีช่องโล่ง)
        left_text = (
            f"[bold cyan]{host_esc}[/] [green]{ip_esc}[/] [dim]·[/] {cidr_text} [dim]·[/] GW [magenta]{gw_text}[/]"
            f" [dim]·[/] {iface_text}"
        )
        try:
            wide = self.screen.size.width >= 110
        except Exception:
            wide = True
        now_hm = datetime.now().strftime("%H:%M:%S")
        ifaces = ""
        if len(self._infos) > 1:
            try:
                cur = self._infos.index(info) if info in self._infos else 0
                ifaces = f" [dim]·[/] I:{cur + 1}/{len(self._infos)}"
            except Exception:
                pass
        right_text = (
            f"📊 [bold]{online}/{total}[/]{' [dim]·[/] 🔒 [yellow]' + str(private_count) + '[/]' if private_count else ''}"
            f"{' [dim]·[/] ✏️ [cyan]' + str(named) + f'/{total}[/]' if total else ''}"
            f" [dim]#{self._scan_count}[/]{ifaces}{self._hidden_suffix()}"
            f" {state}"
            f"{' [dim]' + now_hm + '[/]' if wide else ''}"
        )
        top = self.query_one("#topbar_info", Static)
        top.update(Text.from_markup(left_text))
        try:
            self.query_one("#topbar_right", Static).update(Text.from_markup(right_text))
        except Exception:
            pass
        self.update_appbar()

        left = self.query_one("#status_left", Static)
        right = self.query_one("#status_right", Static)
        now = datetime.now().strftime("%H:%M:%S")
        # แถบสถานะบรรทัดเดียว — ย่อให้พอดีจอแคบ
        sel = self.get_selected_device()
        if self.is_scanning:
            left.update(t("status_scanning", self.lang, cidr=cidr_text))
        elif self.filter_text:
            left.update(t("status_filter", self.lang, f=_short(self.filter_text, 24), n=len(self.devices)))
        elif sel:
            lock = " 🔒" if getattr(sel, 'is_randomized', False) else ""
            left.update(t("status_selected", self.lang, now=now, ip=self._mi(sel.ip), lock=lock))
        else:
            left.update(t("status_done", self.lang, now=now))

        if len(self._infos) > 1:
            cur = self._infos.index(info) if info in self._infos else 0
            right.update(f"I: {cur + 1}/{len(self._infos)} · {cidr_text}{self._hidden_suffix()}")
        else:
            right.update(f"{cidr_text}{self._hidden_suffix()}")

    def update_table(self):
        table = self.query_one("#device_table", DataTable)
        # จำตำแหน่งไว้ก่อนวาดใหม่ (กัน cursor/scroll กระโดดตอนสแกนหรือย่อขยายจอ)
        try:
            _crow = max(0, table.cursor_row or 0)
        except Exception:
            _crow = 0
        try:
            _ccol = max(0, table.cursor_column or 0)
        except Exception:
            _ccol = 0
        try:
            _sx, _sy = table.scroll_x, table.scroll_y
        except Exception:
            _sx, _sy = 0, 0

        devices = list(self._all_devices)
        if self.filter_text:
            ft = self.filter_text.lower()
            devices = [
                d for d in devices
                if ft in (d.ip or "").lower()
                or ft in (d.mac or "").lower()
                or ft in (d.vendor or "").lower()
                or ft in (d.hostname or "").lower()
                or ft in (d.model or "").lower()
                or ft in (d.device_type or "").lower()
            ]

        def _ip_key(d: Device):
            try:
                return tuple(map(int, (d.ip or "0.0.0.0").split(".")))
            except Exception:
                return (9999,)

        if self._sort_key == "ip":
            devices = sorted(devices, key=_ip_key, reverse=self._sort_reverse)
        elif self._sort_key == "vendor":
            devices = sorted(devices, key=lambda d: (d.vendor or "").lower(), reverse=self._sort_reverse)
        elif self._sort_key == "hostname":
            devices = sorted(devices, key=lambda d: (d.hostname or "").lower(), reverse=self._sort_reverse)
        elif self._sort_key == "latency":
            devices = sorted(devices, key=lambda d: d.latency_ms if d.latency_ms is not None else 9999, reverse=self._sort_reverse)
        elif self._sort_key == "type":
            devices = sorted(devices, key=lambda d: d.device_type or "", reverse=self._sort_reverse)

        # สำคัญ: เก็บ list ที่เรียง+กรองแล้ว เพื่อให้ get_selected_device() ตรงกับแถวในตาราง
        self.devices = devices

        # วัดเนื้อหาก่อนจัดคอลัมน์ (โหมดจอกว้างจะได้กระชับพอดี ไม่ยืดโล่ง)
        self._measure_content(devices)
        table.clear()  # ล้างแถวก่อน — _fit_columns อาจ rebuild คอลัมน์ต่อจากนี้
        self._fit_columns(allow_rebuild=True)

        for idx, dev in enumerate(devices, 1):
            # IP + marker (ย้าย GW/YOU มาที่นี่ — คอลัมน์สถานะจะได้แคบลง)
            ip_label = self._mi(dev.ip)
            if dev.is_gateway:
                ip_label += " 🌐"
            elif dev.is_self:
                ip_label += " ⭐"
            ip_text = Text(ip_label)
            if dev.is_self:
                ip_text.stylize("bold green")
            elif dev.is_gateway:
                ip_text.stylize("bold magenta")
            elif dev.status == "online":
                ip_text.stylize("cyan")

            # ตัดข้อความตามความกว้างคอลัมน์ปัจจุบัน (ยืด/หดตามจอผ่าน _fit_columns)
            cw = self._col_w
            w_vendor = max(6, cw.get("ยี่ห้อ", 12) - 1)
            w_host = max(6, cw.get("ชื่อเครื่อง", 8) - 1)
            w_model = max(8, cw.get("รุ่น", 12) - 1)

            vendor_raw = _short(dev.vendor, w_vendor, placeholder="Unknown")
            if getattr(dev, 'is_randomized', False) and "🔒" not in vendor_raw and "Private" not in vendor_raw:
                vendor_raw = "🔒 " + vendor_raw
                vendor_raw = _short(vendor_raw, w_vendor, placeholder="Unknown")
            vendor_text = Text(vendor_raw)
            if "Private" in dev.vendor or "Randomized" in dev.vendor or getattr(dev, 'is_randomized', False):
                vendor_text.stylize("yellow")
            elif "Apple" in dev.vendor:
                vendor_text.stylize("bold white")
            elif "Samsung" in dev.vendor or "Xiaomi" in dev.vendor or "China Dragon" in dev.vendor:
                vendor_text.stylize("yellow")
            elif "Intel" in dev.vendor or "Realtek" in dev.vendor:
                vendor_text.stylize("dim")

            hostname_raw = _short(self._mt(dev.hostname), w_host)
            hostname_text = Text(hostname_raw)
            if dev.hostname and dev.hostname != "-":
                hostname_text.stylize("bold cyan" if getattr(dev, 'is_randomized', False) else "white")
            else:
                hostname_text.stylize("dim")

            model_text = Text(_short(dev.model, w_model))
            if "มือถือ" in dev.model or "Phone" in dev.model:
                model_text.stylize("bold cyan")
            elif dev.model != "Unknown Device" and "Unknown" not in dev.model:
                model_text.stylize("green")
            else:
                model_text.stylize("dim")

            # สถานะสั้นๆ — GW/YOU อยู่คอลัมน์ IP แล้ว, 🆕 ถ้าเจอครั้งแรกในรอบนี้
            status_text = Text()
            if dev.status == "online":
                status_text.append("🟢 on", style="green")
            else:
                status_text.append("🔴 off", style="red")
            if getattr(dev, 'is_new', False):
                status_text.append(" 🆕", style="bold yellow")
            elif getattr(dev, 'is_randomized', False):
                status_text.append(" 🔒", style="yellow")

            if dev.latency_ms is not None:
                latency = f"{dev.latency_ms:.0f}ms"
                if getattr(dev, 'ttl', None):
                    latency += f"/{dev.ttl}"
            elif getattr(dev, 'ttl', None):
                latency = f"TTL{dev.ttl}"
            else:
                latency = "-"
            latency_text = Text(latency, style="yellow" if dev.latency_ms is not None and dev.latency_ms < 50 else "white")

            type_text = Text(_short(dev.device_type, 10, placeholder="📦"))
            if "Phone" in dev.device_type:
                type_text.stylize("bold cyan")

            mac_raw = self._mm(dev.mac) or "-"
            if getattr(dev, 'is_randomized', False):
                mac_raw += "🔒"
            mac_text = Text(_short(mac_raw, 19), style="yellow" if getattr(dev, 'is_randomized', False) else "dim")
            # วาดเฉพาะคอลัมน์ที่ visible (จอแคบอาจซ่อนบางคอลัมน์ไว้)
            cells = {
                "#": str(idx),
                "IP": ip_text,
                "MAC": mac_text,
                "ยี่ห้อ": vendor_text,
                "ชื่อเครื่อง": hostname_text,
                "รุ่น": model_text,
                "ประเภท": type_text,
                "สถานะ": status_text,
                "Ping": latency_text,
            }
            try:
                table.add_row(*(cells[n] for n in self._visible))
            except Exception:
                # กัน visible ไม่ตรงกับคอลัมน์จริง (เช่น rebuild ไม่สำเร็จ) — วาดเท่าที่ได้
                try:
                    ncols = len(table.ordered_columns)
                    table.add_row(*([cells[n] for n in self._visible[:ncols]]))
                except Exception:
                    pass

        # คืนตำแหน่ง cursor/scroll ที่จำไว้
        try:
            if self.devices:
                ncols = max(1, len(table.ordered_columns))
                table.move_cursor(row=min(_crow, len(self.devices) - 1),
                                  column=min(_ccol, ncols - 1),
                                  animate=False, scroll=False)
        except Exception:
            pass
        try:
            table.scroll_to(x=_sx, y=_sy, animate=False)
        except Exception:
            pass

        self.update_topbar()
        self.update_detail()

    @work(exclusive=True, thread=True)
    def do_scan(self):
        self.is_scanning = True
        self.call_from_thread(self.update_topbar)

        info = self.network_info
        if not info:
            self.is_scanning = False
            return

        def progress(done, total, ip, ok):
            if done % 20 == 0 or done == total:
                try:
                    self.call_from_thread(lambda d=done, t=total, addr=ip, ok_=ok: self.query_one("#status_left", Static).update(f"⏳ สแกน {d}/{t} — {addr} {'✓' if ok_ else '·'}"))
                except Exception:
                    pass

        try:
            devices = scan_network(
                network_info=info,
                timeout_ms=700,
                max_workers=80,
                progress_cb=progress,
                do_hostname=True,
                lang=self.lang,
            )
            self._all_devices = devices
            self._scan_count += 1
            # เทียบประวัติ rogue-device (baseline/ใหม่/หาย/IP เปลี่ยน)
            try:
                from .history import check as history_check
                new, gone, changed, is_baseline = history_check(devices)
                self._sec_new = new
                self._sec_gone = gone
                self._sec_changed = changed
                self._sec_baseline = is_baseline
            except Exception:
                self._sec_new, self._sec_gone, self._sec_changed, self._sec_baseline = [], [], [], False
        except Exception as e:
            self.call_from_thread(lambda err=str(e): self.notify(t("scan_failed", self.lang, e=err), severity="error", timeout=5))
            # ไม่ล้าง _all_devices — เก็บผลสแกนครั้งก่อนไว้ดูต่อ
        finally:
            self.is_scanning = False
            self.call_from_thread(self.update_table)
            self.call_from_thread(self._notify_scan_done)

    def _notify_scan_done(self):
        """แจ้งผลสแกน + สรุป security (baseline/ใหม่/หาย/IP เปลี่ยน) + สภาพเครือข่าย"""
        try:
            lang = self.lang
            info = self.network_info
            # วงใหญ่ (มหาลัย/หอพัก /16): บอกว่าสแกนแค่รอบตัว
            try:
                if info and getattr(info, "scanned_cidr", "") and getattr(info, "total_hosts", 0) > 512:
                    self.notify(t("net_big", lang, orig=info.cidr, n=info.total_hosts, cidr=info.scanned_cidr), timeout=6)
            except Exception:
                pass
            # เจอแค่ตัวเอง+gateway (หรือน้อยกว่านั้น): สงสัย Client Isolation
            try:
                online_n = sum(1 for d in (self._all_devices or []) if getattr(d, "status", "") == "online")
                if self._all_devices and online_n <= 2:
                    self.notify(t("net_isolation", lang, n=online_n), timeout=6)
            except Exception:
                pass
            if getattr(self, "_sec_baseline", False) and self._all_devices:
                self.notify(t("sec_baseline", lang, n=len(self._all_devices)), timeout=5)
                return
            msgs = []
            new = getattr(self, "_sec_new", []) or []
            gone = getattr(self, "_sec_gone", []) or []
            changed = getattr(self, "_sec_changed", []) or []
            if new:
                ips = ", ".join(d.ip for d in new[:3]) + ("…" if len(new) > 3 else "")
                msgs.append(t("sec_new", lang, n=len(new), ips=ips))
            if gone:
                ips = ", ".join(g.get("ip", "?") for g in gone[:3]) + ("…" if len(gone) > 3 else "")
                msgs.append(t("sec_gone", lang, n=len(gone), ips=ips))
            if changed:
                pairs = ", ".join(f"{c['device'].ip} ({c['old_ip']}→{c['new_ip']})" for c in changed[:3])
                if len(changed) > 3:
                    pairs += "…"
                msgs.append(t("sec_changed", lang, n=len(changed), pairs=pairs))
            if msgs:
                for m in msgs:
                    self.notify(m, severity="warning" if gone or changed else "information", timeout=6)
            else:
                self.notify(t("scan_done", lang, n=len(self._all_devices)), timeout=3)
        except Exception:
            pass

    def action_scan(self):
        if self.is_scanning:
            self.notify(t("scan_busy", self.lang), severity="warning")
            return
        self.notify(t("scan_started", self.lang), timeout=2)
        self.do_scan()

    def action_alias(self):
        dev = self.get_selected_device()
        if not dev:
            self.notify(t("alias_no_dev", self.lang), severity="warning")
            return
        if dev.is_gateway:
            self.notify(t("alias_no_gw", self.lang), severity="warning")
            return
        # เปิดหน้าตั้งชื่อ
        from textual.screen import ModalScreen
        lg = self.lang

        class AliasScreen(ModalScreen):
            CSS = """
            AliasScreen {
                align: center middle;
            }
            #alias_dialog {
                width: 70;
                height: 18;
                border: thick $primary;
                background: $surface;
                padding: 1 2;
            }
            #alias_dialog Label {
                height: 1;
                color: $text;
            }
            Input {
                margin: 1 0;
            }
            """

            def __init__(self, device: Device):
                super().__init__()
                self.device = device

            def compose(self):
                with Vertical(id="alias_dialog"):
                    yield Static(f"[bold cyan]{t('alias_title', lg)}[/] — {self.device.ip}  {self.device.mac or ''}", markup=True)
                    yield Static(f"[dim]{t('alias_sub', lg, vendor=self.device.vendor, model=self.device.model)}[/]", markup=True)
                    yield Label(t("alias_name", lg))
                    yield Input(value=self.device.hostname if self.device.hostname != "-" else "", placeholder=t("alias_name_ph", lg), id="alias_name")
                    yield Label(t("alias_model", lg))
                    yield Input(value=self.device.model if "Unknown" not in self.device.model and "Private" not in self.device.model else "", placeholder=t("alias_model_ph", lg), id="alias_model")
                    with Horizontal():
                        yield Button(t("alias_save", lg), variant="primary", id="save")
                        yield Button(t("alias_delete", lg), variant="warning" if self.device.hostname != "-" else "default", id="delete")
                        yield Button(t("alias_cancel", lg), variant="error", id="cancel")
                    yield Static(f"[dim]{t('alias_tip', lg)}[/]", markup=True)

            def on_button_pressed(self, event: Button.Pressed):
                name_inp = self.query_one("#alias_name", Input)
                model_inp = self.query_one("#alias_model", Input)
                if event.button.id == "save":
                    self.dismiss((name_inp.value.strip(), model_inp.value.strip(), "save"))
                elif event.button.id == "delete":
                    self.dismiss(("", "", "delete"))
                else:
                    self.dismiss(None)

            def on_input_submitted(self, event: Input.Submitted):
                name_inp = self.query_one("#alias_name", Input)
                model_inp = self.query_one("#alias_model", Input)
                self.dismiss((name_inp.value.strip(), model_inp.value.strip(), "save"))

        def handle_result(result):
            if result is None:
                return
            name, model, action = result
            if action == "delete":
                try:
                    save_alias(dev.mac, "", "")
                    self.notify(t("alias_deleted", self.lang, ip=dev.ip), timeout=3)
                    # อัปเดตในหน่วยความจำเลย
                    for d in self._all_devices:
                        if d.mac == dev.mac:
                            d.hostname = "-"
                            d.model = "Unknown Device"
                            d.device_type = "📦 Device"
                    self.update_table()
                except Exception as e:
                    self.notify(t("alias_delete_fail", self.lang, e=e), severity="error")
                return
            # save
            if not name and not model:
                self.notify(t("alias_need_input", self.lang), severity="warning")
                return
            try:
                save_alias(dev.mac, name, model)
                # อัปเดตหน่วยความจำทันทีโดยไม่ต้องสแกนใหม่
                for d in self._all_devices:
                    if d.mac == dev.mac:
                        if name:
                            d.hostname = name
                        if model:
                            d.model = model
                            # เดาประเภทใหม่
                            from .oui import guess_device_type
                            d.device_type = guess_device_type(d.vendor, model, name or d.hostname)
                        else:
                            # ถ้าไม่ได้ใส่รุ่น ให้คงรุ่นเดิม
                            pass
                        # ถ้าตั้งชื่อแล้ว ให้ถือว่าไม่ใช่ Unknown
                        d.is_randomized = False if name else d.is_randomized
                self.update_table()
                self.notify(t("alias_saved", self.lang, ip=dev.ip, name=name or dev.hostname, model=model or dev.model), timeout=4)
            except Exception as e:
                self.notify(t("alias_save_fail", self.lang, e=e), severity="error")

        self.push_screen(AliasScreen(dev), handle_result)

    def action_filter(self):
        if self.filter_text:
            self.filter_text = ""
            self.update_table()
            self.notify(t("filter_cleared", self.lang), timeout=2)
            return
        from textual.widgets import Input
        lg = self.lang
        def _ask_filter():
            from textual.screen import ModalScreen
            class FilterScreen(ModalScreen):
                CSS = """
                FilterScreen {
                    align: center middle;
                }
                #dialog {
                    width: 60;
                    height: 11;
                    border: thick $primary;
                    background: $surface;
                    padding: 1 2;
                }
                #dialog Label {
                    height: 1;
                    color: $text;
                }
                Input {
                    margin: 1 0;
                }
                """
                def compose(self):
                    with Vertical(id="dialog"):
                        yield Label(t("filter_title", lg))
                        yield Input(placeholder=t("filter_ph", lg), id="filter_input")
                        with Horizontal():
                            yield Button(t("filter_ok", lg), variant="primary", id="ok")
                            yield Button(t("filter_clear", lg), variant="default", id="clear")
                            yield Button(t("filter_cancel", lg), variant="error", id="cancel")
                def on_button_pressed(self, event: Button.Pressed):
                    inp = self.query_one("#filter_input", Input)
                    if event.button.id == "ok":
                        self.dismiss(inp.value.strip())
                    elif event.button.id == "clear":
                        self.dismiss("")
                    else:
                        self.dismiss(None)
                def on_input_submitted(self, event: Input.Submitted):
                    self.dismiss(event.value.strip())
            def handle_result(result):
                if result is None:
                    return
                self.filter_text = result
                self.update_table()
                if result:
                    self.notify(t("filter_applied", self.lang, f=result, n=len(self.devices)), timeout=3)
            self.push_screen(FilterScreen(), handle_result)
        _ask_filter()

    def action_sort(self):
        keys = ["ip", "vendor", "hostname", "type", "latency"]
        try:
            idx = keys.index(self._sort_key)
            self._sort_key = keys[(idx + 1) % len(keys)]
            self._sort_reverse = False
        except Exception:
            self._sort_key = "ip"
            self._sort_reverse = False
        self._notify_sort()
        self.update_table()

    def action_sort_reverse(self):
        """Shift+S — สลับน้อย→มาก / มาก→น้อย โดยไม่เปลี่ยนคอลัมน์"""
        self._sort_reverse = not self._sort_reverse
        self._notify_sort()
        self.update_table()

    def _notify_sort(self):
        names = {
            "ip": t("sort_ip", self.lang),
            "vendor": t("sort_vendor", self.lang),
            "hostname": t("sort_hostname", self.lang),
            "type": t("sort_type", self.lang),
            "latency": t("sort_latency", self.lang),
        }
        arrow = " ↓" if self._sort_reverse else " ↑"
        self.notify(t("sort_notify", self.lang, name=names.get(self._sort_key, self._sort_key), arrow=arrow), timeout=2)

    def action_export(self):
        if not self._all_devices:
            self.notify(t("export_no_data", self.lang), severity="warning")
            return
        filename = f"network_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["#", "IP", "MAC", t("col_vendor", self.lang), t("col_hostname", self.lang), t("col_model", self.lang), t("col_type", self.lang), "Status", "Latency(ms)", "TTL", "Randomized", "Interface", "Gateway", "IsSelf"])
                for idx, d in enumerate(self._all_devices, 1):
                    w.writerow([
                        idx, d.ip, d.mac, d.vendor, d.hostname, d.model, d.device_type,
                        d.status, d.latency_ms if d.latency_ms is not None else "", getattr(d, 'ttl', '') or "", "YES" if getattr(d, 'is_randomized', False) else "",
                        d.interface, "GW" if d.is_gateway else "", "YOU" if d.is_self else ""
                    ])
            self.notify(t("export_ok", self.lang, f=filename), timeout=5)
        except Exception as e:
            self.notify(t("export_fail", self.lang, e=e), severity="error")

    def action_change_interface(self):
        if not self._infos or len(self._infos) <= 1:
            self.notify(t("iface_single", self.lang), severity="warning")
            return
        self._current_iface_index = (self._current_iface_index + 1) % len(self._infos)
        self.network_info = self._infos[self._current_iface_index]
        self.notify(t("iface_switched", self.lang, iface=self.network_info.interface, ip=self.network_info.local_ip), timeout=3)
        self.update_topbar()
        self.action_scan()

    def action_help(self):
        from textual.screen import ModalScreen
        lg = self.lang
        class HelpScreen(ModalScreen):
            CSS = """
            HelpScreen {
                align: center middle;
            }
            #help_dialog {
                width: 72;
                height: auto;
                max-height: 90%;
                border: round $primary;
                background: $surface;
                padding: 1 2;
            }
            """
            def compose(self):
                with Vertical(id="help_dialog"):
                    yield Static(f"[bold cyan]{t('help_title', lg)}[/]", markup=True)
                    yield Static(t("help_body", lg), markup=True)
                    yield Button(t("help_close", lg), variant="primary", id="close")
            def on_button_pressed(self, event):
                self.dismiss()
            def on_key(self, event):
                if event.key in ("escape", "q", "?"):
                    self.dismiss()
        self.push_screen(HelpScreen())

    @on(Click, "#appbar_left")
    def _click_globe_help(self) -> None:
        """คลิกไอคอน 🌐 มุมซ้ายบน → เปิด command palette (รวมคำสั่งทั้งหมด)"""
        try:
            self.action_command_palette()
        except Exception:
            pass

    def action_quit(self):
        self.exit()
