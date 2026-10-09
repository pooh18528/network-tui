"""
OUI Vendor Database + Device Model Guess
- ฐานข้อมูลยี่ห้อจาก MAC prefix 6 หลักแรก
- เดารุ่น/ประเภทอุปกรณ์จาก vendor + hostname + TTL
"""

# ยี่ห้อหลักๆ ~300+ รายการ (6 hex ตัวแรกของ MAC)
OUI_DB = {
    # --- Network / Router ---
    "C8B6D3": "Fiberhome / 3BB Router",
    "A06720": "TP-Link",
    "A4CF12": "TP-Link / Kasa Smart",
    "50C7BF": "TP-Link",
    "60E327": "TP-Link",
    "F4EC38": "TP-Link",
    "EC089F": "TP-Link",
    "D46E0E": "TP-Link",
    "001A8F": "3COM",
    "001B11": "D-Link",
    "C4A81D": "D-Link",
    "1C7EE5": "D-Link",
    "BCF685": "D-Link",
    "784476": "Huawei",
    "E8CD2D": "Huawei",
    "04C06F": "Huawei",
    "00259E": "Huawei",
    "F48B32": "Huawei",
    "38BC1A": "Huawei",
    "485B39": "Huawei",
    "64A62F": "Huawei",
    "AC4122": "ZTE",
    "8C53CD": "ZTE",
    "4C09D4": "ZTE",
    "001F9F": "Thomson / Technicolor",
    "B0A7B9": "Fiberhome",
    "FCF5E3": "Fiberhome",
    "DCFE07": "Ubiquiti",
    "FC6551": "Ubiquiti",
    "788A20": "Ubiquiti",
    "247A4C": "Ubiquiti",
    "FC45C3": "Cisco",
    "00AABB": "Cisco",
    "001DE5": "Cisco",
    "C0FFD4": "Cisco Meraki",
    "D072DC": "ASUS",
    "2C56DC": "ASUS",
    "AC220B": "ASUS",
    "50465D": "ASUSTek",
    "107BEF": "ASUSTek",
    "188331": "ASUSTek",
    "7085C2": "ASUSTek",
    "001E8C": "ASUSTek",
    "C8D719": "Netgear",
    "A00460": "Netgear",
    "9CA3BA": "Netgear",
    "28C68A": "Netgear",

    # --- Apple ---
    "F0D1A9": "Apple",
    "A4B197": "Apple",
    "F437B8": "Apple",
    "A85CF0": "Apple",
    "D0C5D3": "Apple",
    "8C8590": "Apple",
    "AC87A3": "Apple",
    "BC9C31": "Apple",
    "88E9FE": "Apple",
    "F09CBE": "Apple",
    "3C0754": "Apple",
    "40A6D9": "Apple",
    "64B9E8": "Apple",
    "2CBE08": "Apple",
    "8C2DAA": "Apple",
    "0452C7": "Apple",
    "ACDE48": "Apple",
    "D8A25E": "Apple",
    "18F642": "Apple",
    "6034CB": "Apple",
    "B0E1AA": "Apple",
    "A4E9A3": "Apple",
    "F0B479": "Apple",
    "D4619D": "Apple",

    # --- Samsung ---
    "F47B09": "Samsung",
    "90B6D0": "Samsung",
    "D0C1B1": "Samsung",
    "787339": "Samsung",
    "649D99": "Samsung",
    "E4E0C5": "Samsung",
    "B05CB8": "Samsung",
    "001632": "Samsung",
    "C49DEE": "Samsung",
    "E8FDF7": "Samsung",
    "38AA3C": "Samsung",
    "A8029A": "Samsung",
    "C0F97C": "Samsung",
    "84BF3F": "Samsung",

    # --- Xiaomi / Redmi / POCO ---
    "64CC2E": "Xiaomi",
    "F48B93": "Xiaomi",
    "28E347": "Xiaomi",
    "7440BB": "Xiaomi",
    "78D753": "Xiaomi",
    "7C1DD9": "Xiaomi",
    "C4143C": "Xiaomi",
    "14F65A": "Xiaomi",
    "9426EF": "Xiaomi",
    "C88AD8": "China Dragon / Xiaomi",  # พบจริง 192.168.1.146
    "A45E60": "Xiaomi",
    "7CB03E": "Xiaomi",
    "28C1A7": "Xiaomi",

    # --- OPPO / vivo / OnePlus / Realme ---
    "9C2F9D": "OPPO",
    "38B45A": "OPPO",
    "E02A82": "OPPO",
    "848CAE": "vivo",
    "60D0A9": "vivo",
    "C8E7D8": "OnePlus",
    "9C9E63": "OnePlus",
    "E4AAEA": "Realme",
    "606D3C": "Realme",
    "1CC371": "OPPO",
    "B4E6CD": "OPPO",

    # --- Huawei Mobile ---
    "60569A": "Huawei Mobile",
    "20808C": "Huawei Mobile",
    "38B4F7": "Huawei Mobile",
    "10D07A": "Huawei Mobile",

    # --- Lenovo / Motorola ---
    "A4DB30": "Lenovo",
    "8C1645": "Lenovo",
    "E8B54D": "Lenovo",
    "000A3A": "Lenovo",
    "10A5D0": "Motorola",
    "04273C": "Motorola",

    # --- Dell / HP / Lenovo PC ---
    "F8BC12": "Dell",
    "D0D0FD": "Dell",
    "185A4D": "Dell",
    "1CC1DE": "Dell",
    "A41F72": "Dell",
    "98E7F4": "HP",
    "3C3556": "HP",
    "408B07": "HP",
    "941882": "HP",
    "8CB864": "HP",
    "E4115B": "Lenovo PC",
    "8CE55E": "Lenovo PC",
    "54EE75": "Lenovo PC",

    # --- Intel / Realtek / Qualcomm (PC NIC) ---
    "0016EA": "Intel",
    "A4BADB": "Intel",
    "3C5810": "Intel",
    "24B2B9": "Intel / Realtek (PC Wi-Fi)",
    "7CC2C6": "Intel",
    "001500": "Intel",
    "00E04C": "Realtek",
    "52A9E3": "Realtek",
    "E0D55E": "Realtek",
    "001365": "Realtek",
    "3C95A4": "Intel",
    "F4A4D4": "Qualcomm",
    "9CC431": "Qualcomm",

    # --- VMware / Virtual ---
    "000569": "VMware",
    "000C29": "VMware",
    "005056": "VMware",
    "00155D": "Hyper-V / Microsoft",
    "525400": "QEMU / KVM",
    "080027": "VirtualBox",

    # --- IoT / Smart ---
    "18B430": "Espressif (ESP8266/ESP32)",
    "24A160": "Espressif",
    "A020A6": "Espressif",
    "DC4F22": "Espressif",
    "B4E62D": "Espressif",
    "D8A011": "Espressif",
    "7CF5CD": "Espressif",
    "EC64C9": "Espressif",
    "FCF5C4": "Espressif",
    "B8F0B4": "Espressif",
    "D8B6BF": "Tuya Smart",
    "687CA6": "Tuya",
    "AC8555": "Midea",
    "70A66A": "Xiaomi IoT",

    # --- Printer ---
    "0017A4": "Brother",
    "308D99": "Brother",
    "3C2AF4": "Brother",
    "00BAEF": "Epson",
    "48D24D": "Epson",
    "0001E6": "Canon",
    "781DBA": "Canon",
    "AC1F6B": "Canon",

    # --- TV / Console ---
    "FC4499": "LG",
    "A8B8A7": "LG",
    "785441": "LG",
    "CC3A61": "LG",
    "001CDF": "Sony",
    "302303": "Sony",
    "04D3B5": "Sony PlayStation",
    "00DBDF": "Samsung TV",
    "E4E749": "Samsung TV",
    "001DD8": "Sony Bravia",
    "F8FFC2": "Xiaomi TV",

    # --- Google ---
    "F4F5D8": "Google",
    "64B0A6": "Google",

    # --- Amazon ---
    "FC65DE": "Amazon",
    "A002DC": "Amazon Echo",
    "8871A5": "Amazon",

    # --- Microsoft ---
    "7CE9D3": "Microsoft",

    # --- เพิ่มเติม: ชิปมือถือทั่วไป ---
    "E8502B": "China Mobile / Spreadtrum",
    "D05FB8": "Xiaomi / China Dragon",
    "3C71BF": "Espressif / IoT",
    "FCAA14": "Espressif",
    # --- ชิปมือถือ Mediatek/Unisoc/Apple-modem (เจอบ่อยในวง hotspot) ---
    "020470": "MediaTek / Xiaomi Hotspot",
    "0A7135": "MediaTek",
    "0C6160": "MediaTek",
    "7C2F80": "Samsung / MediaTek",
    "2EBAA9": "OPPO / MediaTek",
    "6AC1A6": "vivo / MediaTek",
    "8EA7D4": "Realme / MediaTek",
    "3641DF": "Unisoc / Spreadtrum",
    "B26EC4": "Unisoc",
    # --- USB tether / Virtual NIC (แชร์เน็ตผ่านสาย) ---
    "02050A": "Android USB Tether",
    "0221A9": "Android USB Tether",
    "3290CB": "iPhone USB Tether",
}

