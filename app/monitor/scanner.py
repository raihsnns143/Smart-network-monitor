"""
app/monitor/scanner.py
======================
Network scanning engine.

Strategies (auto-selected based on available permissions):
  1. ARP scan via Scapy  — most accurate, requires root/sudo
  2. Ping + ARP-cache    — works without root on most Linux/Mac
  3. Mock scan           — demo mode when no network privileges exist

MAC vendor lookup uses the locally bundled prefix table to avoid
any external API dependency.
"""
import os
import re
import json
import socket
import struct
import subprocess
import platform
import ipaddress
from datetime import datetime
from typing import List, Dict, Optional

# Optional imports — gracefully degrade if unavailable
try:
    from scapy.all import ARP, Ether, srp       # type: ignore
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

try:
    import psutil                               # type: ignore
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# ── MAC vendor prefix table (top 30 vendors) ─────────────────────────────────
MAC_VENDOR_TABLE: Dict[str, str] = {
    "00:50:56": "VMware",
    "00:0C:29": "VMware",
    "00:1A:11": "Google",
    "AC:DE:48": "Apple",
    "3C:5A:B4": "Apple",
    "F0:18:98": "Apple",
    "B8:27:EB": "Raspberry Pi Foundation",
    "DC:A6:32": "Raspberry Pi Foundation",
    "E4:5F:01": "Raspberry Pi Foundation",
    "00:1B:63": "Apple",
    "78:4F:43": "Apple",
    "68:FF:7B": "Apple",
    "00:25:9C": "Cisco",
    "00:1E:13": "Cisco",
    "FC:FB:FB": "Cisco",
    "00:23:14": "Dell",
    "14:18:77": "Dell",
    "18:DB:F2": "Dell",
    "20:47:47": "Lenovo",
    "54:EE:75": "Lenovo",
    "98:FA:9B": "Lenovo",
    "00:21:CC": "HP",
    "3C:D9:2B": "HP",
    "94:57:A5": "HP",
    "00:E0:4C": "Realtek",
    "74:D4:35": "Giga-byte",
    "FC:AA:14": "ASUSTeK",
    "50:46:5D": "Microsoft",
    "28:D2:44": "Microsoft",
    "00:15:5D": "Microsoft Hyper-V",
}


def get_vendor(mac: str) -> str:
    """Return vendor name from the first 3 MAC octets."""
    prefix = mac[:8].upper()
    return MAC_VENDOR_TABLE.get(prefix, "Unknown Vendor")


def get_local_ip() -> str:
    """Get the local machine's primary IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_network_range() -> str:
    """Derive /24 network range from local IP."""
    local_ip = get_local_ip()
    parts    = local_ip.rsplit(".", 1)
    return f"{parts[0]}.0/24"


def resolve_hostname(ip: str) -> str:
    """Try reverse DNS, fall back to 'Unknown'."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return "Unknown"


# ── Scan methods ──────────────────────────────────────────────────────────────

def _scan_arp_scapy(network: str) -> List[Dict]:
    """ARP scan using Scapy (requires root privileges)."""
    results = []
    try:
        packet   = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network)
        answered, _ = srp(packet, timeout=3, verbose=False)
        for sent, received in answered:
            mac  = received.hwsrc.upper()
            ip   = received.psrc
            results.append({
                "ip_address":  ip,
                "mac_address": mac,
                "hostname":    resolve_hostname(ip),
                "vendor":      get_vendor(mac),
                "status":      "online",
                "scan_method": "arp_scapy",
            })
    except Exception as e:
        print(f"[Scanner] Scapy ARP error: {e}")
    return results


