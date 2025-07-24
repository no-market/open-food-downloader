#!/usr/bin/env python3
"""
Test the compute_given_name function to ensure it follows the requirements.
"""

from utils import compute_given_name, add_given_name_to_results

def test_given_name_from_categories():
    """Test given_name calculation from categories."""
    
    # Test case 1: Last category without colon
    document1 = {
        "categories": "Spreads,Sweet Spreads,Chocolate Spreads,Hazelnut Chocolate Spreads",
        "product_name": [{"lang": "main", "text": "Test Product"}]
    }
    result1 = compute_given_name(document1)
    assert result1 == "Hazelnut Chocolate Spreads", f"Expected 'Hazelnut Chocolate Spreads', got '{result1}'"
    
    # Test case 2: Categories with colons (should skip them)
    document2 = {
        "categories": "Spreads,Sweet Spreads,en:chocolate-spreads,fr:pates-a-tartiner,Hazelnut Spreads",
        "product_name": [{"lang": "main", "text": "Test Product"}]
    }
    result2 = compute_given_name(document2)
    assert result2 == "Hazelnut Spreads", f"Expected 'Hazelnut Spreads', got '{result2}'"
    
    # Test case 3: All categories have colons (should fallback to product_name)
    document3 = {
        "categories": "en:spreads,fr:produits-a-tartiner,en:sweet-spreads",
        "product_name": [{"lang": "main", "text": "Nutella Spread"}]
    }
    result3 = compute_given_name(document3)
    assert result3 == "Nutella Spread", f"Expected 'Nutella Spread', got '{result3}'"
    
    # Test case 4: Categories as list instead of string
    document4 = {
        "categories": ["Spreads", "Sweet Spreads", "en:chocolate-spreads", "Hazelnut Spreads"],
        "product_name": [{"lang": "main", "text": "Test Product"}]
    }
    result4 = compute_given_name(document4)
    assert result4 == "Hazelnut Spreads", f"Expected 'Hazelnut Spreads', got '{result4}'"
    
    print("✅ Categories-based given_name tests passed!")


def test_given_name_from_product_names():
    """Test given_name calculation from product_names."""
    
    # Test case 1: Main language preference
    document1 = {
        "categories": "en:spreads,fr:produits-a-tartiner",  # All have colons
        "product_name": [
            {"lang": "fr", "text": "Pâte à tartiner"},
            {"lang": "main", "text": "Hazelnut Spread"},
            {"lang": "en", "text": "Chocolate Spread"}
        ]
    }
    result1 = compute_given_name(document1)
    assert result1 == "Hazelnut Spread", f"Expected 'Hazelnut Spread', got '{result1}'"
    
    # Test case 2: No main language, should take first
    document2 = {
        "categories": "en:spreads",  # Has colon
        "product_name": [
            {"lang": "fr", "text": "Pâte à tartiner"},
            {"lang": "en", "text": "Chocolate Spread"}
        ]
    }
    result2 = compute_given_name(document2)
    assert result2 == "Pâte à tartiner", f"Expected 'Pâte à tartiner', got '{result2}'"
    
    # Test case 3: Empty categories and no main language
    document3 = {
        "categories": "",
        "product_name": [
            {"lang": "fr", "text": "Test Product French"}
        ]
    }
    result3 = compute_given_name(document3)
    assert result3 == "Test Product French", f"Expected 'Test Product French', got '{result3}'"
    
    print("✅ Product names-based given_name tests passed!")


def test_given_name_edge_cases():
    """Test edge cases for given_name calculation."""
    
    # Test case 1: No categories and no product_name
    document1 = {
        "categories": "",
        "product_name": []
    }
    result1 = compute_given_name(document1)
    assert result1 == "", f"Expected empty string, got '{result1}'"
    
    # Test case 2: Missing fields entirely
    document2 = {}
    result2 = compute_given_name(document2)
    assert result2 == "", f"Expected empty string, got '{result2}'"
    
    # Test case 3: Product names with empty text
    document3 = {
        "categories": "en:spreads",  # Has colon
        "product_name": [
            {"lang": "main", "text": ""},
            {"lang": "fr", "text": "Valid Text"}
        ]
    }
    result3 = compute_given_name(document3)
    assert result3 == "Valid Text", f"Expected 'Valid Text', got '{result3}'"
    
    # Test case 4: Categories with only empty strings and colons
    document4 = {
        "categories": ",en:spreads, ,fr:test,",
        "product_name": [{"lang": "main", "text": "Fallback Name"}]
    }
    result4 = compute_given_name(document4)
    assert result4 == "Fallback Name", f"Expected 'Fallback Name', got '{result4}'"
    
    print("✅ Edge cases given_name tests passed!")


def test_add_given_name_to_results():
    """Test the add_given_name_to_results function."""
    
    # Sample results list
    results = [
        {
            "_id": "test1",
            "categories": "Spreads,Sweet Spreads,Chocolate Spreads",
            "product_name": [{"lang": "main", "text": "Product 1"}]
        },
        {
            "_id": "test2", 
            "categories": "en:spreads,fr:produits-a-tartiner",
            "product_name": [{"lang": "main", "text": "Product 2"}]
        }
    ]
    
    # Add given_name to results
    results_with_given_name = add_given_name_to_results(results)
    
    # Verify the function added given_name field
    assert 'given_name' in results_with_given_name[0], "given_name field missing from first result"
    assert 'given_name' in results_with_given_name[1], "given_name field missing from second result"
    
    # Verify the values are correct
    assert results_with_given_name[0]['given_name'] == "Chocolate Spreads", f"Expected 'Chocolate Spreads', got '{results_with_given_name[0]['given_name']}'"
    assert results_with_given_name[1]['given_name'] == "Product 2", f"Expected 'Product 2', got '{results_with_given_name[1]['given_name']}'"
    
    print("✅ add_given_name_to_results function test passed!")


def test_real_data_example():
    """Test with real data from first_record.json."""
    
    # Real data example based on first_record.json
    document = {
        "categories": "Petit-déjeuners,Produits à tartiner,Produits à tartiner sucrés,Pâtes à tartiner,Pâtes à tartiner aux noisettes,Pâtes à tartiner au chocolat,Pâtes à tartiner aux noisettes et au cacao",
        "product_name": [
            {"lang": "main", "text": "Véritable pâte à tartiner noisettes chocolat noir"},
            {"lang": "fr", "text": "Véritable pâte à tartiner noisettes chocolat noir"}
        ]
    }
    
    result = compute_given_name(document)
    expected = "Pâtes à tartiner aux noisettes et au cacao"  # Last category without colon
    assert result == expected, f"Expected '{expected}', got '{result}'"
    
    print("✅ Real data example test passed!")


if __name__ == "__main__":
    print("Testing given_name field calculation...")
    print("=" * 50)
    
    test_given_name_from_categories()
    test_given_name_from_product_names()
    test_given_name_edge_cases()
    test_add_given_name_to_results()
    test_real_data_example()
    
    print("\n🎉 All given_name tests passed!")
    print("The given_name field calculation is working correctly.")