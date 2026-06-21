"""Named Entity Recognition (NER) validation for article disambiguation.

Validates that articles are actually about the target company, not just keyword matches.
Uses pattern matching and entity extraction without requiring heavy ML models.
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class NERValidationResult:
    is_valid: bool
    confidence: float  # 0-1 confidence that article is about the target entity
    matched_entities: List[str]
    reason: Optional[str] = None


class NERValidator:
    """Lightweight NER validator for financial news articles.
    
    Uses pattern matching and entity extraction to verify articles
    are actually about the target company, not false positives.
    """
    
    # Common false positive patterns for tickers that are also common words
    FALSE_POSITIVE_TICKERS = {
        "A": ["article", "a ", "a-"],  # Too short, many false positives
        "AI": ["artificial intelligence", "ai-powered", "ai-based"],
        "ON": ["on the", "on a", "on its"],
        "T": ["the", "t-mobile"],  # AT&T vs common word
        "IT": ["information technology", "it is", "it was"],
        "IN": ["in the", "in a", "investment"],
        "FOR": ["for the", "for a", "for its"],
        "BE": ["will be", "to be", "being"],
        "GO": ["going to", "go public", "go up"],
        "UP": ["up to", "up by", "up from"],
        "NEXT": ["next week", "next month", "next year"],
    }
    
    # Context patterns that strongly indicate a company mention
    COMPANY_CONTEXT_PATTERNS = [
        r"\b(?:shares?|stock|ticker|trading|NASDAQ|NYSE)\s+(?:of\s+)?{entity}",
        r"\b{entity}\s+(?:Corp\.?|Corporation|Inc\.?|Incorporated|Ltd\.?|Limited|Company|Co\.?|Group|Holdings|PLC)",
        r"\b(?:CEO|CFO|CTO|President|Chairman)\s+(?:of\s+)?{entity}",
        r"\b{entity}\s+(?:CEO|CFO|CTO|President|Chairman|executive)",
        r"\b(?:earnings|revenue|profit|loss|quarter|fiscal)\s+(?:report|call|results?|announcement).*?{entity}",
        r"\b{entity}\s+(?:earnings|revenue|profit|loss|quarter|fiscal)",
        r"\b(?:analyst|analysts|brokerage|firm)\s+(?:at|from)\s+{entity}",
        r"\b{entity}\s+(?:said|announced|reported|disclosed|filed)",
    ]
    
    # Negative patterns that suggest the article is NOT about the company
    NEGATIVE_PATTERNS = [
        r"\b(?:Apple\s+(?:fruit|pie|orchard|cider)|fruit\s+apple)\b",
        r"\b(?:Amazon\s+(?:rainforest|river|jungle))\b",
        r"\b(?:Tesla\s+(?:coil|unit|electricity|inventor))\b",
        r"\b(?:oil\s+well|well\s+drilling)\b.*?(?:OXY|XOM|CVX)",  # Energy context vs ticker
    ]
    
    def __init__(self):
        self._pattern_cache: Dict[str, List[re.Pattern]] = {}
    
    def _get_company_patterns(self, ticker: str, company_name: str) -> List[re.Pattern]:
        """Get or create regex patterns for a specific company.
        
        Args:
            ticker: Stock ticker
            company_name: Company name
            
        Returns:
            List of compiled regex patterns
        """
        cache_key = f"{ticker}:{company_name}"
        if cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]
        
        patterns = []
        
        # Exact ticker match (word boundaries)
        patterns.append(re.compile(rf"\b{re.escape(ticker)}\b", re.IGNORECASE))
        
        # Company name parts (for multi-word names, match key words)
        name_parts = company_name.split()
        if len(name_parts) > 1:
            # Full company name
            patterns.append(re.compile(rf"\b{re.escape(company_name)}\b", re.IGNORECASE))
            # Key distinctive words (exclude common words)
            common_words = {"the", "a", "an", "and", "&", "of", "in", "corporation", "inc", "corp", "company", "co", "limited", "ltd", "group", "holdings"}
            for part in name_parts:
                if part.lower() not in common_words and len(part) > 2:
                    patterns.append(re.compile(rf"\b{re.escape(part)}\b", re.IGNORECASE))
        else:
            # Single word company name
            patterns.append(re.compile(rf"\b{re.escape(company_name)}\b", re.IGNORECASE))
        
        # Common variations
        variations = self._get_name_variations(ticker, company_name)
        for var in variations:
            patterns.append(re.compile(rf"\b{re.escape(var)}\b", re.IGNORECASE))
        
        self._pattern_cache[cache_key] = patterns
        return patterns
    
    def _get_name_variations(self, ticker: str, company_name: str) -> List[str]:
        """Generate common name variations for a company.
        
        Args:
            ticker: Stock ticker
            company_name: Company name
            
        Returns:
            List of name variations
        """
        variations = []
        
        # Ticker with $ prefix (social media style)
        variations.append(f"${ticker}")
        
        # Known variations for specific companies
        KNOWN_VARIATIONS = {
            "BRK.B": ["Berkshire", "Berkshire Hathaway", "Buffett"],
            "GOOGL": ["Google", "Alphabet"],
            "META": ["Facebook", "Instagram", "WhatsApp"],
            "XOM": ["Exxon", "Exxon Mobil"],
            "JPM": ["JPMorgan", "JP Morgan", "JPMorgan Chase"],
            "BAC": ["Bank of America", "BofA"],
            "WFC": ["Wells Fargo"],
            "C": ["Citigroup", "Citi"],
            "GS": ["Goldman Sachs"],
            "MS": ["Morgan Stanley"],
            "V": ["Visa"],
            "MA": ["Mastercard"],
            "AXP": ["American Express", "Amex"],
            "DIS": ["Disney"],
            "NFLX": ["Netflix"],
            "TSLA": ["Tesla"],
            "F": ["Ford"],
            "GM": ["General Motors"],
            "BA": ["Boeing"],
            "LMT": ["Lockheed Martin"],
            "RTX": ["Raytheon"],
            "NOC": ["Northrop Grumman"],
            "GE": ["General Electric"],
            "HON": ["Honeywell"],
            "CAT": ["Caterpillar"],
            "DE": ["John Deere"],
            "MMM": ["3M", "Minnesota Mining"],
            "PG": ["Procter & Gamble", "Procter and Gamble"],
            "KO": ["Coca-Cola", "Coca Cola"],
            "PEP": ["PepsiCo", "Pepsi"],
            "WMT": ["Walmart"],
            "TGT": ["Target"],
            "COST": ["Costco"],
            "HD": ["Home Depot"],
            "LOW": ["Lowe's", "Lowes"],
            "MCD": ["McDonald's", "McDonalds"],
            "SBUX": ["Starbucks"],
            "NKE": ["Nike"],
            "LULU": ["Lululemon"],
            "AAPL": ["Apple", "iPhone", "iPad", "Mac", "iOS", "iCloud"],
            "MSFT": ["Microsoft", "Windows", "Azure", "Office 365", "Xbox"],
            "AMZN": ["Amazon", "AWS", "Prime", "Alexa"],
            "NVDA": ["Nvidia", "GeForce", "CUDA"],
            "AMD": ["Advanced Micro Devices"],
            "INTC": ["Intel"],
            "QCOM": ["Qualcomm"],
            "CRM": ["Salesforce"],
            "ADBE": ["Adobe"],
            "ORCL": ["Oracle"],
            "IBM": ["International Business Machines"],
            "UBER": ["Uber", "Uber Eats"],
            "LYFT": ["Lyft"],
            "ABNB": ["Airbnb"],
            "BABA": ["Alibaba", "Ali Baba"],
            "JD": ["JD.com", "Jingdong"],
            "COIN": ["Coinbase"],
            "HOOD": ["Robinhood"],
            "SQ": ["Block", "Square"],
            "PYPL": ["PayPal"],
            "SHOP": ["Shopify"],
            "PLTR": ["Palantir"],
            "SNOW": ["Snowflake"],
            "DDOG": ["Datadog"],
            "MDB": ["MongoDB"],
            "NET": ["Cloudflare"],
            "OKTA": ["Okta"],
            "ZS": ["Zscaler"],
            "CRWD": ["CrowdStrike"],
            "S": ["SentinelOne"],
            "FTNT": ["Fortinet"],
            "PANW": ["Palo Alto Networks"],
            "CYBR": ["CyberArk"],
            "RPD": ["Rapid7"],
            "QLYS": ["Qualys"],
            "TENB": ["Tenable"],
            "VRNS": ["Varonis"],
            "Okta": ["OKTA"],
            "SNOW": ["Snowflake"],
        }
        
        if ticker in KNOWN_VARIATIONS:
            variations.extend(KNOWN_VARIATIONS[ticker])
        
        return list(set(variations))  # Remove duplicates
    
    def _is_false_positive_ticker(self, ticker: str, text: str) -> bool:
        """Check if a ticker match is likely a false positive.
        
        Args:
            ticker: Stock ticker
            text: Article text
            
        Returns:
            True if likely false positive
        """
        ticker_upper = ticker.upper()
        text_lower = text.lower()
        
        if ticker_upper in self.FALSE_POSITIVE_TICKERS:
            patterns = self.FALSE_POSITIVE_TICKERS[ticker_upper]
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    return True
        
        return False
    
    def validate_article(
        self,
        article: Dict,
        ticker: str,
        company_name: str,
        min_confidence: float = 0.6
    ) -> NERValidationResult:
        """Validate that an article is actually about the target company.
        
        Args:
            article: Article dictionary with title, description, etc.
            ticker: Stock ticker
            company_name: Company name
            min_confidence: Minimum confidence threshold to consider valid
            
        Returns:
            NERValidationResult with validation details
        """
        # Combine title and content for analysis
        text_parts = []
        if article.get("title"):
            text_parts.append(article["title"])
        if article.get("description"):
            text_parts.append(article["description"])
        if article.get("content"):
            text_parts.append(article["content"])
        
        full_text = " ".join(text_parts)
        if not full_text:
            return NERValidationResult(
                is_valid=False,
                confidence=0.0,
                matched_entities=[],
                reason="Empty article content"
            )
        
        # Check for false positive tickers
        if self._is_false_positive_ticker(ticker, full_text):
            return NERValidationResult(
                is_valid=False,
                confidence=0.0,
                matched_entities=[],
                reason=f"Ticker {ticker} is likely a false positive (common word)"
            )
        
        # Get patterns for this company
        patterns = self._get_company_patterns(ticker, company_name)
        
        # Count matches
        matched_entities = []
        match_count = 0
        for pattern in patterns:
            matches = pattern.findall(full_text)
            if matches:
                match_count += len(matches)
                matched_entities.extend(matches[:3])  # Keep first 3 matches
        
        matched_entities = list(set(matched_entities))  # Deduplicate
        
        # Calculate confidence based on match diversity and count
        confidence = min(1.0, (match_count * 0.2) + (len(matched_entities) * 0.3))
        
        # Check for strong company context patterns
        context_score = 0
        for pattern_template in self.COMPANY_CONTEXT_PATTERNS:
            # Try with ticker
            pattern_str = pattern_template.format(entity=re.escape(ticker))
            if re.search(pattern_str, full_text, re.IGNORECASE):
                context_score += 0.25
            
            # Try with company name (first word only for multi-word names)
            name_key = company_name.split()[0]
            if len(name_key) > 3:  # Only if it's a substantial word
                pattern_str = pattern_template.format(entity=re.escape(name_key))
                if re.search(pattern_str, full_text, re.IGNORECASE):
                    context_score += 0.2
        
        confidence = min(1.0, confidence + context_score)
        
        # Check for negative patterns
        for neg_pattern in self.NEGATIVE_PATTERNS:
            if re.search(neg_pattern, full_text, re.IGNORECASE):
                confidence *= 0.3  # Significant penalty
        
        is_valid = confidence >= min_confidence
        
        return NERValidationResult(
            is_valid=is_valid,
            confidence=round(confidence, 3),
            matched_entities=matched_entities,
            reason=None if is_valid else f"Confidence {confidence:.2f} below threshold {min_confidence}"
        )
    
    def validate_articles(
        self,
        articles: List[Dict],
        ticker: str,
        company_name: str,
        min_confidence: float = 0.6
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """Validate a batch of articles and separate valid from invalid.
        
        Args:
            articles: List of article dictionaries
            ticker: Stock ticker
            company_name: Company name
            min_confidence: Minimum confidence threshold
            
        Returns:
            Tuple of (valid_articles, invalid_articles, stats)
        """
        valid = []
        invalid = []
        
        for article in articles:
            result = self.validate_article(article, ticker, company_name, min_confidence)
            
            # Add NER metadata to article
            article["_ner_confidence"] = result.confidence
            article["_ner_matched"] = result.matched_entities
            
            if result.is_valid:
                valid.append(article)
            else:
                article["_ner_rejection_reason"] = result.reason
                invalid.append(article)
        
        stats = {
            "input": len(articles),
            "valid": len(valid),
            "invalid": len(invalid),
            "avg_confidence": sum(a.get("_ner_confidence", 0) for a in valid) / len(valid) if valid else 0,
        }
        
        return valid, invalid, stats


# Singleton instance for reuse
_validator_instance: Optional[NERValidator] = None


def get_validator() -> NERValidator:
    """Get or create the NER validator singleton."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = NERValidator()
    return _validator_instance
