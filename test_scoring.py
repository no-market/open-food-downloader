#!/usr/bin/env python3
"""
Unit tests for the RapidFuzz scoring functions.
Tests the scoring functions with various input cases.
"""

import pytest
from utils import (
    extract_product_names, 
    score_product_names, 
    score_brands, 
    score_categories, 
    score_labels, 
    score_quantity, 
    compute_rapidfuzz_score
)


class TestExtractProductNames:
    """Test class for extract_product_names function."""
    
    def test_extract_product_names_valid_input(self):
        """Test with valid product_name array."""
        product_name_data = [
            {"lang": "main", "text": "Chocolate Spread"},
            {"lang": "fr", "text": "Pâte à tartiner chocolat"},
            {"lang": "en", "text": "Chocolate Spread"}  # Duplicate
        ]
        result = extract_product_names(product_name_data)
        assert result == ["Chocolate Spread", "Pâte à tartiner chocolat"]
    
    def test_extract_product_names_empty_input(self):
        """Test with empty input."""
        assert extract_product_names([]) == []
        assert extract_product_names(None) == []
    
    def test_extract_product_names_invalid_format(self):
        """Test with invalid format."""
        assert extract_product_names("not a list") == []
        assert extract_product_names([{"lang": "en"}]) == []  # Missing text
        assert extract_product_names([{"text": ""}]) == []  # Empty text


class TestScoringFunctions:
    """Test class for individual scoring functions."""
    
    def test_score_product_names(self):
        """Test product name scoring."""
        product_names = ["Nutella Hazelnut Spread", "Chocolate Spread"]
        
        # Exact match should score high
        score = score_product_names("nutella", product_names)
        assert score > 80
        
        # Partial match should score moderately
        score = score_product_names("hazelnut", product_names)
        assert score > 50
        
        # No match should score low
        score = score_product_names("pizza", product_names)
        assert score < 50  # Adjusted threshold
        
        # Empty inputs
        assert score_product_names("", product_names) == 0.0
        assert score_product_names("test", []) == 0.0
    
    def test_score_brands(self):
        """Test brand scoring."""
        brands = "Nutella, Ferrero"
        
        # Good match
        score = score_brands("nutella", brands)
        assert score > 80
        
        # Partial match
        score = score_brands("ferrero", brands)
        assert score > 80
        
        # No match
        score = score_brands("coca cola", brands)
        assert score < 40  # Adjusted threshold
        
        # Empty inputs
        assert score_brands("", brands) == 0.0
        assert score_brands("test", "") == 0.0
    
    def test_score_categories(self):
        """Test category scoring with specificity."""
        categories = "Food,Spreads,Chocolate Spreads,Hazelnut Chocolate Spreads"
        categories_tags = ["en:food", "en:spreads", "en:chocolate-spreads"]
        
        # Should match categories
        score = score_categories("chocolate", categories, categories_tags)
        assert score > 50
        
        # Should match tags (with language prefix removal)
        score = score_categories("spreads", categories, categories_tags)
        assert score > 50
        
        # Later categories should get higher weights
        score_specific = score_categories("hazelnut", categories, [])
        score_general = score_categories("food", categories, [])
        # Hazelnut appears later in the list, so should get higher weighted score
        assert score_specific >= score_general
    
    def test_score_labels(self):
        """Test label scoring."""
        labels = "Gluten-free,No palm oil,Organic"
        
        # Good match
        score = score_labels("gluten", labels)
        assert score > 50
        
        # Multiple word match
        score = score_labels("palm oil", labels)
        assert score > 50
        
        # No match
        score = score_labels("dairy", labels)
        assert score < 50  # Adjusted threshold
    
    def test_score_quantity(self):
        """Test quantity scoring."""
        quantity = "350 g"
        
        # Exact match
        score = score_quantity("350 g", quantity)
        assert score > 90
        
        # Partial match
        score = score_quantity("350", quantity)
        assert score > 50
        
        score = score_quantity("g", quantity)
        assert score > 50
        
        # No match
        score = score_quantity("ml", quantity)
        assert score < 30


class TestComputeRapidFuzzScore:
    """Test class for the main compute_rapidfuzz_score function."""
    
    def test_compute_rapidfuzz_score_comprehensive(self):
        """Test comprehensive scoring with a realistic document."""
        document = {
            "product_name": [
                {"lang": "main", "text": "Nutella Hazelnut Spread"},
                {"lang": "fr", "text": "Pâte à tartiner aux noisettes"}
            ],
            "brands": "Ferrero",
            "categories": "Spreads,Sweet Spreads,Chocolate Spreads,Hazelnut Chocolate Spreads",
            "categories_tags": ["en:spreads", "en:sweet-spreads", "en:chocolate-spreads"],
            "labels": "Gluten-free,No palm oil",
            "quantity": "350 g"
        }
        
        # Search for "nutella" - should score high on product name
        score = compute_rapidfuzz_score("nutella", document)
        assert score > 200  # High score due to 3.0 weight on product names
        
        # Search for "ferrero" - should score high on brand
        score = compute_rapidfuzz_score("ferrero", document)
        assert score > 150  # High score due to 2.0 weight on brands
        
        # Search for "chocolate" - should score on categories
        score = compute_rapidfuzz_score("chocolate", document)
        assert score > 100  # Moderate score due to 1.5 weight on categories
        
        # Search for "350g" - should score on quantity
        score = compute_rapidfuzz_score("350g", document)
        assert score > 30  # Lower score due to 0.5 weight on quantity
    
    def test_compute_rapidfuzz_score_empty_inputs(self):
        """Test with empty inputs."""
        document = {"product_name": [], "brands": "", "categories": ""}
        
        assert compute_rapidfuzz_score("", document) == 0.0
        assert compute_rapidfuzz_score("test", {}) == 0.0
    
    def test_compute_rapidfuzz_score_missing_fields(self):
        """Test with missing fields in document."""
        document = {
            "product_name": [{"lang": "en", "text": "Test Product"}]
            # Missing other fields
        }
        
        score = compute_rapidfuzz_score("test", document)
        assert score > 0  # Should still work with just product name


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__])