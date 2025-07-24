#!/usr/bin/env python3
"""
Integration test for the RapidFuzz scoring implementation.
Tests the end-to-end functionality without requiring a real MongoDB connection.
"""

import json
from search_products import apply_rapidfuzz_scoring


def test_rapidfuzz_integration():
    """Test the complete RapidFuzz scoring integration."""
    
    # Mock search results that would come from MongoDB
    mock_results = [
        {
            "_id": "product1",
            "score": 10.5,  # MongoDB text score
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
        },
        {
            "_id": "product2", 
            "score": 8.2,  # Lower MongoDB text score
            "product_name": [
                {"lang": "main", "text": "Organic Chocolate Spread"},
                {"lang": "en", "text": "Premium Chocolate Spread"}
            ],
            "brands": "Organic Valley",
            "categories": "Spreads,Chocolate Spreads",
            "categories_tags": ["en:spreads", "en:chocolate-spreads", "en:organic"],
            "labels": "Organic,Gluten-free",
            "quantity": "350 g",
            "search_string": "organic chocolate spread premium valley 350g"
        },
        {
            "_id": "product3",
            "score": 12.1,  # High MongoDB text score
            "product_name": [
                {"lang": "main", "text": "Almond Butter Spread"}
            ],
            "brands": "Natural Foods",
            "categories": "Spreads,Nut Spreads,Almond Spreads", 
            "categories_tags": ["en:spreads", "en:nut-spreads"],
            "labels": "Natural,No added sugar",
            "quantity": "500 g",
            "search_string": "almond butter spread natural foods 500g nuts"
        }
    ]
    
    # Test search for "nutella" - should prioritize product1
    search_string = "nutella"
    results = apply_rapidfuzz_scoring(search_string, mock_results.copy())
    
    print(f"Search for '{search_string}':")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result['_id']}: RapidFuzz={result.get('rapidfuzz_score', 0):.2f}, MongoDB={result['score']:.2f}")
    
    # Product1 (Nutella) should have the highest RapidFuzz score
    assert results[0]['_id'] == 'product1', f"Expected product1 first, got {results[0]['_id']}"
    assert results[0]['rapidfuzz_score'] > results[1]['rapidfuzz_score']
    print("✓ Nutella search correctly prioritized Nutella product")
    
    # Test search for "organic" - should prioritize product2
    search_string = "organic"
    results = apply_rapidfuzz_scoring(search_string, mock_results.copy())
    
    print(f"\nSearch for '{search_string}':")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result['_id']}: RapidFuzz={result.get('rapidfuzz_score', 0):.2f}, MongoDB={result['score']:.2f}")
    
    # Product2 (Organic) should have higher RapidFuzz score for "organic"
    organic_product_score = next((r['rapidfuzz_score'] for r in results if r['_id'] == 'product2'), 0)
    other_scores = [r['rapidfuzz_score'] for r in results if r['_id'] != 'product2']
    assert organic_product_score > max(other_scores), "Organic product should score highest for 'organic' search"
    print("✓ Organic search correctly prioritized organic product")
    
    # Test search for "almond" - should prioritize product3
    search_string = "almond"
    results = apply_rapidfuzz_scoring(search_string, mock_results.copy())
    
    print(f"\nSearch for '{search_string}':")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result['_id']}: RapidFuzz={result.get('rapidfuzz_score', 0):.2f}, MongoDB={result['score']:.2f}")
    
    # Product3 (Almond) should have higher RapidFuzz score for "almond"
    almond_product_score = next((r['rapidfuzz_score'] for r in results if r['_id'] == 'product3'), 0)
    other_scores = [r['rapidfuzz_score'] for r in results if r['_id'] != 'product3']
    assert almond_product_score > max(other_scores), "Almond product should score highest for 'almond' search"
    print("✓ Almond search correctly prioritized almond product")
    
    print("\n✅ All integration tests passed!")


if __name__ == "__main__":
    test_rapidfuzz_integration()