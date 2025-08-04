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
    gpt35_result, gpt4_result = process_openai_assistance(search_query, mock_results)
    
    if gpt35_result:
        print(f"\n✅ GPT-3.5 was triggered!")
        print(f"  Model: {gpt35_result.model}")
        print(f"  Decision: {gpt35_result.decision}")
        print(f"  Error: {gpt35_result.error}")
        if gpt35_result.rephrased_query:
            print(f"  Rephrased query: {gpt35_result.rephrased_query}")
        if gpt35_result.reasoning:
            print(f"  Reasoning: {gpt35_result.reasoning}")
    else:
        print("❌ GPT-3.5 was not triggered")
    
    if gpt4_result:
        print(f"\n✅ GPT-4 was triggered!")
        print(f"  Model: {gpt4_result.model}")
        print(f"  Decision: {gpt4_result.decision}")
        print(f"  Error: {gpt4_result.error}")
        if gpt4_result.rephrased_query:
            print(f"  Rephrased query: {gpt4_result.rephrased_query}")
        if gpt4_result.reasoning:
            print(f"  Reasoning: {gpt4_result.reasoning}")
    else:
        print("❌ GPT-4 was not triggered")

if __name__ == "__main__":
    test_guaranteed_low_score()