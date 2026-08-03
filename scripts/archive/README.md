# Archived one-off scripts

Moved out of the `sentiment_analysis` root during workspace cleanup — manual
diagnostic/smoke-test scripts, not part of the pytest suite (`backend/tests/`)
and not referenced anywhere else in this repo:

- `debug_sources.py` — debug individual source client responses (Yahoo
  Finance, Finviz, SEC EDGAR).
- `test_sources.py` — diagnostic check for Yahoo Finance/Finviz/SEC EDGAR
  sources against a running backend.
- `test_api.py` — manual smoke test for `POST /api/analyze` (AAPL); writes
  `api_test_result.json` when run.
- `test_msft.py` — manual smoke test for `POST /api/analyze` (MSFT); writes
  `msft_result.json` when run.

The generated `api_test_result.json`/`msft_result.json` outputs, a stray
empty `package-lock.json`, `frontend.log`, and a stale `polygon_cache.sqlite`
were also removed from the repo root as part of this cleanup.
