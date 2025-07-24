#!/usr/bin/env python3
"""
Utility functions for the open-food-downloader project.
Contains string formatting and processing functions and RapidFuzz scoring.
"""

import re
from typing import Dict, Any, List
from rapidfuzz import fuzz


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


def extract_product_names(product_name_data: List[Dict[str, str]]) -> List[str]:
    """
    Extract unique product names from product_name array.
    
    Args:
        product_name_data: The product_name field from MongoDB document
        
    Returns:
        List of unique product names
    """
    unique_product_names = []
    if isinstance(product_name_data, list):
        seen_texts = set()
        for name_obj in product_name_data:
            if isinstance(name_obj, dict) and 'text' in name_obj:
                text = name_obj['text']
                if text and text not in seen_texts:
                    unique_product_names.append(text)
                    seen_texts.add(text)
    return unique_product_names


def score_product_names(search_string: str, product_names: List[str]) -> float:
    """
    Score product names using RapidFuzz with highest weight.
    
    Args:
        search_string: The search query string
        product_names: List of product names from the document
        
    Returns:
        Best matching score (0-100)
    """
    if not search_string or not product_names:
        return 0.0
    
    best_score = 0.0
    for name in product_names:
        if name:
            # Use both partial_ratio and token_sort_ratio, take the better one
            partial_score = fuzz.partial_ratio(search_string.lower(), name.lower())
            token_score = fuzz.token_sort_ratio(search_string.lower(), name.lower())
            name_score = max(partial_score, token_score)
            best_score = max(best_score, name_score)
    
    return best_score


def score_brands(search_string: str, brands: str) -> float:
    """
    Score brands using RapidFuzz with medium weight.
    
    Args:
        search_string: The search query string
        brands: Brands string from the document
        
    Returns:
        Matching score (0-100)
    """
    if not search_string or not brands:
        return 0.0
    
    # Use both partial_ratio and token_sort_ratio, take the better one
    partial_score = fuzz.partial_ratio(search_string.lower(), brands.lower())
    token_score = fuzz.token_sort_ratio(search_string.lower(), brands.lower())
    
    return max(partial_score, token_score)


def score_categories(search_string: str, categories, categories_tags: List[str] = None) -> float:
    """
    Score categories with specificity weighting (later categories have higher weight).
    
    Args:
        search_string: The search query string
        categories: Categories as string (comma-separated) or list
        categories_tags: Optional list of category tags
        
    Returns:
        Weighted category score (0-100)
    """
    if not search_string:
        return 0.0
    
    scores = []
    
    # Score the categories (handle both string and list formats)
    if categories:
        if isinstance(categories, list):
            category_list = [cat.strip() for cat in categories if cat and cat.strip()]
        else:
            category_list = [cat.strip() for cat in categories.split(',') if cat.strip()]
        for i, category in enumerate(category_list):
            # Use both partial_ratio and token_sort_ratio
            partial_score = fuzz.partial_ratio(search_string.lower(), category.lower())
            token_score = fuzz.token_sort_ratio(search_string.lower(), category.lower())
            cat_score = max(partial_score, token_score)
            
            # Weight by specificity (later categories are more specific)
            specificity_weight = 1.0 + (i * 0.1)  # Increase weight for later categories
            weighted_score = cat_score * specificity_weight
            scores.append(weighted_score)
    
    # Score the category tags if available
    if categories_tags:
        for tag in categories_tags:
            if tag:
                # Remove language prefixes like "en:", "fr:" for better matching
                clean_tag = re.sub(r'^[a-z]{2}:', '', tag)
                clean_tag = clean_tag.replace('-', ' ')  # Convert dashes to spaces
                
                partial_score = fuzz.partial_ratio(search_string.lower(), clean_tag.lower())
                token_score = fuzz.token_sort_ratio(search_string.lower(), clean_tag.lower())
                tag_score = max(partial_score, token_score)
                scores.append(tag_score)
    
    # Return the best score, capped at 100
    return min(max(scores) if scores else 0.0, 100.0)


