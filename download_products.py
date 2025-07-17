#!/usr/bin/env python3
"""
Script to download and extract food records from OpenFoodFacts dataset.
Downloads first 5 records from the Hugging Face dataset and prints them to console.
"""

import json
import sys
from typing import List, Dict, Any


def get_mock_data() -> List[Dict[str, Any]]:
    """Returns mock data for testing when internet access is not available."""
    return [
        {
            "code": "3017620422003",
            "product_name": "Nutella",
            "brands": "Ferrero",
            "categories": "Spreads, Sweet spreads, Cocoa and hazelnuts spreads",
            "countries": "France",
            "ingredients_text": "Sugar, Palm Oil, Hazelnuts (13%), Skimmed Milk Powder (8.7%), Fat-reduced Cocoa (7.4%)",
            "nutrition_grades": "e",
            "main_category": "en:sweet-spreads",
            "created_datetime": "2023-01-15T10:30:00Z"
        },
        {
            "code": "3033710065967",
            "product_name": "Coca-Cola",
            "brands": "Coca-Cola",
            "categories": "Beverages, Carbonated drinks, Sodas",
            "countries": "France, Germany, Spain",
            "ingredients_text": "Carbonated water, sugar, caramel color, phosphoric acid, natural flavor, caffeine",
            "nutrition_grades": "d",
            "main_category": "en:sodas",
            "created_datetime": "2023-02-10T14:25:00Z"
        },
        {
            "code": "8000500037515",
            "product_name": "Barilla Spaghetti",
            "brands": "Barilla",
            "categories": "Plant-based foods, Cereals and their products, Pasta",
            "countries": "Italy, France, Germany",
            "ingredients_text": "Durum wheat semolina, water",
            "nutrition_grades": "a",
            "main_category": "en:pasta",
            "created_datetime": "2023-03-05T09:15:00Z"
        },
        {
            "code": "3229820787015",
            "product_name": "Danone Yogurt",
            "brands": "Danone",
            "categories": "Dairy products, Fermented dairy products, Yogurts",
            "countries": "France",
            "ingredients_text": "Whole milk, live yogurt cultures (L. bulgaricus, S. thermophilus)",
            "nutrition_grades": "b",
            "main_category": "en:yogurts",
            "created_datetime": "2023-04-12T16:45:00Z"
        },
        {
            "code": "3560070462414",
            "product_name": "Lay's Classic Chips",
            "brands": "Lay's",
            "categories": "Snacks, Salty snacks, Appetizers, Chips and fries, Potato chips",
            "countries": "France, Belgium, Netherlands",
            "ingredients_text": "Potatoes, vegetable oils, salt",
            "nutrition_grades": "d",
            "main_category": "en:potato-chips",
            "created_datetime": "2023-05-20T11:30:00Z"
        }
    ]


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
        print("🔄 Falling back to mock data for demonstration...")
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
    
    # Fall back to mock data if download failed
    if not records:
        print("🔄 Using mock data for demonstration...")
        records = get_mock_data()
    
    # Print the records to console
    print_records(records)
    
    print("\n" + "=" * 80)
    print("✅ Processing complete!")
    print(f"📊 Displayed {len(records)} food product records")
    print("=" * 80)


if __name__ == "__main__":
    main()
