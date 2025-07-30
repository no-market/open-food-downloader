#!/usr/bin/env python3
"""
Integration test for download_products module to verify the import works
and basic functionality can be tested without running the full download.
"""

import pytest
from unittest.mock import Mock, patch
from download_products import is_valid_product, download_from_huggingface


def test_import_works():
    """Test that we can import the download_products module successfully."""
    # If we get here, the import worked
    assert is_valid_product is not None
    assert download_from_huggingface is not None


def test_validation_integration_with_real_data_structure():
    """Test validation with data structures that match the real OpenFoodFacts format."""
    
    # Test with a realistic valid product
    valid_product = {
        'code': '3017620422003',
        'lang': 'pl',
        'product_name': [
            {'lang': 'en', 'text': 'Nutella'},
            {'lang': 'pl', 'text': 'Nutella Krem Orzechowy'}
        ],
        'brands': 'Ferrero',
        'categories': 'Food,Spreads,Sweet spreads,Cocoa and hazelnuts spreads',
        'categories_tags': ['en:food', 'en:spreads', 'en:sweet-spreads'],
        'labels': 'Palm oil free',
        'quantity': '750g'
    }
    
    assert is_valid_product(valid_product) == True
    
    # Test with a realistic invalid product (categories all have colons)
    invalid_product_categories = {
        'code': '1234567890123',
        'lang': 'pl',
        'product_name': [
            {'lang': 'en', 'text': 'Some Product'}
        ],
        'categories': 'en:spreads,fr:pates-a-tartiner,de:brotaufstriche',
        'brands': 'Test Brand'
    }
    
    assert is_valid_product(invalid_product_categories) == False
    
    # Test with a realistic invalid product (no valid product names)
    invalid_product_names = {
        'code': '9876543210987',
        'lang': 'pl',
        'product_name': [
            {'lang': 'en', 'text': ''},
            {'lang': 'pl', 'text': '   '}
        ],
        'categories': 'Food,Spreads,Sweet spreads',
        'brands': 'Test Brand'
    }
    
    assert is_valid_product(invalid_product_names) == False