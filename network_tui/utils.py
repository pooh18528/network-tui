import ipaddress
import math
import socket
import re
import subprocess
import platform
from typing import Optional


def build_ping_cmd(ip: str, timeout_ms: int = 800) -> list:
    """สร้างคำสั่ง ping ตาม OS — แยก test ได้โดยไม่ต้องรันจริง

    Windows : ping -n 1 -w <ms>
    macOS   : ping -c 1 -W <ms>      (-W หน่วยมิลลิวินาที)
    Linux   : ping -c 1 -W <วินาทีปัดขึ้น> (iputils รับเลขเต็มชัวร์สุด)
    OpenBSD : ping -c 1 -w <วินาทีปัดขึ้น> (ไม่มี -W)
    อื่นๆ   : แบบ Linux (BSD ส่วนใหญ่มี -w หรือ -W อย่างใดอย่างหนึ่ง — ลอง -w ก่อนแล้ว fallback ใน ping_once_with_ttl)
    """
    system = platform.system().lower()
    if "windows" in system:
        return ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    if "darwin" in system or "macos" in system:
        return ["ping", "-c", "1", "-W", str(max(1, int(timeout_ms))), ip]
    if "openbsd" in system:
        return ["ping", "-c", "1", "-w", str(max(1, math.ceil(timeout_ms / 1000.0))), ip]
    # Linux / FreeBSD / NetBSD / อื่นๆ: -W วินาที (ปัดขึ้น, อย่างน้อย 1)
    return ["ping", "-c", "1", "-W", str(max(1, math.ceil(timeout_ms / 1000.0))), ip]


def ip_to_int(ip: str) -> int:
    return int(ipaddress.IPv4Address(ip))


def int_to_ip(n: int) -> str:
    return str(ipaddress.IPv4Address(n))


def cidr_to_ips(cidr: str, max_hosts: int = 2048):
    """คืน list IP ทั้งหมดใน subnet (ไม่รวม network/broadcast ถ้า /24 ปกติจะรวมหมดเพื่อ ping)"""
    net = ipaddress.IPv4Network(cidr, strict=False)
    if net.num_addresses > max_hosts + 2:
        raise ValueError(f"subnet ใหญ่เกิน ({net.num_addresses} addresses) — รองรับสูงสุด ~{max_hosts}")
    return [str(ip) for ip in net.hosts()]


def get_cidr_from_ip_netmask(ip: str, netmask: str) -> str:
    try:
        net = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
        return str(net)
    except Exception:
        # netmask เป็น CIDR อยู่แล้ว
        if "/" in netmask:
            return netmask
        return f"{ip}/24"


def is_valid_ipv4(ip: str) -> bool:
    try:
        ipaddress.IPv4Address(ip)
        return True
    except:
        return False


MASK_CHAR = "•"


def mask_ip(ip: str) -> str:
    """ปกปิด IP สำหรับ screenshot/แชร์จอ — เก็บโครงสร้างจุดไว้: 192.168.1.105 -> •••.•••.•••.•••"""
    if not ip:
        return ip
    return re.sub(r"[0-9A-Za-z]", MASK_CHAR, ip)


def mask_mac(mac: str) -> str:
    """ปกปิด MAC — เก็บตัวคั่นไว้: C8:B6:D3:0E:C9:05 -> ••:••:••:••:••:••"""
    if not mac or mac.strip() in ("", "-"):
        return mac
    return re.sub(r"[0-9A-Fa-f]", MASK_CHAR, mac)


def mask_text(s: str) -> str:
    """ปกปิดข้อความทั่วไป (เช่น hostname) — คงความยาวไว้: มือถือหลัก -> •••••"""
    if not s or s.strip() in ("", "-"):
        return s
    return MASK_CHAR * len(s)


