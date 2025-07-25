#!/usr/bin/env python3
"""
Test the search output format to ensure it matches the requirements.
"""

import json
from utils import compute_rapidfuzz_score, compute_given_name

def test_search_output_format():
    """Test that the search output format matches requirements."""
    
    # Sample document that would come from MongoDB
    sample_document = {
        "_id": "test123",
        "score": 10.5,  # MongoDB score
        "product_name": [
            {"lang": "main", "text": "Nutella Hazelnut Spread"},
            {"lang": "fr", "text": "Pâte à tartiner aux noisettes"}
        ],
        "brands": "Ferrero",
        "categories": "Spreads,Sweet Spreads,Chocolate Spreads,Hazelnut Chocolate Spreads",
        "categories_tags": ["en:spreads", "en:sweet-spreads", "en:chocolate-spreads"],
        "labels": "Gluten-free,No palm oil",
        "quantity": "750 g",
        "search_string": "nutella ferrero hazelnut spread 750g chocolate"
    }
    
    # Test RapidFuzz scoring
    search_query = "nutella chocolate"
    rapidfuzz_score = compute_rapidfuzz_score(search_query, sample_document)
    
    # Add scores to document (as would happen in apply_rapidfuzz_scoring)
    sample_document['rapidfuzz_score'] = rapidfuzz_score
    
    # Add given_name field (as would happen in add_given_name_to_results)
    sample_document['given_name'] = compute_given_name(sample_document)
    
    print("Sample search result with RapidFuzz scoring and given_name:")
    print(f"MongoDB Score: {sample_document['score']}")
    print(f"RapidFuzz Score: {sample_document['rapidfuzz_score']:.2f}")
    print(f"Given Name: {sample_document['given_name']}")
    print(f"Product Names: {[item['text'] for item in sample_document['product_name']]}")
    print(f"Brands: {sample_document['brands']}")
    print(f"Categories: {sample_document['categories']}")
    print(f"Labels: {sample_document['labels']}")
    print(f"Quantity: {sample_document['quantity']}")
    
    # Validate structure maintains MongoDB format with added fields
    required_fields = ['_id', 'score', 'product_name', 'brands', 'categories', 'labels', 'quantity']
    for field in required_fields:
        assert field in sample_document, f"Missing required field: {field}"
    
    # Validate new fields were added
    assert 'rapidfuzz_score' in sample_document, "Missing rapidfuzz_score field"
    assert 'given_name' in sample_document, "Missing given_name field"
    assert isinstance(sample_document['rapidfuzz_score'], (int, float)), "rapidfuzz_score should be numeric"
    assert sample_document['rapidfuzz_score'] >= 0, "rapidfuzz_score should be non-negative"
    assert isinstance(sample_document['given_name'], str), "given_name should be a string"
    
    # Test scoring components
    assert rapidfuzz_score > 100, "Should score high for good matches due to weighted scoring"
    
    # Test given_name logic - should be last category without colon
    expected_given_name = "Hazelnut Chocolate Spreads"  # Last category without ":"
    assert sample_document['given_name'] == expected_given_name, f"Expected '{expected_given_name}', got '{sample_document['given_name']}'"
    
    print("\n✅ Output format validation passed!")
    print(f"✅ RapidFuzz score computed: {rapidfuzz_score:.2f}")
    print(f"✅ Given name computed: '{sample_document['given_name']}'")
    print("✅ All required fields present")
    print("✅ Score structure maintains MongoDB compatibility")


if __name__ == "__main__":
    test_search_output_format()