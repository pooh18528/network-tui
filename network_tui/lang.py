"""TH/EN language strings + persisted setting (settings.json ข้างๆ aliases.json)."""
import json
from pathlib import Path

SUPPORTED = ("th", "en")
_current = "en"  # ภาษาเริ่มต้น: อังกฤษ (กด L สลับเป็นไทยได้ จำค่าไว้ครั้งหน้า)


def _base_dir() -> Path:
    return Path(__file__).parent.parent


def settings_path() -> Path:
    return _base_dir() / "settings.json"


def load_lang() -> str:
    """อ่านภาษาที่จำไว้ (default อังกฤษ)"""
    global _current
    try:
        p = settings_path()
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            lang = str(data.get("lang", "en")).lower()
            if lang in SUPPORTED:
                _current = lang
    except Exception:
        pass
    return _current


def save_lang(lang: str) -> None:
    """จำภาษาไว้ใช้ครั้งหน้า"""
    global _current
    if lang not in SUPPORTED:
        return
    _current = lang
    try:
        settings_path().write_text(
            json.dumps({"lang": lang}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def set_current(lang: str) -> None:
    global _current
    if lang in SUPPORTED:
        _current = lang


def get_current() -> str:
    return _current


def other(lang: str) -> str:
    return "en" if lang == "th" else "th"


STRINGS = {
    "th": {
        "loading": "กำลังโหลดข้อมูลเครือข่าย...",
        "helpbar": "R สแกน · F กรอง · S เรียง · ⇧S กลับด้าน · E Export · I เปลี่ยนวง · N ตั้งชื่อ · L ภาษา · Q ออก · ? ช่วย",
        "state_scanning": "⏳ สแกน...",
        "state_ready": "✓ พร้อม",
        "status_scanning": "⏳ สแกน {cidr} ...",
        "status_filter": "🔍 '{f}' → {n} รายการ",
        "status_selected": "✓ {now} · {ip}{lock} · N ตั้งชื่อ · ←/→ เลื่อน",
        "status_done": "✓ สแกน {now} · N ตั้งชื่อ",
        "sort_ip": "IP Address",
        "sort_vendor": "ยี่ห้อ",
        "sort_hostname": "ชื่อเครื่อง",
        "sort_type": "ประเภท",
        "sort_latency": "Latency",
        "sort_notify": "เรียงตาม: {name}{arrow}",
        "col_vendor": "ยี่ห้อ",
        "col_hostname": "ชื่อเครื่อง",
        "col_model": "รุ่น",
        "col_type": "ประเภท",
        "col_status": "สถานะ",
        "help_title": "Network-TUI — คู่มือ",
        "help_body": (
            "[yellow]คีย์ลัด:[/]\n"
            "  [bold]R[/] สแกนใหม่  [bold]F//[/] กรอง  [bold]S[/] เรียง  [bold]⇧S[/] กลับด้าน\n"
            "  [bold]N[/] ตั้งชื่อที่เลือก  [bold]E[/] Export  [bold]I[/] สลับวง\n"
            "  [bold]L[/] สลับภาษา ไทย/English  [bold]Q[/] ออก\n"
            "  [bold]←/→[/] เลื่อนตารางแนวนอน  [bold]↑/↓[/] เลือกแถว\n"
            "\n"
            "[yellow]ตั้งชื่อ:[/] เลือกแถว → [bold]N[/] → ใส่ชื่อ/รุ่น → Enter\n"
            "  🔒 Private MAC: ปิดสุ่ม MAC บนมือถือจะเห็นยี่ห้อจริง\n"
            "\n"
            "[dim]Tip: รันเป็น Administrator ได้ Hostname ครบกว่า[/]"
        ),
        "help_close": "ปิด (Esc)",
        "alias_title": "ตั้งชื่ออุปกรณ์",
        "alias_sub": "ยี่ห้อ: {vendor} | รุ่นปัจจุบัน: {model}",
        "alias_name": "ชื่อเล่น / Hostname (เช่น มือถือแม่, iPad ลูก, ทีวีห้องนั่งเล่น):",
        "alias_name_ph": "เช่น มือถือแม่",
        "alias_model": "รุ่น / Model (เช่น iPhone 14, OPPO A78, Samsung A54):",
        "alias_model_ph": "เช่น iPhone 14 หรือปล่อยว่างให้เดาอัตโนมัติ",
        "alias_save": "บันทึก",
        "alias_delete": "ลบชื่อ",
        "alias_cancel": "ยกเลิก",
        "alias_tip": "Tip: กด Enter เพื่อบันทึก | ลบชื่อ = ล้างแล้วสแกนใหม่จะกลับเป็นอัตโนมัติ",
        "filter_title": "🔍 กรองอุปกรณ์ (พิมพ์ IP / MAC / ยี่ห้อ / ชื่อเครื่อง / รุ่น):",
        "filter_ph": "เช่น 192.168.1 , samsung, iphone, xiaomi ...",
        "filter_ok": "ตกลง",
        "filter_clear": "ล้าง",
        "filter_cancel": "ยกเลิก",
        "filter_cleared": "ล้างตัวกรองแล้ว",
        "filter_applied": "กรอง: '{f}' — พบ {n} รายการ",
        "export_no_data": "ไม่มีข้อมูลให้ export",
        "export_ok": "✅ Export สำเร็จ: {f}",
        "export_fail": "Export ล้มเหลว: {e}",
        "iface_single": "มีแค่ 1 Interface",
        "iface_switched": "เปลี่ยนเป็น: {iface} ({ip})",
        "scan_busy": "กำลังสแกนอยู่...",
        "scan_started": "🚀 เริ่มสแกนเครือข่าย...",
        "scan_failed": "สแกนล้มเหลว: {e} (เก็บผลเก่าไว้)",
        "scan_done": "สแกนเสร็จ — พบ {n} อุปกรณ์ (กด N ตั้งชื่อ)",
        "alias_no_dev": "เลือกอุปกรณ์ในตารางก่อน (ใช้ลูกศรขึ้น/ลง)",
        "alias_no_gw": "ไม่ต้องตั้งชื่อ Router (Gateway)",
        "alias_deleted": "ลบชื่อ {ip} แล้ว — กด R สแกนใหม่",
        "alias_delete_fail": "ลบไม่สำเร็จ: {e}",
        "alias_need_input": "กรอกชื่อหรือรุ่นอย่างน้อย 1 อย่าง",
        "alias_saved": "บันทึก {ip} → {name} ({model}) แล้ว",
        "alias_save_fail": "บันทึกไม่สำเร็จ: {e}",
        "detail_title": "🔍 รายละเอียด",
        "detail_loading": "กำลังโหลด...",
        "detail_none": "ไม่มีข้อมูล\nใช้ ↑↓ เลือกแถว",
        "detail_scanning": "⏳ กำลังสแกน...\nรอสักครู่",
        "detail_vendor": "ยี่ห้อ",
        "detail_hostname": "ชื่อเครื่อง",
        "detail_model": "รุ่น",
        "detail_type": "ประเภท",
        "detail_status": "สถานะ",
        "detail_iface": "Interface",
        "detail_hint": "N ตั้งชื่อ · E Export",
        "detail_private": "🔒 Private MAC: ปิดสุ่ม MAC บนมือถือเพื่อเห็นยี่ห้อจริง",
        "narrow_tiny": "จอกว้าง {w} คอลัมน์ — แคบเกินไป ขยายหน้าต่างเพื่อใช้งาน (←/→ เลื่อนดู)",
        "narrow_hidden": "จอแคบ: ซ่อน {cols} — ขยายจอเพื่อดูครบ (←/→ เลื่อน)",
        "lang_switched": "เปลี่ยนภาษา: English (กด L สลับกลับ)",
        "sec_baseline": "📌 จำอุปกรณ์ {n} เครื่องเป็น baseline แล้ว — รอบหน้ามีเครื่องแปลกปลอมจะเตือน",
        "sec_new": "🆕 อุปกรณ์ใหม่ {n} เครื่อง: {ips}",
        "sec_gone": "⚠️ หายไปเกิน 24 ชม. {n} เครื่อง: {ips}",
        "sec_changed": "🔁 MAC เดิมแต่ IP เปลี่ยน {n} รายการ: {pairs}",
        "net_big": "🌐 วงใหญ่ {orig} ({n} hosts): สแกนเฉพาะ {cidr} รอบตัว + ที่ ARP รู้จัก",
        "net_isolation": "👻 เจอแค่ {n} เครื่อง — วงนี้อาจเปิด Client Isolation (eduroam/หอพักมักเป็น) หรืออุปกรณ์ปิด ping",
        "detail_first": "เจอครั้งแรก",
        "detail_last": "เจอล่าสุด",
        "model_phone_private": "มือถือ (Private MAC)",
        "model_tablet_private": "มือถือ / Tablet (Private MAC)",
        "model_linux_ttl": "อุปกรณ์ Linux/Android (TTL 64)",
        "model_win_ttl": "อุปกรณ์ Windows (TTL 128)",
        "cli_table_title": "ผลสแกน — พบ {n} อุปกรณ์ ({cidr})",
        "cli_col_no": "#",
        "cli_col_vendor": "ยี่ห้อ",
        "cli_col_hostname": "ชื่อเครื่อง",
        "cli_col_model": "รุ่น",
        "cli_col_type": "ประเภท",
        "cli_col_status": "สถานะ",
        "cli_private1": "🔒 พบ Private/Randomized MAC {n} เครื่อง — มือถือรุ่นใหม่สุ่ม MAC เพื่อความเป็นส่วนตัว",
        "cli_private2": "   วิธีดูรุ่นจริง: 1) บนมือถือ ปิดสุ่ม MAC: Wi-Fi > ชื่อ Wi-Fi > Private/สุ่ม MAC > ปิด > ต่อใหม่",
        "cli_private3": '   2) แก้ aliases.json: "C8:8A:D8:10:0D:30": {"name": "มือถือแม่", "model": "OPPO A78"} แล้วรันใหม่',
        "cli_exported": "✅ Export: {f}",
        "cli_tip1": "Tip: รัน python main.py เพื่อเปิดโหมด TUI แบบเต็ม",
        "cli_tip2": "     python main.py --help  ดูตัวเลือก",
        "cli_panel_title": "🌐 Network-TUI — CLI Mode",
        "cli_scanning": "กำลังสแกน {cidr} ...",
        "cli_no_iface": "ไม่พบ network interface",
    },
    "en": {
        "loading": "Loading network info...",
        "helpbar": "R Scan · F Filter · S Sort · ⇧S Reverse · E Export · I Switch net · N Rename · L ภาษา · Q Quit · ? Help",
        "state_scanning": "⏳ Scanning...",
        "state_ready": "✓ Ready",
        "status_scanning": "⏳ Scanning {cidr} ...",
        "status_filter": "🔍 '{f}' → {n} items",
        "status_selected": "✓ {now} · {ip}{lock} · N rename · ←/→ scroll",
        "status_done": "✓ Scanned {now} · N rename",
        "sort_ip": "IP Address",
        "sort_vendor": "Vendor",
        "sort_hostname": "Hostname",
        "sort_type": "Type",
        "sort_latency": "Latency",
        "sort_notify": "Sort by: {name}{arrow}",
        "col_vendor": "Vendor",
        "col_hostname": "Hostname",
        "col_model": "Model",
        "col_type": "Type",
        "col_status": "Status",
        "help_title": "Network-TUI — Help",
        "help_body": (
            "[yellow]Keys:[/]\n"
            "  [bold]R[/] Rescan  [bold]F//[/] Filter  [bold]S[/] Sort  [bold]⇧S[/] Reverse\n"
            "  [bold]N[/] Rename selected  [bold]E[/] Export  [bold]I[/] Switch network\n"
            "  [bold]L[/] Switch language ไทย/English  [bold]Q[/] Quit\n"
            "  [bold]←/→[/] Scroll table  [bold]↑/↓[/] Select row\n"
            "\n"
            "[yellow]Rename:[/] select row → [bold]N[/] → name/model → Enter\n"
            "  🔒 Private MAC: turn off MAC randomization on the phone to see the real vendor\n"
            "\n"
            "[dim]Tip: run as Administrator for complete hostnames[/]"
        ),
        "help_close": "Close (Esc)",
        "alias_title": "Rename device",
        "alias_sub": "Vendor: {vendor} | Current model: {model}",
        "alias_name": "Nickname / Hostname (e.g. Mom's phone, living-room TV):",
        "alias_name_ph": "e.g. Mom's phone",
        "alias_model": "Model (e.g. iPhone 14, OPPO A78, Samsung A54):",
        "alias_model_ph": "e.g. iPhone 14, or leave blank for auto-detect",
        "alias_save": "Save",
        "alias_delete": "Delete name",
        "alias_cancel": "Cancel",
        "alias_tip": "Tip: Enter to save | Delete clears back to auto-detect",
        "filter_title": "🔍 Filter devices (IP / MAC / vendor / hostname / model):",
        "filter_ph": "e.g. 192.168.1 , samsung, iphone, xiaomi ...",
        "filter_ok": "OK",
        "filter_clear": "Clear",
        "filter_cancel": "Cancel",
        "filter_cleared": "Filter cleared",
        "filter_applied": "Filter: '{f}' — {n} items",
        "export_no_data": "No data to export",
        "export_ok": "✅ Exported: {f}",
        "export_fail": "Export failed: {e}",
        "iface_single": "Only 1 interface",
        "iface_switched": "Switched to: {iface} ({ip})",
        "scan_busy": "Already scanning...",
        "scan_started": "🚀 Scanning network...",
        "scan_failed": "Scan failed: {e} (kept previous results)",
        "scan_done": "Scan done — {n} devices (press N to rename)",
        "alias_no_dev": "Select a device in the table first (↑/↓)",
        "alias_no_gw": "No need to rename the Router (Gateway)",
        "alias_deleted": "Cleared name for {ip} — press R to rescan",
        "alias_delete_fail": "Delete failed: {e}",
        "alias_need_input": "Enter a name or a model (at least one)",
        "alias_saved": "Saved {ip} → {name} ({model})",
        "alias_save_fail": "Save failed: {e}",
        "detail_title": "🔍 Details",
        "detail_loading": "Loading...",
        "detail_none": "No data\nUse ↑↓ to select a row",
        "detail_scanning": "⏳ Scanning...\nPlease wait",
        "detail_vendor": "Vendor",
        "detail_hostname": "Hostname",
        "detail_model": "Model",
        "detail_type": "Type",
        "detail_status": "Status",
        "detail_iface": "Interface",
        "detail_hint": "N rename · E Export",
        "detail_private": "🔒 Private MAC: turn off MAC randomization on the phone to see the real vendor",
        "narrow_tiny": "Width {w} cols — too narrow, enlarge the window (←/→ to scroll)",
        "narrow_hidden": "Narrow: hid {cols} — enlarge to see all (←/→ scroll)",
        "lang_switched": "Language: ไทย (press L to switch back)",
        "sec_baseline": "📌 Saved {n} devices as baseline — newcomers will be flagged next time",
        "sec_new": "🆕 {n} new device(s): {ips}",
        "sec_gone": "⚠️ {n} device(s) gone >24h: {ips}",
        "sec_changed": "🔁 Same MAC, new IP ({n}): {pairs}",
        "net_big": "🌐 Large network {orig} ({n} hosts): scanned nearby {cidr} + known ARP only",
        "net_isolation": "👻 Only {n} device(s) — this network may use Client Isolation (eduroam/dorms often do), or devices block ping",
        "detail_first": "First seen",
        "detail_last": "Last seen",
        "model_phone_private": "Phone (Private MAC)",
        "model_tablet_private": "Phone / Tablet (Private MAC)",
        "model_linux_ttl": "Linux/Android device (TTL 64)",
        "model_win_ttl": "Windows device (TTL 128)",
        "cli_table_title": "Scan results — {n} devices ({cidr})",
        "cli_col_no": "#",
        "cli_col_vendor": "Vendor",
        "cli_col_hostname": "Hostname",
        "cli_col_model": "Model",
        "cli_col_type": "Type",
        "cli_col_status": "Status",
        "cli_private1": "🔒 {n} Private/Randomized MACs — newer phones randomize MAC for privacy",
        "cli_private2": "   To see real models: 1) on the phone, turn off MAC randomization: Wi-Fi > network name > Private MAC > off > reconnect",
        "cli_private3": '   2) edit aliases.json: "C8:8A:D8:10:0D:30": {"name": "Mom phone", "model": "OPPO A78"} and rerun',
        "cli_exported": "✅ Exported: {f}",
        "cli_tip1": "Tip: run python main.py for the full TUI mode",
        "cli_tip2": "     python main.py --help  for options",
        "cli_panel_title": "🌐 Network-TUI — CLI Mode",
        "cli_scanning": "Scanning {cidr} ...",
        "cli_no_iface": "No network interface found",
    },
}


def t(key: str, lang: str = None, **kwargs) -> str:
    """ดึงข้อความตามภาษา ( + .format kwargs) — fallback ไทยถ้า key หาย"""
    lg = lang or _current
    pack = STRINGS.get(lg, STRINGS["th"])
    s = pack.get(key, STRINGS["th"].get(key, key))
    try:
        return s.format(**kwargs) if kwargs else s
    except Exception:
        return s
