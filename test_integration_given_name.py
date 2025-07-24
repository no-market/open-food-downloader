#!/usr/bin/env python3
"""
Integration test for given_name field in search results (mock test without MongoDB).
"""

import json
from utils import add_given_name_to_results

def test_integration_given_name():
    """Test that given_name field is properly added to search results."""
    
    # Mock search results that would come from MongoDB
    mock_results = [
        {
            "_id": "test1",
            "score": 15.2,
            "categories": "Spreads,Sweet Spreads,Chocolate Spreads,Hazelnut Spreads",
            "product_name": [
                {"lang": "main", "text": "Nutella Original"},
                {"lang": "fr", "text": "Nutella Originale"}
            ],
            "brands": "Ferrero",
            "labels": "Gluten-free",
            "quantity": "400 g",
            "search_string": "nutella ferrero hazelnut spread 400g"
        },
        {
            "_id": "test2", 
            "score": 12.8,
            "categories": "en:spreads,fr:produits-a-tartiner,en:sweet-spreads",  # All have colons
            "product_name": [
                {"lang": "main", "text": "Organic Almond Butter"},
                {"lang": "en", "text": "Natural Almond Spread"}
            ],
            "brands": "Nature Valley", 
            "labels": "Organic,No palm oil",
            "quantity": "250 g",
            "search_string": "organic almond butter nature valley 250g"
        },
        {
            "_id": "test3",
            "score": 8.4,
            "categories": "",  # Empty categories
            "product_name": [
                {"lang": "fr", "text": "Pâte à tartiner maison"},  # No main language
                {"lang": "en", "text": "Homemade Spread"}
            ],
            "brands": "Local Brand",
            "labels": "Handmade",
            "quantity": "200 g", 
            "search_string": "homemade spread local brand 200g"
        }
    ]
    
    print("Testing integration of given_name field...")
    print("=" * 50)
    
    # Test adding given_name to direct search results
    print("1. Testing direct search results with given_name...")
    direct_results = add_given_name_to_results(mock_results.copy())
    
    # Verify given_name was added to all results
    for i, result in enumerate(direct_results):
        assert 'given_name' in result, f"given_name missing from result {i+1}"
        print(f"   Result {i+1}: given_name = '{result['given_name']}'")
    
    # Verify expected values
    assert direct_results[0]['given_name'] == "Hazelnut Spreads", "First result should use last category without colon"
    assert direct_results[1]['given_name'] == "Organic Almond Butter", "Second result should use main product name"
    assert direct_results[2]['given_name'] == "Pâte à tartiner maison", "Third result should use first product name"
    
    print("   ✅ Direct search results correctly include given_name")
    
    # Test RapidFuzz results with given_name
    print("\n2. Testing RapidFuzz search results with given_name...")
    search_string = "nutella spread"
    
    # Apply RapidFuzz scoring (simulating apply_rapidfuzz_scoring function)
    rapidfuzz_results = []
    for result in mock_results.copy():
        # Add a mock rapidfuzz_score
        result['rapidfuzz_score'] = 85.5  # Mock score
        rapidfuzz_results.append(result)
    
    # Add given_name to rapidfuzz results
    rapidfuzz_results = add_given_name_to_results(rapidfuzz_results)
    
    # Verify both rapidfuzz_score and given_name are present
    for i, result in enumerate(rapidfuzz_results):
        assert 'rapidfuzz_score' in result, f"rapidfuzz_score missing from result {i+1}"
        assert 'given_name' in result, f"given_name missing from result {i+1}"
        print(f"   Result {i+1}: rapidfuzz_score = {result['rapidfuzz_score']}, given_name = '{result['given_name']}'")
    
    print("   ✅ RapidFuzz search results correctly include both scores and given_name")
    
    # Test JSON serialization (ensuring results can be saved)
    print("\n3. Testing JSON serialization of results...")
    try:
        json_output = json.dumps({
            "direct_search": {"results": direct_results},
            "rapidfuzz_search": {"results": rapidfuzz_results}
        }, indent=2, ensure_ascii=False)
        print("   ✅ Results successfully serialized to JSON")
        
        # Verify given_name appears in JSON
        assert '"given_name"' in json_output, "given_name field not found in JSON output"
        print("   ✅ given_name field found in JSON output")
        
    except Exception as e:
        print(f"   ❌ JSON serialization failed: {e}")
        raise
    
    print("\n🎉 Integration test passed!")
    print("The given_name field is correctly integrated into search results.")


if __name__ == "__main__":
    test_integration_given_name()