"""
Strict article matching and filtering to reduce false positives.

Pipeline applied in order:
  1. Cross-source deduplication (by normalized title + URL)
  2. Trusted financial domain whitelist (keyword-sourced articles only)
  3. Title relevance: ticker context regex + company alias map
  4. NER validation: verify article is actually about the target company

FinBERT confidence-based relevance filtering happens in the analyzer
(dropped after sentiment scoring when max_prob < threshold).
"""
import re
from typing import List, Dict, Set, Tuple
from urllib.parse import urlparse
from .ner_validator import get_validator


# ---------------------------------------------------------------------------
# Ticker → alias map for stricter title matching.
# ---------------------------------------------------------------------------
# Common S&P 500 / mega-cap tickers. Falls back to user-provided company_name
# for tickers not listed here.
TICKER_ALIASES: Dict[str, List[str]] = {
    "AAPL": ["Apple", "Apple Inc", "Cupertino", "Tim Cook", "iPhone", "iPad", "Mac ", "macOS", "iOS"],
    "MSFT": ["Microsoft", "Redmond", "Satya Nadella", "Azure", "Xbox", "LinkedIn"],
    "GOOGL": ["Google", "Alphabet", "Sundar Pichai", "YouTube", "DeepMind", "Gemini AI"],
    "GOOG": ["Google", "Alphabet", "Sundar Pichai", "YouTube", "DeepMind", "Gemini AI"],
    "META": ["Meta", "Facebook", "Instagram", "WhatsApp", "Zuckerberg", "Reality Labs"],
    "AMZN": ["Amazon", "AWS", "Andy Jassy", "Bezos", "Whole Foods"],
    "TSLA": ["Tesla", "Elon Musk", "Cybertruck", "Model 3", "Model Y", "Model S", "Model X", "Gigafactory"],
    "NVDA": ["Nvidia", "Jensen Huang", "GeForce", "CUDA", "Blackwell", "Hopper"],
    "NFLX": ["Netflix", "Ted Sarandos", "Reed Hastings"],
    "AMD":  ["AMD", "Advanced Micro Devices", "Lisa Su", "Ryzen", "Radeon", "EPYC"],
    "INTC": ["Intel", "Pat Gelsinger", "Foundry"],
    "JPM":  ["JPMorgan", "JP Morgan", "Jamie Dimon", "Chase Bank"],
    "BAC":  ["Bank of America", "BofA"],
    "WFC":  ["Wells Fargo"],
    "GS":   ["Goldman Sachs", "Goldman"],
    "MS":   ["Morgan Stanley"],
    "C":    ["Citigroup", "Citibank"],
    "WMT":  ["Walmart"],
    "DIS":  ["Disney", "Walt Disney", "Marvel", "Pixar", "ESPN"],
    "PYPL": ["PayPal", "Venmo"],
    "NKE":  ["Nike"],
    "KO":   ["Coca-Cola", "Coca Cola", "Coke Inc"],
    "PEP":  ["PepsiCo", "Pepsi"],
    "MCD":  ["McDonald", "McDonalds", "McDonald's"],
    "SBUX": ["Starbucks"],
    "V":    ["Visa Inc", "Visa card", "Visa stock"],
    "MA":   ["Mastercard"],
    "F":    ["Ford Motor", "Ford Inc", "Ford stock", "Ford shares"],
    "GM":   ["General Motors", "Mary Barra"],
    "BA":   ["Boeing"],
    "HD":   ["Home Depot"],
    "LOW":  ["Lowe's", "Lowes"],
    "PFE":  ["Pfizer"],
    "JNJ":  ["Johnson & Johnson", "J&J"],
    "LLY":  ["Eli Lilly", "Lilly"],
    "MRK":  ["Merck"],
    "UNH":  ["UnitedHealth", "United Health"],
    "XOM":  ["Exxon", "ExxonMobil"],
    "CVX":  ["Chevron"],
    "T":    ["AT&T", "AT&T Inc"],
    "VZ":   ["Verizon"],
    "TMUS": ["T-Mobile"],
    "CRM":  ["Salesforce"],
    "ORCL": ["Oracle"],
    "IBM":  ["IBM", "International Business Machines"],
    "UBER": ["Uber"],
    "LYFT": ["Lyft"],
    "SHOP": ["Shopify"],
    "SQ":   ["Block Inc", "Square Inc", "Jack Dorsey"],
    "COIN": ["Coinbase"],
    "PLTR": ["Palantir"],
    "SNOW": ["Snowflake"],
    "NOW":  ["ServiceNow"],
    "ADBE": ["Adobe"],
    "CSCO": ["Cisco"],
    "AVGO": ["Broadcom"],
    "QCOM": ["Qualcomm"],
    "TXN":  ["Texas Instruments"],
    "ABBV": ["AbbVie"],
    "TMO":  ["Thermo Fisher"],
    "ABT":  ["Abbott Laboratories", "Abbott Labs"],
    "COST": ["Costco"],
    "TGT":  ["Target Corp"],
    "PG":   ["Procter & Gamble", "P&G"],
    "CL":   ["Colgate"],
    "UNP":  ["Union Pacific"],
    "UPS":  ["UPS", "United Parcel"],
    "FDX":  ["FedEx"],
    "RTX":  ["Raytheon", "RTX Corp"],
    "LMT":  ["Lockheed Martin"],
    "GE":   ["General Electric", "GE Aerospace"],
    "CAT":  ["Caterpillar"],
    "DE":   ["John Deere", "Deere & Co"],
    "MMM":  ["3M"],
    "BRK.B": ["Berkshire Hathaway", "Warren Buffett", "Buffett"],
    "BRK.A": ["Berkshire Hathaway", "Warren Buffett", "Buffett"],
    "SPOT": ["Spotify"],
    "ABNB": ["Airbnb"],
    "DASH": ["DoorDash"],
    "RBLX": ["Roblox"],
    "RIVN": ["Rivian"],
    "LCID": ["Lucid Motors", "Lucid Group"],
    "NIO":  ["NIO Inc"],
    "BABA": ["Alibaba"],
    "PDD":  ["Pinduoduo", "Temu"],
    "JD":   ["JD.com"],
    "TSM":  ["TSMC", "Taiwan Semiconductor"],
    "ASML": ["ASML"],
    "SMCI": ["Super Micro", "Supermicro"],
    "MU":   ["Micron"],
    "ARM":  ["Arm Holdings", "Arm Ltd"],
    "MP":   ["MP Materials"],
}


