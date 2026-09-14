#!/usr/bin/env python3
"""
Unit tests for product validation in the download_products module.
Tests the is_valid_product function with various product scenarios.
"""

import pytest
from download_products import (
    build_direct_category_details,
    get_direct_category,
    is_valid_product,
    limit_mapping_items,
)


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
    
    def test_valid_product_with_pl_category(self):
        """Test that a product with pl: category passes validation."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': 'Test Product'}
            ],
            'categories': 'en:spreads,pl:czekolada,fr:chocolat'
        }
        assert is_valid_product(record) == True
    
    def test_valid_product_with_uppercase_PL_category(self):
        """Test that a product with uppercase PL: category passes validation."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': 'Test Product'}
            ],
            'categories': 'en:spreads,PL:masło,fr:beurre'
        }
        assert is_valid_product(record) == True
    
    def test_valid_product_with_only_pl_categories(self):
        """Test that a product with only pl: categories passes validation."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': 'Test Product'}
            ],
            'categories': 'pl:jedzenie,pl:czekolada'
        }
        assert is_valid_product(record) == True
    
    def test_invalid_product_all_non_pl_categories_have_colons(self):
        """Test that a product with only non-pl colon categories fails validation."""
        record = {
            'product_name': [
                {'lang': 'en', 'text': 'Test Product'}
            ],
            'categories': 'en:spreads,fr:pates-a-tartiner,de:brotaufstriche,es:untables'
        }
        assert is_valid_product(record) == False


class TestDirectCategory:
    """Test direct category extraction for product counts."""

    def test_get_direct_category_uses_last_non_tag_category(self):
        category_list = [
            'Food',
            'Spreads',
            'en:chocolate-spreads',
            'Hazelnut Spreads',
        ]

        assert get_direct_category(category_list) == 'Hazelnut Spreads'

    def test_get_direct_category_does_not_return_parent_category(self):
        category_list = [
            'Food',
            'Spreads',
            'Chocolate Spreads',
        ]

        direct_category = get_direct_category(category_list)

        assert direct_category == 'Chocolate Spreads'
        assert direct_category != 'Food'
        assert direct_category != 'Spreads'

    def test_get_direct_category_returns_none_for_tag_only_categories(self):
        category_list = [
            'en:food',
            'fr:pates-a-tartiner',
        ]

        assert get_direct_category(category_list) is None

    def test_build_direct_category_details_includes_path_count_and_language(self):
        class FakeLanguageModel:
            def predict(self, text, k=1):
                return ['__label__pol_Latn'], [0.98]

        details = build_direct_category_details(
            {'Herbaty aromatyzowane': 'Napoje > Herbata > Herbaty aromatyzowane'},
            {'Herbaty aromatyzowane': 3},
            FakeLanguageModel(),
        )

        assert details == {
            'Herbaty aromatyzowane': {
                'path': 'Napoje > Herbata > Herbaty aromatyzowane',
                'product_count': 3,
                'language': 'pol_Latn',
                'language_score': 0.98,
            }
        }

    def test_build_direct_category_details_without_model_has_empty_language(self):
        details = build_direct_category_details(
            {'Chocolate Spreads': 'Food > Spreads > Chocolate Spreads'},
            {'Chocolate Spreads': 2},
            None,
        )

        assert details['Chocolate Spreads']['path'] == 'Food > Spreads > Chocolate Spreads'
        assert details['Chocolate Spreads']['product_count'] == 2
        assert details['Chocolate Spreads']['language'] is None
        assert details['Chocolate Spreads']['language_score'] is None

    def test_build_direct_category_details_keeps_counts_when_model_fails(self):
        class FailingLanguageModel:
            def predict(self, text, k=1):
                raise ValueError("model failed")

        details = build_direct_category_details(
            {'Chocolate Spreads': 'Food > Spreads > Chocolate Spreads'},
            {'Chocolate Spreads': 2},
            FailingLanguageModel(),
        )

        assert details['Chocolate Spreads'] == {
            'path': 'Food > Spreads > Chocolate Spreads',
            'product_count': 2,
            'language': None,
            'language_score': None,
        }

    def test_limit_mapping_items_caps_output(self):
        categories = {
            'A': 'Food > A',
            'B': 'Food > B',
            'C': 'Food > C',
        }

        assert limit_mapping_items(categories, 2) == {
            'A': 'Food > A',
            'B': 'Food > B',
        }
