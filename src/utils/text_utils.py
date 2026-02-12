"""Text processing utilities"""

import re
from typing import Optional


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_keywords(text: str, keywords: dict) -> dict:
    """
    Extract matching keywords from text with scores

    Args:
        text: Text to search
        keywords: dict of {keyword: score}

    Returns:
        dict of {keyword: count}
    """
    text_lower = text.lower()
    matches = {}

    for keyword in keywords:
        # Check for phrase (with spaces) or word boundary match
        if ' ' in keyword:
            # Phrase match
            count = text_lower.count(keyword)
        else:
            # Word boundary match
            pattern = r'\b' + re.escape(keyword) + r'\b'
            count = len(re.findall(pattern, text_lower))

        if count > 0:
            matches[keyword] = count

    return matches


def remove_html_tags(html: str) -> str:
    """Remove HTML tags from text"""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    # Decode common HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    # Clean whitespace
    text = clean_text(text)
    return text


def calculate_keyword_score(text: str, keywords: dict) -> float:
    """
    Calculate keyword-based score for text

    Args:
        text: Text to score
        keywords: dict of {keyword: weight}

    Returns:
        Total score
    """
    matches = extract_keywords(text, keywords)
    score = sum(keywords[kw] * count for kw, count in matches.items())
    return score