# เดา model จาก vendor + hostname pattern
MODEL_HINTS = {
    "iphone": "iPhone",
    "ipad": "iPad",
    "macbook": "MacBook",
    "imac": "iMac",
    "android": "Android Phone",
    "galaxy": "Samsung Galaxy",
    "sm-": "Samsung Galaxy",
    "samsung": "Samsung Galaxy",
    "redmi": "Redmi",
    "poco": "POCO",
    "m210": "Xiaomi Phone",
    "oppo": "OPPO Phone",
    "vivo": "vivo Phone",
    "realme": "realme Phone",
    "oneplus": "OnePlus Phone",
    "huawei": "Huawei Phone",
    "honor": "HONOR Phone",
    "nokia": "Nokia Phone",
    "pixel": "Google Pixel",
    "esp_": "ESP8266/ESP32 IoT",
    "tasmota": "Tasmota IoT",
    "shelly": "Shelly IoT",
    "mi-": "Xiaomi Device",
    "mibox": "Mi Box",
    "chromecast": "Chromecast",
    "nest": "Google Nest",
    "echo": "Amazon Echo",
    "alexa": "Amazon Echo",
    "printer": "Printer",
    "brother": "Brother Printer",
    "epson": "Epson Printer",
    "canon": "Canon Printer",
    "hp-": "HP Printer",
    "deskjet": "HP DeskJet",
    "laserjet": "HP LaserJet",
    "playstation": "PlayStation",
    "ps5": "PlayStation 5",
    "ps4": "PlayStation 4",
    "xbox": "Xbox",
    "nintendo": "Nintendo Switch",
    "switch": "Nintendo Switch",
    "lg-tv": "LG TV",
    "samsung-tv": "Samsung TV",
    "bravia": "Sony Bravia TV",
    "roku": "Roku TV",
    "desktop": "Windows PC",
    "laptop": "Windows Laptop",
    "thinkpad": "Lenovo ThinkPad",
    "inspiron": "Dell Inspiron",
    "pavilion": "HP Pavilion",
    "mac-": "Apple Mac",
    "anime": "PC / Laptop (anime)",
}


