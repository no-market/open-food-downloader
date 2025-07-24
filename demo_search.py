#!/usr/bin/env python3
"""
Test script to demonstrate the search functionality without requiring MongoDB connection.
This simulates what the search output would look like.
"""

from search_products import apply_rapidfuzz_scoring, save_results
from utils import extract_product_names
from datetime import datetime
import json


def simulate_search_demo():
    """Simulate a complete search demo with mock data."""
    
    # Simulate MongoDB search results
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
    
    print("🔍 Food Product Search Demo")
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
    output_file = save_results(results, "demo_search_results.json")
    
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
    
    print("✅ Demo completed successfully!")
    print("\n🎯 Key Observations:")
    print("- RapidFuzz reordered results based on search relevance to 'chocolate nutella'")
    print("- Nutella product scored highest despite lower MongoDB score")
    print("- Both MongoDB and RapidFuzz results available in output structure")
    print("- Same output format maintained, with added rapidfuzz_score field")


if __name__ == "__main__":
    simulate_search_demo()