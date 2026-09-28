import asyncio
import subprocess
import socket
import platform
import re
import ipaddress
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Callable, Optional, Tuple

from .utils import (
    normalize_mac, ping_once, ping_once_with_ttl, resolve_hostname,
    get_cidr_from_ip_netmask, cidr_to_ips, is_randomized_mac as is_rand_utils
)
from .oui import lookup_vendor, guess_model, guess_device_type, is_randomized_mac
from .models import Device, NetworkInfo

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ---------- Alias handling ----------
def load_aliases() -> Dict[str, dict]:
    """โหลด aliases.json ถ้ามี — map MAC -> {name, model, type}"""
    candidates = []
    # 1. ไฟล์ข้างๆ scanner.py
    candidates.append(Path(__file__).parent.parent / "aliases.json")
    candidates.append(Path(__file__).parent.parent / "devices.json")
    # 2. cwd
    candidates.append(Path.cwd() / "aliases.json")
    candidates.append(Path.cwd() / "devices.json")
    # 3. ที่ตั้ง main.py
    try:
        import sys
        # ลองหาจาก sys.argv[0]
        candidates.append(Path(sys.argv[0]).parent / "aliases.json")
    except:
        pass

    for p in candidates:
        try:
            if p.exists() and p.is_file():
                data = json.loads(p.read_text(encoding="utf-8"))
                # normalize keys
                out = {}
                for k, v in data.items():
                    # ข้าม key ที่เริ่มด้วย _ (comment)
                    if k.startswith("_"):
                        continue
                    nk = normalize_mac(k)
                    if isinstance(v, str):
                        out[nk] = {"alias": v}
                    elif isinstance(v, dict):
                        out[nk] = v
                if out:
                    return out
        except Exception as e:
            print(f"alias load error {p}: {e}")
    return {}


def get_alias_for_mac(mac: str, alias_map: Dict[str, dict]) -> Optional[dict]:
    if not mac or not alias_map:
        return None
    nm = normalize_mac(mac)
    return alias_map.get(nm)


def _run_cmd(cmd: list, timeout: int = 5) -> str:
    """รันคำสั่งแบบทน encoding ภาษาไทย (cp874/cp1252/utf-8)"""
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout)
        raw = (proc.stdout or b"") + b"\n" + (proc.stderr or b"")
        if not raw.strip():
            return ""
        import locale
        for enc in (locale.getpreferredencoding(False) or "utf-8", "utf-8", "cp874", "cp1252", "tis-620"):
            try:
                return raw.decode(enc)
            except:
                continue
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def get_network_infos() -> List[NetworkInfo]:
    """ดึงข้อมูล interface ทั้งหมด (IPv4)"""
    infos: List[NetworkInfo] = []

    if HAS_PSUTIL:
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            gateways = {}
            # ลองดึง gateway จาก ipconfig / route
            gws = _get_gateways_psutil()
            for iface, snics in addrs.items():
                if iface.lower().startswith("loopback") or "loopback" in iface.lower():
                    continue
                # skip ที่ไม่มี address
                has_ipv4 = any(s.family == socket.AF_INET for s in snics)
                if not has_ipv4:
                    continue
                is_up = True
                if iface in stats:
                    is_up = stats[iface].isup
                if not is_up:
                    continue

                ipv4 = None
                netmask = None
                mac = ""
                for s in snics:
                    if s.family == socket.AF_INET:
                        ipv4 = s.address
                        netmask = s.netmask
                    elif s.family == psutil.AF_LINK:
                        mac = s.address

                if not ipv4 or ipv4.startswith("127."):
                    continue
                # ข้าม APIPA 169.254.x.x ถ้าไม่ใช่ interface หลัก
                if ipv4.startswith("169.254."):
                    continue

                cidr = get_cidr_from_ip_netmask(ipv4, netmask or "255.255.255.0")
                gw = gws.get(iface, "") or _get_gateway_for_ip(ipv4) or ""
                # ถ้า gateway ไม่ได้ผูกกับ iface ให้ลองหา default gateway
                if not gw:
                    gw = _get_default_gateway() or ""

                infos.append(NetworkInfo(
                    interface=iface,
                    local_ip=ipv4,
                    netmask=netmask or "255.255.255.0",
                    cidr=cidr,
                    gateway=gw,
                    mac=mac or "",
                ))
        except Exception as e:
            print(f"psutil error: {e}")

    # fallback: parse ipconfig (Windows) / ifconfig (Unix)
    if not infos:
        if platform.system().lower() == "windows":
            infos = _parse_ipconfig_fallback()
        else:
            infos = _parse_ifconfig_fallback()

    # ถ้ายังไม่มี psutil ให้เพิ่ม gateway กรณีไม่มี
    _route_gw, _route_iface = get_default_route()
    for info in infos:
        if not info.gateway:
            info.gateway = _route_gw or _get_gateway_for_ip(info.local_ip) or ""

    if len(infos) > 1:
        _default_iface = (_route_iface or "").lower()

        def score(info: NetworkInfo):
            name = (info.interface or "").lower()
            # วงของ default route มาก่อนเสมอ (ข้ามการเดาจากชื่อบน macOS ที่ en0 เป็นได้ทั้ง Wi-Fi/LAN)
            if _default_iface and name == _default_iface:
                return -1
            is_virtual = any(x in name for x in (
                "vmware", "virtualbox", "veth", "wsl", "docker", "hyper-v", "tailscale",
                "loopback", "vboxnet", "vmnet", "virbr", "bridge", "br-", "lxc",
                "tun", "tap", "ppp", "gif", "stf", "utun", "awdl", "llw", "anpi", "xhc",
            ))
            # ชื่อ interface จริงราย OS:
            #  Windows: Wi-Fi / Ethernet | macOS: en0..en9 | Linux: eth/wlan/wlp/enp/eno/ens
            #  BSD: em/re/igb/ix/iwn/iwx/ath/ral/rtw/bge
            is_physical = any(x in name for x in (
                "wi-fi", "wifi", "wireless", "wlan", "ethernet", "eth", "enp", "eno", "ens",
                "em", "re", "igb", "ixl", "ix", "iwn", "iwx", "ath", "ral", "rtw", "bge",
                "wlp", "lan",
            ))
            if is_virtual:
                return 10
            if is_physical:
                if info.local_ip.startswith("192.168.1.") or info.local_ip.startswith("192.168.0."):
                    return 0
                return 1
            return 5
        infos.sort(key=score)

    return infos


