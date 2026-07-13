#!/usr/bin/env python3
"""Validate rendered IOS XR config files with lightweight offline checks."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RENDERED_DIR = BASE_DIR / "rendered"


BAD_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bNone\b"),
    re.compile(r"\{\{|\}\}"),
    re.compile(r"{%|%}"),
]


def validate_file(path: Path) -> list[str]:
    errors = []
    text = path.read_text(encoding="utf-8")
    for pattern in BAD_PATTERNS:
        if pattern.search(text):
            errors.append(f"{path}: unresolved token matching {pattern.pattern}")

    if "router bgp" in text and "address-family vpnv4 unicast" not in text:
        errors.append(f"{path}: router bgp block missing vpnv4 address-family")
    if "vrf " in text and "import route-target" not in text:
        errors.append(f"{path}: VRF block missing import route-target")
    if "router isis" in text and "prefix-sid index" not in text:
        errors.append(f"{path}: ISIS block missing prefix-sid index")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rendered-dir", type=Path, default=DEFAULT_RENDERED_DIR)
    args = parser.parse_args()

    config_files = sorted(args.rendered_dir.rglob("*.cfg"))
    if not config_files:
        print(f"No rendered config files found under {args.rendered_dir}")
        return 1

    errors = []
    for path in config_files:
        errors.extend(validate_file(path))

    if errors:
        print("Rendered config validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Rendered config OK: {len(config_files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
