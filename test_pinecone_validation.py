#!/usr/bin/env python3
"""
Test for Pinecone category ID validation.
Tests the validation logic to ensure invalid records are skipped.
"""

import unittest
import unicodedata


def generate_category_id(category_name):
    """
    Extract the category ID generation logic for testing.
    This mirrors the logic in pinecone_integration.py lines 59-64.
    """
    category_id = category_name.lower().replace(' ', '_').replace('&', 'and')
    # Convert non-ASCII characters to ASCII equivalent
    category_id = unicodedata.normalize('NFKD', category_id).encode('ascii', 'ignore').decode('ascii')
    # Remove any special characters that might cause issues
    category_id = ''.join(c for c in category_id if c.isalnum() or c in '_-')
    return category_id


def validate_and_filter_categories(unique_last_categories):
    """
    Simulate the validation logic from the fixed pinecone_integration.py.
    Returns valid categories only.
    """
    valid_categories = []
    skipped_categories = []
    
    for category_name, full_path in unique_last_categories.items():
        category_id = generate_category_id(category_name)
        
        # Validate category ID - skip if empty (Pinecone requires ID length >= 1)
        if not category_id or len(category_id) == 0:
            skipped_categories.append((category_name, full_path))
            continue
        
        valid_categories.append((category_name, full_path, category_id))
    
    return valid_categories, skipped_categories


class TestPineconeValidation(unittest.TestCase):
    """Test cases for Pinecone category ID validation."""

    def test_category_id_generation_with_empty_strings(self):
        """Test that empty category names produce empty IDs."""
        # Test categories that should result in empty IDs
        problematic_categories = [
            "",
            "   ",
            "!!!",
            "中文",
            "тест", 
            "🎉🎊",
            "@#$%^&*()",
            "///",
            "...",
        ]
        
        print("Testing problematic category names:")
        empty_ids = []
        for category_name in problematic_categories:
            category_id = generate_category_id(category_name)
            print(f"Input: {repr(category_name)} -> Output: {repr(category_id)} (length: {len(category_id)})")
            if len(category_id) == 0:
                empty_ids.append(category_name)
        
        print(f"Categories that generate empty IDs: {empty_ids}")
        print(f"Number of empty IDs: {len(empty_ids)}")
        
        # This demonstrates the problem - we have empty IDs that would fail Pinecone validation
        self.assertGreater(len(empty_ids), 0, "There should be some categories that generate empty IDs")
    
    def test_category_id_generation_with_valid_strings(self):
        """Test that valid category names produce valid IDs."""
        valid_categories = [
            "Chocolate Spreads",
            "Hazelnut & Cocoa",  
            "Breakfast Items",
            "émotions",
            "café",
            "Test Category",
            "Simple",
        ]
        
        print("Testing valid category names:")
        for category_name in valid_categories:
            category_id = generate_category_id(category_name)
            print(f"Input: {repr(category_name)} -> Output: {repr(category_id)} (length: {len(category_id)})")
            
            # All generated IDs should be non-empty
            self.assertTrue(len(category_id) > 0, f"Category ID should not be empty for: {category_name}")
            self.assertIsInstance(category_id, str)
    
    def test_validation_filters_invalid_categories(self):
        """Test that the validation logic properly filters out invalid categories."""
        mixed_categories = {
            "Valid Category": "path/to/valid",
            "": "path/to/empty",
            "Another Valid": "path/to/another/valid", 
            "!!!": "path/to/special",
            "中文": "path/to/chinese",
            "Chocolate & Nuts": "path/to/chocolate/nuts",
            "   ": "path/to/spaces",
            "Normal Category": "path/to/normal",
        }
        
        print("Testing validation filtering:")
        valid_categories, skipped_categories = validate_and_filter_categories(mixed_categories)
        
        print(f"Input categories: {list(mixed_categories.keys())}")
        print(f"Valid categories: {[item[0] for item in valid_categories]}")
        print(f"Valid category IDs: {[item[2] for item in valid_categories]}")
        print(f"Skipped categories: {[item[0] for item in skipped_categories]}")
        print(f"Input count: {len(mixed_categories)}")
        print(f"Valid count: {len(valid_categories)}")
        print(f"Skipped count: {len(skipped_categories)}")
        
        # Verify that all valid categories have non-empty IDs
        for category_name, full_path, category_id in valid_categories:
            self.assertTrue(len(category_id) > 0, f"Valid category should have non-empty ID: {category_name}")
            self.assertIsInstance(category_id, str)
        
        # Verify that skipped categories would have had empty IDs
        for category_name, full_path in skipped_categories:
            category_id = generate_category_id(category_name)
            self.assertEqual(len(category_id), 0, f"Skipped category should have empty ID: {category_name}")
        
        # Total should match input
        self.assertEqual(len(valid_categories) + len(skipped_categories), len(mixed_categories))
        
        # Should have both valid and skipped
        self.assertGreater(len(valid_categories), 0, "Should have some valid categories")
        self.assertGreater(len(skipped_categories), 0, "Should have some skipped categories")
    
    def test_pinecone_id_requirements(self):
        """Test that all generated IDs meet Pinecone requirements."""
        test_categories = {
            "Chocolate": "path/to/chocolate",
            "Hazelnut & Cocoa": "path/to/hazelnut", 
            "Test-Category": "path/to/test",
            "émotions français": "path/to/emotions",
        }
        
        valid_categories, skipped_categories = validate_and_filter_categories(test_categories)
        
        print("Testing Pinecone ID requirements:")
        for category_name, full_path, category_id in valid_categories:
            print(f"Category: {category_name} -> ID: {category_id}")
            
            # Pinecone requirements: ID length >= 1
            self.assertGreaterEqual(len(category_id), 1, f"ID must be at least 1 character: {category_id}")
            
            # Should only contain valid characters (alphanumeric, underscore, hyphen)
            valid_chars = set('abcdefghijklmnopqrstuvwxyz0123456789_-')
            for char in category_id:
                self.assertIn(char, valid_chars, f"Invalid character '{char}' in ID: {category_id}")
        
        # No categories should be skipped for valid input
        self.assertEqual(len(skipped_categories), 0, "No valid categories should be skipped")


if __name__ == "__main__":
    unittest.main()