def _get_gateways_psutil():
    """พยายามดึง gateway ต่อ interface (best effort)"""
    result = {}
    if platform.system().lower() != "windows":
        return result
    try:
        out = _run_cmd(["ipconfig"], timeout=5)
        current_iface = ""
        for line in out.splitlines():
            if "adapter" in line.lower():
                m = re.search(r"adapter (.+):", line, re.IGNORECASE)
                if m:
                    current_iface = m.group(1).strip()
            if "Default Gateway" in line and current_iface:
                ips = re.findall(r"\d+\.\d+\.\d+\.\d+", line)
                for ip in ips:
                    if not ip.startswith("0.0.0.0") and not ip.startswith("fe80"):
                        result[current_iface] = ip
                        break
    except:
        pass
    return result


def _parse_ipconfig_fallback() -> List[NetworkInfo]:
    infos = []
    try:
        out = _run_cmd(["ipconfig"], timeout=5)
        blocks = re.split(r"\r?\n\r?\n", out)
        for block in blocks:
            if "IPv4 Address" not in block:
                continue
            m_ip = re.search(r"IPv4 Address.*?:\s*(\d+\.\d+\.\d+\.\d+)", block)
            m_mask = re.search(r"Subnet Mask.*?:\s*(\d+\.\d+\.\d+\.\d+)", block)
            m_gw = re.search(r"Default Gateway.*?:\s*(\d+\.\d+\.\d+\.\d+)", block)
            m_iface = re.search(r"adapter (.+):", block, re.IGNORECASE)
            if not m_ip:
                continue
            ip = m_ip.group(1)
            if ip.startswith("127.") or ip.startswith("169.254."):
                continue
            netmask = m_mask.group(1) if m_mask else "255.255.255.0"
            gw = m_gw.group(1) if m_gw else ""
            iface = m_iface.group(1).strip() if m_iface else "Unknown"
            cidr = get_cidr_from_ip_netmask(ip, netmask)
            infos.append(NetworkInfo(interface=iface, local_ip=ip, netmask=netmask, cidr=cidr, gateway=gw))
    except Exception as e:
        print(f"ipconfig parse error: {e}")
    return infos


