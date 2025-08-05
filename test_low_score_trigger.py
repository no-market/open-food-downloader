#!/usr/bin/env python3
"""
Test to verify OpenAI triggering with guaranteed low scores.
"""

from openai_assistant import OpenAIAssistant, SCORE_THRESHOLD

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
    
    # Test OpenAI assistance with low score simulation
    assistant = OpenAIAssistant()
    
    # Check if low scores would trigger OpenAI
    best_score = max(result.get('rapidfuzz_score', 0) for result in mock_results)
    should_trigger = assistant.should_use_openai(best_score)
    
    print(f"Best score: {best_score}")
    print(f"Threshold: {SCORE_THRESHOLD}")
    print(f"Should trigger OpenAI: {should_trigger}")
    
    if should_trigger:
        print(f"\n✅ OpenAI would be triggered (score {best_score} < threshold {SCORE_THRESHOLD})")
        
        # Test Level 1 processing
        top_result_name = mock_results[0].get('given_name') if mock_results else None
        level1_result = assistant.process_with_level1(search_query, top_result_name)
        
        print(f"\nLevel 1 Result:")
        print(f"  Model: {level1_result.model}")
        print(f"  Decision: {level1_result.decision}")
        print(f"  Error: {level1_result.error}")
        if level1_result.rephrased_query:
            print(f"  Rephrased query: {level1_result.rephrased_query}")
        
        # Test Level 2 processing
        level2_result = assistant.process_with_level2(search_query, top_result_name, level1_result)
        
        print(f"\nLevel 2 Result:")
        print(f"  Model: {level2_result.model}")
        print(f"  Decision: {level2_result.decision}")
        print(f"  Error: {level2_result.error}")
        if level2_result.rephrased_query:
            print(f"  Rephrased query: {level2_result.rephrased_query}")
    else:
        print(f"❌ OpenAI would not be triggered (score {best_score} >= threshold {SCORE_THRESHOLD})")

if __name__ == "__main__":
    test_guaranteed_low_score()