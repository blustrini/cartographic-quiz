# AGENTS

Scope: `tests/`

## Testing Rules
- Use `pytest` function-style tests.
- Mock network and geocoding in unit tests.
- Do not rely on live Wikipedia/API calls.

## Coverage Expectations
- Add regression tests for parsing bugs before/with fixes.
- Include edge cases for BC/BCE, AD/CE, approximate dates, and split tokens.
- Verify living-person exclusion behavior.

## Run
- Full suite: `uv run pytest`
- Targeted: `uv run pytest tests/test_biography.py -k <pattern>`