# ---------------------------------------------------------------------------
# Trusted financial/business domains. Only applied to keyword-based sources
# (NewsAPI, Google News, Twitter) where false positives are common.
# Ticker-bound sources (Finnhub, Yahoo, Finviz, SEC EDGAR) skip this check.
# ---------------------------------------------------------------------------
TRUSTED_DOMAINS: Set[str] = {
    # Top-tier finance
    "reuters.com", "bloomberg.com", "wsj.com", "ft.com", "cnbc.com",
    "marketwatch.com", "barrons.com", "investors.com", "thestreet.com",
    "benzinga.com", "seekingalpha.com", "fool.com", "zacks.com",
    "forbes.com", "businessinsider.com", "fortune.com", "economist.com",
    # Yahoo family
    "yahoo.com", "finance.yahoo.com",
    # Data/market sites
    "investing.com", "nasdaq.com", "investopedia.com", "morningstar.com",
    "kiplinger.com", "tipranks.com", "simplywall.st", "stockstotrade.com",
    # Press release wires
    "businesswire.com", "prnewswire.com", "globenewswire.com", "newswire.com",
    "streetinsider.com", "finance.yahoo.com",
    # Tech/business (often covers public companies)
    "techcrunch.com", "theverge.com", "arstechnica.com", "engadget.com",
    "theinformation.com", "axios.com", "quartz.com", "qz.com",
    # Mainstream with business desks
    "nytimes.com", "washingtonpost.com", "bbc.com", "cnn.com",
    "ap.org", "apnews.com", "foxbusiness.com",
    # Canadian / Intl finance
    "financialpost.com", "theglobeandmail.com",
}

# Sources that search by keyword (ticker OR company name) and thus need
# stricter filtering. Ticker-bound sources are trusted by default.
KEYWORD_SOURCES: Set[str] = {"newsapi", "googlenews", "twitter"}

