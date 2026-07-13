#!/usr/bin/env python3
"""Build an offline topology view from CCIE SP full-config text files."""

from __future__ import annotations

import csv
import ipaddress
import os
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
LAB_DIR = BASE_DIR.parent
CONFIG_DIR = Path(os.environ.get("CCIE_SP_CONFIG_DIR", LAB_DIR / "full-configs"))
GENERATED_DIR = Path(os.environ.get("CCIE_SP_GENERATED_DIR", BASE_DIR / "generated"))


HOST_RE = re.compile(r"^hostname\s+(\S+)", re.IGNORECASE)
INT_RE = re.compile(r"^interface\s+(.+)$", re.IGNORECASE)
DESC_RE = re.compile(r"^\s*description\s+(.+)$", re.IGNORECASE)
IPV4_RE = re.compile(r"^\s*ipv4 address\s+(\S+)\s+(\S+)", re.IGNORECASE)
IPV6_RE = re.compile(r"^\s*ipv6 address\s+(\S+)", re.IGNORECASE)
PEER_RE = re.compile(r"->\s*([A-Za-z0-9_.-]+)\s+(.+)$")


def role_from_hostname(hostname: str) -> str:
    name = hostname.upper()
    if name.startswith("CUST"):
        return "customer"
    if "RR" in name:
        return "route_reflector"
    if "PCE" in name:
        return "pce"
    if name.startswith("PE"):
        return "pe"
    if name.startswith("P"):
        return "p"
    return "unknown"


def normalize_peer(peer: str) -> str:
    return peer.strip().upper().replace("_", "-")


def normalize_interface(interface_name: str) -> str:
    name = interface_name.strip()
    replacements = {
        "Gi": "GigabitEthernet",
        "Lo": "Loopback",
    }
    for short, long in replacements.items():
        if name.startswith(short) and not name.startswith(long):
            return long + name[len(short) :]
    return name


def parse_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    hostname = None
    interfaces: dict[str, dict] = {}
    current_int = None

    protocols = {
        "isis": False,
        "bgp": False,
        "segment_routing": False,
        "pce": False,
        "pim": False,
        "vrf": False,
    }

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        host_match = HOST_RE.match(stripped)
        if host_match and hostname is None:
            hostname = host_match.group(1).upper()

        lower = stripped.lower()
        if lower.startswith("router isis"):
            protocols["isis"] = True
        elif lower.startswith("router bgp"):
            protocols["bgp"] = True
        elif lower.startswith("segment-routing"):
            protocols["segment_routing"] = True
        elif lower == "pce" or lower.startswith("pce "):
            protocols["pce"] = True
        elif lower.startswith("router pim"):
            protocols["pim"] = True
        elif lower.startswith("vrf "):
            protocols["vrf"] = True

        int_match = INT_RE.match(stripped)
        if int_match:
            current_int = normalize_interface(int_match.group(1).strip())
            interfaces.setdefault(
                current_int,
                {
                    "description": "",
                    "ipv4": "",
                    "ipv6": "",
                    "shutdown": False,
                    "peer": "",
                    "peer_interface": "",
                },
            )
            continue

        if current_int is None:
            continue

        if stripped == "!":
            current_int = None
            continue

        if lower == "shutdown":
            interfaces[current_int]["shutdown"] = True
            continue

        desc_match = DESC_RE.match(line)
        if desc_match:
            desc = desc_match.group(1).strip()
            interfaces[current_int]["description"] = desc
            peer_match = PEER_RE.search(desc)
            if peer_match:
                interfaces[current_int]["peer"] = normalize_peer(peer_match.group(1))
                interfaces[current_int]["peer_interface"] = normalize_interface(peer_match.group(2).strip())
            continue

        ipv4_match = IPV4_RE.match(line)
        if ipv4_match:
            ip_addr, mask = ipv4_match.groups()
            try:
                prefix = ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
                interfaces[current_int]["ipv4"] = f"{ip_addr}/{prefix}"
            except ValueError:
                interfaces[current_int]["ipv4"] = f"{ip_addr} {mask}"
            continue

        ipv6_match = IPV6_RE.match(line)
        if ipv6_match:
            interfaces[current_int]["ipv6"] = ipv6_match.group(1)

    hostname = hostname or path.stem.upper()
    loopback = interfaces.get("Loopback600", {})

    active_interfaces = {
        name: data
        for name, data in interfaces.items()
        if not data.get("shutdown") and (data.get("ipv4") or data.get("ipv6") or data.get("description"))
    }

    return {
        "hostname": hostname,
        "source_file": path.name,
        "role": role_from_hostname(hostname),
        "loopback600_ipv4": loopback.get("ipv4", ""),
        "loopback600_ipv6": loopback.get("ipv6", ""),
        "protocols": protocols,
        "interfaces": active_interfaces,
    }


