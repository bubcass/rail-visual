# Ireland Rail Traffic

A standalone, GitHub Pages-ready proof of concept that visualises scheduled Irish Rail services over a single day. It takes its visual direction from the animated French rail-traffic map: a dark basemap, moving train heads, fading trails, and a 24-hour timeline.

It is deliberately separate from Constituency Insights while the idea is being evaluated.

## Publish

The site is fully static. Push this repository to GitHub, then in **Settings → Pages** select **Deploy from a branch**, choose `main`, and select the `/docs` folder. No build action or server is needed.

## What is included

- `docs/` — the site served by GitHub Pages, including the generated day of train trajectories.
- `scripts/build_day.py` — rebuilds the browser data from the official GTFS feed using only the Python standard library.

The downloaded GTFS zip and the local French-project research checkout are intentionally ignored; they are not required to run the published proof of concept.

## Rebuild the timetable day

Download the current Irish Rail GTFS archive as `GTFS_Irish_Rail.zip` in the repository root, then run:

```bash
python3 scripts/build_day.py 2026-09-30
```

Use any date covered by the downloaded feed. The script writes `docs/data/irish-rail-day.json`.

## Data and credits

The timetable, route and stop geometry is derived from the National Transport Authority's Irish Rail GTFS feed, licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The moving dots represent scheduled services interpolated along GTFS route shapes — they are not live train positions.

The basemap is CARTO's Dark Matter style, with OpenStreetMap contributors. The application code in this repository is MIT licensed; the transit data retains its own licence and attribution requirements.
# rail-visual
