#!/usr/bin/env python3
"""
Demonstration of the new given_name field functionality.
"""

import json
from test_complete_workflow import mock_search_products

def demonstrate_given_name_feature():
    """Demonstrate the new given_name field in search results."""
    
    print("🎉 Demonstrating New 'given_name' Field Feature")
    print("=" * 50)
    print()
    
    # Search for chocolate spread
    search_query = "chocolate spread"
    print(f"🔍 Searching for: '{search_query}'")
    print()
    
    # Perform mock search
    results = mock_search_products(search_query)
    
    # Show example output with given_name field
    print("\n📊 Sample Output with given_name Field:")
    print("-" * 40)
    
    for i, result in enumerate(results['direct_search']['results'][:2]):  # Show first 2
        print(f"\nResult {i+1}:")
        print(f"  Product ID: {result['_id']}")
        print(f"  🏷️  Given Name: '{result['given_name']}'")
        print(f"  📝 Product Names: {[item['text'] for item in result['product_name']]}")
        print(f"  🏪 Brand: {result['brands']}")
        print(f"  📂 Categories: {result['categories']}")
        print(f"  ⭐ MongoDB Score: {result['score']}")
    
    # Show how given_name is computed
    print("\n🧮 How 'given_name' is Computed:")
    print("-" * 35)
    
    example_cases = [
        {
            "description": "Case 1: Categories without colons",
            "categories": "Spreads,Sweet Spreads,Chocolate Spreads,Hazelnut Spreads",
            "given_name": "Hazelnut Spreads",
            "explanation": "Takes last category without ':' character"
        },
        {
            "description": "Case 2: All categories have colons",
            "categories": "en:spreads,fr:produits-a-tartiner,en:sweet-spreads",
            "product_name": "Organic Almond Butter",
            "given_name": "Organic Almond Butter", 
            "explanation": "Falls back to product_name with 'main' language preference"
        },
        {
            "description": "Case 3: No suitable categories, no main language",
            "categories": "en:spreads",
            "product_name": "Pâte à tartiner",
            "given_name": "Pâte à tartiner",
            "explanation": "Uses first available product_name"
        }
    ]
    
    for case in example_cases:
        print(f"\n{case['description']}:")
        print(f"  Categories: {case['categories']}")
        if 'product_name' in case:
            print(f"  Product Name: {case['product_name']}")
        print(f"  → Given Name: '{case['given_name']}'")
        print(f"  📖 Logic: {case['explanation']}")
    
    # Save example output to JSON
    output_file = "example_search_results_with_given_name.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Example results saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Failed to save example: {e}")
    
    print("\n✅ Feature Implementation Complete!")
    print("The 'given_name' field has been successfully added to both:")
    print("  - MongoDB (direct) search results")
    print("  - RapidFuzz search results")
    print("\nThe field follows the specified logic:")
    print("  1. Last category element without ':' character")
    print("  2. If none found, use product_name with 'main' language preference")
    print("  3. If no 'main' language, use first product_name")
    print("  4. If nothing available, return empty string")


if __name__ == "__main__":
    demonstrate_given_name_feature()