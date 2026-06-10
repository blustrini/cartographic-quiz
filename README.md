# cartographic_quiz

Wikipedia-based cartographic life quiz generator.

It scrapes birth/death dates and locations for historical figures, resolves coordinates, and renders an interactive HTML map quiz.

## Features

- Single-person quiz map generation.
- Multi-round random quiz generation from bundled name pools.
- Persistent cache and list maintenance (`people_cache.json`, `people_bad.txt`, `people_good.txt`).
- Bad-name rescanning to re-check previously invalid names.
- Date parsing support for BC/BCE and AD/CE formats, including approximate forms (`c.`, `ca.`, `circa`).
- Living people are excluded (both birth and death data are required).

## Usage

- Single-person quiz:

```bash
uv run cartographic-quiz <name> [-o output.html]
```

- Random multi-round quiz:

```bash
uv run cartographic-quiz --num-random <N> [-o output.html]
```

- Rescan bad-name list:

```bash
uv run cartographic-quiz --rescan-bad
```

Notes:

- Multi-word names are unquoted-safe; arguments are joined into one name.
- If `-o/--output` has no extension, `.html` is appended.

## Data Files

Under `data/`:

- `people_easy.txt`, `people_medium.txt`, `people_hard.txt`: bundled source pools for random mode.
- `people_good.txt`: accumulated valid names.
- `people_bad.txt`: known invalid names.
- `people_cache.json`: cached biography scrape/validation results.

## Development

- Run tests:

```bash
uv run pytest
```

- Key code paths:
  - CLI entry: `src/cartographic_quiz/__main__.py`
  - Scraping/parsing: `src/cartographic_quiz/biography.py`
  - Geocoding/network: `src/cartographic_quiz/geo.py`
  - Map rendering/UI overlay: `src/cartographic_quiz/map_renderer.py`
  - Marker SVGs: `src/cartographic_quiz/svg_markers.py`