def _scan_arp_cache(network: str) -> List[Dict]:
    """
    Parse the OS ARP cache (no root needed).
    Works after pinging the broadcast address first.
    """
    results = []
    try:
        # Ping broadcast to populate ARP cache
        net = ipaddress.IPv4Network(network, strict=False)
        broadcast = str(net.broadcast_address)
        subprocess.run(
            ["ping", "-b", "-c", "1", "-W", "1", broadcast],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # Read ARP table
        output = subprocess.check_output(["arp", "-n"],
                                         stderr=subprocess.DEVNULL,
                                         text=True)
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                ip  = parts[0]
                mac = parts[2]
                if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip) and \
                   re.match(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$", mac):
                    try:
                        if ipaddress.ip_address(ip) in net:
                            mac_upper = mac.upper()
                            results.append({
                                "ip_address":  ip,
                                "mac_address": mac_upper,
                                "hostname":    resolve_hostname(ip),
                                "vendor":      get_vendor(mac_upper),
                                "status":      "online",
                                "scan_method": "arp_cache",
                            })
                    except Exception:
                        pass
    except Exception as e:
        print(f"[Scanner] ARP cache error: {e}")
    return results


def _scan_mock() -> List[Dict]:
    """
    Return realistic demo devices for development / sandbox mode.
    Used when no network scan is possible.
    """
    return [
        {"ip_address": "192.168.1.1",   "mac_address": "00:11:22:33:44:55",
         "hostname": "gateway.local",   "vendor": "Cisco Systems",
         "status": "online",            "scan_method": "mock"},
        {"ip_address": "192.168.1.5",   "mac_address": "AC:DE:48:AB:CD:EF",
         "hostname": "macbook-pro",     "vendor": "Apple",
         "status": "online",            "scan_method": "mock"},
        {"ip_address": "192.168.1.10",  "mac_address": "B8:27:EB:12:34:56",
         "hostname": "raspberrypi",     "vendor": "Raspberry Pi Foundation",
         "status": "online",            "scan_method": "mock"},
        {"ip_address": "192.168.1.15",  "mac_address": "50:46:5D:78:9A:BC",
         "hostname": "DESKTOP-WIN11",   "vendor": "Microsoft",
         "status": "online",            "scan_method": "mock"},
        {"ip_address": "192.168.1.20",  "mac_address": "00:23:14:DE:AD:BE",
         "hostname": "hp-printer",      "vendor": "HP",
         "status": "online",            "scan_method": "mock"},
        {"ip_address": "192.168.1.25",  "mac_address": "F0:18:98:56:78:9A",
         "hostname": "iphone-14",       "vendor": "Apple",
         "status": "offline",           "scan_method": "mock"},
        {"ip_address": "192.168.1.30",  "mac_address": "74:D4:35:AA:BB:CC",
         "hostname": "gaming-pc",       "vendor": "Giga-byte",
         "status": "online",            "scan_method": "mock"},
        {"ip_address": "192.168.1.35",  "mac_address": "28:D2:44:11:22:33",
         "hostname": "xbox-console",    "vendor": "Microsoft",
         "status": "offline",           "scan_method": "mock"},
    ]


# ── Public API ────────────────────────────────────────────────────────────────

def scan_network(network: Optional[str] = None) -> Dict:
    """
    Run a network scan using the best available method.

    Returns:
        dict with keys:
          - devices: List[Dict]  — discovered devices
          - method:  str         — scan method used
          - duration: float      — scan time in seconds
          - network:  str        — range scanned
    """
    if network is None:
        network = get_network_range()

    start = datetime.utcnow()
    devices = []
    method  = "none"

    if SCAPY_AVAILABLE and os.geteuid() == 0:
        devices = _scan_arp_scapy(network)
        method  = "arp_scapy"

    if not devices:
        devices = _scan_arp_cache(network)
        method  = "arp_cache"

    if not devices:
        devices = _scan_mock()
        method  = "mock"

    duration = (datetime.utcnow() - start).total_seconds()
    return {
        "devices":  devices,
        "method":   method,
        "duration": round(duration, 2),
        "network":  network,
    }


def get_network_stats() -> Dict:
    """
    Collect current network I/O statistics using psutil.
    Returns bytes/packets sent & received since boot.
    """
    if not PSUTIL_AVAILABLE:
        return {"bytes_sent": 0, "bytes_recv": 0,
                "packets_sent": 0, "packets_recv": 0}
    counters = psutil.net_io_counters()
    return {
        "bytes_sent":   counters.bytes_sent,
        "bytes_recv":   counters.bytes_recv,
        "packets_sent": counters.packets_sent,
        "packets_recv": counters.packets_recv,
    }
