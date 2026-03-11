# Changelog

> **Format:** `## vX.Y.Z — YYYY-MM-DD — commit message`
> Use the text after the date as your `git commit -m "..."` message.
> Keep entries to 3 lines max. Use imperative mood (fix, add, remove — not fixed, added).

## v1.0.1 — 2026-03-11 — fix: API connectivity and cross-platform path issues

- Fix API port detection bug caused by Flask debug reloader overwriting `.api_port`
- Add React dev server proxy to eliminate port mismatch issues
- Fix Windows-style path in `ONE_processor.py` for macOS compatibility
