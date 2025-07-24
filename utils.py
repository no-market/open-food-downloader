#!/usr/bin/env python3
"""
Utility functions for the open-food-downloader project.
Contains string formatting and processing functions.
"""

import re


def format_search_string(input_string: str) -> str:
    """
    Format search string according to requirements:
    - Split camelCase format words  
    - Split numbers from letters
    - Remove "," and ";"
    - Convert to lowercase
    - Keep space " " as separator
    
    Uses regex-based approach for camelCase splitting to support
    all character sets including Polish characters.
    
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
    
    # Step 2: Split camelCase using regex approach
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
    Split camelCase using regex patterns.
    
    Args:
        text: Input text to split
        
    Returns:
        Text with camelCase split by spaces
    """
    # Split on lowercase letter followed by uppercase letter (including Polish characters)
    text = re.sub(r'([a-ząćęłńóśźż])([A-ZĄĆĘŁŃÓŚŹŻ])', r'\1 \2', text)
    
    # Split consecutive uppercase letters when followed by lowercase letter (e.g., XMLHttp -> XML Http)
    # This handles cases like "XMLHttpRequest" -> "XML Http Request"
    text = re.sub(r'([A-ZĄĆĘŁŃÓŚŹŻ]+)([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż])', r'\1 \2', text)
    
    return text