def score_labels(search_string: str, labels) -> float:
    """
    Score labels using RapidFuzz (optional field).
    
    Args:
        search_string: The search query string
        labels: Labels as string (comma-separated) or list
        
    Returns:
        Matching score (0-100)
    """
    if not search_string or not labels:
        return 0.0
    
    scores = []
    
    # Handle both string and list formats
    if isinstance(labels, list):
        label_list = [label.strip() for label in labels if label and label.strip()]
    else:
        label_list = [label.strip() for label in labels.split(',') if label.strip()]
    
    for label in label_list:
        partial_score = fuzz.partial_ratio(search_string.lower(), label.lower())
        token_score = fuzz.token_sort_ratio(search_string.lower(), label.lower())
        scores.append(max(partial_score, token_score))
    
    return max(scores) if scores else 0.0


def score_quantity(search_string: str, quantity: str) -> float:
    """
    Score quantity and unit with low weight.
    
    Args:
        search_string: The search query string
        quantity: Quantity string like "350 g"
        
    Returns:
        Matching score (0-100)
    """
    if not search_string or not quantity:
        return 0.0
    
    # Use both partial_ratio and token_sort_ratio
    partial_score = fuzz.partial_ratio(search_string.lower(), quantity.lower())
    token_score = fuzz.token_sort_ratio(search_string.lower(), quantity.lower())
    
    return max(partial_score, token_score)


def add_given_name_to_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add given_name field to each result in the list.
    
    Args:
        results: List of search result documents
        
    Returns:
        List of results with given_name field added
    """
    for result in results:
        result['given_name'] = compute_given_name(result)
    return results


def compute_given_name(document: Dict[str, Any]) -> str:
    """
    Compute the given_name field based on categories and product_names.
    
    Rules:
    1. Take the very last possible element of 'categories' array which is not empty and does not contain ":" char
    2. If not found, take from product_names: preferably with 'main' lang, if no product_names[0].text, if no - empty
    
    Args:
        document: MongoDB document
        
    Returns:
        The computed given_name string
    """
    # Try to get suitable category first
    categories = document.get('categories', '')
    if categories:
        # Handle both string and list formats
        if isinstance(categories, list):
            category_list = [cat.strip() for cat in categories if cat and cat.strip()]
        else:
            category_list = [cat.strip() for cat in categories.split(',') if cat.strip()]
        
        # Search from last to first for category without ":"
        for category in reversed(category_list):
            if category and ':' not in category:
                return category
    
    # If no suitable category found, try product_names
    product_name_data = document.get('product_name', [])
    if isinstance(product_name_data, list):
        # First try to find 'main' language
        for name_obj in product_name_data:
            if isinstance(name_obj, dict) and name_obj.get('lang') == 'main':
                text = name_obj.get('text', '')
                if text:
                    return text
        
        # If no 'main' language found, try first entry
        for name_obj in product_name_data:
            if isinstance(name_obj, dict):
                text = name_obj.get('text', '')
                if text:
                    return text
    
    # Return empty string if nothing found
    return ""


def compute_rapidfuzz_score(search_string: str, document: Dict[str, Any]) -> float:
    """
    Compute custom relevance score using RapidFuzz for a MongoDB document.
    
    Args:
        search_string: The search query string
        document: MongoDB document
        
    Returns:
        Combined weighted score
    """
    if not search_string:
        return 0.0
    
    # Extract and score product names (weight: 3.0)
    product_names = extract_product_names(document.get('product_name', []))
    name_score = score_product_names(search_string, product_names) * 3.0
    
    # Score brands (weight: 2.0)
    brands = document.get('brands', '')
    brand_score = score_brands(search_string, brands) * 2.0
    
    # Score categories with specificity (weight: 1.5)
    categories = document.get('categories', '')
    categories_tags = document.get('categories_tags', [])
    category_score = score_categories(search_string, categories, categories_tags) * 1.5
    
    # Score labels (optional, no explicit weight mentioned, using 1.0)
    labels = document.get('labels', '')
    label_score = score_labels(search_string, labels) * 1.0
    
    # Score quantity (weight: 0.5)
    quantity = document.get('quantity', '')
    quantity_score = score_quantity(search_string, quantity) * 0.5
    
    # Combine all scores
    total_score = name_score + brand_score + category_score + label_score + quantity_score
    
    return total_score