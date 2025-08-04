#!/usr/bin/env python3
"""
Simple test for OpenAI integration without requiring MongoDB or API keys.
"""

from openai_assistant import OpenAIAssistant, process_openai_assistance, SCORE_THRESHOLD


def test_openai_assistant_initialization():
    """Test OpenAI assistant initialization without API key."""
    assistant = OpenAIAssistant()
    
    # Should initialize without error even without API key
    assert assistant is not None
    print("✓ OpenAI assistant initialization works")


def test_score_threshold_logic():
    """Test the score threshold logic."""
    assistant = OpenAIAssistant()
    
    # High score should not trigger OpenAI
    assert not assistant.should_use_openai(80.0)
    print(f"✓ Score 80.0 correctly does not trigger OpenAI (threshold: {SCORE_THRESHOLD})")
    
    # Low score should trigger OpenAI
    assert assistant.should_use_openai(30.0)
    print(f"✓ Score 30.0 correctly triggers OpenAI (threshold: {SCORE_THRESHOLD})")


def test_process_openai_assistance_no_results():
    """Test OpenAI assistance with no search results."""
    gpt35_result, gpt4_result = process_openai_assistance("test", [])
    
    # Should return None when no results
    assert gpt35_result is None
    assert gpt4_result is None
    print("✓ No OpenAI processing when no search results")


def test_process_openai_assistance_high_scores():
    """Test OpenAI assistance with high scores (should not trigger)."""
    mock_results = [
        {"rapidfuzz_score": 85.0, "given_name": "Test Product"},
        {"rapidfuzz_score": 75.0, "given_name": "Another Product"}
    ]
    
    gpt35_result, gpt4_result = process_openai_assistance("test", mock_results)
    
    # Should return None when scores are high
    assert gpt35_result is None
    assert gpt4_result is None
    print("✓ No OpenAI processing when scores are above threshold")


def test_process_openai_assistance_low_scores():
    """Test OpenAI assistance with low scores (should trigger but fail without API key)."""
    mock_results = [
        {"rapidfuzz_score": 25.0, "given_name": "Test Product"},
        {"rapidfuzz_score": 15.0, "given_name": "Another Product"}
    ]
    
    gpt35_result, gpt4_result = process_openai_assistance("test", mock_results)
    
    # Should return results (though with errors due to no API key)
    assert gpt35_result is not None
    assert gpt4_result is not None
    
    # Should have errors due to missing API key
    assert gpt35_result.error is not None
    assert gpt4_result.error is not None
    
    print("✓ OpenAI processing triggered for low scores (with expected API key errors)")
    print(f"  GPT-3.5 error: {gpt35_result.error}")
    print(f"  GPT-4 error: {gpt4_result.error}")


if __name__ == "__main__":
    print("Testing OpenAI Integration...")
    print("=" * 40)
    
    test_openai_assistant_initialization()
    test_score_threshold_logic()
    test_process_openai_assistance_no_results()
    test_process_openai_assistance_high_scores()
    test_process_openai_assistance_low_scores()
    
    print("\n✅ All tests passed!")
    print("\nNote: To fully test with real OpenAI API:")
    print("1. Set OPENAI_API_KEY environment variable")
    print("2. Set MONGO_URI environment variable") 
    print("3. Run: python search_products.py 'test product'")