# For sources like Google News where the URL is a redirector (news.google.com),
# we instead check the publisher name embedded in the article.source field
# against this whitelist of trusted publisher names (case-insensitive match).
TRUSTED_PUBLISHERS: Set[str] = {
    "reuters", "bloomberg", "wall street journal", "wsj", "financial times",
    "ft.com", "cnbc", "marketwatch", "barron's", "barrons",
    "investor's business daily", "thestreet", "the street", "benzinga",
    "seeking alpha", "motley fool", "fool.com", "zacks", "forbes",
    "business insider", "fortune", "the economist", "yahoo finance", "yahoo",
    "investing.com", "nasdaq", "investopedia", "morningstar", "tipranks",
    "kiplinger", "pr newswire", "business wire", "globe newswire",
    "streetinsider", "street insider", "techcrunch", "the verge",
    "ars technica", "engadget", "the information", "axios", "quartz",
    "new york times", "nytimes", "washington post", "bbc", "cnn",
    "cnn business", "associated press", "ap", "apnews", "fox business",
    "financial post", "globe and mail", "valuewalk", "simplywall.st",
}


# ---------------------------------------------------------------------------
# Ticker context words: when bare ticker appears in title, require one of
# these nearby to confirm it's about the stock, not an unrelated token.
# ---------------------------------------------------------------------------
FINANCIAL_CONTEXT_WORDS = (
    r"stock|stocks|shares|share|earnings|revenue|ipo|nasdaq|nyse|market|"
    r"trading|trade|ticker|dividend|quarterly|analyst|rating|target|"
    r"bullish|bearish|buy|sell|hold|upgrade|downgrade|price|equity|"
    r"investor|investing|portfolio|valuation|outlook|guidance|forecast"
)


def _build_ticker_pattern(ticker: str) -> re.Pattern:
    """
    Build a regex that matches a ticker in title/description text.

    For tickers with >= 4 characters, bare mention is allowed (unambiguous).
    For shorter tickers (F, T, V, M, HP), require financial context nearby
    to avoid matching random initials or words.
    """
    t = re.escape(ticker.upper())
    if len(ticker) >= 4:
        pattern = (
            rf"(\${t}\b"                                        # $TICKER
            rf"|\({t}\)"                                        # (TICKER)
            rf"|(?:NASDAQ|NYSE|OTC|AMEX):\s*{t}\b"              # Exchange:TICKER
            rf"|\b{t}\b)"                                       # bare TICKER
        )
    else:
        pattern = (
            rf"(\${t}\b"                                        # $TICKER
            rf"|\({t}\)"                                        # (TICKER)
            rf"|(?:NASDAQ|NYSE|OTC|AMEX):\s*{t}\b"              # Exchange:TICKER
            rf"|\b{t}\s+(?:{FINANCIAL_CONTEXT_WORDS})\b"        # TICKER stock/shares/etc
            rf"|\b(?:{FINANCIAL_CONTEXT_WORDS})\s+[\w\s]{{0,20}}\b{t}\b)"  # finance word then TICKER
        )
    return re.compile(pattern, re.IGNORECASE)


