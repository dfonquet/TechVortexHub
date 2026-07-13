#!/usr/bin/env python3
"""Validate change YAML before templates are rendered."""

from __future__ import annotations

import argparse
import ipaddress
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "Missing dependency. Install with: python -m pip install -r automation/requirements.txt"
    ) from exc


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CHANGE = BASE_DIR / "change-data" / "customers" / "cust-new-vrf.yml"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_prefix(errors: list[str], value: str, label: str) -> None:
    if not value:
        return
    try:
        ipaddress.ip_interface(value)
    except ValueError:
        errors.append(f"{label}: invalid interface address {value}")


def validate_ip(errors: list[str], value: str, label: str) -> None:
    if not value:
        return
    try:
        ipaddress.ip_address(value)
    except ValueError:
        errors.append(f"{label}: invalid IP address {value}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--change-file", type=Path, default=DEFAULT_CHANGE)
    args = parser.parse_args()

    with args.change_file.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    errors: list[str] = []
    require(errors, isinstance(data, dict), "change file must be a YAML mapping")
    if errors:
        print("\n".join(errors))
        return 1

    for key in ("change", "service", "provider"):
        require(errors, key in data, f"missing top-level key: {key}")

    service = data.get("service", {})
    provider = data.get("provider", {})
    pe_devices = data.get("pe_devices", [])

    require(errors, service.get("vrf_name"), "service.vrf_name is required")
    require(errors, provider.get("asn"), "provider.asn is required")
    require(errors, provider.get("isis_process"), "provider.isis_process is required")
    require(errors, provider.get("isis_area"), "provider.isis_area is required")
    require(errors, isinstance(pe_devices, list) and pe_devices, "pe_devices must contain at least one PE")

    seen_hosts = set()
    for index, pe in enumerate(pe_devices, start=1):
        label = f"pe_devices[{index}]"
        hostname = pe.get("hostname")
        require(errors, hostname, f"{label}.hostname is required")
        if hostname in seen_hosts:
            errors.append(f"{label}.hostname duplicates {hostname}")
        seen_hosts.add(hostname)

        require(errors, pe.get("pe_id") is not None, f"{label}.pe_id is required for ISIS NET and prefix-sid")
        validate_ip(errors, pe.get("loopback_ipv4", ""), f"{label}.loopback_ipv4")

        intf = pe.get("customer_interface", {})
        require(errors, intf.get("name"), f"{label}.customer_interface.name is required")
        validate_prefix(errors, intf.get("ipv4", ""), f"{label}.customer_interface.ipv4")
        validate_prefix(errors, intf.get("ipv6", ""), f"{label}.customer_interface.ipv6")

        ce_bgp = pe.get("ce_bgp", {})
        require(errors, ce_bgp.get("asn"), f"{label}.ce_bgp.asn is required")
        validate_ip(errors, ce_bgp.get("ipv4_neighbor", ""), f"{label}.ce_bgp.ipv4_neighbor")
        validate_ip(errors, ce_bgp.get("ipv6_neighbor", ""), f"{label}.ce_bgp.ipv6_neighbor")

    if errors:
        print("Change data validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Change data OK: {args.change_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
