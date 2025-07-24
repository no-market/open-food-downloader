#!/usr/bin/env python3
"""
Utility functions for the open-food-downloader project.
Contains string formatting and processing functions.
"""

import re
try:
    import inflection
    HAS_INFLECTION = True
except ImportError:
    HAS_INFLECTION = False


def format_search_string(input_string: str) -> str:
    """
    Format search string according to requirements:
    - Split camelCase format words  
    - Split numbers from letters
    - Remove "," and ";"
    - Convert to lowercase
    - Keep space " " as separator
    
    Uses the inflection library for camelCase handling if available and appropriate,
    falls back to regex-based approach for better Polish character support.
    
    Args:
        input_string: The input search string
        
    Returns:
        Formatted search string
        
    Examples:
        >>> format_search_string("BorówkaAmeryk500g")
        'borówka ameryk 500 g'
        >>> format_search_string("iPhone13,Pro;500g")
        'i phone 13 pro 500 g'
        >>> format_search_string("XMLHttpRequest")
        'xml http request'
        >>> format_search_string("KrówkaŚmietankowa")
        'krówka śmietankowa'
    """
    if not input_string:
        return ""
    
    # Step 1: Replace commas and semicolons with spaces first
    formatted = re.sub(r'[,;]', ' ', input_string)
    
    # Step 2: Split camelCase
    # Check if string contains Polish characters - if so, use regex approach
    has_polish_chars = bool(re.search(r'[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', formatted))
    
    if HAS_INFLECTION and not has_polish_chars:
        # Use inflection for strings without Polish characters
        try:
            formatted = inflection.underscore(formatted)
            formatted = formatted.replace('_', ' ')
        except Exception:
            # Fall back to regex approach if inflection fails
            formatted = _split_camel_case_regex(formatted)
    else:
        # Use regex approach for Polish characters or when inflection is not available
        formatted = _split_camel_case_regex(formatted)
    
    # Step 3: Split numbers from letters - insert space between letters and numbers
    # Insert space before numbers that follow letters (including Unicode letters)
    formatted = re.sub(r'([a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ])(\d)', r'\1 \2', formatted)
    # Insert space after numbers that are followed by letters  
    formatted = re.sub(r'(\d)([a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ])', r'\1 \2', formatted)
    
    # Step 4: Convert to lowercase
    formatted = formatted.lower()
    
    # Step 5: Normalize spaces - replace multiple spaces with single space and strip
    formatted = re.sub(r'\s+', ' ', formatted).strip()
    
    return formatted


def _split_camel_case_regex(text: str) -> str:
    """
    Split camelCase using regex patterns (fallback method).
    
    Args:
        text: Input text to split
        
    Returns:
        Text with camelCase split by spaces
    """
    # Split on lowercase letter followed by uppercase letter (including Polish characters)
    text = re.sub(r'([a-ząćęłńóśźż])([A-ZĄĆĘŁŃÓŚŹŻ])', r'\1 \2', text)
    # Split consecutive uppercase letters when followed by lowercase letter (e.g., XMLHttp -> XML Http)
    text = re.sub(r'([A-ZĄĆĘŁŃÓŚŹŻ])([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż])', r'\1 \2', text)
    # Split between consecutive uppercase letters if they are 3+ chars (e.g., XMLDOM -> XML DOM)
    text = re.sub(r'([A-ZĄĆĘŁŃÓŚŹŻ]{2,})([A-ZĄĆĘŁŃÓŚŹŻ]{2,})', r'\1 \2', text)
    return text


def is_inflection_available() -> bool:
    """
    Check if the inflection library is available.
    
    Returns:
        True if inflection library is available, False otherwise
    """
    return HAS_INFLECTION