def _hex_netmask_to_dotted(hexmask: str) -> str:
    """0xffffff00 -> 255.255.255.0 (ifconfig บน macOS/BSD)"""
    try:
        h = hexmask.strip().lower().removeprefix("0x")
        n = int(h, 16)
        return ".".join(str((n >> s) & 0xFF) for s in (24, 16, 8, 0))
    except Exception:
        return "255.255.255.0"


def _parse_ifconfig_fallback() -> List[NetworkInfo]:
    """fallback กรณีไม่มี psutil บน macOS/Linux/BSD — parse `ifconfig`"""
    infos = []
    try:
        out = _run_cmd(["ifconfig"], timeout=5)
        if not out.strip():
            return infos
        gw, _iface = get_default_route()
        # แยกเป็นบล็อกต่อ interface (บรรทัดไม่ขึ้นต้นด้วยช่องว่าง = ชื่อ interface)
        blocks = re.split(r"(?m)^(?=\S)", out)
        for block in blocks:
            m_iface = re.match(r"^([^\s:]+)", block)
            if not m_iface:
                continue
            iface = m_iface.group(1).strip()
            if iface.startswith("lo"):
                continue
            for m_ip in re.finditer(r"\binet\s+(\d+\.\d+\.\d+\.\d+)\s+netmask\s+(\S+)", block):
                ip = m_ip.group(1)
                mask_raw = m_ip.group(2)
                if ip.startswith("127.") or ip.startswith("169.254."):
                    continue
                netmask = _hex_netmask_to_dotted(mask_raw) if mask_raw.lower().startswith("0x") else mask_raw
                m_mac = re.search(r"\bether\s+([0-9a-fA-F:]{17}|(?:[0-9a-fA-F]{1,2}:){5}[0-9a-fA-F]{1,2})", block)
                mac = normalize_mac(m_mac.group(1)) if m_mac else ""
                cidr = get_cidr_from_ip_netmask(ip, netmask)
                infos.append(NetworkInfo(interface=iface, local_ip=ip, netmask=netmask,
                                         cidr=cidr, gateway=gw, mac=mac))
    except Exception as e:
        print(f"ifconfig parse error: {e}")
    return infos


def get_default_route() -> Tuple[str, str]:
    """หา default route -> (gateway, interface) รองรับ Windows/macOS/Linux/OpenBSD

    Windows : parse `ipconfig` หา Default Gateway
    Linux   : `ip route show default` -> `default via X dev Y`
    macOS   : `route -n get default` -> `gateway: X` + `interface: Y`
    OpenBSD : `route -n get default` ก่อน, ไม่ได้ค่อย `netstat -rn` / `route -n show -inet`
    """
    system = platform.system().lower()
    try:
        if "windows" in system:
            out = _run_cmd(["ipconfig"], timeout=5)
            for line in out.splitlines():
                if "Default Gateway" in line:
                    ips = re.findall(r"\d+\.\d+\.\d+\.\d+", line)
                    for ip in ips:
                        if ip != "0.0.0.0" and not ip.startswith("fe80"):
                            return ip, ""
        elif "darwin" in system or "macos" in system:
            out = _run_cmd(["route", "-n", "get", "default"], timeout=5)
            gw, iface = "", ""
            for line in out.splitlines():
                m = re.match(r"\s*gateway:\s*(\d+\.\d+\.\d+\.\d+)", line)
                if m:
                    gw = m.group(1)
                m2 = re.match(r"\s*interface:\s*(\S+)", line)
                if m2:
                    iface = m2.group(1)
            if gw:
                return gw, iface
        elif "linux" in system:
            for cmd in (["ip", "route", "show", "default"], ["ip", "route"]):
                out = _run_cmd(cmd, timeout=5)
                m = re.search(r"default via (\d+\.\d+\.\d+\.\d+)(?:\s+dev\s+(\S+))?", out)
                if m:
                    return m.group(1), m.group(2) or ""
        else:
            # BSD (OpenBSD/FreeBSD/NetBSD) + อื่นๆ
            for cmd in (["route", "-n", "get", "default"], ["netstat", "-rn", "-f", "inet"], ["netstat", "-rn"]):
                out = _run_cmd(cmd, timeout=5)
                if not out.strip():
                    continue
                gw, iface = "", ""
                for line in out.splitlines():
                    mg = re.search(r"gateway:\s*(\d+\.\d+\.\d+\.\d+)", line)
                    if mg:
                        gw = mg.group(1)
                    mi = re.search(r"interface:\s*(\S+)", line)
                    if mi:
                        iface = mi.group(1)
                if gw:
                    return gw, iface
                # route show / netstat ตาราง: หาบรรทัด default
                for line in out.splitlines():
                    if re.match(r"\s*(default|0\.0\.0\.0)\s", line):
                        ips = re.findall(r"\d+\.\d+\.\d+\.\d+", line)
                        gw = next((x for x in ips[1:] if not x.startswith("0.0.0.0")), ips[0] if ips else "")
                        if not gw:
                            continue
                        toks = line.split()
                        last = toks[-1] if toks else ""
                        if re.fullmatch(r"[a-zA-Z]{2,}[0-9][a-zA-Z0-9_.:-]*", last):
                            iface = last
                        return gw, iface
    except Exception:
        pass
    return "", ""


