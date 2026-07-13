#!/usr/bin/env python3
"""Render IOS XR change configs from YAML data and Jinja2 templates."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    import yaml
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError as exc:
    raise SystemExit(
        "Missing dependency. Install with: python -m pip install -r automation/requirements.txt"
    ) from exc


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CHANGE = BASE_DIR / "change-data" / "customers" / "cust-new-vrf.yml"
DEFAULT_OUTPUT = BASE_DIR / "rendered"
TEMPLATE_DIR = BASE_DIR / "templates" / "iosxr"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def sanitize(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")


def isis_net(area: str, node_id: int) -> str:
    node = f"{int(node_id):04d}"
    return f"49.{area}.{node}.{node}.{node}.00"


def enrich_device(device: dict, provider: dict) -> dict:
    enriched = dict(device)
    node_id = enriched.get("pe_id", enriched.get("node_id"))
    if node_id is not None:
        enriched["isis_net"] = enriched.get("isis_net") or isis_net(provider["isis_area"], int(node_id))
    return enriched


def render_device(env: Environment, context: dict, device: dict) -> str:
    sections = []
    templates = device.get("render_templates", [])
    for template_name in templates:
        template = env.get_template(template_name)
        sections.append(template.render({**context, "device": device}).rstrip())
    return "\n\n".join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--change-file", type=Path, default=DEFAULT_CHANGE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    data = load_yaml(args.change_file)
    provider = data["provider"]
    change_id = sanitize(data["change"]["id"])
    output_dir = args.output_dir / change_id
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    context = {
        "change": data["change"],
        "service": data["service"],
        "provider": provider,
        "pe_devices": [enrich_device(device, provider) for device in data.get("pe_devices", [])],
        "route_reflectors": data.get("route_reflectors", []),
        "validation": data.get("validation", {}),
    }

    rendered_files = []
    all_devices = context["pe_devices"] + [enrich_device(device, provider) for device in data.get("route_reflectors", [])]
    for device in all_devices:
        config = render_device(env, context, device)
        filename = output_dir / f"{sanitize(device['hostname'])}.cfg"
        filename.write_text(config, encoding="utf-8")
        rendered_files.append(str(filename))

    manifest = {
        "change_id": data["change"]["id"],
        "change_file": str(args.change_file),
        "output_dir": str(output_dir),
        "rendered_files": rendered_files,
    }
    (output_dir / "manifest.yml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    print(f"Rendered {len(rendered_files)} config files to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
