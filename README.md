# cartographic_quiz

Wikipedia-based cartographic life quiz generator.

The CLI scrapes birth/death dates and locations from Wikipedia, resolves coordinates, and renders an interactive HTML map quiz.

## Features

- Single-person quiz generation (`cartographic-quiz <name>`).
- Multi-round random quiz generation from bundled pools (`--num-random N`).
- Persistent cache/list maintenance (`people_cache.json`, `people_bad.txt`, `people_good.txt`).
- Bad-name rescanning to re-check previously invalid names (`--rescan-bad`).
- Date parsing support for BC/BCE and AD/CE formats, including approximate forms (`c.`, `ca.`, `circa`).
- Living people are excluded (both birth and death data are required).
- Country-level locations are rendered as approximate circles instead of precise city pins.

## Install / Run

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## CLI Usage

Generate a single-person quiz map:

```bash
uv run cartographic-quiz Ada Lovelace
```

Generate a random multi-round quiz:

```bash
uv run cartographic-quiz --num-random 10 -o quizzes/random-10.html
```

Re-scan names currently marked bad:

```bash
uv run cartographic-quiz --rescan-bad
```

Clear cache/list status files:

```bash
uv run cartographic-quiz --clear-cache
# or
uv run clear-cache
```

Publish an existing HTML quiz file to `docs/index.html`:

```bash
uv run publish quizzes/output.html
```

Publish without pushing (copies and commits docs files only):

```bash
uv run publish quizzes/output.html --no-push
```

Notes:

- Multi-word names are unquoted-safe (`uv run cartographic-quiz Marie Curie` works).
- If `-o/--output` has no extension, `.html` is appended automatically.
- You must pass one of: person name, `--num-random N`, `--rescan-bad`, or `--clear-cache`.

## Quiz Behavior

Single-person mode:

- Shows one person with birth/death map markers.
- Accepts minor typos and accent/quote variations in guesses.
- Tracks `Correct` and `Streak` in browser session storage.

Random multi-round mode:

- Uses one guess per round; reveals answer immediately.
- Includes `Continue`, `Force Correct`, and `Force Wrong` controls per round.
- Shows final accuracy summary and per-round recap.
- Lets you click recap items to re-focus the map on that round.

## Data Files

Files under `data/`:

- `people_easy.txt`, `people_medium.txt`, `people_hard.txt`: bundled random source pools.
- `people_good.txt`: accumulated valid names (also included in random pool input).
- `people_bad.txt`: names known to fail scraping/validation.
- `people_cache.json`: cached scrape/validation records.

Difficulty curation guidance:

- `docs/people_difficulty_criteria.md`

## Development

Run tests:

```bash
uv run pytest
```

Useful entry points:

- CLI: `src/cartographic_quiz/__main__.py`
- Scraping/parsing: `src/cartographic_quiz/biography.py`
- Geocoding/network: `src/cartographic_quiz/geo.py`
- Map rendering/UI: `src/cartographic_quiz/map_renderer.py`
- Marker SVGs: `src/cartographic_quiz/svg_markers.py`
