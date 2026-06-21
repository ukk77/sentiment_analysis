from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from app.utils.text import clean_text, truncate_text, deduplicate_articles
from app.config import get_settings
from app.services.article_filter import get_source_weight
from huggingface_hub import login


@dataclass
class SentimentResult:
    label: str
    score: float
    confidence: float


class FinBERTAnalyzer:
    """
    Sentiment analyzer using FinBERT model from Hugging Face.
    FinBERT is specifically trained on financial text for better accuracy.
    """
    
    MODEL_NAME = "ProsusAI/finbert"
    
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.classifier = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_model()
    
    def _load_model(self):
        """Load the FinBERT model and tokenizer."""
        try:
            # Authenticate with Hugging Face if token is available
            settings = get_settings()
            if settings.HF_TOKEN:
                print("Authenticating with Hugging Face...")
                login(token=settings.HF_TOKEN)
            
            print(f"Loading FinBERT model on {self.device}...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.MODEL_NAME,
                use_fast=True,
                token=settings.HF_TOKEN if settings.HF_TOKEN else None
            )
            
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.MODEL_NAME,
                token=settings.HF_TOKEN if settings.HF_TOKEN else None
            ).to(self.device)
            
            self.model.eval()
            
            # Create pipeline for easier inference
            self.classifier = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1,
                return_all_scores=True
            )
            
            print("FinBERT model loaded successfully")
            
        except Exception as e:
            print(f"Error loading FinBERT model: {e}")
            raise
    
    def analyze_text(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of a single text.
        
        Args:
            text: Text to analyze
        
        Returns:
            SentimentResult with label and scores
        """
        if not text or not text.strip():
            return SentimentResult(label="neutral", score=0.0, confidence=0.0)
        
        # Clean and prepare text
        clean = clean_text(text)
        clean = truncate_text(clean, max_length=512)
        
        try:
            # Get prediction using direct model inference for better control
            inputs = self.tokenizer(clean, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                probs = probs.cpu().numpy()[0]
            
            # FinBERT labels: 0=positive, 1=negative, 2=neutral
            labels = ["positive", "negative", "neutral"]
            
            # Find the highest probability label
            best_idx = probs.argmax()
            label = labels[best_idx]
            confidence = float(probs[best_idx])
            
            # Calculate sentiment score on -1 to 1 scale
            # positive = 1, neutral = 0, negative = -1
            if label == "positive":
                sentiment_score = confidence
            elif label == "negative":
                sentiment_score = -confidence
            else:
                sentiment_score = 0.0
            
            return SentimentResult(
                label=label,
                score=sentiment_score,
                confidence=confidence
            )
            
        except Exception as e:
            print(f"Error analyzing text: {e}")
            import traceback
            traceback.print_exc()
            return SentimentResult(label="neutral", score=0.0, confidence=0.0)
    
    def analyze_article(self, article: Dict) -> Dict:
        """
        Analyze sentiment of a news article.
        
        Args:
            article: Article dictionary with title, description, content
        
        Returns:
            Article dictionary with added sentiment data
        """
        # Combine title and content for analysis
        title = article.get("title", "")
        description = article.get("description", "")
        content = article.get("content", "")
        
        # Use title + description primarily, content if available
        text_to_analyze = f"{title}. {description}"
        if content and len(content) > 50:
            text_to_analyze += f" {content}"
        
        sentiment = self.analyze_text(text_to_analyze)
        
        # Add sentiment data to article
        article_with_sentiment = {
            **article,
            "sentiment": sentiment.label,
            "sentiment_score": sentiment.score,
            "confidence": sentiment.confidence
        }
        
        return article_with_sentiment
    
    def analyze_articles(
        self,
        articles: List[Dict],
        min_confidence: float = 0.0,
    ) -> Tuple[List[Dict], Dict]:
        """
        Analyze sentiment for multiple articles.

        Args:
            articles: List of article dictionaries
            min_confidence: FinBERT relevance threshold. Articles where the
                highest-probability class is below this are dropped as
                likely off-topic (FinBERT trained on financial text tends
                to produce confident predictions on genuine financial
                content). Set to 0.0 to disable. 0.40 is a good default.

        Returns:
            Tuple of (articles with sentiment, aggregated metrics)
        """
        if not articles:
            return [], {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "average_score": 0.0,
                "overall_sentiment": "neutral",
                "relevance_dropped": 0,
            }

        # Deduplicate first (legacy basic dedup; stronger filter runs upstream)
        unique_articles = deduplicate_articles(articles)

        # Analyze each article
        analyzed_all = []
        for article in unique_articles:
            analyzed_article = self.analyze_article(article)
            analyzed_all.append(analyzed_article)

        # FinBERT relevance pre-filter: drop articles where the model is
        # uncertain (max prob < threshold). These are typically off-topic
        # articles that slipped through keyword/domain filtering.
        if min_confidence > 0.0:
            analyzed = [a for a in analyzed_all if a.get("confidence", 0.0) >= min_confidence]
            relevance_dropped = len(analyzed_all) - len(analyzed)
            if relevance_dropped > 0:
                print(f"[finbert_relevance] dropped {relevance_dropped} articles with confidence < {min_confidence}")
        else:
            analyzed = analyzed_all
            relevance_dropped = 0

        # Stamp source credibility weight onto each article
        for article in analyzed:
            article["source_weight"] = get_source_weight(article)

        # Calculate aggregated metrics — use source-credibility weighted average
        total = len(analyzed)
        positive = sum(1 for a in analyzed if a["sentiment"] == "positive")
        negative = sum(1 for a in analyzed if a["sentiment"] == "negative")
        neutral = sum(1 for a in analyzed if a["sentiment"] == "neutral")

        # Credibility-weighted average sentiment score
        weights = [a["source_weight"] for a in analyzed]
        scores = [a["sentiment_score"] for a in analyzed]
        total_weight = sum(weights)
        if total_weight > 0:
            avg_score = float(np.average(scores, weights=weights))
        else:
            avg_score = float(np.mean(scores)) if scores else 0.0

        # Compute impact score per article: |score - avg| * confidence * source_weight, normalized to 0-1
        for article in analyzed:
            deviation = abs(article["sentiment_score"] - avg_score)
            confidence = article.get("confidence", 0.0)
            sw = article.get("source_weight", 1.0)
            article["impact_score"] = round(float(deviation * confidence * sw / 2.0), 4)

        # Determine overall sentiment
        if avg_score > 0.1:
            overall = "positive"
        elif avg_score < -0.1:
            overall = "negative"
        else:
            overall = "neutral"

        metrics = {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "average_score": float(avg_score),
            "overall_sentiment": overall,
            "confidence": float(np.mean([a["confidence"] for a in analyzed])) if analyzed else 0.0,
            "relevance_dropped": relevance_dropped,
        }
        
        return analyzed, metrics
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None and self.tokenizer is not None
