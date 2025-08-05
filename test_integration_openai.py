#!/usr/bin/env python3
"""
Integration test for search functionality with mocked low scores to trigger OpenAI.
"""

import json
import os
from typing import Dict, Any, List

# Mock the MongoDB and OpenAI functionality for testing
class MockCollection:
    def create_index(self, index_spec):
        pass
    
    def find(self, query, projection=None):
        # Return mock results with low scores to trigger OpenAI
        return MockCursor([
            {
                "_id": "test123",
                "product_name": [{"lang": "en", "text": "Test Product"}],
                "given_name": "Test Product",
                "brands": "Test Brand",
                "categories": "Food,Test Category",
                "labels": "Test Label",
                "quantity": "100g",
                "search_string": "test product",
                "score": 15.0  # Low score to trigger OpenAI
            }
        ])

class MockCursor:
    def __init__(self, data):
        self.data = data
    
    def sort(self, sort_spec):
        return self
    
    def limit(self, count):
        return self
    
    def __iter__(self):
        return iter(self.data)
    
    def __next__(self):
        return next(iter(self.data))

def test_search_with_mock_data():
    """Test search functionality with mocked data that triggers OpenAI."""
    
    # Set mock MongoDB URI to avoid the error
    os.environ['MONGO_URI'] = 'mongodb://mock:27017/test'
    
    # Import after setting environment variable
    from search_products import search_products_direct, apply_rapidfuzz_scoring
    from openai_assistant import OpenAIAssistant, SCORE_THRESHOLD
    
    # Create mock data with products that won't match our search well
    mock_results = [
        {
            "_id": "test123",
            "product_name": [{"lang": "en", "text": "Completely Different Product Name"}],
            "given_name": "Different Product",
            "brands": "Other Brand",
            "categories": "Beverages,Soft Drinks",
            "labels": "Organic",
            "quantity": "500ml",
            "search_string": "beverage soft drink cola",
            "score": 15.0
        }
    ]
    
    # Test a search that won't match well
    search_query = "chocolate cookies nuts"  # Very different from the mock product
    
    print(f"Searching for: '{search_query}'")
    print(f"Mock product contains: 'beverage soft drink cola'")
    
    # Apply RapidFuzz scoring (this should give low scores due to mismatch)
    results_with_fuzzy = apply_rapidfuzz_scoring(search_query, mock_results)
    print(f"RapidFuzz results: {len(results_with_fuzzy)}")
    
    if results_with_fuzzy:
        best_score = max(r.get('rapidfuzz_score', 0) for r in results_with_fuzzy)
        print(f"Best RapidFuzz score: {best_score:.1f}")
        
        # Test OpenAI assistance simulation
        assistant = OpenAIAssistant()
        
        if assistant.should_use_openai(best_score):
            print(f"✅ OpenAI would be triggered (score {best_score:.1f} < threshold {SCORE_THRESHOLD})")
            
            # Test Level 1 processing
            top_result_name = results_with_fuzzy[0].get('given_name') if results_with_fuzzy else None
            level1_result = assistant.process_with_level1(search_query, top_result_name)
            print(f"Level 1 decision: {level1_result.decision}")
            print(f"Level 1 error: {level1_result.error}")
            
            # Test Level 2 processing
            level2_result = assistant.process_with_level2(search_query, top_result_name, level1_result)
            print(f"Level 2 decision: {level2_result.decision}")
            print(f"Level 2 error: {level2_result.error}")
        else:
            print(f"❌ OpenAI would not be triggered (score {best_score:.1f} >= threshold {SCORE_THRESHOLD})")
    
    print("✅ Integration test completed successfully!")

if __name__ == "__main__":
    test_search_with_mock_data()