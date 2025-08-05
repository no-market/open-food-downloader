#!/usr/bin/env python3
"""
Simple test for OpenAI integration without requiring MongoDB or API keys.
"""

from openai_assistant import OpenAIAssistant, SCORE_THRESHOLD


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


def test_assistant_methods_exist():
    """Test that the assistant has the expected methods."""
    assistant = OpenAIAssistant()
    
    # Check that methods exist (even if client is not available)
    assert hasattr(assistant, 'process_with_level1')
    assert hasattr(assistant, 'process_with_level2') 
    assert hasattr(assistant, 'should_use_openai')
    print("✓ Assistant has expected methods")


def test_singleton_pattern():
    """Test that OpenAI assistant uses singleton pattern."""
    assistant1 = OpenAIAssistant()
    assistant2 = OpenAIAssistant()
    
    # Should be the same instance
    assert assistant1 is assistant2
    print("✓ Singleton pattern works correctly")


def test_level1_processing_without_api():
    """Test Level 1 processing without API key."""
    assistant = OpenAIAssistant()
    
    result = assistant.process_with_level1("test query", "test product")
    
    # Should return a result with error due to no API key
    assert result is not None
    assert result.error is not None
    assert "not available" in result.error
    print("✓ Level 1 processing handles missing API key gracefully")


def test_level2_processing_without_api():
    """Test Level 2 processing without API key."""
    assistant = OpenAIAssistant()
    
    result = assistant.process_with_level2("test query", "test product")
    
    # Should return a result with error due to no API key
    assert result is not None
    assert result.error is not None
    assert "not available" in result.error
    print("✓ Level 2 processing handles missing API key gracefully")


if __name__ == "__main__":
    print("Testing OpenAI Integration...")
    print("=" * 40)
    
    test_openai_assistant_initialization()
    test_score_threshold_logic()
    test_assistant_methods_exist()
    test_singleton_pattern()
    test_level1_processing_without_api()
    test_level2_processing_without_api()
    
    print("\n✅ All tests passed!")
    print("\nNote: To fully test with real OpenAI API:")
    print("1. Set OPENAI_API_KEY environment variable")
    print("2. Set MONGO_URI environment variable") 
    print("3. Run: python search_products.py 'test product'")