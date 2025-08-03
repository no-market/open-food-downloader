#!/usr/bin/env python3
"""
Test the categories collection functionality with mock data,
simulating the full download flow without actual MongoDB or dataset download.
"""

import os
import sys
from unittest.mock import Mock, MagicMock
from download_products import store_categories_collection

def test_full_categories_flow():
    """Test the complete categories flow."""
    print("Testing complete categories collection flow...")
    
    # Simulate data that would be collected during product processing
    # This mirrors the structure created in download_products.py
    unique_last_categories = {
        "Czekoladowe pasty": "Żywność > Słodycze > Czekoladowe pasty",
        "Ciastka": "Żywność > Przekąski > Ciastka", 
        "Mleko": "Żywność > Napoje > Nabiał > Mleko",
        "Chleb": "Żywność > Pieczywo > Chleb",
        "Jogurt": "Żywność > Nabiał > Jogurt",
        "Kawa": "Żywność > Napoje > Kawa",
        "Masło": "Żywność > Nabiał > Masło",
        "Ser": "Żywność > Nabiał > Sery > Ser",
        "Woda": "Napoje > Woda",  # Single level category
        "Piwo": "Napoje > Alkoholowe > Piwo"
    }
    
    print(f"Processing {len(unique_last_categories)} unique categories...")
    
    # Create mock MongoDB components
    class MockResult:
        def __init__(self, is_new=True):
            self.upserted_id = "new_id" if is_new else None
    
    class MockCollection:
        def __init__(self):
            self.created_indexes = []
            self.stored_documents = []
        
        def list_indexes(self):
            # Simulate no existing indexes
            return []
        
        def create_index(self, field):
            self.created_indexes.append(field)
            
        def replace_one(self, filter_doc, replacement_doc, upsert=False):
            self.stored_documents.append({
                'filter': filter_doc,
                'document': replacement_doc,
                'upsert': upsert
            })
            return MockResult(is_new=True)
    
    class MockDB:
        def __init__(self):
            self.collections = {}
        
        def __getitem__(self, name):
            if name not in self.collections:
                self.collections[name] = MockCollection()
            return self.collections[name]
    
    # Create mock database and call function
    mock_db = MockDB()
    store_categories_collection(mock_db, unique_last_categories)
    
    # Verify the results
    categories_collection = mock_db['categories']
    
    print(f"\nResults:")
    print(f"Indexes created: {categories_collection.created_indexes}")
    print(f"Documents stored: {len(categories_collection.stored_documents)}")
    
    # Verify index creation
    assert 'name' in categories_collection.created_indexes, "Name index should be created"
    
    # Verify all categories were stored
    assert len(categories_collection.stored_documents) == len(unique_last_categories), \
        f"Expected {len(unique_last_categories)} documents, got {len(categories_collection.stored_documents)}"
    
    # Test specific category structures
    stored_names = []
    for doc_info in categories_collection.stored_documents:
        doc = doc_info['document']
        name = doc['name']
        ancestors = doc['ancestors']
        stored_names.append(name)
        
        print(f"  Category: '{name}' -> Ancestors: {ancestors}")
        
        # Verify structure matches expected pattern
        assert 'name' in doc, "Document should have 'name' field"
        assert 'ancestors' in doc, "Document should have 'ancestors' field"
        assert isinstance(ancestors, list), "Ancestors should be a list"
        
        # Verify specific categories
        if name == "Czekoladowe pasty":
            assert ancestors == ["Żywność", "Słodycze"], f"Wrong ancestors for {name}: {ancestors}"
        elif name == "Ser":
            assert ancestors == ["Żywność", "Nabiał", "Sery"], f"Wrong ancestors for {name}: {ancestors}"
        elif name == "Woda":
            assert ancestors == ["Napoje"], f"Wrong ancestors for {name}: {ancestors}"
    
    # Verify all categories were processed
    expected_names = set(unique_last_categories.keys())
    actual_names = set(stored_names)
    assert expected_names == actual_names, f"Missing categories: {expected_names - actual_names}"
    
    print(f"\n✅ All {len(unique_last_categories)} categories processed correctly!")
    print("✅ Index creation verified!")
    print("✅ Document structure verified!")
    print("✅ Ancestor parsing verified!")
    
    # Test edge cases
    print("\nTesting edge cases...")
    
    # Test with existing index
    mock_db2 = MockDB()
    categories_collection2 = mock_db2['categories']
    # Mock existing index
    categories_collection2.list_indexes = lambda: [{'key': {'name': 1}}]
    categories_collection2.created_indexes = []
    
    store_categories_collection(mock_db2, {"Test": "Test"})
    assert len(categories_collection2.created_indexes) == 0, "Should not create index when it exists"
    print("✅ Existing index handling verified!")
    
    print("\n🎉 All categories collection tests passed!")

if __name__ == "__main__":
    test_full_categories_flow()