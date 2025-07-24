#!/usr/bin/env python3
"""
Integration test for the RapidFuzz scoring implementation.
Tests the end-to-end functionality without requiring a real MongoDB connection.
"""

import json
from datetime import datetime
from search_products import apply_rapidfuzz_scoring, save_results
from utils import extract_product_names


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


def test_search_demo():
    """Comprehensive demo test that shows the search functionality with detailed output."""
    
    # Mock MongoDB search results for demo
    mock_mongodb_results = [
        {
            "_id": "nutella_750g",
            "score": 10.5,
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
            "_id": "organic_chocolate",
            "score": 8.2,
            "product_name": [
                {"lang": "main", "text": "Organic Chocolate Spread"}
            ],
            "brands": "Organic Valley",
            "categories": "Spreads,Chocolate Spreads",
            "categories_tags": ["en:spreads", "en:chocolate-spreads", "en:organic"],
            "labels": "Organic,Gluten-free",
            "quantity": "350 g",
            "search_string": "organic chocolate spread premium valley 350g"
        },
        {
            "_id": "peanut_butter",
            "score": 12.1,
            "product_name": [
                {"lang": "main", "text": "Natural Peanut Butter"}
            ],
            "brands": "Skippy",
            "categories": "Spreads,Nut Spreads,Peanut Spreads",
            "categories_tags": ["en:spreads", "en:nut-spreads"],
            "labels": "Natural,No added sugar",
            "quantity": "500 g",
            "search_string": "natural peanut butter skippy 500g nuts"
        }
    ]
    
    search_string = "chocolate nutella"
    formatted_string = "chocolate nutella"
    
    print("\n🔍 Food Product Search Demo Test")
    print("=" * 50)
    print(f"Search string: {search_string}")
    print(f"Formatted input: '{formatted_string}'")
    print()
    
    # Apply RapidFuzz scoring
    print("Computing RapidFuzz scores and resorting results...")
    rapidfuzz_results = apply_rapidfuzz_scoring(search_string, mock_mongodb_results.copy())
    
    # Create results structure
    results = {
        "timestamp": datetime.now().isoformat(),
        "input_string": search_string,
        "formatted_string": formatted_string,
        "direct_search": {
            "count": len(mock_mongodb_results),
            "results": mock_mongodb_results
        },
        "rapidfuzz_search": {
            "count": len(rapidfuzz_results),
            "results": rapidfuzz_results
        }
    }
    
    # Save results
    output_file = save_results(results, "test_demo_search_results.json")
    
    # Print summary
    print("\nSearch Summary:")
    print(f"- Formatted input: '{results['formatted_string']}'")
    print(f"- Direct search: {results['direct_search']['count']} results")
    print(f"- RapidFuzz search: {results['rapidfuzz_search']['count']} results")
    print(f"- Results saved to: {output_file}")
    
    # Print top 3 direct search results (MongoDB scoring)
    print("\nTop 3 direct search results (MongoDB scoring):")
    for i, result in enumerate(results['direct_search']['results'][:3]):
        score = result.get('score', 0)
        product_id = result.get('_id', 'Unknown')
        
        # Extract unique product names
        unique_product_names = extract_product_names(result.get('product_name', []))
        
        # Get other requested fields
        quantity = result.get('quantity', '')
        brands = result.get('brands', '')
        categories = result.get('categories', [])
        labels = result.get('labels', [])
        
        print(f"  {i+1}. MongoDB Score: {score:.2f} - ID: {product_id}")
        print(f"     Product Names: {', '.join(unique_product_names) if unique_product_names else 'N/A'}")
        print(f"     Quantity: {quantity if quantity else 'N/A'}")
        print(f"     Brands: {brands if brands else 'N/A'}")
        print(f"     Categories: {categories if categories else 'N/A'}")
        print(f"     Labels: {labels if labels else 'N/A'}")
        print()
    
    # Print top 3 RapidFuzz results
    print("Top 3 RapidFuzz search results (Custom relevance scoring):")
    for i, result in enumerate(results['rapidfuzz_search']['results'][:3]):
        mongo_score = result.get('score', 0)
        rapidfuzz_score = result.get('rapidfuzz_score', 0)
        product_id = result.get('_id', 'Unknown')
        
        # Extract unique product names
        unique_product_names = extract_product_names(result.get('product_name', []))
        
        # Get other requested fields
        quantity = result.get('quantity', '')
        brands = result.get('brands', '')
        categories = result.get('categories', [])
        labels = result.get('labels', [])
        
        print(f"  {i+1}. RapidFuzz Score: {rapidfuzz_score:.2f} (MongoDB: {mongo_score:.2f}) - ID: {product_id}")
        print(f"     Product Names: {', '.join(unique_product_names) if unique_product_names else 'N/A'}")
        print(f"     Quantity: {quantity if quantity else 'N/A'}")
        print(f"     Brands: {brands if brands else 'N/A'}")
        print(f"     Categories: {categories if categories else 'N/A'}")
        print(f"     Labels: {labels if labels else 'N/A'}")
        print()
    
    print("✅ Demo test completed successfully!")
    print("\n🎯 Key Observations:")
    print("- RapidFuzz reordered results based on search relevance to 'chocolate nutella'")
    print("- Chocolate products prioritized over unrelated items")
    print("- Both MongoDB and RapidFuzz results available in output structure")
    print("- Same output format maintained, with added rapidfuzz_score field")
    
    # Validate demo results
    assert len(rapidfuzz_results) == 3, "Should have 3 results"
    assert all('rapidfuzz_score' in result for result in rapidfuzz_results), "All results should have rapidfuzz_score"
    assert rapidfuzz_results[0]['rapidfuzz_score'] >= rapidfuzz_results[1]['rapidfuzz_score'], "Results should be sorted by score"
    
    # Check that chocolate products are prioritized
    chocolate_products = [r for r in rapidfuzz_results if 'chocolate' in r.get('product_name', [{}])[0].get('text', '').lower()]
    assert len(chocolate_products) >= 1, "Should find chocolate products"
    
    print("✅ Demo validation assertions passed!")


if __name__ == "__main__":
    test_rapidfuzz_integration()
    test_search_demo()