def normalize_mac(mac: str) -> str:
    """แปลง ff-ff-ff-ff-ff-ff หรือ ff:ff:ff:ff:ff:ff -> AA:BB:CC:DD:EE:FF"""
    if not mac or mac.strip() == "":
        return ""
    mac = mac.strip().lower().replace("-", ":").replace(".", ":")
    # handle cisco style 0000.1111.2222
    if mac.count(":") == 2 and len(mac.replace(":", "")) == 12:
        raw = mac.replace(":", "")
        mac = ":".join(raw[i:i+2] for i in range(0, 12, 2))
    parts = mac.split(":")
    if len(parts) == 6:
        try:
            return ":".join(f"{int(p, 16):02X}" for p in parts)
        except:
            return mac.upper()
    return mac.upper()


def is_randomized_mac(mac: str) -> bool:
    """เช็ค Private/Randomized MAC (Locally Administered bit)"""
    if not mac:
        return False
    try:
        clean = mac.replace(":", "").replace("-", "").replace(".", "")
        if len(clean) < 2:
            return False
        first_byte = int(clean[0:2], 16)
        return bool(first_byte & 0x02)
    except:
        return False


def ping_once(ip: str, timeout_ms: int = 800) -> tuple[bool, Optional[float]]:
    """ping 1 ครั้ง คืน (success, latency_ms) - รองรับ Windows/Unix (backward compat)"""
    ok, latency, _ttl = ping_once_with_ttl(ip, timeout_ms)
    return ok, latency


def ping_once_with_ttl(ip: str, timeout_ms: int = 800) -> tuple[bool, Optional[float], Optional[int]]:
    """ping 1 ครั้ง คืน (success, latency_ms, ttl) - รองรับ Windows/macOS/Linux/OpenBSD"""
    system = platform.system().lower()
    candidates = [build_ping_cmd(ip, timeout_ms)]
    # กันเหนียว: บาง BSD ไม่มี -W แต่มี -w (หรือกลับกัน) — ลองสลับ flag ถ้าคำสั่งแรก error ทันที
    if "windows" not in system and "darwin" not in system:
        alt = list(candidates[0])
        if "-W" in alt:
            alt[alt.index("-W")] = "-w"
            candidates.append(alt)
        elif "-w" in alt:
            alt[alt.index("-w")] = "-W"
            candidates.append(alt)

    for cmd in candidates:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_ms / 1000 + 4,
                                  encoding="utf-8", errors="replace")
        except Exception:
            continue
        out = (proc.stdout or "") + (proc.stderr or "")
        out_low = out.lower()
        # flag ผิด (invalid/illegal option, usage) และไม่มี ttl → ลองคำสั่งถัดไปทันที
        if "ttl=" not in out_low and (
            "invalid option" in out_low
            or "illegal option" in out_low
            or "unknown option" in out_low
            or "usage:" in out_low
        ):
            continue
        if proc.returncode == 0 and "ttl=" in out_low:
            # extract time — รองรับ "time=2ms", "time<1ms", "time=1.23 ms"
            latency = None
            ttl = None
            m = re.search(r"time[=<]\s*([\d.]+)", out, re.IGNORECASE)
            if m:
                try:
                    latency = float(m.group(1))
                except:
                    pass
            else:
                m2 = re.search(r"(\d+(?:\.\d+)?)\s*ms", out)
                if m2:
                    try:
                        latency = float(m2.group(1))
                    except:
                        pass
            # "<1ms" แปลว่าเร็วมาก — ปัดเป็น 0.5ms แทน None
            if latency is None and re.search(r"time\s*<\s*1\s*ms", out, re.IGNORECASE):
                latency = 0.5
            # extract TTL
            m_ttl = re.search(r"TTL[=\s]+(\d+)", out, re.IGNORECASE)
            if m_ttl:
                try:
                    ttl = int(m_ttl.group(1))
                except:
                    pass
            return True, latency, ttl
        # ping ไม่ติด (host down) — ไม่ลอง candidate ถัดไป (เสียเวลาเปล่า)
        return False, None, None
    # ลองครบทุก candidate แล้วยังไม่ได้ (เช่น โดน exception ทุกครั้ง)
    return False, None, None


