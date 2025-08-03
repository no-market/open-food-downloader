#!/usr/bin/env python3
"""
Tests for categories collection functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, call
from download_products import store_categories_collection


class TestCategoriesCollection:
    """Test cases for categories collection storage."""
    
    def test_store_categories_collection_basic(self):
        """Test basic categories collection storage."""
        # Mock database and collection
        mock_db = MagicMock()
        mock_collection = Mock()
        mock_db['categories'] = mock_collection
        
        # Mock list_indexes to return empty list (no existing indexes)
        mock_collection.list_indexes.return_value = []
        
        # Mock replace_one to return upserted_id for new insertions
        mock_result = Mock()
        mock_result.upserted_id = "some_id"
        mock_collection.replace_one.return_value = mock_result
        
        # Test data
        unique_last_categories = {
            "Chocolate Spreads": "Food > Spreads > Chocolate Spreads",
            "Cookies": "Food > Snacks > Cookies",
            "Milk": "Food > Beverages > Dairy > Milk"
        }
        
        # Call function
        store_categories_collection(mock_db, unique_last_categories)
        
        # Verify index creation was called
        mock_collection.create_index.assert_called_once_with('name')
        
        # Verify replace_one was called for each category
        assert mock_collection.replace_one.call_count == 3
        
        # Check specific calls
        expected_calls = [
            call(
                {'name': 'Chocolate Spreads'},
                {'name': 'Chocolate Spreads', 'ancestors': ['Food', 'Spreads']},
                upsert=True
            ),
            call(
                {'name': 'Cookies'},
                {'name': 'Cookies', 'ancestors': ['Food', 'Snacks']},
                upsert=True
            ),
            call(
                {'name': 'Milk'},
                {'name': 'Milk', 'ancestors': ['Food', 'Beverages', 'Dairy']},
                upsert=True
            )
        ]
        
        mock_collection.replace_one.assert_has_calls(expected_calls, any_order=True)
    
    def test_store_categories_collection_with_existing_index(self):
        """Test categories collection storage when index already exists."""
        # Mock database and collection
        mock_db = MagicMock()
        mock_collection = Mock()
        mock_db['categories'] = mock_collection
        
        # Mock list_indexes to return existing index on name
        mock_index = {'key': {'name': 1}}
        mock_collection.list_indexes.return_value = [mock_index]
        
        # Mock replace_one
        mock_result = Mock()
        mock_result.upserted_id = None  # Existing document
        mock_collection.replace_one.return_value = mock_result
        
        # Test data
        unique_last_categories = {
            "Bread": "Food > Bakery > Bread"
        }
        
        # Call function
        store_categories_collection(mock_db, unique_last_categories)
        
        # Verify index creation was NOT called
        mock_collection.create_index.assert_not_called()
        
        # Verify replace_one was called
        mock_collection.replace_one.assert_called_once_with(
            {'name': 'Bread'},
            {'name': 'Bread', 'ancestors': ['Food', 'Bakery']},
            upsert=True
        )
    
    def test_store_categories_collection_single_level(self):
        """Test categories with no ancestors (single level)."""
        # Mock database and collection
        mock_db = MagicMock()
        mock_collection = Mock()
        mock_db['categories'] = mock_collection
        
        # Mock list_indexes
        mock_collection.list_indexes.return_value = []
        
        # Mock replace_one
        mock_result = Mock()
        mock_result.upserted_id = "some_id"
        mock_collection.replace_one.return_value = mock_result
        
        # Test data - single level category
        unique_last_categories = {
            "Food": "Food"
        }
        
        # Call function
        store_categories_collection(mock_db, unique_last_categories)
        
        # Verify the category was stored with empty ancestors
        mock_collection.replace_one.assert_called_once_with(
            {'name': 'Food'},
            {'name': 'Food', 'ancestors': []},
            upsert=True
        )
    
    def test_store_categories_collection_empty_data(self):
        """Test categories collection with empty data."""
        # Mock database and collection
        mock_db = MagicMock()
        mock_collection = Mock()
        mock_db['categories'] = mock_collection
        
        # Mock list_indexes
        mock_collection.list_indexes.return_value = []
        
        # Test with empty data
        unique_last_categories = {}
        
        # Call function
        store_categories_collection(mock_db, unique_last_categories)
        
        # Verify index creation was called but no categories processed
        mock_collection.create_index.assert_called_once_with('name')
        mock_collection.replace_one.assert_not_called()
    
    def test_store_categories_collection_invalid_data(self):
        """Test categories collection with invalid data."""
        # Mock database and collection
        mock_db = MagicMock()
        mock_collection = Mock()
        mock_db['categories'] = mock_collection
        
        # Mock list_indexes
        mock_collection.list_indexes.return_value = []
        
        # Test data with invalid entries
        unique_last_categories = {
            "": "Empty > Name",  # Empty name
            "Valid": "",  # Empty path
            "Another": "Valid > Path > Another"  # Valid entry
        }
        
        # Mock replace_one
        mock_result = Mock()
        mock_result.upserted_id = "some_id"
        mock_collection.replace_one.return_value = mock_result
        
        # Call function
        store_categories_collection(mock_db, unique_last_categories)
        
        # Verify only the valid entry was processed
        mock_collection.replace_one.assert_called_once_with(
            {'name': 'Another'},
            {'name': 'Another', 'ancestors': ['Valid', 'Path']},
            upsert=True
        )
    
    def test_store_categories_collection_path_parsing(self):
        """Test correct parsing of category paths with various separators."""
        # Mock database and collection
        mock_db = MagicMock()
        mock_collection = Mock()
        mock_db['categories'] = mock_collection
        
        # Mock list_indexes
        mock_collection.list_indexes.return_value = []
        
        # Mock replace_one
        mock_result = Mock()
        mock_result.upserted_id = "some_id"
        mock_collection.replace_one.return_value = mock_result
        
        # Test data with various path formats
        unique_last_categories = {
            "Final": "First > Second > Third > Final",
            "Single": "Single",
            "WithSpaces": "Food  >  Drinks  >  WithSpaces"  # Extra spaces
        }
        
        # Call function
        store_categories_collection(mock_db, unique_last_categories)
        
        # Verify calls with proper ancestor parsing
        expected_calls = [
            call(
                {'name': 'Final'},
                {'name': 'Final', 'ancestors': ['First', 'Second', 'Third']},
                upsert=True
            ),
            call(
                {'name': 'Single'},
                {'name': 'Single', 'ancestors': []},
                upsert=True
            ),
            call(
                {'name': 'WithSpaces'},
                {'name': 'WithSpaces', 'ancestors': ['Food', 'Drinks']},
                upsert=True
            )
        ]
        
        mock_collection.replace_one.assert_has_calls(expected_calls, any_order=True)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])