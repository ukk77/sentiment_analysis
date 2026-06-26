"""Comprehensive ticker analysis for deep-dive research reports.

This module is intentionally kept inside sentiment_analysis only. It is exposed
through a single, auth-protected FastAPI endpoint (`POST /api/comprehensive`) and
is meant to be invoked by the harness CLI only.

Data sources:
  - yfinance (live quote, financials, balance sheet, info)
  - YahooFinanceClient (recent news)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import yfinance as yf

from app.services.yahoofinance import YahooFinanceClient


def _pct_change(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous is None or previous == 0:
        return None
    return round(((current - previous) / abs(previous)) * 100, 2)


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _format_millions(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(value / 1_000_000, 2)


def get_current_data(ticker: str) -> Dict[str, Any]:
    """Retrieve live market data and 52-week range positioning."""
    ticker = ticker.upper()
    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}

        price = _safe_float(info.get("currentPrice")) or _safe_float(info.get("regularMarketPrice"))
        prev_close = _safe_float(info.get("previousClose")) or _safe_float(info.get("regularMarketPreviousClose"))
        change = None
        change_pct = None
        if price is not None and prev_close is not None and prev_close != 0:
            change = round(price - prev_close, 2)
            change_pct = round((change / prev_close) * 100, 2)

        bid = _safe_float(info.get("bid"))
        ask = _safe_float(info.get("ask"))
        spread = None
        if bid is not None and ask is not None:
            spread = round(ask - bid, 3)

        volume = _safe_int(info.get("volume")) or _safe_int(info.get("regularMarketVolume"))
        avg_volume = _safe_int(info.get("averageVolume")) or _safe_int(info.get("averageDailyVolume3Month"))
        volume_vs_avg = None
        if volume is not None and avg_volume is not None and avg_volume != 0:
            volume_vs_avg = round(volume / avg_volume, 2)

        high_52w = _safe_float(info.get("fiftyTwoWeekHigh"))
        low_52w = _safe_float(info.get("fiftyTwoWeekLow"))
        position_in_range = None
        if price is not None and high_52w is not None and low_52w is not None and high_52w != low_52w:
            position_in_range = round(((price - low_52w) / (high_52w - low_52w)) * 100, 2)

        day_high = _safe_float(info.get("dayHigh")) or _safe_float(info.get("regularMarketDayHigh"))
        day_low = _safe_float(info.get("dayLow")) or _safe_float(info.get("regularMarketDayLow"))
        open_price = _safe_float(info.get("open")) or _safe_float(info.get("regularMarketOpen"))
        market_cap = _safe_float(info.get("marketCap"))

        return {
            "ticker": ticker,
            "price": price,
            "previous_close": prev_close,
            "change": change,
            "change_percent": change_pct,
            "bid": bid,
            "ask": ask,
            "spread": spread,
            "volume": volume,
            "average_volume": avg_volume,
            "volume_vs_average": volume_vs_avg,
            "day_high": day_high,
            "day_low": day_low,
            "open": open_price,
            "fifty_two_week_high": high_52w,
            "fifty_two_week_low": low_52w,
            "position_in_52w_range_percent": position_in_range,
            "market_cap_millions": _format_millions(market_cap),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange", ""),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "error": f"Could not fetch current data: {e}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


def _parse_quarterly_financials(stock) -> Dict[str, Any]:
    """Extract revenue and earnings trend from yfinance quarterly financials."""
    result = {
        "revenue_series": [],
        "net_income_series": [],
        "ebitda_series": [],
        "latest_quarter_revenue_millions": None,
        "latest_quarter_net_income_millions": None,
        "revenue_yoy_growth_percent": None,
        "earnings_yoy_growth_percent": None,
        "revenue_trend": "unknown",
        "earnings_trend": "unknown",
    }
    try:
        fin = stock.quarterly_financials
        if fin is not None and not fin.empty:
            # Common index labels across yfinance versions
            revenue_idx = next(
                (idx for idx in fin.index if "Total Revenue" in str(idx) or "Revenue" in str(idx)),
                None,
            )
            ni_idx = next(
                (idx for idx in fin.index if "Net Income" in str(idx)),
                None,
            )
            ebitda_idx = next(
                (idx for idx in fin.index if "EBITDA" in str(idx)),
                None,
            )
            cols = list(fin.columns)
            if revenue_idx is not None:
                values = [_safe_float(fin.loc[revenue_idx, col]) for col in cols]
                result["revenue_series"] = [
                    {"period": _col_label(col), "value_millions": _format_millions(v)}
                    for col, v in zip(cols, values)
                ]
                if len(values) >= 1:
                    result["latest_quarter_revenue_millions"] = _format_millions(values[0])
                if len(values) >= 5:
                    result["revenue_yoy_growth_percent"] = _pct_change(values[0], values[4])
            if ni_idx is not None:
                values = [_safe_float(fin.loc[ni_idx, col]) for col in cols]
                result["net_income_series"] = [
                    {"period": _col_label(col), "value_millions": _format_millions(v)}
                    for col, v in zip(cols, values)
                ]
                if len(values) >= 1:
                    result["latest_quarter_net_income_millions"] = _format_millions(values[0])
                if len(values) >= 5:
                    result["earnings_yoy_growth_percent"] = _pct_change(values[0], values[4])
            if ebitda_idx is not None:
                values = [_safe_float(fin.loc[ebitda_idx, col]) for col in cols]
                result["ebitda_series"] = [
                    {"period": _col_label(col), "value_millions": _format_millions(v)}
                    for col, v in zip(cols, values)
                ]

        # Determine trend direction from latest 4 quarters if available
        if len(result["revenue_series"]) >= 4:
            vals = [s["value_millions"] for s in result["revenue_series"][:4] if s["value_millions"] is not None]
            if len(vals) >= 4:
                if vals[0] > vals[1] > vals[2] > vals[3]:
                    result["revenue_trend"] = "up"
                elif vals[0] < vals[1] < vals[2] < vals[3]:
                    result["revenue_trend"] = "down"
                else:
                    result["revenue_trend"] = "mixed"
        if len(result["net_income_series"]) >= 4:
            vals = [s["value_millions"] for s in result["net_income_series"][:4] if s["value_millions"] is not None]
            if len(vals) >= 4:
                if vals[0] > vals[1] > vals[2] > vals[3]:
                    result["earnings_trend"] = "up"
                elif vals[0] < vals[1] < vals[2] < vals[3]:
                    result["earnings_trend"] = "down"
                else:
                    result["earnings_trend"] = "mixed"
    except Exception as e:
        result["error_revenue"] = str(e)
    return result


def _col_label(col) -> str:
    try:
        if hasattr(col, "strftime"):
            return col.strftime("%Y-%m-%d")
    except Exception:
        pass
    return str(col)


def _parse_balance_sheet(stock) -> Dict[str, Any]:
    """Extract balance sheet health indicators."""
    result = {
        "total_debt_millions": None,
        "cash_millions": None,
        "total_assets_millions": None,
        "total_liabilities_millions": None,
        "shareholders_equity_millions": None,
        "current_ratio": None,
        "quick_ratio": None,
        "debt_to_equity": None,
        "net_debt_millions": None,
        "debt_to_assets": None,
    }
    try:
        bs = stock.quarterly_balance_sheet
        if bs is not None and not bs.empty:
            latest = bs.columns[0]
            def _val(keywords):
                for idx in bs.index:
                    if any(kw.lower() in str(idx).lower() for kw in keywords):
                        return _safe_float(bs.loc[idx, latest])
                return None

            total_debt = _val(["Total Debt"])
            cash = _val(["Cash And Cash Equivalents", "Cash and Cash Equivalents"])
            total_assets = _val(["Total Assets"])
            total_liabilities = _val(["Total Liabilities Net Minority Interest", "Total Liabilities"])
            shareholders_equity = _val(["Stockholders Equity", "Shareholders Equity", "Common Stock Equity"])
            current_assets = _val(["Current Assets"])
            current_liabilities = _val(["Current Liabilities"])
            inventory = _val(["Inventory"])

            result["total_debt_millions"] = _format_millions(total_debt)
            result["cash_millions"] = _format_millions(cash)
            result["total_assets_millions"] = _format_millions(total_assets)
            result["total_liabilities_millions"] = _format_millions(total_liabilities)
            result["shareholders_equity_millions"] = _format_millions(shareholders_equity)

            if total_debt is not None and cash is not None:
                result["net_debt_millions"] = _format_millions(total_debt - cash)
            if current_assets is not None and current_liabilities is not None and current_liabilities != 0:
                result["current_ratio"] = round(current_assets / current_liabilities, 2)
            if current_assets is not None and inventory is not None and current_liabilities is not None and current_liabilities != 0:
                result["quick_ratio"] = round((current_assets - inventory) / current_liabilities, 2)
            if total_debt is not None and shareholders_equity is not None and shareholders_equity != 0:
                result["debt_to_equity"] = round(total_debt / shareholders_equity, 2)
            if total_debt is not None and total_assets is not None and total_assets != 0:
                result["debt_to_assets"] = round(total_debt / total_assets, 2)
    except Exception as e:
        result["error_balance_sheet"] = str(e)
    return result


def _derive_risks(info: Dict[str, Any], financials: Dict[str, Any], balance: Dict[str, Any]) -> List[str]:
    """Generate a list of risk flags from raw metrics."""
    risks = []
    try:
        if _safe_float(info.get("profitMargins")) and info.get("profitMargins", 0) < 0:
            risks.append("Company is currently unprofitable (negative profit margin).")
        if _safe_float(info.get("earningsGrowth")) and info.get("earningsGrowth", 0) < -0.1:
            risks.append("Earnings growth is deeply negative year-over-year.")
        if balance.get("debt_to_equity") is not None and balance["debt_to_equity"] > 1.0:
            risks.append("Debt-to-equity ratio above 1.0 — balance sheet is highly leveraged.")
        if balance.get("current_ratio") is not None and balance["current_ratio"] < 1.0:
            risks.append("Current ratio below 1.0 — potential short-term liquidity pressure.")
        if _safe_float(info.get("beta")) and info.get("beta", 0) > 1.5:
            risks.append(f"High beta ({info.get('beta'):.2f}) — stock is materially more volatile than the market.")
        if _safe_float(info.get("trailingPE")) and info.get("trailingPE", 0) > 50:
            risks.append("Very high trailing P/E ratio — valuation may be stretched if growth slows.")
        if _safe_float(info.get("priceToBook")) and info.get("priceToBook", 0) > 10:
            risks.append("Very high price-to-book ratio — valuation reliant on future growth.")
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        if sector:
            risks.append(f"Sector exposure: {sector} ({industry or 'industry not disclosed'}).")
        if info.get("country") and info.get("country").lower() != "united states":
            risks.append(f"Non-US domicile ({info.get('country')}) — adds currency/geopolitical risk.")
        # Always include a few macro/contextual risks
        risks.append("Macro risk: interest rates, inflation, and broad equity sentiment affect demand and valuation.")
        risks.append("Execution risk: forward guidance and management execution must match expectations.")
    except Exception as e:
        risks.append(f"Risk derivation incomplete: {e}")
    return risks


def _competitive_landscape(info: Dict[str, Any]) -> Dict[str, Any]:
    """Build a qualitative competitive snapshot."""
    sector = info.get("sector", "Unknown")
    industry = info.get("industry", "Unknown")
    market_cap = _safe_float(info.get("marketCap"))
    pe = _safe_float(info.get("trailingPE"))
    forward_pe = _safe_float(info.get("forwardPE"))
    profit_margin = _safe_float(info.get("profitMargins"))
    revenue_growth = _safe_float(info.get("revenueGrowth"))

    # Size tier
    size_tier = "Unknown"
    if market_cap is not None:
        if market_cap >= 200_000_000_000:
            size_tier = "Mega-cap"
        elif market_cap >= 10_000_000_000:
            size_tier = "Large-cap"
        elif market_cap >= 2_000_000_000:
            size_tier = "Mid-cap"
        else:
            size_tier = "Small-cap"

    assessment = "neutral"
    if profit_margin is not None and revenue_growth is not None:
        if profit_margin > 0.15 and revenue_growth > 0.10:
            assessment = "strong"
        elif profit_margin < 0 and revenue_growth < 0:
            assessment = "weak"
        elif profit_margin < 0 and revenue_growth > 0:
            assessment = "growth-stage, unprofitable"
        elif profit_margin > 0 and revenue_growth < 0:
            assessment = "mature, slowing"

    return {
        "sector": sector,
        "industry": industry,
        "size_tier": size_tier,
        "market_cap_millions": _format_millions(market_cap),
        "trailing_pe": pe,
        "forward_pe": forward_pe,
        "profit_margin": profit_margin,
        "revenue_growth": revenue_growth,
        "relative_assessment": assessment,
        "note": (
            "Competitors are inferred from sector/industry. Compare margin, growth, and valuation "
            "against the largest names in the same industry for a true relative ranking."
        ),
    }


def _future_growth(info: Dict[str, Any], financials: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize growth drivers and what has to go right."""
    earnings_growth = _safe_float(info.get("earningsGrowth"))
    revenue_growth = _safe_float(info.get("revenueGrowth"))
    target_mean = _safe_float(info.get("targetMeanPrice"))
    target_high = _safe_float(info.get("targetHighPrice"))
    target_low = _safe_float(info.get("targetLowPrice"))
    price = _safe_float(info.get("currentPrice")) or _safe_float(info.get("regularMarketPrice"))
    upside_to_target = None
    if price is not None and target_mean is not None and price != 0:
        upside_to_target = round(((target_mean - price) / price) * 100, 2)

    what_has_to_go_right = []
    if revenue_growth is not None and revenue_growth > 0.1:
        what_has_to_go_right.append("Maintain or accelerate revenue growth trajectory.")
    if earnings_growth is not None and earnings_growth < 0:
        what_has_to_go_right.append("Return to profitability / expand margins.")
    if _safe_float(info.get("profitMargins")) and info.get("profitMargins", 0) < 0.15:
        what_has_to_go_right.append("Improve operating margins to justify valuation.")
    what_has_to_go_right.append("Execute on guidance and avoid material operational setbacks.")
    what_has_to_go_right.append("Macro and sector sentiment remain supportive.")

    return {
        "earnings_growth": earnings_growth,
        "revenue_growth": revenue_growth,
        "analyst_target_mean": target_mean,
        "analyst_target_high": target_high,
        "analyst_target_low": target_low,
        "upside_to_target_percent": upside_to_target,
        "what_has_to_go_right": what_has_to_go_right,
    }


