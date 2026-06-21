"""Sector mapping utility for sector-relative sentiment analysis.

Maps tickers to their sector ETFs and provides sector classification.
"""
from typing import Optional, Dict, List

# Sector ETF mapping - major US market sectors
SECTOR_ETFS = {
    "technology": "XLK",
    "healthcare": "XLV",
    "financials": "XLF",
    "consumer_discretionary": "XLY",
    "consumer_staples": "XLP",
    "industrials": "XLI",
    "energy": "XLE",
    "utilities": "XLU",
    "materials": "XLB",
    "real_estate": "XLRE",
    "communication": "XLC",
}

# Ticker to sector mapping (selective list of common tickers)
TICKER_SECTORS: Dict[str, str] = {
    # Technology
    "AAPL": "XLK",
    "MSFT": "XLK",
    "NVDA": "XLK",
    "GOOGL": "XLK",
    "META": "XLK",
    "AMZN": "XLK",
    "AVGO": "XLK",
    "TSLA": "XLK",
    "AMD": "XLK",
    "ORCL": "XLK",
    "CRM": "XLK",
    "ADBE": "XLK",
    "QCOM": "XLK",
    "INTC": "XLK",
    "CSCO": "XLK",
    "PLTR": "XLK",
    "COIN": "XLK",
    "MSTR": "XLK",
    "LITE": "XLK",
    "NVTS": "XLK",
    "MU": "XLK",
    "ASML": "XLK",
    "SMCI": "XLK",
    "NB": "XLK",
    # Healthcare
    "LLY": "XLV",
    "JNJ": "XLV",
    "UNH": "XLV",
    "MRK": "XLV",
    "ABBV": "XLV",
    # Financials
    "JPM": "XLF",
    "V": "XLF",
    "MA": "XLF",
    "BRK.B": "XLF",
    "KMI": "XLF",
    "WMB": "XLF",
    "CAT": "XLF",
    # Consumer Discretionary
    "HD": "XLY",
    "MCD": "XLY",
    "COST": "XLY",
    "WMT": "XLP",  # Staples
    "BABA": "XLY",
    "UBER": "XLY",
    # Energy
    "XOM": "XLE",
    "EQT": "XLE",
    "VST": "XLE",
    "FCX": "XLE",  # Materials/Energy hybrid
    "GE": "XLE",  # Industrial/Energy hybrid
    # Industrials
    "BA": "XLI",
    "LMT": "XLI",
    "RTX": "XLI",
    # Materials
    "NUE": "XLB",
    "MP": "XLB",
    "UUUU": "XLB",
    # Utilities
    "USAR": "XLU",
    # Real Estate
    "XLRE": "XLRE",
}

# Sector names for display
SECTOR_NAMES = {
    "XLK": "Technology",
    "XLV": "Healthcare",
    "XLF": "Financials",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
    "XLI": "Industrials",
    "XLE": "Energy",
    "XLU": "Utilities",
    "XLB": "Materials",
    "XLRE": "Real Estate",
    "XLC": "Communication Services",
    "SPY": "Broad Market",
    "QQQ": "Nasdaq 100",
    "IWM": "Russell 2000",
}


def get_sector_etf(ticker: str) -> Optional[str]:
    """Get the sector ETF for a given ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Sector ETF symbol or None if not mapped
    """
    return TICKER_SECTORS.get(ticker.upper())


def get_sector_name(etf: str) -> str:
    """Get the human-readable sector name for an ETF.
    
    Args:
        etf: Sector ETF symbol
        
    Returns:
        Sector name
    """
    return SECTOR_NAMES.get(etf, etf)


def get_all_sector_etfs() -> List[str]:
    """Get all sector ETF symbols.
    
    Returns:
        List of sector ETF symbols
    """
    return list(SECTOR_ETFS.values())


def get_tickers_in_sector(etf: str) -> List[str]:
    """Get all tickers mapped to a sector ETF.
    
    Args:
        etf: Sector ETF symbol
        
    Returns:
        List of ticker symbols in that sector
    """
    return [ticker for ticker, sector in TICKER_SECTORS.items() if sector == etf]


def is_sector_etf(ticker: str) -> bool:
    """Check if a ticker is a sector ETF.
    
    Args:
        ticker: Ticker symbol
        
    Returns:
        True if it's a sector ETF
    """
    return ticker.upper() in SECTOR_NAMES
