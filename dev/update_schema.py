#!/usr/bin/env python3
"""Export the JSON schema for applications (applications.yaml) in YAML format."""

import argparse
import sys
from pathlib import Path

# Add project root to path when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
from pydantic import RootModel

from app.models import Application

ApplicationsList = RootModel[list[Application]]


def main() -> int:
    parser = argparse.ArgumentParser(description="Export applications JSON schema in YAML format")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("docs/applications.schema.yaml"),
        help="Output file path (default: docs/applications.schema.yaml)",
    )
    args = parser.parse_args()

    schema = ApplicationsList.model_json_schema()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print(f"Schema written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
