---
description: Run a comprehensive deep-dive analysis on one or more tickers via the harness
---

Run a full ticker report through the sentiment_analysis service. This is a user-only
harness command that returns live market data, deep financial research, and recent
material news.

1. **Prerequisites** — Ensure the sentiment_analysis service is running on port 8000.
   If it is not running, the harness command will start it automatically.

2. **Run the analysis** from the trading root:
   ```powershell
   python -m harness.cli comprehensive AAPL
   python -m harness.cli comprehensive AAPL MSFT TSLA
   ```
   Run from `c:\Users\ukard\OneDrive\Desktop\trading`.

3. **What is returned** for each ticker:
   - **Current Data** — live price, bid/ask spread, volume vs average, 52-week high/low, and current position within the 52-week range.
   - **Deep Research** — revenue/earnings trend (latest quarter + YoY), balance sheet health (debt, cash, ratios), competitive landscape, key risks, business operations summary, and future growth outlook.
   - **News Check** — recent material news articles with source, age, and summary.

4. **Output** — The harness prints a formatted report to the terminal and saves a JSON copy under `results/comprehensive_<timestamp>.json` for later reference.

5. **Scope note** — The underlying `/api/comprehensive` endpoint is not part of the scheduled reconciliation/scheduler flow. It is only intended to be called through this user-invoked harness command.
