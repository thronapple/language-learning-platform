"""
Text processing utilities for content import and analysis.
"""
import re
import logging
from typing import List

logger = logging.getLogger(__name__)


class TextProcessor:
    """Handles text processing operations like sentence splitting and cleanup."""

    def __init__(self):
        # Sentence boundary patterns for multiple languages
        self.sentence_patterns = [
            # English punctuation
            r"(?<=[\.!?])\s+",
            # Chinese punctuation
            r"(?<=[。！？])\s*",
            # Additional patterns can be added here
        ]

    def split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using multiple language patterns.

        Args:
            text: Input text to split

        Returns:
            List of sentence strings
        """
        if not text or not text.strip():
            return []

        # Normalize whitespace
        text = text.replace("\r", " ").replace("\n", " ")
        text = re.sub(r"\s+", " ", text).strip()

        # Apply sentence splitting patterns
        parts = [text]
        for pattern in self.sentence_patterns:
            new_parts = []
            for part in parts:
                new_parts.extend(re.split(pattern, part))
            parts = new_parts

        # Clean and filter segments
        segments = []
        for part in parts:
            part = part.strip()
            if part and len(part) > 1:  # Filter out single characters
                segments.append(part)

        logger.debug(f"Split text into {len(segments)} sentences", extra={
            "original_length": len(text),
            "segments_count": len(segments)
        })

        return segments

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.

        Args:
            text: Input text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common HTML entities that might have been missed
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")

        return text.strip()

    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """
        Extract potential keywords from text (basic implementation).

        Args:
            text: Input text
            max_keywords: Maximum number of keywords to return

        Returns:
            List of keyword strings
        """
        if not text:
            return []

        # Simple keyword extraction - can be enhanced with NLP libraries
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fa5]{3,}\b', text.lower())

        # Filter common stop words (basic set)
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
            'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }

        keywords = [word for word in words if word not in stop_words]

        # Count frequency and return most common
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        return [word for word, freq in sorted_words[:max_keywords]]

    def estimate_reading_level(self, text: str) -> str:
        """
        Estimate reading difficulty level (basic implementation).

        Args:
            text: Input text to analyze

        Returns:
            Reading level estimate (A1, A2, B1, B2, C1, C2)
        """
        if not text:
            return "A1"

        sentences = self.split_sentences(text)
        if not sentences:
            return "A1"

        # Simple heuristics based on sentence length and complexity
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

        # Basic level estimation
        if avg_sentence_length <= 8:
            return "A1"
        elif avg_sentence_length <= 12:
            return "A2"
        elif avg_sentence_length <= 16:
            return "B1"
        elif avg_sentence_length <= 20:
            return "B2"
        elif avg_sentence_length <= 25:
            return "C1"
        else:
            return "C2"