def _business_operations(info: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize what the company actually does right now."""
    return {
        "company_name": info.get("longName", ""),
        "country": info.get("country", ""),
        "employees": _safe_int(info.get("fullTimeEmployees")),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "website": info.get("website", ""),
        "business_summary": info.get("longBusinessSummary", ""),
    }


def get_deep_research(ticker: str) -> Dict[str, Any]:
    """Pull financials, balance sheet, competitors, risks, and growth outlook."""
    ticker = ticker.upper()
    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
        financials = _parse_quarterly_financials(stock)
        balance = _parse_balance_sheet(stock)

        # Merge yfinance info metrics for display
        key_metrics = {
            "trailing_pe": _safe_float(info.get("trailingPE")),
            "forward_pe": _safe_float(info.get("forwardPE")),
            "peg_ratio": _safe_float(info.get("pegRatio")),
            "price_to_book": _safe_float(info.get("priceToBook")),
            "price_to_sales": _safe_float(info.get("priceToSalesTrailing12Months")),
            "profit_margin": _safe_float(info.get("profitMargins")),
            "operating_margin": _safe_float(info.get("operatingMargins")),
            "return_on_equity": _safe_float(info.get("returnOnEquity")),
            "return_on_assets": _safe_float(info.get("returnOnAssets")),
            "beta": _safe_float(info.get("beta")),
            "dividend_yield": _safe_float(info.get("dividendYield")),
        }

        return {
            "ticker": ticker,
            "financials": financials,
            "balance_sheet": balance,
            "key_metrics": key_metrics,
            "business_operations": _business_operations(info),
            "competitive_landscape": _competitive_landscape(info),
            "risks": _derive_risks(info, financials, balance),
            "future_growth": _future_growth(info, financials),
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "error": f"Could not fetch deep research: {e}",
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }


def get_news_check(ticker: str, yahoo_client: YahooFinanceClient) -> Dict[str, Any]:
    """Surface recent material news and developments."""
    ticker = ticker.upper()
    try:
        articles = yahoo_client.get_news(ticker, max_articles=15) or []
        # Normalize date and keep the most recent 10
        now = datetime.utcnow()
        recent = []
        for art in articles:
            title = (art.get("title") or "").strip()
            if not title:
                continue
            pub = art.get("published_at", "")
            try:
                if pub.endswith("Z"):
                    pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                else:
                    pub_dt = datetime.fromisoformat(pub)
                if pub_dt.tzinfo:
                    pub_dt = pub_dt.replace(tzinfo=None)
                age_days = (now - pub_dt).days
            except Exception:
                age_days = None
            recent.append({
                "title": title,
                "source": art.get("source", "Yahoo Finance"),
                "published_at": pub,
                "age_days": age_days,
                "url": art.get("url", ""),
                "summary": (art.get("description") or "")[:300],
            })
        recent.sort(key=lambda x: x["age_days"] if x["age_days"] is not None else 9999)
        material = [r for r in recent if r["age_days"] is not None and r["age_days"] <= 7]
        return {
            "ticker": ticker,
            "total_articles_found": len(recent),
            "material_recent_count": len(material),
            "articles": recent[:10],
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "error": f"Could not fetch news: {e}",
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }


def run_comprehensive_analysis(ticker: str, yahoo_client: YahooFinanceClient) -> Dict[str, Any]:
    """Run all three sections and return a unified report."""
    ticker = ticker.upper()
    return {
        "ticker": ticker,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "current_data": get_current_data(ticker),
        "deep_research": get_deep_research(ticker),
        "news_check": get_news_check(ticker, yahoo_client),
    }