def _normalize_title(title: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace for dedup comparison."""
    if not title:
        return ""
    t = re.sub(r"[^\w\s]", " ", title.lower())
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _get_domain(url: str) -> str:
    """Extract root domain from URL, stripping www. prefix."""
    if not url:
        return ""
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def _domain_matches_trusted(domain: str) -> bool:
    """Check if a domain (or any parent domain) is in the trusted list."""
    if not domain:
        return False
    if domain in TRUSTED_DOMAINS:
        return True
    parts = domain.split(".")
    for i in range(1, len(parts) - 1):
        candidate = ".".join(parts[i:])
        if candidate in TRUSTED_DOMAINS:
            return True
    return False


# ---------------------------------------------------------------------------
# Public filter functions
# ---------------------------------------------------------------------------

def deduplicate_articles(articles: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Drop duplicates across sources using normalized title + URL.

    Returns (unique_articles, num_dropped).
    """
    seen_titles: Set[str] = set()
    seen_urls: Set[str] = set()
    unique: List[Dict] = []
    dropped = 0
    for a in articles:
        title_key = _normalize_title(a.get("title", ""))
        url = (a.get("url") or "").strip().lower()
        is_dup = False
        if title_key and title_key in seen_titles:
            is_dup = True
        elif url and url in seen_urls:
            is_dup = True
        if is_dup:
            dropped += 1
            continue
        if title_key:
            seen_titles.add(title_key)
        if url:
            seen_urls.add(url)
        unique.append(a)
    return unique, dropped


def _publisher_matches_trusted(publisher: str) -> bool:
    """Case-insensitive substring match of publisher name against trusted list."""
    if not publisher:
        return False
    p = publisher.lower().strip()
    if p in TRUSTED_PUBLISHERS:
        return True
    # Substring match in either direction (e.g. "Reuters Business" contains "reuters")
    for trusted in TRUSTED_PUBLISHERS:
        if trusted in p or p in trusted:
            return True
    return False


def passes_domain_whitelist(article: Dict) -> bool:
    """
    Keyword-sourced articles must come from a trusted financial source.
      - Google News: check the publisher name (article.source) since the URL
        is a news.google.com redirector.
      - NewsAPI: check the URL domain.
      - Twitter: no URL domain to check, trust through.
      - Ticker-bound sources (Finnhub, Yahoo, Finviz, SEC EDGAR): trust through.
    """
    source_tag = article.get("_source", "")
    if source_tag not in KEYWORD_SOURCES:
        return True
    if source_tag == "twitter":
        return True
    if source_tag == "googlenews":
        # Google News URL is a redirector — check publisher name instead
        return _publisher_matches_trusted(article.get("source", ""))
    # NewsAPI: check URL domain
    domain = _get_domain(article.get("url", ""))
    if not domain:
        return False
    return _domain_matches_trusted(domain)


def passes_title_relevance(article: Dict, ticker: str, company_name: str) -> bool:
    """
    Require ticker pattern OR a known company alias to appear in title
    (or description as fallback). Prevents 'apple fruit' false positives.
    """
    haystack = (article.get("title") or "")
    # Also check description as a fallback to avoid being too strict
    desc = article.get("description") or ""
    combined = f"{haystack} {desc}"
    if not combined.strip():
        return False

    # 1. Ticker context regex
    ticker_pat = _build_ticker_pattern(ticker)
    if ticker_pat.search(combined):
        return True

    # 2. Known alias list + user-provided company name
    aliases = list(TICKER_ALIASES.get(ticker.upper(), []))
    if company_name and company_name not in aliases:
        aliases.append(company_name)
    # Also check simplified company name (drop "Inc.", "Corp.", "Ltd.", etc.)
    simplified = re.sub(r"\b(inc|incorporated|corp|corporation|ltd|limited|co|company|plc|llc|sa|nv|ag)\.?\b",
                        "", company_name.lower()).strip()
    if simplified and simplified != company_name.lower():
        aliases.append(simplified)

    combined_lower = combined.lower()
    for alias in aliases:
        if alias and len(alias) >= 2 and alias.lower() in combined_lower:
            return True
    return False


def filter_articles(
    articles: List[Dict],
    ticker: str,
    company_name: str,
    verbose: bool = True,
    enable_ner_validation: bool = True,
    ner_min_confidence: float = 0.6,
) -> Tuple[List[Dict], Dict[str, int]]:
    """
    Run full filter pipeline: dedup → domain whitelist → title relevance → NER validation.

    Returns (filtered_articles, stats_dict).
    Stats keys: input, dedup_dropped, domain_dropped, title_dropped, ner_validation_dropped, output
    """
    stats = {
        "input": len(articles),
        "dedup_dropped": 0,
        "domain_dropped": 0,
        "title_dropped": 0,
        "ner_validation_dropped": 0,
        "output": 0,
    }

    # 1. Cross-source deduplication
    articles, stats["dedup_dropped"] = deduplicate_articles(articles)

    # 2. Domain whitelist (keyword sources only)
    kept_domain = [a for a in articles if passes_domain_whitelist(a)]
    stats["domain_dropped"] = len(articles) - len(kept_domain)
    articles = kept_domain

    # 3. Title relevance (ticker regex + aliases)
    kept_title = [a for a in articles if passes_title_relevance(a, ticker, company_name)]
    stats["title_dropped"] = len(articles) - len(kept_title)
    articles = kept_title

    # 4. NER validation (verify articles are actually about the company)
    if enable_ner_validation and articles:
        validator = get_validator()
        articles, ner_invalid, ner_stats = validator.validate_articles(
            articles, ticker, company_name, min_confidence=ner_min_confidence
        )
        stats["ner_validation_dropped"] = ner_stats["invalid"]
        if verbose and ner_stats["invalid"] > 0:
            print(f"[article_filter] NER validation dropped {ner_stats['invalid']} articles")

    stats["output"] = len(articles)
    if verbose:
        print(
            f"[article_filter] {stats['input']} in  -> "
            f"dedup -{stats['dedup_dropped']}  -> "
            f"domain -{stats['domain_dropped']}  -> "
            f"title -{stats['title_dropped']}  -> "
            f"ner -{stats['ner_validation_dropped']}  -> "
            f"{stats['output']} out"
        )
    return articles, stats
