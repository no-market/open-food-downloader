#!/usr/bin/env python3
"""
Mock test to demonstrate the complete search workflow with given_name field.
"""

import json
from datetime import datetime
from utils import format_search_string, add_given_name_to_results, compute_rapidfuzz_score

def mock_search_products(search_string: str):
    """
    Mock version of search_products function to demonstrate given_name integration.
    
    Args:
        search_string: The input search string
        
    Returns:
        Dictionary containing search results with given_name field
    """
    
    # Format the search string (same as real implementation)
    formatted_string = format_search_string(search_string)
    print(f"Original input: '{search_string}'")
    print(f"Formatted input: '{formatted_string}'")
    
    # Mock MongoDB search results (would come from database in real implementation)
    mock_direct_results = [
        {
            "_id": "0000101209159",
            "score": 15.8,
            "product_name": [
                {"lang": "main", "text": "Véritable pâte à tartiner noisettes chocolat noir"},
                {"lang": "fr", "text": "Véritable pâte à tartiner noisettes chocolat noir"}
            ],
            "brands": "Bovetti",
            "categories": "Petit-déjeuners,Produits à tartiner,Produits à tartiner sucrés,Pâtes à tartiner,Pâtes à tartiner aux noisettes,Pâtes à tartiner au chocolat,Pâtes à tartiner aux noisettes et au cacao",
            "labels": "Sans gluten,Sans huile de palme",
            "quantity": "350 g",
            "search_string": "véritable pâte tartiner noisettes chocolat noir bovetti 350g sans gluten"
        },
        {
            "_id": "nutella001",
            "score": 14.2,
            "product_name": [
                {"lang": "main", "text": "Nutella Hazelnut Spread"},
                {"lang": "fr", "text": "Pâte à tartiner aux noisettes"}
            ],
            "brands": "Ferrero",
            "categories": "Spreads,Sweet Spreads,Chocolate Spreads,Hazelnut Chocolate Spreads",
            "labels": "Gluten-free,No palm oil",
            "quantity": "750 g",
            "search_string": "nutella ferrero hazelnut spread 750g chocolate"
        },
        {
            "_id": "organic001",
            "score": 9.5,
            "product_name": [
                {"lang": "en", "text": "Organic Almond Butter"}
            ],
            "brands": "Nature's Best",
            "categories": "en:spreads,en:nut-butters,en:almond-butters",  # All have colons - should fallback to product_name
            "labels": "Organic,No sugar added",
            "quantity": "250 g",
            "search_string": "organic almond butter natures best 250g no sugar"
        }
    ]
    
    # Add given_name field to direct results (as implemented in real search)
    print("Adding given_name field to direct search results...")
    direct_results = add_given_name_to_results(mock_direct_results.copy())
    
    # Apply RapidFuzz scoring and add given_name (as implemented in real search)
    print("Computing RapidFuzz scores and adding given_name...")
    rapidfuzz_results = []
    for result in mock_direct_results.copy():
        # Compute RapidFuzz score
        rapidfuzz_score = compute_rapidfuzz_score(search_string, result)
        result['rapidfuzz_score'] = rapidfuzz_score
        rapidfuzz_results.append(result)
    
    # Sort by RapidFuzz score descending
    rapidfuzz_results.sort(key=lambda x: x.get('rapidfuzz_score', 0), reverse=True)
    
    # Add given_name to rapidfuzz results
    rapidfuzz_results = add_given_name_to_results(rapidfuzz_results)
    
    # Prepare results (same structure as real implementation)
    results = {
        "timestamp": datetime.now().isoformat(),
        "input_string": search_string,
        "formatted_string": formatted_string,
        "direct_search": {
            "count": len(direct_results),
            "results": direct_results
        },
        "rapidfuzz_search": {
            "count": len(rapidfuzz_results),
            "results": rapidfuzz_results
        }
    }
    
    return results


def test_complete_search_workflow():
    """Test the complete search workflow with given_name field."""
    
    print("Testing complete search workflow with given_name field...")
    print("=" * 60)
    
    search_query = "chocolate spread"
    results = mock_search_products(search_query)
    
    print(f"\nSearch completed for: '{search_query}'")
    print(f"Direct search found: {results['direct_search']['count']} results")
    print(f"RapidFuzz search found: {results['rapidfuzz_search']['count']} results")
    
    # Verify given_name field in direct search results
    print("\nDirect Search Results with given_name:")
    for i, result in enumerate(results['direct_search']['results']):
        print(f"  {i+1}. ID: {result['_id']}")
        print(f"     Given Name: '{result['given_name']}'")
        print(f"     Score: {result['score']}")
        print()
    
    # Verify given_name field in RapidFuzz search results
    print("RapidFuzz Search Results with given_name:")
    for i, result in enumerate(results['rapidfuzz_search']['results']):
        print(f"  {i+1}. ID: {result['_id']}")
        print(f"     Given Name: '{result['given_name']}'")
        print(f"     RapidFuzz Score: {result['rapidfuzz_score']:.2f}")
        print(f"     MongoDB Score: {result['score']}")
        print()
    
    # Verify expected given_name values for direct results
    expected_direct_given_names = [
        "Pâtes à tartiner aux noisettes et au cacao",  # Last category without colon
        "Hazelnut Chocolate Spreads",  # Last category without colon  
        "Organic Almond Butter"  # From product_name (categories have colons)
    ]
    
    for i, expected in enumerate(expected_direct_given_names):
        direct_result = results['direct_search']['results'][i]
        assert direct_result['given_name'] == expected, f"Direct result {i+1} given_name mismatch: expected '{expected}', got '{direct_result['given_name']}'"
    
    # Verify that all RapidFuzz results have given_name field (order may differ due to scoring)
    rapidfuzz_given_names = [r['given_name'] for r in results['rapidfuzz_search']['results']]
    for expected in expected_direct_given_names:
        assert expected in rapidfuzz_given_names, f"Expected given_name '{expected}' not found in RapidFuzz results"
    
    # Test JSON serialization 
    print("Testing JSON serialization...")
    try:
        json_output = json.dumps(results, indent=2, ensure_ascii=False)
        assert '"given_name"' in json_output, "given_name not found in JSON output"
        print("✅ Results successfully serialized to JSON with given_name field")
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        raise
    
    print("\n🎉 Complete search workflow test passed!")
    print("✅ given_name field correctly integrated into both search result types")
    print("✅ given_name values computed according to requirements")
    print("✅ Results maintain compatibility with existing structure")
    print("✅ JSON serialization works correctly")


if __name__ == "__main__":
    test_complete_search_workflow()