#!/usr/bin/env python3
"""
Script to download and extract food records from OpenFoodFacts dataset.
Downloads first 5 records from the Hugging Face dataset and prints them to console.
"""

import json
import sys
from typing import List, Dict, Any



def download_from_huggingface() -> List[Dict[str, Any]]:
    """Download first 5 records from the OpenFoodFacts dataset on Hugging Face."""
    try:
        from datasets import load_dataset
        
        print("📥 Downloading dataset from Hugging Face...")
        print("🔗 Dataset: openfoodfacts/product-database")
        
        # Load dataset in streaming mode for efficiency
        dataset = load_dataset('openfoodfacts/product-database', split='train', streaming=True)
        
        print("✅ Dataset loaded successfully!")
        print("📊 Extracting first 5 records...")
        
        records = []
        for i, record in enumerate(dataset):
            if i >= 5:
                break
            records.append(record)
            print(f"  📄 Record {i+1}: {len(record)} fields")
        
        print(f"✅ Successfully downloaded {len(records)} records")
        return records
        
    except ImportError:
        print("❌ Required packages not installed. Please run: pip install -r requirements.txt")
        return []
    except Exception as e:
        print(f"❌ Error downloading from Hugging Face: {e}")
        return []


def print_records(records: List[Dict[str, Any]]) -> None:
    """Print records to console in a formatted way."""
    if not records:
        print("❌ No records to display")
        return
    
    print("\n" + "=" * 80)
    print("🍕 OPENFOODFACTS PRODUCT RECORDS")
    print("=" * 80)
    
    for i, record in enumerate(records, 1):
        print(f"\n📄 RECORD #{i}")
        print("-" * 40)
        
        # Display key fields in a nice format
        important_fields = [
            ('code', '🔢 Product Code'),
            ('product_name', '🏷️  Product Name'),
            ('brands', '🏢 Brand'),
            ('categories', '📂 Categories'),
            ('countries', '🌍 Countries'),
            ('ingredients_text', '🧪 Ingredients'),
            ('nutrition_grades', '⭐ Nutrition Grade'),
            ('main_category', '📁 Main Category'),
            ('created_datetime', '📅 Created')
        ]
        
        for field_key, field_label in important_fields:
            value = record.get(field_key, 'N/A')
            if value and value != 'N/A':
                # Truncate very long values
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"  {field_label}: {value}")
        
        # Show additional field count
        additional_fields = len(record) - len([f for f, _ in important_fields if record.get(f)])
        if additional_fields > 0:
            print(f"  📊 Additional fields: {additional_fields}")


def main():
    """Main function to download and display food records."""
    print("🍕 OpenFoodFacts Product Downloader")
    print("=" * 50)
    print("📥 Downloading first 5 food records from dataset")
    print("🔗 Source: https://huggingface.co/datasets/openfoodfacts/product-database")
    print()
    
    # Try to download from Hugging Face
    records = download_from_huggingface()
    
    # Print the records to console
    print_records(records)
    
    print("\n" + "=" * 80)
    print("✅ Processing complete!")
    print(f"📊 Displayed {len(records)} food product records")
    print("=" * 80)


if __name__ == "__main__":
    main()