def is_randomized_mac(mac: str) -> bool:
    """เช็คว่าเป็น Private/Randomized MAC ไหม (Locally Administered bit = 1)
    iOS 14+, Android 10+, Windows 10+ สุ่ม MAC ต่อ SSID เพื่อความเป็นส่วนตัว
    """
    if not mac:
        return False
    try:
        clean = mac.replace(":", "").replace("-", "").replace(".", "")
        if len(clean) < 2:
            return False
        first_byte = int(clean[0:2], 16)
        return bool(first_byte & 0x02)  # bit 1 = locally administered
    except:
        return False


def lookup_vendor(mac: str) -> str:
    if not mac:
        return "Unknown"
    mac_clean = mac.replace(":", "").replace("-", "").upper()
    if len(mac_clean) < 6:
        return "Unknown"
    # ถ้าเป็น Randomized ให้บอกชัดเจน
    if is_randomized_mac(mac):
        oui = mac_clean[:6]
        real = OUI_DB.get(oui)
        if real:
            return f"{real} (Private?)"
        return "Private / Randomized"
    oui = mac_clean[:6]
    return OUI_DB.get(oui, "Unknown / Generic")


def guess_model(hostname: str, vendor: str, mac: str = "", ttl: int = None, lang: str = "th", open_ports=None) -> str:
    """เดารุ่นจาก hostname + vendor + mac + ttl + open_ports (lang: th/en เฉพาะข้อความภาษาไทย)"""
    from .lang import t
    h = (hostname or "").lower()
    v = (vendor or "").lower()
    is_rand = is_randomized_mac(mac) if mac else False
    ports = set(open_ports or [])

    # 0. ดูจาก open_ports ก่อน (แม่นสุดสำหรับเครื่องปิด ping แต่เปิดพอร์ต)
    # 445/139 = Windows แชร์ไฟล์เกือบชัวร์, 631 = Printer, 554 = กล้อง, 22 = Linux/Router
    if ports:
        if 631 in ports:
            return f"{vendor} Printer" if vendor not in ("Unknown / Generic", "Unknown", "Private / Randomized") else "Network Printer"
        if 554 in ports and not h:
            return "IP Camera"
        if (445 in ports or 139 in ports) and "printer" not in h and "canon" not in v and "epson" not in v and "brother" not in v:
            # Windows PC (มือถือไม่เปิด 445)
            if h and h not in ("-", ""):
                for hint, model in MODEL_HINTS.items():
                    if hint in h:
                        return model
            return "Windows PC (SMB)"
        if ports == {22} or (22 in ports and len(ports) == 1):
            if "router" in v or "ubiquiti" in v or "cisco" in v or ttl == 64:
                pass  # ปล่อยให้ logic vendor ด้านล่างตัดสิน (router/linux)
            elif not h:
                return "Linux Device (SSH)"

    # 1. ดูจาก hostname ก่อน (แม่นสุด)
    for hint, model in MODEL_HINTS.items():
        if hint in h:
            if vendor and vendor not in ("Unknown / Generic", "Unknown", "Private / Randomized") and vendor.lower() not in model.lower():
                return f"{vendor} {model}"
            return model

    # 2. ดูจาก vendor
    if "apple" in v:
        if "mac" in h or "macbook" in h:
            return "Apple Mac"
        return "Apple Device (iPhone/iPad/Mac)"
    if "samsung" in v:
        # Samsung ส่วนใหญ่เป็นมือถือ ถ้า TTL 64 ให้เป็น Phone
        if ttl == 64 or is_rand:
            return "Samsung Phone (Galaxy)"
        return "Samsung Device"
    if "xiaomi" in v or "china dragon" in v:
        # China Dragon ทำชิปให้ Xiaomi/POCO/Redmi — ส่วนใหญ่เป็นมือถือ
        if ttl == 64 or is_rand:
            return "Xiaomi Phone (Redmi/POCO)"
        if is_rand:
            return "Xiaomi/Redmi (Private MAC)"
        return "Xiaomi Device"
    if "huawei" in v:
        if ttl == 64 or is_rand:
            return "Huawei Phone"
        return "Huawei Device"
    if "oppo" in v:
        return "OPPO Phone"
    if "vivo" in v:
        return "vivo Phone"
    if "oneplus" in v:
        return "OnePlus Phone"
    if "realme" in v:
        return "realme Phone"
    if "tp-link" in v or "tplink" in v:
        return "TP-Link Device"
    if "asus" in v:
        return "ASUS Device"
    if "d-link" in v or "dlink" in v:
        return "D-Link Device"
    if "fiberhome" in v or "3bb" in v:
        return "Router / ONU (Fiberhome)"
    if "huawei" in v and "router" in v:
        return "Huawei Router"
    if "zte" in v:
        return "ZTE Router/ONU"
    if "cisco" in v:
        return "Cisco Device"
    if "ubiquiti" in v:
        return "Ubiquiti Device"
    if "espressif" in v or "esp" in v:
        return "IoT ESP32/ESP8266"
    if "tuya" in v:
        return "Tuya Smart IoT"
    if "vmware" in v:
        return "VMware VM"
    if "virtualbox" in v:
        return "VirtualBox VM"
    if "qemu" in v:
        return "QEMU/KVM VM"
    if "hyper-v" in v or ("microsoft" in v and "vm" in h):
        return "Hyper-V VM"
    if "dell" in v:
        return "Dell PC"
    if "hp" in v:
        return "HP PC/Printer"
    if "lenovo" in v:
        return "Lenovo PC"
    if "intel" in v or "realtek" in v or "qualcomm" in v:
        return "PC / Laptop (NIC)"
    if "brother" in v or "epson" in v or "canon" in v:
        return f"{vendor} Printer"

    # 3. ถ้าเป็น Private/Randomized MAC — มือถือรุ่นใหม่ 90% ใช้สุ่ม
    if is_rand or "private" in v or "randomized" in v:
        # ดู TTL เพื่อแยก Phone vs Laptop
        # TTL 64 = Linux/Android/iOS/macOS, 128 = Windows, 255 = Cisco/Unix
        if ttl == 64:
            return t("model_tablet_private", lang)
        if ttl == 128:
            return "PC / Laptop (Private MAC)"
        if ttl == 255:
            return "Network Device (Private MAC)"
        # ถ้าไม่มี TTL ให้เดาว่าเป็นมือถือ (พบบ่อยกว่า)
        return t("model_phone_private", lang)

    if vendor and vendor not in ("Unknown / Generic", "Unknown"):
        return vendor

    # สุดท้าย: ถ้าไม่มีข้อมูลเลย แต่ TTL บอก OS ได้
    if ttl == 64:
        return t("model_linux_ttl", lang)
    if ttl == 128:
        return t("model_win_ttl", lang)

    return "Unknown Device"


