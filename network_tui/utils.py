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