def resolve_hostname(ip: str, timeout: float = 1.5, try_nbtstat: bool = True) -> str:
    """พยายาม resolve hostname หลายวิธี (ไม่แตะ global socket timeout)"""
    # 1. reverse DNS — ใช้ thread-safe ด้วยการ save/restore timeout เดิม
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        try:
            host, _, _ = socket.gethostbyaddr(ip)
            if host and host != ip:
                # ตัด .local หรือ domain ออกให้สั้น
                host = host.split(".")[0].strip()
                if host:
                    return host
        except:
            pass
    finally:
        try:
            socket.setdefaulttimeout(old_timeout)
        except:
            pass

    # 2. nbtscan / nbtstat (windows) — ช้า จึงให้ข้ามได้สำหรับ IP ที่ ping ไม่ติด
    if try_nbtstat and platform.system().lower() == "windows":
        try:
            proc = subprocess.run(["nbtstat", "-A", ip], capture_output=True, text=True, timeout=2,
                                   encoding="utf-8", errors="replace")
            out = proc.stdout or ""
            for line in out.splitlines():
                if "<00>" in line and "UNIQUE" in line:
                    parts = line.split()
                    if parts:
                        name = parts[0].strip()
                        if name and name != ip and name not in ("-", ""):
                            return name
        except:
            pass

    # 3. NetBIOS / mDNS ฝั่ง Unix (macOS/Linux/BSD) — best effort, ไม่มี lib เพิ่ม
    if try_nbtstat:
        sys = platform.system().lower()
        # 3a. nmblookup (samba) — เจอชื่อ Windows/Android ที่ตั้งแชร์ไฟล์ไว้
        for cmd in (["nmblookup", "-A", ip],):
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=2,
                                      encoding="utf-8", errors="replace")
                out = proc.stdout or ""
                # หาบรรทัด "<00> - ..." ที่ไม่ใช่ <GROUP>
                best = ""
                for line in out.splitlines():
                    if "<00>" in line and "<GROUP>" not in line:
                        parts = line.strip().split()
                        if parts:
                            name = parts[0].strip()
                            if name and name not in ("-", ip) and not name.startswith("#"):
                                best = name
                                break
                if best:
                    return best
            except Exception:
                pass
        # 3b. avahi-resolve (Linux mDNS) — เจอ .local ของ iPhone/Mac/IoT
        if "linux" in sys or "darwin" in sys or "macos" in sys or "bsd" in sys:
            for cmd in (["avahi-resolve", "-a", ip],):
                try:
                    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=2,
                                          encoding="utf-8", errors="replace")
                    out = (proc.stdout or "").strip()
                    # รูปแบบ: "192.168.1.5\tiphone-witcha.local"
                    if out and "\t" in out:
                        name = out.split("\t", 1)[1].strip()
                        name = re.sub(r"\.local\.?$", "", name, flags=re.IGNORECASE).split(".")[0]
                        if name and name != ip:
                            return name
                except Exception:
                    pass
        # 3c. dig -x (ถ้ามี) — reverse DNS ผ่าน DNS server ตรงๆ เผื่อ gethostbyaddr โดน timeout
        try:
            proc = subprocess.run(["dig", "+short", "-x", ip], capture_output=True, text=True, timeout=2,
                                  encoding="utf-8", errors="replace")
            out = (proc.stdout or "").strip().splitlines()
            if out:
                name = out[0].strip().rstrip(".").split(".")[0]
                if name and name != ip and re.match(r"^[A-Za-z0-9][A-Za-z0-9_-]*$", name):
                    return name
        except Exception:
            pass

    return ""


def mdns_resolve(ip: str, timeout: float = 1.0) -> str:
    """ลองค้นหาชื่อ mDNS ผ่าน zeroconf ถ้ามี (optional) — ไม่ error ถ้าไม่มี lib"""
    try:
        # ลอง import zeroconf แบบ optional
        from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
        # ใช้วิธีง่าย: ลอง reverse DNS แบบ mDNS โดยตรงผ่าน socket
        # แต่ Zeroconf ต้อง browse service ซึ่งช้า เราจะข้ามไปก่อน
        pass
    except ImportError:
        pass
    return ""


