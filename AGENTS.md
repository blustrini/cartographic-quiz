# AGENTS

Scope: whole repository.

## Purpose
- Build a Wikipedia-based cartographic life quiz.
- CLI supports:
  - single-person map quiz generation
  - multi-round random quiz generation from bundled pools
  - cache/list maintenance via bad-name rescans

## Rules
- Keep changes small and explicit.
- Prefer deterministic parsing over broad heuristics.
- Preserve support for BC/BCE and AD/CE date formats.
- Living people are excluded (must have both birth and death dates).

## Runbook
- Run tests: `uv run pytest`
- Run single-person quiz: `uv run cartographic-quiz <name> [-o output.html]`
- Run random multi-round quiz: `uv run cartographic-quiz --num-random <N> [-o output.html]`
- Rescan bad-name list: `uv run cartographic-quiz --rescan-bad`
- Clear cache/list files: `uv run cartographic-quiz --clear-cache`
- Clear cache/list files (entrypoint): `uv run clear-cache`
- Publish existing HTML to GitHub Pages docs site: `uv run publish <path-to-output.html> [--no-push]`
- Multi-word names are unquoted-safe (arg parser joins tokens).

## Key Paths
- CLI entry: `src/cartographic_quiz/__main__.py`
- Scraping/parsing: `src/cartographic_quiz/biography.py`
- Geocoding/network: `src/cartographic_quiz/geo.py`
- Map rendering/UI overlay: `src/cartographic_quiz/map_renderer.py`
- Marker SVGs: `src/cartographic_quiz/svg_markers.py`
- Tests: `tests/`

## Quality Bar
- Add/adjust tests for every parsing regression.
- Prefer mocked HTML/API tests; avoid network in unit tests.
- Keep docs and behavior aligned.
