import re
from typing import List


def clean_text(text: str) -> str:
    """Clean and normalize text for analysis."""
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-\;\:\'\"]', ' ', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text.strip()


def truncate_text(text: str, max_length: int = 512) -> str:
    """Truncate text to a maximum length while preserving sentence boundaries."""
    if len(text) <= max_length:
        return text
    
    # Try to find the last sentence boundary before max_length
    truncated = text[:max_length]
    last_sentence = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
    
    if last_sentence > max_length * 0.7:  # If we have at least 70% of max length
        return text[:last_sentence + 1]
    
    return truncated


def deduplicate_articles(articles: List[dict]) -> List[dict]:
    """Remove duplicate articles based on title similarity."""
    seen_titles = set()
    unique_articles = []
    
    for article in articles:
        title = article.get('title', '').lower().strip()
        
        # Simple deduplication - check for exact match
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_articles.append(article)
    
    return unique_articles


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """Extract simple keywords from text (can be enhanced with NLP)."""
    # Simple keyword extraction - capitalized words and financial terms
    words = text.split()
    keywords = []
    
    financial_terms = {
        'earnings', 'revenue', 'profit', 'growth', 'decline', 'stock', 'shares',
        'investment', 'investor', 'market', 'trading', 'price', 'dividend',
        'quarter', 'fiscal', 'analyst', 'upgrade', 'downgrade', 'bullish', 'bearish'
    }
    
    for word in words:
        word_clean = re.sub(r'[^\w]', '', word).lower()
        if word_clean in financial_terms:
            keywords.append(word_clean)
    
    # Get unique keywords
    keywords = list(set(keywords))
    
    return keywords[:max_keywords]
