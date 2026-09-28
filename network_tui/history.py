"""จำอุปกรณ์ที่เคยเจอ (known_devices.json) + เทียบหาของใหม่/ของหาย — ฟีเจอร์ security.

- สแกนครั้งแรก = ตั้ง baseline (ไม่แจ้ง NEW รัว)
- เจอ MAC ใหม่ = is_new (เตือน 🆕)
- MAC ที่หายไปเกิน GONE_AFTER_HOURS = gone (เตือน ⚠️) — กัน flapping จากสแกนหลุดรอบเดียว
- ไฟล์เก็บข้างๆ aliases.json (ข้อมูลเครื่องตัวเอง ไม่ควร commit ขึ้น git)
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

from .utils import normalize_mac

GONE_AFTER_HOURS = 24


def _base_dir() -> Path:
    return Path(__file__).parent.parent


def history_path() -> Path:
    return _base_dir() / "known_devices.json"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_known() -> Dict[str, dict]:
    """โหลด {MAC: {first_seen, last_seen, ip, vendor, hostname, model}}"""
    try:
        p = history_path()
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def save_known(known: Dict[str, dict]) -> None:
    try:
        history_path().write_text(
            json.dumps(known, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def get_entry(mac: str) -> dict:
    """ดึงประวัติของ MAC เดียว (สำหรับแผงรายละเอียด)"""
    try:
        return load_known().get(normalize_mac(mac or ""), {}) or {}
    except Exception:
        return {}


def _parse_iso(s: str):
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def check(devices, now: datetime = None) -> Tuple[List, List, List, bool]:
    """เทียบผลสแกนกับประวัติ -> (new, gone, changed_ip, is_baseline)

    - new: MAC ไม่เคยเจอ (ตั้ง is_new=True ให้แล้ว)
    - gone: ไม่เจอในรอบนี้ และหายไปเกิน GONE_AFTER_HOURS
    - changed_ip: MAC เดิมแต่ IP เปลี่ยน (เช่น DHCP ย้าย / ARP spoofing เบื้องต้น)
    - is_baseline: สแกนครั้งแรก (ตั้งต้น ไม่แจ้ง NEW)
    """
    now = now or datetime.now()
    known = load_known()
    is_baseline = not bool(known)

    seen = {}
    changed = []
    for d in devices:
        mac = normalize_mac(getattr(d, "mac", "") or "")
        if not mac:
            continue
        seen[mac] = d
        try:
            d.is_new = False
        except Exception:
            pass
        entry = known.get(mac)
        if entry is None:
            known[mac] = {
                "first_seen": _now_iso(),
                "last_seen": _now_iso(),
                "ip": d.ip,
                "vendor": d.vendor,
                "hostname": d.hostname,
                "model": d.model,
            }
            if not is_baseline:
                try:
                    d.is_new = True
                except Exception:
                    pass
        else:
            prev_ip = (entry.get("ip") or "")
            if prev_ip and prev_ip != d.ip:
                # MAC เดิมแต่ IP เปลี่ยน — ปกติคือ DHCP ย้าย แต่ก็เป็นอาการ ARP spoofing ได้
                changed.append({"device": d, "old_ip": prev_ip, "new_ip": d.ip})
            entry["last_seen"] = _now_iso()
            entry["ip"] = d.ip
            entry["vendor"] = d.vendor
            entry["hostname"] = d.hostname
            entry["model"] = d.model

    new = [d for d in devices if getattr(d, "is_new", False)]

    gone = []
    for mac, entry in known.items():
        if mac in seen:
            continue
        last = _parse_iso(entry.get("last_seen", ""))
        if last and now - last > timedelta(hours=GONE_AFTER_HOURS):
            gone.append({"mac": mac, **entry})

    save_known(known)
    return new, gone, changed, is_baseline
