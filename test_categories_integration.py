#!/usr/bin/env python3
"""
Integration test for categories collection functionality with a real MongoDB instance.
This test is meant to be run manually to verify the functionality works correctly.
"""

import os
import sys
from download_products import store_categories_collection

def test_categories_collection_with_mock_db():
    """Test categories collection storage with a simple mock."""
    
    class MockResult:
        def __init__(self, is_new=True):
            self.upserted_id = "new_id" if is_new else None
    
    class MockCollection:
        def __init__(self):
            self.indexes = []
            self.documents = []
            self.index_created = False
            self.operations = []
        
        def list_indexes(self):
            return self.indexes
        
        def create_index(self, field):
            self.index_created = True
            self.operations.append(f"create_index({field})")
            
        def replace_one(self, filter_doc, replacement_doc, upsert=False):
            self.operations.append(f"replace_one({filter_doc}, {replacement_doc}, upsert={upsert})")
            return MockResult(is_new=True)
    
    class MockDB:
        def __init__(self):
            self.collections = {}
        
        def __getitem__(self, name):
            if name not in self.collections:
                self.collections[name] = MockCollection()
            return self.collections[name]
    
    # Test data
    unique_last_categories = {
        "Chocolate Spreads": "Food > Spreads > Chocolate Spreads",
        "Cookies": "Food > Snacks > Cookies",
        "Milk": "Food > Beverages > Dairy > Milk",
        "Bread": "Food > Bakery > Bread"
    }
    
    # Create mock database
    mock_db = MockDB()
    
    # Call the function
    print("Testing categories collection storage...")
    store_categories_collection(mock_db, unique_last_categories)
    
    # Verify results
    categories_collection = mock_db['categories']
    
    print("\nVerification:")
    print(f"Index created: {categories_collection.index_created}")
    print(f"Total operations: {len(categories_collection.operations)}")
    
    # Check that index was created
    assert categories_collection.index_created, "Index should have been created"
    
    # Check that we have the right number of operations (1 index + 4 replace_one)
    expected_operations = 5  # 1 create_index + 4 replace_one
    assert len(categories_collection.operations) == expected_operations, \
        f"Expected {expected_operations} operations, got {len(categories_collection.operations)}"
    
    # Check first operation is index creation
    assert "create_index(name)" in categories_collection.operations[0], \
        "First operation should be index creation"
    
    # Check that all categories were processed
    replace_operations = [op for op in categories_collection.operations if op.startswith("replace_one")]
    assert len(replace_operations) == 4, f"Expected 4 replace operations, got {len(replace_operations)}"
    
    print("✅ All verifications passed!")
    
    # Test specific category structures
    expected_structures = {
        "Chocolate Spreads": ["Food", "Spreads"],
        "Cookies": ["Food", "Snacks"], 
        "Milk": ["Food", "Beverages", "Dairy"],
        "Bread": ["Food", "Bakery"]
    }
    
    for operation in replace_operations:
        for category_name, expected_ancestors in expected_structures.items():
            if f"'name': '{category_name}'" in operation:
                assert f"'ancestors': {expected_ancestors}" in operation, \
                    f"Category {category_name} should have ancestors {expected_ancestors}"
                print(f"✅ {category_name} has correct ancestors: {expected_ancestors}")
                break
    
    print("\n🎉 Categories collection test completed successfully!")

if __name__ == "__main__":
    test_categories_collection_with_mock_db()