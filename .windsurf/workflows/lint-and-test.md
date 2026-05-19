---
description: Lint and test the Sentiment Analysis FastAPI service
---

1. Verify the FastAPI app imports cleanly from `c:\Users\ukard\OneDrive\Desktop\trading\sentiment_analysis\backend`:
   `sentiment_analysis\venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'backend'); from app.main import app; print('Import OK')"`
   Run from `c:\Users\ukard\OneDrive\Desktop\trading`.

2. Run the quick import smoke test from `c:\Users\ukard\OneDrive\Desktop\trading\sentiment_analysis\backend`:
   `sentiment_analysis\venv\Scripts\python.exe test_import.py`

3. Run pytest against the API and source tests from `c:\Users\ukard\OneDrive\Desktop\trading\sentiment_analysis`:
   `sentiment_analysis\venv\Scripts\python.exe -m pytest test_api.py test_msft.py -v`
   Note: full runs require NEWSAPI_KEY and FINNHUB_KEY env vars. Tests may be skipped/degraded without them.

4. Run flake8 linting across the backend (skip if not installed):
   `sentiment_analysis\venv\Scripts\python.exe -m flake8 backend --select=E,W --max-line-length=120 --statistics --count`

5. Report any import errors, test failures, or lint violations found.