def guess_device_type(vendor: str, model: str, hostname: str) -> str:
    """เดาประเภทอุปกรณ์ -> icon + type"""
    text = f"{vendor} {model} {hostname}".lower()

    # Private MAC ที่เดาว่าเป็นมือถือ
    if "มือถือ" in model or "private mac" in model.lower():
        # ถ้า TTL 128 อาจเป็น PC แต่เราเดาไว้แล้วใน model
        if "มือถือ" in model:
            return "📱 Phone"
        if "pc" in model.lower() or "laptop" in model.lower():
            return "💻 Laptop"
        return "📱 Phone"

    if any(x in text for x in ["router", "onu", "fiberhome", "zte", "gateway", "ubiquiti", "meraki", "cisco", "tplink", "tp-link", "d-link", "asus router"]):
        return "🌐 Router"
    if any(x in text for x in ["iphone", "galaxy", "redmi", "poco", "oppo", "vivo", "realme", "oneplus", "pixel", "phone", "มือถือ", "huawei phone"]):
        return "📱 Phone"
    if any(x in text for x in ["ipad", "tablet"]):
        return "📱 Tablet"
    if any(x in text for x in ["macbook", "thinkpad", "inspiron", "pavilion", "laptop"]):
        return "💻 Laptop"
    if any(x in text for x in ["desktop", "pc", "windows pc"]):
        return "🖥️ PC"
    if any(x in text for x in ["apple", "mac"]):
        return "🍎 Apple"
    if any(x in text for x in ["tv", "bravia", "chromecast", "mibox", "roku"]):
        return "📺 TV"
    if any(x in text for x in ["printer", "brother", "epson", "canon", "deskjet", "laserjet"]):
        return "🖨️ Printer"
    if any(x in text for x in ["playstation", "xbox", "nintendo", "switch", "console"]):
        return "🎮 Console"
    if any(x in text for x in ["echo", "nest", "google home", "alexa"]):
        return "🔊 Smart Speaker"
    if any(x in text for x in ["esp", "tuya", "shelly", "iot", "tasmota"]):
        return "💡 IoT"
    if any(x in text for x in ["vmware", "virtualbox", "qemu", "hyper-v", "vm"]):
        return "🖥️ VM"
    return "📦 Device"