def _get_default_gateway() -> str:
    """(backward compat) คืนแค่ gateway"""
    gw, _iface = get_default_route()
    return gw


def _get_gateway_for_ip(local_ip: str) -> str:
    try:
        parts = local_ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.1"
    except:
        return ""


def parse_arp_table() -> Dict[str, str]:
    """อ่าน arp -a -> {ip: mac} — รองรับ Windows/Linux/macOS/BSD

    Windows : `  192.168.1.1           c8-b6-d3-0e-c9-05     dynamic`
    Linux   : `? (192.168.1.1) at c8:b6:d3:0e:c9:05 [ether] on eth0`
    macOS   : `? (192.168.1.1) at 0:11:22:33:44:55 on en0 ifscope [ethernet]` (กลุ่มหลักเดียว!)
    OpenBSD : `? (192.168.1.1) at c8:b6:d3:0e:c9:05 on em0`
    """
    result = {}
    try:
        out = _run_cmd(["arp", "-a"], timeout=5)
        for line in out.splitlines():
            low = line.lower()
            # ข้ามรายการค้าง/ใช้ไม่ได้ (Linux/BSD: "at <incomplete>", "expired")
            # หมายเหตุ: "permanent" อย่างเดียวไม่ข้าม (static entry ที่ผู้ใช้ตั้งเองยังใช้งานได้)
            if "incomplete" in low or "expired" in low or "no entry" in low:
                continue
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F]{1,2}[:-]){5}[0-9a-fA-F]{1,2}\b", line)
            if m:
                ip = m.group(1)
                mac_raw = m.group(0).split(None, 1)[1]
                mac = normalize_mac(mac_raw)
                if not re.fullmatch(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", mac):
                    continue
                if mac in ("FF:FF:FF:FF:FF:FF", "00:00:00:00:00:00") or ip.startswith("224.") or ip.startswith("239.") or ip == "255.255.255.255":
                    continue
                result[ip] = mac
                continue
            m2 = re.search(r"\((\d+\.\d+\.\d+\.\d+)\) at ((?:[0-9a-fA-F]{1,2}[:-]){5}[0-9a-fA-F]{1,2})\b", line)
            if m2:
                ip = m2.group(1)
                mac = normalize_mac(m2.group(2))
                if not re.fullmatch(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", mac):
                    continue
                result[ip] = mac
    except Exception as e:
        print(f"arp error: {e}")
    return result


def ping_sweep(ips: List[str], max_workers: int = 64, timeout_ms: int = 700, progress_cb: Optional[Callable] = None) -> Dict[str, Tuple[Optional[float], Optional[int]]]:
    """ping ทุก IP แบบขนาน -> {ip: (latency_ms, ttl)} เฉพาะที่ตอบกลับ"""
    alive: Dict[str, Tuple[Optional[float], Optional[int]]] = {}
    total = len(ips)
    done = 0

    def task(ip):
        ok, latency, ttl = ping_once_with_ttl(ip, timeout_ms=timeout_ms)
        return ip, ok, latency, ttl

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(task, ip): ip for ip in ips}
        for fut in as_completed(futures):
            ip, ok, latency, ttl = fut.result()
            done += 1
            if progress_cb:
                try:
                    progress_cb(done, total, ip, ok)
                except:
                    pass
            if ok:
                alive[ip] = (latency if latency is not None else 0.0, ttl)
    return alive


def plan_scan_targets(cidr: str, local_ip: str, limit: int = 512) -> Tuple[object, object, bool]:
    """วางแผนสแกน: คืน (net_ที่จะping, net_ทั้งหมด, โดนย่อไหม)

    วงใหญ่ (เช่น /16 มหาลัย = 65k hosts) ping หมดไม่ไหว — ย่อเหลือ /24 รอบตัว
    แต่ยังเก็บ net ทั้งหมดไว้กรอง ARP (เครื่องที่ ARP รู้จักนอก /24 ก็ยังโชว์)
    """
    orig = ipaddress.IPv4Network(cidr, strict=False)
    if orig.num_addresses > limit:
        scan_net = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        return scan_net, orig, True
    return orig, orig, False


def scan_network(
    network_info: Optional[NetworkInfo] = None,
    timeout_ms: int = 700,
    max_workers: int = 80,
    progress_cb: Optional[Callable] = None,
    do_hostname: bool = True,
    lang: str = "th",
) -> List[Device]:
    """
    สแกนเครือข่าย:
    1. หา local network
    2. ping sweep ทั้ง subnet (เก็บ latency + TTL)
    3. อ่าน arp table
    4. resolve hostname + vendor + model (รวม TTL + alias + randomized)
    """

    if network_info is None:
        infos = get_network_infos()
        if not infos:
            raise RuntimeError("ไม่พบ network interface ที่ใช้งานได้")
        network_info = infos[0]

    cidr = network_info.cidr
    local_ip = network_info.local_ip
    gateway = network_info.gateway

    # โหลด alias
    alias_map = load_aliases()

    try:
        scan_net, orig_net, truncated = plan_scan_targets(cidr, local_ip)
        # ฝากข้อมูลให้ UI แจ้งเตือน (วงใหญ่/ย่อ)
        try:
            network_info.total_hosts = orig_net.num_addresses
            network_info.scanned_cidr = str(scan_net) if truncated else ""
        except Exception:
            pass
        cidr = str(scan_net)
        ips = [str(ip) for ip in scan_net.hosts()]
        if len(ips) > 1024:
            ips = ips[:1024]
    except Exception as e:
        raise RuntimeError(f"CIDR ไม่ถูกต้อง {cidr}: {e}")

    # 1. Ping sweep (ได้ latency + ttl)
    alive = ping_sweep(ips, max_workers=max_workers, timeout_ms=timeout_ms, progress_cb=progress_cb)

    # 2. เก็บ ARP (หลัง ping จะมีข้อมูลมากขึ้น)
    arp = parse_arp_table()

    all_ips = set(k for k in alive.keys()) | set(arp.keys())
    all_ips.add(local_ip)
    if gateway:
        all_ips.add(gateway)

    try:
        # กรองด้วยวงทั้งหมด (ไม่ใช่แค่วงที่ย่อ) — ARP ที่รู้จักนอก /24 ยังเก็บไว้
        net_obj = orig_net
        filtered = set()
        for ip in all_ips:
            try:
                if ipaddress.IPv4Address(ip) in net_obj:
                    filtered.add(ip)
            except:
                pass
        if len(filtered) >= 2:
            all_ips = filtered
    except:
        pass

    devices: List[Device] = []

    hostname_map: Dict[str, str] = {}
    if do_hostname:
        # nbtstat ช้า (Windows) — ใช้เฉพาะ IP ที่ ping ติด + gateway/self เท่านั้น
        # IP ที่เหลือใช้แค่ reverse DNS เร็วๆ ก็พอ
        def _resolve(ip: str) -> str:
            important = (ip in alive) or (ip == local_ip) or (ip == gateway)
            try:
                return resolve_hostname(ip, timeout=1.5, try_nbtstat=important) or ""
            except Exception:
                return ""
        with ThreadPoolExecutor(max_workers=20) as ex:
            futs = {ex.submit(_resolve, ip): ip for ip in all_ips}
            for fut in as_completed(futs):
                ip = futs[fut]
                try:
                    hostname_map[ip] = fut.result() or ""
                except:
                    hostname_map[ip] = ""

    for ip in sorted(all_ips, key=lambda x: tuple(map(int, x.split(".")))):
        mac = arp.get(ip, "")
        is_self = (ip == local_ip)
        if is_self and not mac and network_info.mac:
            try:
                mac = normalize_mac(network_info.mac)
            except:
                mac = network_info.mac

        # เช็ค alias ก่อน
        alias = get_alias_for_mac(mac, alias_map) if mac else None
        is_rand = is_randomized_mac(mac) if mac else False

        vendor = lookup_vendor(mac) if mac else "Unknown"
        hostname = hostname_map.get(ip, "")

        if is_self and not hostname:
            try:
                hostname = socket.gethostname()
            except:
                hostname = ""

        # ถ้า vendor Unknown แต่ hostname มีคำว่า iphone/samsung ให้เดา vendor
        if vendor in ("Unknown / Generic", "Unknown", "Private / Randomized"):
            h = hostname.lower()
            if "iphone" in h or "ipad" in h or "macbook" in h or "imac" in h:
                vendor = "Apple"
            elif "galaxy" in h or h.startswith("sm-"):
                vendor = "Samsung"
            elif "redmi" in h or "poco" in h or "xiaomi" in h:
                vendor = "Xiaomi"

        # เอา TTL มาช่วยเดารุ่น
        ttl = None
        latency = None
        if ip in alive:
            latency, ttl = alive[ip]
        # ถ้า gateway มี mac แต่ไม่มี ttl ให้เดา ttl 64 (router ส่วนใหญ่เป็น Linux)
        if ip == gateway and ttl is None and mac:
            ttl = 64
        if is_self and ttl is None:
            # TTL ตั้งต้นของเครื่องตัวเอง: Windows=128, macOS/Linux/BSD=64
            ttl = 128 if platform.system().lower() == "windows" else 64

        # ถ้ามี alias ให้ override
        if alias:
            # alias format: {"name": "Witcha iPhone", "model": "iPhone 15", "vendor": "Apple"}
            if alias.get("vendor"):
                vendor = alias["vendor"]
            if alias.get("name"):
                hostname = alias["name"]
            # model จะ override ด้านล่าง
            alias_model = alias.get("model")
            alias_type = alias.get("type")
        else:
            alias_model = None
            alias_type = None

        if alias_model:
            model = alias_model
        else:
            model = guess_model(hostname, vendor, mac, ttl, lang=lang)

        if alias_type:
            dtype = alias_type
        else:
            dtype = guess_device_type(vendor, model, hostname)

        # ถ้าเป็น Private MAC แต่ยังเป็น 📦 Device ให้บังคับเป็น Phone
        if is_rand and dtype == "📦 Device":
            # ถ้า TTL 64 เดาว่าเป็นมือถือ ถ้า 128 เป็น PC
            if ttl == 64 or ttl is None:
                dtype = "📱 Phone"

        # online = ping ติดจริง หรือเป็นเครื่องตัวเอง หรือ gateway ที่มี MAC
        # ARP อย่างเดียวแต่ ping ไม่ติด = offline (ARP ค้าง) — เดิมนับเป็น online ทำให้ตัวเลขหลอก
        if ip in alive or is_self:
            status = "online"
        elif ip == gateway and mac:
            status = "online"
            if latency is None:
                latency = 1.0
        elif mac:
            status = "offline"
        else:
            status = "offline"

        devices.append(Device(
            ip=ip,
            mac=mac,
            vendor=vendor,
            hostname=hostname,
            model=model,
            device_type=dtype,
            latency_ms=latency,
            ttl=ttl,
            status=status,
            is_gateway=(ip == gateway),
            is_self=is_self,
            interface=network_info.interface,
            is_randomized=is_rand,
        ))

    def sort_key(d: Device):
        if d.is_gateway:
            return (0, tuple(map(int, d.ip.split("."))))
        if d.is_self:
            return (1, tuple(map(int, d.ip.split("."))))
        if d.status == "online":
            return (2, tuple(map(int, d.ip.split("."))))
        return (3, tuple(map(int, d.ip.split("."))))

    devices.sort(key=sort_key)
    return devices


def get_all_network_infos_with_devices(progress_cb=None):
    infos = get_network_infos()
    return infos
