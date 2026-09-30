#!/usr/bin/env python3
"""Make a lean browser copy of the constituency-boundary GeoJSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def clean_name(value: str) -> str:
    return value.rsplit(" (", 1)[0].strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="source Constituency Insights GeoJSON")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/data/constituencies.json")
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    features = []
    for feature in source["features"]:
        name = clean_name(feature.get("properties", {}).get("ENG_NAME_VALUE", ""))
        if name and feature.get("geometry"):
            features.append({"type": "Feature", "properties": {"name": name}, "geometry": feature["geometry"]})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {args.output}: {len(features):,} boundary fragments across {len({f['properties']['name'] for f in features})} constituencies.")


if __name__ == "__main__":
    main()
