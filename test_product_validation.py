#!/usr/bin/env python3
"""
Unit tests for product validation in the download_products module.
Tests the is_valid_product function with various product scenarios.
"""

import pytest
from download_products import is_valid_product


class TestProductValidation:
    """Test class for is_valid_product function."""
    
    def test_valid_product_with_good_name_and_category(self):
        """Test that a product with valid name and category passes validation."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': 'Nutella Hazelnut Spread'}
            ],
            'categories': 'Food,Spreads,Chocolate Spreads,Hazelnut Spreads'
        }
        assert is_valid_product(record) == True
    
    def test_valid_product_with_multiple_names(self):
        """Test that a product with multiple valid names passes validation."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': ''},  # Empty name should be ignored
                {'lang': 'fr', 'text': 'Pâte à tartiner'},
                {'lang': 'de', 'text': 'Nuss-Nougat-Creme'}
            ],
            'categories': 'Food,Spreads,Chocolate Spreads'
        }
        assert is_valid_product(record) == True
    
    def test_valid_product_with_mixed_categories(self):
        """Test that a product with mixed categories (some with colons) passes if at least one is valid."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': 'Test Product'}
            ],
            'categories': 'en:spreads,Food,fr:pates-a-tartiner,Chocolate Spreads'
        }
        assert is_valid_product(record) == True
    
    def test_invalid_product_no_valid_names(self):
        """Test that a product with no valid names fails validation."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': ''},  # Empty
                {'lang': 'fr', 'text': '   '},  # Whitespace only
            ],
            'categories': 'Food,Spreads,Chocolate Spreads'
        }
        assert is_valid_product(record) == False
    
    def test_invalid_product_empty_product_name_list(self):
        """Test that a product with empty product_name list fails validation."""
        record = {
            'product_name': [],
            'categories': 'Food,Spreads,Chocolate Spreads'
        }
        assert is_valid_product(record) == False
    
    def test_invalid_product_missing_product_name(self):
        """Test that a product with missing product_name field fails validation."""
        record = {
            'categories': 'Food,Spreads,Chocolate Spreads'
        }
        assert is_valid_product(record) == False
    
    def test_invalid_product_all_categories_have_colons(self):
        """Test that a product with only categories containing colons fails validation."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': 'Test Product'}
            ],
            'categories': 'en:spreads,fr:pates-a-tartiner,de:brotaufstriche'
        }
        assert is_valid_product(record) == False
    
    def test_invalid_product_empty_categories(self):
        """Test that a product with empty categories fails validation."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': 'Test Product'}
            ],
            'categories': ''
        }
        assert is_valid_product(record) == False
    
    def test_invalid_product_missing_categories(self):
        """Test that a product with missing categories field fails validation."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': 'Test Product'}
            ]
        }
        assert is_valid_product(record) == False
    
    def test_invalid_product_only_whitespace_categories(self):
        """Test that a product with only whitespace categories fails validation."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': 'Test Product'}
            ],
            'categories': '   ,  ,   '
        }
        assert is_valid_product(record) == False
    
    def test_edge_case_malformed_product_name(self):
        """Test that malformed product_name entries are handled gracefully."""
        record = {
            'product_name': [
                'not_a_dict',  # Should be ignored
                {'no_text_field': 'value'},  # Should be ignored
                {'text': 'Valid Product Name'}  # This should work
            ],
            'categories': 'Food,Spreads'
        }
        assert is_valid_product(record) == True
    
    def test_edge_case_product_name_not_list(self):
        """Test that non-list product_name is handled gracefully."""
        record = {
            'product_name': 'not_a_list',
            'categories': 'Food,Spreads'
        }
        assert is_valid_product(record) == False
    
    def test_categories_with_trailing_commas(self):
        """Test that categories with trailing commas are handled correctly."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': 'Test Product'}
            ],
            'categories': 'Food,Spreads,Chocolate Spreads,'
        }
        assert is_valid_product(record) == True
    
    def test_both_requirements_fail(self):
        """Test that a product failing both requirements is properly rejected."""
        record = {
            'product_name': [],
            'categories': 'en:spreads,fr:pates-a-tartiner'
        }
        assert is_valid_product(record) == False