def get_local_hostname() -> str:
    try:
        return socket.gethostname()
    except:
        return ""


def format_bytes(b: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(b) < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


# ---------- สแกนเสริม: TCP + Hotspot ----------

#: พอร์ตยอดฮิตสำหรับ TCP probe — เจอแม้เครื่องปิด ping (มือถือ/Windows Firewall)
#: ลำดับสำคัญ: 445/139 (Windows แชร์ไฟล์), 80/443 (มือถือเปิด hotspot captive/tv),
#: 22 (linux), 53 (router DNS), 8080/8008/8000 (กล้อง/IoT/TV), 554 (กล้อง), 631 (printer)
DEFAULT_TCP_PORTS = (445, 139, 80, 443, 22, 53, 8080, 8008, 8000, 554, 631, 21)

#: Gateway ทั่วไปของมือถือ Hotspot — ใช้ auto-tune ให้สแกนดุกว่าเดิม
HOTSPOT_GATEWAYS = {
    "192.168.43.1",   # Android มาตรฐาน
    "192.168.49.1",   # Android ใหม่ / Samsung
    "192.168.48.1",
    "192.168.137.1",  # Windows ICS / USB tether
    "192.168.42.129", # USB tether บางรุ่น
    "172.20.10.1",    # iPhone Personal Hotspot
}


def is_hotspot_network(local_ip: str = "", gateway: str = "", cidr: str = "") -> bool:
    """เช็คว่าเป็นวง Hotspot มือถือไหม (จะได้สแกนแรงขึ้น + เตือนถูก)"""
    gw = (gateway or "").strip()
    if gw in HOTSPOT_GATEWAYS:
        return True
    lip = (local_ip or "").strip()
    # วง iPhone 172.20.10.0/28 และ Android 192.168.43/49/48 เกือบทั้งหมดคือ hotspot
    if lip.startswith("172.20.10.") or lip.startswith("192.168.43.") or lip.startswith("192.168.49."):
        return True
    if lip.startswith("192.168.48.") and (not cidr or "/24" in cidr or "/28" in cidr or "/29" in cidr):
        # วงเล็ก /24 ที่ gateway ลงท้าย .1 และ IP อยู่ในช่วง hotspot — เดาแบบเผื่อ
        if gw.endswith(".1"):
            return True
    return False


def tcp_probe_once(ip: str, ports=None, timeout_ms: int = 400) -> tuple:
    """ลอง TCP connect หลายพอร์ต คืน (alive, latency_ms, [open_ports]) — ไม่ต้องใช้ admin

    ใช้จับเครื่องที่ปิด ICMP (iPhone ล็อกจอ / Android Doze / Windows Firewall)
    แต่ยังเปิดพอร์ตไว้ (445/80/ฯลฯ) — ช้ากว่า ping นิดหน่อยแต่แม่นขึ้นมาก
    """
    import time
    if ports is None:
        ports = DEFAULT_TCP_PORTS
    timeout = max(0.15, timeout_ms / 1000.0)
    open_ports: list = []
    best_lat: Optional[float] = None
    for port in ports:
        t0 = time.perf_counter()
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            rc = s.connect_ex((ip, int(port)))
            dt = (time.perf_counter() - t0) * 1000.0
            if rc == 0:
                open_ports.append(int(port))
                if best_lat is None or dt < best_lat:
                    best_lat = dt
                # เจอพอร์ตแรกแล้วพอ — ไม่ต้องไล่ครบทุกพอร์ต (เร็วขึ้น 5-10x)
                # แต่ถ้าเป็นพอร์ตแรกๆ ที่เจอช้า ให้ลองต่ออีก 1 พอร์ตเผื่อ latency ดีกว่า? ไม่ — พอแล้ว
                break
        except Exception:
            continue
        finally:
            try:
                if s is not None:
                    s.close()
            except Exception:
                pass
    if open_ports:
        return True, (best_lat if best_lat is not None else 1.0), open_ports
    return False, None, []
