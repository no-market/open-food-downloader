#!/usr/bin/env python3
"""
Unit tests for product validation in the download_products module.
Tests the is_valid_product function with various product scenarios.
"""

import io
import json

import pytest
from download_products import (
    CategoryLanguageError,
    ProductEligibilityFilter,
    add_category_path_to_hierarchy,
    add_category_path_with_direct_count,
    get_direct_category,
    get_preferred_product_name,
    get_rejection_output_group,
    is_valid_product,
    save_categories_hierarchy_to_json,
    save_categories_hierarchy_with_direct_counts_to_json,
    write_eligible_product_jsonl,
    write_rejected_product_jsonl,
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


class TestCategoryHierarchy:
    def test_merges_paths_and_skips_language_tags(self):
        hierarchy = {}

        add_category_path_to_hierarchy(
            hierarchy,
            ['Żywność', 'en:Plant-based foods', 'Zboża', 'Makarony'],
        )
        add_category_path_to_hierarchy(
            hierarchy,
            ['Żywność', 'Zboża', 'Płatki'],
        )
        add_category_path_to_hierarchy(
            hierarchy,
            ['Żywność', 'Warzywa', 'Cebula'],
        )

        assert hierarchy == {
            'Żywność': {
                'Zboża': {
                    'Makarony': {},
                    'Płatki': {},
                },
                'Warzywa': {
                    'Cebula': {},
                },
            },
        }

    def test_saves_hierarchy_as_json(self, tmp_path, monkeypatch):
        hierarchy = {
            'Żywność': {
                'Zboża': {
                    'Makarony': {},
                },
            },
        }
        monkeypatch.chdir(tmp_path)

        save_categories_hierarchy_to_json(hierarchy)

        saved_hierarchy = json.loads(
            (tmp_path / 'categories_hierarchy.json').read_text(encoding='utf-8')
        )
        assert saved_hierarchy == hierarchy


class TestCategoryHierarchyWithDirectCounts:
    def test_counts_only_products_assigned_directly_to_each_path(self):
        hierarchy = {}

        add_category_path_with_direct_count(hierarchy, ['Żywność', 'Zboża'])
        add_category_path_with_direct_count(
            hierarchy,
            ['Żywność', 'en:Cereals', 'Zboża', 'Makarony'],
        )
        add_category_path_with_direct_count(
            hierarchy,
            ['Żywność', 'Zboża', 'Makarony'],
        )

        assert hierarchy == {
            'Żywność': {
                'Zboża': {
                    '_direct_product_count': 1,
                    'Makarony': {
                        '_direct_product_count': 2,
                    },
                },
            },
        }

    def test_keeps_counts_separate_for_same_category_name_on_different_paths(self):
        hierarchy = {}

        add_category_path_with_direct_count(hierarchy, ['Żywność', 'Produkty'])
        add_category_path_with_direct_count(hierarchy, ['Napoje', 'Produkty'])

        assert hierarchy['Żywność']['Produkty']['_direct_product_count'] == 1
        assert hierarchy['Napoje']['Produkty']['_direct_product_count'] == 1

    def test_saves_hierarchy_with_direct_counts_as_json(self, tmp_path, monkeypatch):
        hierarchy = {
            'Żywność': {
                'Zboża': {
                    '_direct_product_count': 3,
                },
            },
        }
        monkeypatch.chdir(tmp_path)

        save_categories_hierarchy_with_direct_counts_to_json(hierarchy)

        saved_hierarchy = json.loads(
            (
                tmp_path / 'categories_hierarchy_with_direct_counts.json'
            ).read_text(encoding='utf-8')
        )
        assert saved_hierarchy == hierarchy


class TestPreferredProductName:
    def test_prefers_polish_name_over_main_and_first(self):
        product_names = [
            {'lang': 'en', 'text': 'Onions'},
            {'lang': 'main', 'text': 'Red onions'},
            {'lang': 'pl', 'text': 'Czerwona cebula'},
        ]

        assert get_preferred_product_name(product_names) == 'Czerwona cebula'

    def test_falls_back_to_main_name(self):
        product_names = [
            {'lang': 'en', 'text': 'Onions'},
            {'lang': 'main', 'text': 'Red onions'},
        ]

        assert get_preferred_product_name(product_names) == 'Red onions'

    def test_falls_back_to_first_non_empty_name(self):
        product_names = [
            {'lang': 'en', 'text': '  '},
            {'lang': 'de', 'text': 'Zwiebeln'},
            {'lang': 'fr', 'text': 'Oignons'},
        ]

        assert get_preferred_product_name(product_names) == 'Zwiebeln'


class TestProductEligibilityFilter:
    def test_accepts_product_with_polish_direct_category(self):
        class PolishLanguageModel:
            def predict(self, text, k=1):
                predictions = {
                    'Herbaty aromatyzowane': ('pol_Latn', 0.35),
                    'Herbata': ('pol_Latn', 0.91),
                }
                language, score = predictions[text]
                return [f'__label__{language}'], [score]

        product_filter = ProductEligibilityFilter(PolishLanguageModel())

        assessment = product_filter.assess({
            'code': '123',
            'lang': 'pl',
            'product_name': [{'lang': 'pl', 'text': 'Herbata'}],
            'categories': 'Napoje, Herbata, Herbaty aromatyzowane',
        })

        assert assessment.eligible is True
        assert assessment.reason is None
        assert assessment.direct_category == 'Herbaty aromatyzowane'
        assert assessment.detected_category_language == 'pol_Latn'
        assert assessment.detected_category_language_score == pytest.approx(0.35)
        assert assessment.product_name_for_language_detection == 'Herbata'
        assert assessment.detected_product_name_language == 'pol_Latn'
        assert assessment.detected_product_name_language_score == pytest.approx(0.91)

    def test_accepts_polish_product_name_when_direct_category_is_not_polish(self):
        class MixedLanguageModel:
            def predict(self, text, k=1):
                predictions = {
                    'Makarony': ('ceb_Latn', 0.92),
                    'Makaron pełnoziarnisty': ('pol_Latn', 0.98),
                }
                language, score = predictions[text]
                return [f'__label__{language}'], [score]

        assessment = ProductEligibilityFilter(MixedLanguageModel()).assess({
            'lang': 'pl',
            'product_name': [
                {'lang': 'main', 'text': 'Wholegrain pasta'},
                {'lang': 'pl', 'text': 'Makaron pełnoziarnisty'},
            ],
            'categories': 'Żywność, Makarony',
        })

        assert assessment.eligible is True
        assert assessment.reason is None
        assert assessment.detected_category_language == 'ceb_Latn'
        assert assessment.product_name_for_language_detection == 'Makaron pełnoziarnisty'
        assert assessment.detected_product_name_language == 'pol_Latn'

    def test_accepts_polish_direct_category_when_product_name_is_not_polish(self):
        class MixedLanguageModel:
            def predict(self, text, k=1):
                predictions = {
                    'Cebula': ('pol_Latn', 0.97),
                    'Red onions': ('eng_Latn', 0.99),
                }
                language, score = predictions[text]
                return [f'__label__{language}'], [score]

        assessment = ProductEligibilityFilter(MixedLanguageModel()).assess({
            'lang': 'pl',
            'product_name': [{'lang': 'main', 'text': 'Red onions'}],
            'categories': 'Żywność, Cebula',
        })

        assert assessment.eligible is True
        assert assessment.reason is None
        assert assessment.detected_category_language == 'pol_Latn'
        assert assessment.detected_product_name_language == 'eng_Latn'

    def test_reuses_language_for_repeated_direct_category(self):
        class CountingLanguageModel:
            def __init__(self):
                self.inputs = []

            def predict(self, text, k=1):
                self.inputs.append(text)
                return ['__label__pol_Latn'], [0.99]

        model = CountingLanguageModel()
        product_filter = ProductEligibilityFilter(model)
        first_record = {
            'lang': 'pl',
            'product_name': [{'text': 'Pierwszy produkt'}],
            'categories': 'Napoje, Herbaty aromatyzowane',
        }
        second_record = {
            'lang': 'pl',
            'product_name': [{'text': 'Drugi produkt'}],
            'categories': 'Żywność, Napoje, Herbaty aromatyzowane',
        }

        first_assessment = product_filter.assess(first_record)
        second_assessment = product_filter.assess(second_record)

        assert first_assessment.eligible is True
        assert second_assessment.eligible is True
        assert first_assessment.detected_category_language_score == pytest.approx(0.99)
        assert second_assessment.detected_category_language_score == pytest.approx(0.99)
        assert model.inputs == [
            'Herbaty aromatyzowane',
            'Pierwszy produkt',
            'Drugi produkt',
        ]

    def test_rejects_missing_product_name_without_using_model(self):
        class UnusedLanguageModel:
            def predict(self, text, k=1):
                raise AssertionError('language model must not be used')

        assessment = ProductEligibilityFilter(UnusedLanguageModel()).assess({
            'code': 'missing-name',
            'product_name': [{'text': '   '}],
            'categories': 'Napoje, Herbata',
        })

        assert assessment.eligible is False
        assert assessment.reason == 'missing_product_name'
        assert assessment.direct_category is None
        assert assessment.detected_category_language is None

    def test_rejects_missing_valid_category_without_using_model(self):
        class UnusedLanguageModel:
            def predict(self, text, k=1):
                raise AssertionError('language model must not be used')

        assessment = ProductEligibilityFilter(UnusedLanguageModel()).assess({
            'code': 'missing-category',
            'product_name': [{'text': 'Produkt'}],
            'categories': 'en:food, fr:boissons',
        })

        assert assessment.reason == 'missing_valid_category'
        assert assessment.direct_category is None

    def test_rejects_missing_direct_category_without_using_model(self):
        class UnusedLanguageModel:
            def predict(self, text, k=1):
                raise AssertionError('language model must not be used')

        assessment = ProductEligibilityFilter(UnusedLanguageModel()).assess({
            'code': 'tag-only-category',
            'lang': 'pl',
            'product_name': [{'text': 'Produkt'}],
            'categories': 'pl:żywność, pl:herbata',
        })

        assert assessment.reason == 'missing_direct_category'
        assert assessment.direct_category is None

    def test_writes_non_polish_category_rejection_as_jsonl(self):
        class EnglishLanguageModel:
            def predict(self, text, k=1):
                return ['__label__eng_Latn'], [0.99]

        record = {
            'code': 'english-category',
            'lang': 'pl',
            'product_name': [{'text': 'Produkt'}],
            'categories': 'Food, Tea',
        }
        assessment = ProductEligibilityFilter(EnglishLanguageModel()).assess(record)
        output = io.StringIO()

        write_rejected_product_jsonl(output, record, assessment)

        assert json.loads(output.getvalue()) == {
            'code': 'english-category',
            'reason': 'non_polish_direct_category',
            'record_language': 'pl',
            'product_name': [{'text': 'Produkt'}],
            'direct_category': 'Tea',
            'detected_category_language': 'eng_Latn',
            'detected_category_language_score': pytest.approx(0.99),
            'product_name_for_language_detection': 'Produkt',
            'detected_product_name_language': 'eng_Latn',
            'detected_product_name_language_score': pytest.approx(0.99),
            'categories': ['Food', 'Tea'],
        }

    def test_routes_language_rejections_separately_from_other_rejections(self):
        assert (
            get_rejection_output_group('non_polish_direct_category')
            == 'non_polish_direct_category'
        )
        assert get_rejection_output_group('missing_product_name') == 'other'

    def test_writes_eligible_product_as_jsonl(self):
        product = {
            '_id': 'eligible-product',
            'lang': 'pl',
            'product_name': [{'lang': 'pl', 'text': 'Produkt'}],
            'categories': ['Żywność', 'Przekąski'],
        }
        output = io.StringIO()

        write_eligible_product_jsonl(output, product)

        assert output.getvalue().endswith('\n')
        assert json.loads(output.getvalue()) == product

    def test_language_prediction_failure_stops_assessment(self):
        class FailingLanguageModel:
            def predict(self, text, k=1):
                raise ValueError('prediction failed')

        product_filter = ProductEligibilityFilter(FailingLanguageModel())
        record = {
            'lang': 'pl',
            'product_name': [{'text': 'Produkt'}],
            'categories': 'Napoje, Herbata',
        }

        with pytest.raises(CategoryLanguageError, match='Herbata'):
            product_filter.assess(record)

    def test_missing_language_prediction_stops_assessment(self):
        class EmptyLanguageModel:
            def predict(self, text, k=1):
                return [], []

        product_filter = ProductEligibilityFilter(EmptyLanguageModel())
        record = {
            'lang': 'pl',
            'product_name': [{'text': 'Produkt'}],
            'categories': 'Napoje, Herbata',
        }

        with pytest.raises(CategoryLanguageError, match='Herbata'):
            product_filter.assess(record)

    def test_rejects_non_polish_record_language_without_using_model(self):
        class UnusedLanguageModel:
            def predict(self, text, k=1):
                raise AssertionError('language model must not be used')

        assessment = ProductEligibilityFilter(UnusedLanguageModel()).assess({
            'lang': 'en',
            'product_name': [{'text': 'Produkt'}],
            'categories': 'Napoje, Herbata',
        })

        assert assessment.reason == 'non_polish_record_language'
        assert assessment.direct_category is None

    def test_rejects_none_categories_as_missing_valid_category(self):
        class UnusedLanguageModel:
            def predict(self, text, k=1):
                raise AssertionError('language model must not be used')

        assessment = ProductEligibilityFilter(UnusedLanguageModel()).assess({
            'lang': 'pl',
            'product_name': [{'text': 'Produkt'}],
            'categories': None,
        })

        assert assessment.reason == 'missing_valid_category'
