#!/usr/bin/env python3
"""
Test to verify OpenAI triggering with guaranteed low scores.
"""

from openai_assistant import process_openai_assistance

def test_guaranteed_low_score():
    """Test with manually set low RapidFuzz scores to guarantee OpenAI triggering."""
    
    # Create mock results with manually set low scores
    mock_results = [
        {
            "_id": "test123",
            "product_name": [{"lang": "en", "text": "Xyz Abc Random Product"}],
            "given_name": "Random Product",
            "brands": "Unknown Brand",
            "categories": "Random,Category",
            "labels": "Random Label",
            "quantity": "999g",
            "search_string": "xyz abc random product",
            "rapidfuzz_score": 25.0  # Manually set low score
        },
        {
            "_id": "test456", 
            "product_name": [{"lang": "en", "text": "Another Unrelated Item"}],
            "given_name": "Unrelated Item",
            "brands": "Different Brand",
            "categories": "Other,Different",
            "labels": "Other Label",
            "quantity": "123ml",
            "search_string": "another unrelated item",
            "rapidfuzz_score": 15.0  # Manually set low score
        }
    ]
    
    search_query = "BorówkaAmeryk500g"  # From the batch.txt file
    
    print(f"Testing with search query: '{search_query}'")
    print("Mock results have manually set low RapidFuzz scores (25.0 and 15.0)")
    
    # Test OpenAI assistance
    level1_result, level2_result = process_openai_assistance(search_query, mock_results)
    
    if level1_result:
        print(f"\n✅ GPT-3.5 was triggered!")
        print(f"  Model: {level1_result.model}")
        print(f"  Decision: {level1_result.decision}")
        print(f"  Error: {level1_result.error}")
        if level1_result.rephrased_query:
            print(f"  Rephrased query: {level1_result.rephrased_query}")
    else:
        print("❌ GPT-3.5 was not triggered")
    
    if level2_result:
        print(f"\n✅ GPT-4 was triggered!")
        print(f"  Model: {level2_result.model}")
        print(f"  Decision: {level2_result.decision}")
        print(f"  Error: {level2_result.error}")
        if level2_result.rephrased_query:
            print(f"  Rephrased query: {level2_result.rephrased_query}")
    else:
        print("❌ GPT-4 was not triggered")

if __name__ == "__main__":
    test_guaranteed_low_score()