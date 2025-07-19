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
        for i, record in enumerate(dataset):
            if i >= 5:
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

            print(f"Record {i + 1}: {lang}")


        print("Language distribution:")
        for lang, count in langs_map.items():
            print(f" - {lang}: {count}")
        
        print(f"Successfully downloaded {len(products)} records")

        save_products_to_json(products)
        save_food_groups_hierarchy(products)

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


def build_food_groups_hierarchy(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build food groups hierarchy from products data."""
    hierarchy = {}
    
    for product in products:
        food_groups_tags = product.get('food_groups_tags', [])
        if not food_groups_tags:
            continue
            
        # Build hierarchy: food_groups_tags[0] is child of food_groups_tags[1], etc.
        for i in range(len(food_groups_tags)):
            child = food_groups_tags[i]
            
            if child not in hierarchy:
                hierarchy[child] = {'parent': None, 'children': []}
            
            # If there's a parent (next element in array)
            if i + 1 < len(food_groups_tags):
                parent = food_groups_tags[i + 1]
                hierarchy[child]['parent'] = parent
                
                # Ensure parent exists in hierarchy
                if parent not in hierarchy:
                    hierarchy[parent] = {'parent': None, 'children': []}
                
                # Add child to parent's children list if not already there
                if child not in hierarchy[parent]['children']:
                    hierarchy[parent]['children'].append(child)
    
    return hierarchy


def save_food_groups_hierarchy(products: List[Dict[str, Any]]) -> None:
    """Build and save food groups hierarchy to a separate file."""
    hierarchy = build_food_groups_hierarchy(products)
    filename = "food_groups_hierarchy.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(hierarchy, f, indent=2, ensure_ascii=False)
        print(f"Food groups hierarchy saved to '{filename}'")
    except Exception as e:
        print(f"Error saving food groups hierarchy: {e}")


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
    
    # If products.json exists, also process it for food groups hierarchy
    try:
        with open("products.json", 'r', encoding='utf-8') as f:
            existing_products = json.load(f)
            if existing_products:
                print("Processing existing products for food groups hierarchy...")
                save_food_groups_hierarchy(existing_products)
    except FileNotFoundError:
        print("No existing products.json found")
    except Exception as e:
        print(f"Error processing existing products: {e}")
    
    # Print the records to console
    # print_records(records)
    
    print(f"Processing complete!")
    


if __name__ == "__main__":
    main()
