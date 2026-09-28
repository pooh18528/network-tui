from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Device:
    ip: str
    mac: str = ""
    vendor: str = "Unknown"
    hostname: str = ""
    model: str = "Unknown Device"
    device_type: str = "📦 Device"
    latency_ms: Optional[float] = None
    ttl: Optional[int] = None
    status: str = "online"  # online / offline
    is_gateway: bool = False
    is_self: bool = False
    interface: str = ""
    is_randomized: bool = False
    is_new: bool = False  # เจอครั้งแรกในรอบนี้ (rogue-device alert)

    @property
    def is_online(self) -> bool:
        return self.status == "online"

    def latency_label(self) -> str:
        # แบบกระชับ: "12ms/64" (จอแคบ) — CLI ขยายความในหัวคอลัมน์อยู่แล้ว
        if self.latency_ms is not None:
            s = f"{self.latency_ms:.0f}ms"
            if self.ttl:
                s += f"/{self.ttl}"
            return s
        if self.ttl:
            return f"TTL{self.ttl}"
        return "-"

    def status_label(self) -> str:
        base = "🟢 online" if self.status == "online" else "🔴 offline"
        if self.is_gateway:
            base += " 🌐GW"
        if self.is_self:
            base += " ⭐YOU"
        if self.is_new:
            base += " 🆕"
        elif self.is_randomized:
            base += " 🔒"
        return base

    def to_row(self):
        latency = f"{self.latency_ms:.0f} ms" if self.latency_ms is not None else "-"
        status_icon = "🟢" if self.status == "online" else "🔴"
        gw = " 🌐GW" if self.is_gateway else ""
        self_mark = " ⭐YOU" if self.is_self else ""
        return [
            self.ip,
            self.mac or "-",
            self.vendor,
            self.hostname or "-",
            self.model,
            self.device_type,
            f"{status_icon} {self.status}{gw}{self_mark}",
            latency,
        ]

    def to_dict(self):
        return {
            "ip": self.ip,
            "mac": self.mac,
            "vendor": self.vendor,
            "hostname": self.hostname,
            "model": self.model,
            "type": self.device_type,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "ttl": self.ttl,
            "is_randomized": self.is_randomized,
            "is_new": self.is_new,
            "is_gateway": self.is_gateway,
            "is_self": self.is_self,
            "interface": self.interface,
        }


@dataclass
class NetworkInfo:
    interface: str = ""
    local_ip: str = ""
    netmask: str = ""
    gateway: str = ""
    cidr: str = ""
    mac: str = ""
    public_ip: str = ""
    total_hosts: int = 0
    scanned_cidr: str = ""  # วงที่สแกนจริง (วงใหญ่อย่าง /16 จะย่อเหลือ /24 รอบตัว)
