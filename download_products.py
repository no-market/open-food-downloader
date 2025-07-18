#!/usr/bin/env python3
"""
Script to download and extract food records from OpenFoodFacts dataset.
Downloads first 5 records from the Hugging Face dataset and prints them to console.
"""

import json
import sys
from typing import List, Dict, Any



def download_from_huggingface():
    """Download first 5 records from the OpenFoodFacts dataset on Hugging Face."""
    try:
        from datasets import load_dataset
        
        print("Downloading dataset from Hugging Face...")
        print("Dataset: openfoodfacts/product-database")
        
        # Load dataset in streaming mode for efficiency
        dataset = load_dataset('openfoodfacts/product-database', split='food', streaming=True)
        
        # Filter dataset to only include Polish records using built-in filter method
        dataset = dataset.filter(lambda record: record.get('lang') == 'pl')
        
        print("Dataset loaded successfully!")
        print("Extracting records...")
        langs_map = {}
        
        products = []
        record_count = 0
        for i, record in enumerate(dataset):
            if record_count >= 5:
                break
 
            product = {
                '_id': record.get('code'),
                'lang': record.get('lang'),
                'product_name': record.get('product_name'),
                'brands': record.get('brands'),
                'food_groups_tags': record.get('food_groups_tags'),
                'product_quantity_unit': record.get('product_quantity_unit'),
                'product_quantity': record.get('product_quantity'),
                'quantity': record.get('quantity'),
                'categories_tags': record.get('categories_tags'),
                'categories': [c.strip() for c in record.get('categories', '').split(',') if record.get('categories')] if record.get('categories') else [],
                'labels_tags': record.get('labels_tags'),
                'labels': [l.strip() for l in record.get('labels', '').split(',') if record.get('labels')] if record.get('labels') else [],
                'popularity_key': record.get('popularity_key'),
                'popularity_tags': record.get('popularity_tags'),
                'nutriscore_grade': record.get('nutriscore_grade'),
                'nutriscore_score': record.get('nutriscore_score'),
            }
            products.append(product)

            lang = record.get('lang', "None_LANG_ATTRIBUTE")
            langs_map[lang] = langs_map.get(lang, 0) + 1

            record_count += 1
            print(f"Record {record_count}: {lang}")


        print("Language distribution:")
        for lang, count in langs_map.items():
            print(f" - {lang}: {count}")
        
        print(f"Successfully downloaded {record_count} records")

        save_products_to_json(products)

    except ImportError:
        print("Required packages not installed. Please run: pip install -r requirements.txt")
        return []
    except Exception as e:
        print(f"Error downloading from Hugging Face: {e}")
        return []


def save_products_to_json(products: List[Dict[str, Any]]) -> None:
    """Save the products to a JSON file."""
    filename = "products.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"Products saved to '{filename}'")
    except Exception as e:
        print(f"Error saving products to JSON: {e}")


# def print_records(records: List[Dict[str, Any]]) -> None:
#     """Print records to console as raw data."""
#     if not records:
#         print("No records to display")
#         return
    
#     for i, record in enumerate(records, 1):
#         print(f"RECORD {i}:")
#         print(json.dumps(record, indent=2, ensure_ascii=False))
#         print()


def main():
    """Main function to download and display food records."""
    print("OpenFoodFacts Product Downloader")
    print("Downloading first 5 food records from dataset")
    print("Source: https://huggingface.co/datasets/openfoodfacts/product-database")
    print()
    
    # Try to download from Hugging Face
    download_from_huggingface()
    
    # Print the records to console
    # print_records(records)
    
    print(f"Processing complete!")
    


if __name__ == "__main__":
    main()
