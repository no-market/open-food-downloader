#!/usr/bin/env python3
"""
Demonstration script for Pinecone integration with sample data.
Shows how the category embedding and upload functionality works.
"""

import os
from pinecone_integration import process_categories_to_pinecone

def demo_pinecone_functionality():
    """Demonstrate the Pinecone functionality with sample data."""
    
    print("🚀 Pinecone Integration Demo")
    print("=" * 50)
    
    # Sample category data similar to what would be extracted from OpenFoodFacts
    sample_categories = {
        'Instant noodles': 'Food > Pasta > Instant noodles',
        'Dark chocolate': 'Food > Sweets > Chocolate > Dark chocolate',
        'Greek yogurt': 'Food > Dairy > Yogurt > Greek yogurt',
        'Olive oil': 'Food > Oils > Olive oil',
        'Sourdough bread': 'Food > Bakery > Bread > Sourdough bread',
        'Organic coffee': 'Food > Beverages > Coffee > Organic coffee',
        'Quinoa pasta': 'Food > Pasta > Quinoa pasta',
        'Almond milk': 'Food > Dairy alternatives > Plant milk > Almond milk'
    }
    
    print(f"📊 Sample categories to process ({len(sample_categories)} items):")
    for category, path in sample_categories.items():
        print(f"  • {category} → {path}")
    
    print(f"\n🔧 Environment Configuration:")
    print(f"  • SAVE_TO_PINECONE: {os.getenv('SAVE_TO_PINECONE', 'false')}")
    print(f"  • PINECONE_API_KEY: {'✓ Set' if os.getenv('PINECONE_API_KEY') else '✗ Not set'}")
    print(f"  • PINECONE_INDEX_NAME: {os.getenv('PINECONE_INDEX_NAME', 'product-categories')}")
    
    # Check if Pinecone is enabled
    from pinecone_integration import check_pinecone_enabled
    
    if not check_pinecone_enabled():
        print(f"\n⚠️  Pinecone integration is disabled.")
        print(f"To enable it, set: export SAVE_TO_PINECONE=true")
        print(f"Also set your Pinecone credentials:")
        print(f"  export PINECONE_API_KEY=your-api-key")
        print(f"  export PINECONE_INDEX_NAME=product-categories")
        return
    
    print(f"\n✅ Pinecone integration is enabled!")
    
    try:
        from pinecone_integration import get_pinecone_config
        config = get_pinecone_config()
        print(f"  • Using index: {config['index_name']}")
        
        print(f"\n🔄 Processing categories...")
        result = process_categories_to_pinecone(sample_categories)
        
        if result:
            print(f"\n🎉 Success! Categories have been embedded and uploaded to Pinecone.")
            print(f"   • Created embeddings using SentenceTransformers (all-MiniLM-L6-v2)")
            print(f"   • Uploaded {len(sample_categories)} vectors to Pinecone index")
            print(f"   • Each vector includes category ID, 384-dim embedding, and metadata")
            
            print(f"\n📝 Example vector structure:")
            print(f"   {{")
            print(f"     'id': 'instant_noodles',")
            print(f"     'values': [0.1, 0.2, ..., 0.384],  # 384-dimensional embedding")
            print(f"     'metadata': {{")
            print(f"       'full_path': 'Food > Pasta > Instant noodles',")
            print(f"       'category_name': 'instant noodles'")
            print(f"     }}")
            print(f"   }}")
        else:
            print(f"\n❌ Failed to process categories to Pinecone.")
            
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == '__main__':
    demo_pinecone_functionality()