def yaml_scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None or value == "":
        return '""'
    text = str(value)
    if re.fullmatch(r"[A-Za-z0-9_./:-]+", text):
        return text
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_yaml_value(lines: list[str], value, indent: int = 0) -> None:
    pad = " " * indent
    if isinstance(value, dict):
        for key in sorted(value):
            item = value[key]
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}{key}:")
                write_yaml_value(lines, item, indent + 2)
            else:
                lines.append(f"{pad}{key}: {yaml_scalar(item)}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                write_yaml_value(lines, item, indent + 2)
            else:
                lines.append(f"{pad}- {yaml_scalar(item)}")


def write_yaml(path: Path, data: dict) -> None:
    lines = ["---"]
    write_yaml_value(lines, data)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_edges(devices: dict[str, dict]) -> list[dict]:
    edges = []
    seen = set()
    for hostname, facts in devices.items():
        for if_name, intf in facts["interfaces"].items():
            peer = intf.get("peer")
            if not peer:
                continue
            edge_key = tuple(sorted([f"{hostname}:{if_name}", f"{peer}:{intf.get('peer_interface', '')}"]))
            if edge_key in seen:
                continue
            seen.add(edge_key)
            edges.append(
                {
                    "local_device": hostname,
                    "local_interface": if_name,
                    "peer_device": peer,
                    "peer_interface": intf.get("peer_interface", ""),
                    "ipv4": intf.get("ipv4", ""),
                    "ipv6": intf.get("ipv6", ""),
                    "description": intf.get("description", ""),
                }
            )
    return edges


def write_edges_csv(path: Path, edges: list[dict]) -> None:
    fieldnames = [
        "local_device",
        "local_interface",
        "peer_device",
        "peer_interface",
        "ipv4",
        "ipv6",
        "description",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(edges)


def write_mermaid(path: Path, edges: list[dict]) -> None:
    lines = ["graph LR"]
    for edge in edges:
        left = edge["local_device"].replace("-", "_")
        right = edge["peer_device"].replace("-", "_")
        label = f"{edge['local_interface']} - {edge['peer_interface']}".replace('"', "'")
        lines.append(f'  {left}["{edge["local_device"]}"] -- "{label}" --> {right}["{edge["peer_device"]}"]')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_ansible_inventory(path: Path, devices: dict[str, dict]) -> None:
    grouped: dict[str, list[str]] = {}
    for hostname, facts in devices.items():
        grouped.setdefault(facts["role"], []).append(hostname)

    inventory = {
        "all": {
            "children": {
                "iosxr": {
                    "vars": {
                        "ansible_connection": "ansible.netcommon.network_cli",
                        "ansible_network_os": "cisco.iosxr.iosxr",
                        "ansible_user": "{{ lookup('env', 'NETOPS_USER') | default('netops', true) }}",
                    },
                    "hosts": {
                        hostname: {
                            "ansible_host": "TODO_MGMT_IP",
                            "loopback600_ipv4": facts["loopback600_ipv4"],
                            "role": facts["role"],
                        }
                        for hostname, facts in sorted(devices.items())
                    },
                }
            }
        }
    }

    for role, hosts in sorted(grouped.items()):
        inventory["all"]["children"][role] = {"hosts": {host: {} for host in sorted(hosts)}}

    write_yaml(path, inventory)


def main() -> int:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    devices = {}
    for path in sorted(CONFIG_DIR.glob("*.txt")):
        facts = parse_config(path)
        devices[facts["hostname"]] = facts

    edges = build_edges(devices)
    summary = {
        "config_dir": str(CONFIG_DIR),
        "device_count": len(devices),
        "edge_count": len(edges),
        "devices": devices,
    }

    write_yaml(GENERATED_DIR / "lab_facts.yml", summary)
    write_ansible_inventory(GENERATED_DIR / "ansible_inventory.yml", devices)
    write_edges_csv(GENERATED_DIR / "topology_edges.csv", edges)
    write_mermaid(GENERATED_DIR / "topology.mmd", edges)

    print(f"Parsed {len(devices)} devices from {CONFIG_DIR}")
    print(f"Detected {len(edges)} topology edges")
    print(f"Wrote generated files to {GENERATED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
