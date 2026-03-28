"""
Utility functions for Sathi AI.
Contains shared functionality to avoid circular imports.
"""

import re
from difflib import SequenceMatcher

# Define wake words with phonetic variations
WAKE_WORDS = [
    "hey sathi", "hi sathi", "ok sathi",
    "hello sathi", "dear sathi", "sathi please",
    "sathi help", "listen sathi", "sathi are you there",
]

def is_wake_word(text, span_threshold=0.60, token_threshold=0.75):
    """
    Improved wake-word scoring with lower thresholds for better recognition.
    
    Returns a float score between 0.0 and 1.0 indicating how closely the
    given `text` matches any of the `WAKE_WORDS`.
    
    Args:
        text: The text to check
        span_threshold: Threshold for sequence matching (default: 0.60)
        token_threshold: Threshold for token matching (default: 0.75)
        
    Returns:
        float: Score between 0.0 and 1.0
    """
    import re
    from difflib import SequenceMatcher
    from typing import List, Tuple, Optional
    
    # Define wake words
    WAKE_WORDS = ["sathi", "sathy", "sati", "sathi"]
    
    # Normalize text
    text = text.lower().strip()
    
    # Check for exact match first (fast path)
    if text in WAKE_WORDS:
        return 1.0
    
    # Check for substring match
    for word in WAKE_WORDS:
        if word in text or text in word:
            return 0.9
    
    # Tokenize input
    tokens = re.findall(r'\w+', text)
    
    # Check for token subset match
    wake_tokens = set(WAKE_WORDS)
    input_tokens = set(tokens)
    
    if wake_tokens.issubset(input_tokens):
        return 0.85
    
    # Use SequenceMatcher for fuzzy matching
    best_score = 0.0
    
    for wake_word in WAKE_WORDS:
        # Check full text match
        score = SequenceMatcher(None, text, wake_word).ratio()
        if score > best_score:
            best_score = score
        
        # Check token-level matches
        for token in tokens:
            token_score = SequenceMatcher(None, token, wake_word).ratio()
            if token_score > best_score:
                best_score = token_score
    
    # Apply thresholds
    if best_score >= span_threshold:
        return best_score
    
    # Check for partial matches in longer text
    for wake_word in WAKE_WORDS:
        if wake_word in text or any(wake_word.startswith(t) for t in tokens):
            return max(best_score, 0.7)
    
    return best_score
