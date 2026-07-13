#!/usr/bin/env python3
"""Validate CCIE SP full-config consistency without device access."""

from __future__ import annotations

import ipaddress
import os
import re
import sys
from pathlib import Path

from build_lab_facts import build_edges, parse_config


BASE_DIR = Path(__file__).resolve().parents[1]
LAB_DIR = BASE_DIR.parent
CONFIG_DIR = Path(os.environ.get("CCIE_SP_CONFIG_DIR", LAB_DIR / "full-configs"))
PEER_RE = re.compile(r"->\s*([A-Za-z0-9_.-]+)\s+(.+)$")


def canonical_name(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", name.upper())


def resolve_peer(peer: str, hostnames: set[str]) -> str | None:
    if peer in hostnames:
        return peer

    peer_key = canonical_name(peer)
    exact = {canonical_name(hostname): hostname for hostname in hostnames}
    if peer_key in exact:
        return exact[peer_key]

    prefix_matches = [
        hostname
        for hostname in hostnames
        if canonical_name(hostname).startswith(peer_key)
    ]
    if len(prefix_matches) == 1:
        return prefix_matches[0]

    short_matches = [
        hostname
        for hostname in hostnames
        if peer_key.startswith(canonical_name(hostname))
    ]
    if len(short_matches) == 1:
        return short_matches[0]

    return None


def collect_devices() -> dict[str, dict]:
    devices = {}
    for path in sorted(CONFIG_DIR.glob("*.txt")):
        facts = parse_config(path)
        devices[facts["hostname"]] = facts
    return devices


def validate_unique_loopbacks(devices: dict[str, dict]) -> list[str]:
    warnings = []
    seen = {}
    for hostname, facts in devices.items():
        loop = facts.get("loopback600_ipv4")
        if not loop:
            warnings.append(f"{hostname}: missing Loopback600 IPv4")
            continue
        if loop in seen:
            warnings.append(f"{hostname}: duplicate Loopback600 IPv4 {loop} also used by {seen[loop]}")
        seen[loop] = hostname
    return warnings


def validate_duplicate_interface_ips(devices: dict[str, dict]) -> list[str]:
    warnings = []
    seen = {}
    for hostname, facts in devices.items():
        for if_name, intf in facts["interfaces"].items():
            ip_value = intf.get("ipv4")
            if not ip_value:
                continue
            if ip_value in seen:
                warnings.append(f"{hostname} {if_name}: duplicate IPv4 {ip_value} also used by {seen[ip_value]}")
            seen[ip_value] = f"{hostname} {if_name}"
    return warnings


def validate_peer_references(devices: dict[str, dict]) -> list[str]:
    warnings = []
    hostnames = set(devices)
    for hostname, facts in devices.items():
        for if_name, intf in facts["interfaces"].items():
            peer = intf.get("peer")
            peer_interface = intf.get("peer_interface")
            if not peer:
                continue
            resolved_peer = resolve_peer(peer, hostnames)
            if not resolved_peer:
                warnings.append(f"{hostname} {if_name}: peer {peer} not found in configs")
                continue
            peer_intfs = devices[resolved_peer]["interfaces"]
            if peer_interface and peer_interface not in peer_intfs:
                warnings.append(f"{hostname} {if_name}: peer interface {resolved_peer} {peer_interface} not found")
    return warnings


def validate_p2p_prefixes(devices: dict[str, dict]) -> list[str]:
    warnings = []
    for hostname, facts in devices.items():
        for if_name, intf in facts["interfaces"].items():
            ip_value = intf.get("ipv4")
            if not ip_value or not intf.get("peer"):
                continue
            try:
                iface = ipaddress.IPv4Interface(ip_value)
            except ValueError:
                continue
            if iface.network.prefixlen not in (30, 31):
                warnings.append(f"{hostname} {if_name}: P2P link uses {ip_value}, expected /30 or /31")
    return warnings


def main() -> int:
    devices = collect_devices()
    edges = build_edges(devices)
    warnings = []
    warnings.extend(validate_unique_loopbacks(devices))
    warnings.extend(validate_duplicate_interface_ips(devices))
    warnings.extend(validate_peer_references(devices))
    warnings.extend(validate_p2p_prefixes(devices))

    print(f"Devices: {len(devices)}")
    print(f"Edges: {len(edges)}")

    if warnings:
        print("\nValidation warnings:")
        for warning in warnings:
            print(f"- {warning}")
        if "--strict" in sys.argv:
            return 1

    print("Offline lab validation OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
