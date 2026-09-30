#!/usr/bin/env python3
"""Build browser-ready scheduled NTA GTFS trajectories for one service date.

The result uses published GTFS route shapes rather than live vehicle locations
or map-matched road geometry.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import zipfile
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODE_ROUTE_TYPES = {"rail": {2}, "bus": {3}}


def rows(archive: zipfile.ZipFile, name: str):
    with archive.open(name) as source:
        yield from csv.DictReader(io.TextIOWrapper(source, encoding="utf-8-sig"))


def seconds(value: str) -> int:
    hour, minute, second = (int(part) for part in value.split(":"))
    return hour * 3600 + minute * 60 + second


def active_services(archive: zipfile.ZipFile, target: date) -> set[str]:
    weekday = target.strftime("%A").lower()
    services = {
        row["service_id"]
        for row in rows(archive, "calendar.txt")
        if row.get(weekday) == "1"
        and row["start_date"] <= target.strftime("%Y%m%d") <= row["end_date"]
    }
    for row in rows(archive, "calendar_dates.txt"):
        if row["date"] != target.strftime("%Y%m%d"):
            continue
        if row["exception_type"] == "1":
            services.add(row["service_id"])
        elif row["exception_type"] == "2":
            services.discard(row["service_id"])
    return services


def simplify(points: list[tuple[float, float]], maximum: int = 180) -> list[tuple[float, float]]:
    if len(points) <= maximum:
        return points
    step = (len(points) - 1) / (maximum - 1)
    return [points[round(index * step)] for index in range(maximum)]


def point_times(points: list[tuple[float, float]], start: int, end: int) -> list[int]:
    distances = [0.0]
    for (lon_a, lat_a), (lon_b, lat_b) in zip(points, points[1:]):
        distances.append(distances[-1] + math.hypot(lon_b - lon_a, lat_b - lat_a))
    total = distances[-1] or 1.0
    return [round(start + (end - start) * distance / total) for distance in distances]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("date", nargs="?", default="2026-09-30", help="service date, YYYY-MM-DD")
    parser.add_argument("--feed", type=Path, default=ROOT / "GTFS_Irish_Rail.zip")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/data/irish-rail-day.json")
    parser.add_argument("--mode", choices=MODE_ROUTE_TYPES, default="rail", help="GTFS mode to export")
    parser.add_argument("--maximum-points", type=int, default=180, help="maximum shape points per trip")
    args = parser.parse_args()
    target = datetime.strptime(args.date, "%Y-%m-%d").date()

    with zipfile.ZipFile(args.feed) as archive:
        services = active_services(archive, target)
        routes = {row["route_id"]: row for row in rows(archive, "routes.txt")}
        shapes: dict[str, list[tuple[float, float]]] = defaultdict(list)
        for row in rows(archive, "shapes.txt"):
            shapes[row["shape_id"]].append((int(row["shape_pt_sequence"]), float(row["shape_pt_lon"]), float(row["shape_pt_lat"])))
        shape_points = {key: [(lon, lat) for _, lon, lat in sorted(value)] for key, value in shapes.items()}
        allowed_types = MODE_ROUTE_TYPES[args.mode]
        trips = {
            row["trip_id"]: row
            for row in rows(archive, "trips.txt")
            if row["service_id"] in services
            and row.get("shape_id") in shape_points
            and int(routes[row["route_id"]].get("route_type") or -1) in allowed_types
        }
        bounds: dict[str, list[int]] = {}
        for row in rows(archive, "stop_times.txt"):
            trip_id = row["trip_id"]
            if trip_id not in trips:
                continue
            departure = seconds(row["departure_time"])
            entry = bounds.setdefault(trip_id, [departure, departure])
            entry[0] = min(entry[0], departure)
            entry[1] = max(entry[1], departure)

    output = []
    for trip_id, trip in trips.items():
        if trip_id not in bounds:
            continue
        start, end = bounds[trip_id]
        if end <= start:
            continue
        points = simplify(shape_points[trip["shape_id"]], args.maximum_points)
        route = routes[trip["route_id"]]
        output.append({
            "id": trip_id,
            "route": route.get("route_short_name") or "Rail",
            "name": route.get("route_long_name") or f"NTA {args.mode} service",
            "points": [[round(lon, 5), round(lat, 5), timestamp] for (lon, lat), timestamp in zip(points, point_times(points, start, end))],
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"date": args.date, "mode": args.mode, "trips": output}, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {args.output}: {len(output):,} scheduled {args.mode} trips on {args.date}.")


if __name__ == "__main__":
    main()
