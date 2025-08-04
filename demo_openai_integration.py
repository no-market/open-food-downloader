#!/usr/bin/env python3
"""
Demo script showing how to test the complete OpenAI integration.

This script demonstrates how to set up and test the OpenAI assistance feature
for the open-food-downloader project.
"""

import os
import json

def demo_usage():
    """Show usage examples for the OpenAI integration."""
    
    print("🤖 OpenAI Integration Demo")
    print("=" * 50)
    
    print("\n📋 Setup Instructions:")
    print("1. Install dependencies:")
    print("   pip install -r requirements.txt")
    print("\n2. Set environment variables:")
    print("   export MONGO_URI='mongodb://localhost:27017/openfooddb'")
    print("   export OPENAI_API_KEY='your-openai-api-key-here'")
    
    print("\n🔍 Single Product Search:")
    print("   python search_products.py 'BorówkaAmeryk500g'")
    print("   python search_products.py 'ParówKurNatTarcz160g'")
    print("   python search_products.py 'chocolate cookies'")
    
    print("\n📦 Batch Product Search:")
    print("   python search_batch.py -b batch.txt -o results.csv")
    
    print("\n🎯 How OpenAI Assistance Works:")
    print("• Triggers when RapidFuzz score < 50.0")
    print("• GPT-3.5 first: Quick analysis and query rephrasing") 
    print("• GPT-4 second: Advanced analysis with enhanced context")
    print("• Decisions: valid_product, rephrased_successfully, not_a_product, no_match_found")
    
    print("\n📊 Expected Output Structure:")
    output_example = {
        "timestamp": "2024-01-01T12:00:00Z",
        "input_string": "BorówkaAmeryk500g", 
        "formatted_string": "borówka ameryk 500 g",
        "direct_search": {"count": 10, "results": "..."},
        "rapidfuzz_search": {"count": 10, "results": "..."},
        "openai_gpt35": {
            "model": "gpt-3.5-turbo",
            "decision": "rephrased_successfully",
            "rephrased_query": "american blueberry 500g",
            "confidence": 0.85,
            "reasoning": "Recognized Polish product name for American blueberries"
        },
        "openai_gpt4": {
            "model": "gpt-4", 
            "decision": "valid_product",
            "rephrased_query": "blueberry american 500 grams",
            "confidence": 0.92,
            "reasoning": "Enhanced analysis suggests this is frozen American blueberries"
        }
    }
    
    print(json.dumps(output_example, indent=2))
    
    print("\n📋 Batch CSV Output:")
    print("Number    | Input string      | Given Name              | Score | ID  | Categories | Product Names")
    print("----------|-------------------|-------------------------|-------|-----|------------|---------------")
    print("1.Mongo   | BorówkaAmeryk500g | Frozen Blueberries     | 85.2  | ... | Fruits     | American Blueberries")
    print("1.Fuzzy   | BorówkaAmeryk500g | Frozen Blueberries     | 92.1  | ... | Fruits     | American Blueberries") 
    print("1.gpt-3.5 | BorówkaAmeryk500g | rephrased_successfully | 85.0  | AI  | Recognized | american blueberry 500g")
    print("1.gpt-4   | BorówkaAmeryk500g | valid_product          | 92.0  | AI  | Enhanced   | blueberry american 500g")
    
    print("\n⚠️  Error Handling:")
    print("• Missing OPENAI_API_KEY: Graceful degradation (no OpenAI results)")
    print("• API call failures: Error messages in results, processing continues")
    print("• Missing MongoDB: Expected error (primary data source required)")
    
    print("\n🧪 Testing Without API Keys:")
    print("   python test_openai_integration.py")
    print("   python test_low_score_trigger.py")
    
    print("\n✅ Integration Complete!")

if __name__ == "__main__":
    demo_usage()