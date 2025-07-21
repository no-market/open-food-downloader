#!/usr/bin/env python3
"""
Script to download and extract food records from OpenFoodFacts dataset.
Downloads first 5 records from the Hugging Face dataset and prints them to console.
"""

import json
import sys



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
        
        unique_food_groups = set()  # Collect unique food group tags
        unique_categories = set()  # Collect unique category tags
        
        # Open products file for writing incrementally to avoid memory issues
        products_filename = "products.json"
        with open(products_filename, 'w', encoding='utf-8') as products_file:
            products_file.write("[\n")  # Start JSON array
            first_product = True
            
            for i, record in enumerate(dataset):
                # if i >= 5:
                #     break
                
                # Extract unique product names from product_name array
                product_names = record.get('product_name', [])
                unique_product_names = []
                if isinstance(product_names, list):
                    seen_texts = set()
                    for name_obj in product_names:
                        if isinstance(name_obj, dict) and 'text' in name_obj:
                            text = name_obj['text']
                            if text and text not in seen_texts:
                                unique_product_names.append(text)
                                seen_texts.add(text)
                
                # Build search_string by concatenating specified fields
                search_components = []
                
                # Add unique product names
                search_components.extend(unique_product_names)
                
                # Add quantity
                quantity = record.get('quantity', '')
                if quantity:
                    search_components.append(quantity)
                
                # Add brands  
                brands = record.get('brands', '')
                if brands:
                    search_components.append(brands)
                
                # Add categories
                categories = record.get('categories', '')
                if categories:
                    search_components.append(categories)
                
                # Add labels
                labels = record.get('labels', '')
                if labels:
                    search_components.append(labels)
                
                # Create comma-separated search string
                search_string = ', '.join(search_components)
    
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
                    'search_string': search_string,
                }
                
                # Write product to file incrementally
                if not first_product:
                    products_file.write(",\n")
                products_file.write("  ")
                json.dump(product, products_file, ensure_ascii=False)
                first_product = False

                # Collect unique food groups tags
                food_groups_tags = record.get('food_groups_tags', [])
                if food_groups_tags:
                    # Add all tags to unique set
                    unique_food_groups.update(food_groups_tags)

                # Collect unique categories tags
                categories_tags = record.get('categories_tags', [])
                if categories_tags:
                    # Add all tags to unique set
                    unique_categories.update(categories_tags)

                lang = record.get('lang', "None_LANG_ATTRIBUTE")
                langs_map[lang] = langs_map.get(lang, 0) + 1

                print(f"Record {i + 1}: {lang}")

            # Close JSON array and file
            products_file.write("\n]")
        
        print("Language distribution:")
        for lang, count in langs_map.items():
            print(f" - {lang}: {count}")
        
        print(f"Successfully downloaded and saved {i + 1} records to '{products_filename}'")

        save_unique_food_groups_to_json(unique_food_groups)
        save_unique_categories_to_json(unique_categories)

    except ImportError:
        print("Required packages not installed. Please run: pip install -r requirements.txt")
        return []
    except Exception as e:
        print(f"Error downloading from Hugging Face: {e}")
        return []




def save_unique_food_groups_to_json(unique_food_groups: set) -> None:
    """Save unique food group tags to a separate file."""
    filename = "unique_food_groups.json"
    
    try:
        # Convert set to sorted list for consistent output
        unique_list = sorted(list(unique_food_groups))
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(unique_list, f, indent=2, ensure_ascii=False)
        print(f"Unique food groups ({len(unique_list)} tags) saved to '{filename}'")
    except Exception as e:
        print(f"Error saving unique food groups: {e}")




def save_unique_categories_to_json(unique_categories: set) -> None:
    """Save unique category tags to a separate file."""
    filename = "unique_categories.json"
    
    try:
        # Convert set to sorted list for consistent output
        unique_list = sorted(list(unique_categories))
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(unique_list, f, indent=2, ensure_ascii=False)
        print(f"Unique categories ({len(unique_list)} tags) saved to '{filename}'")
    except Exception as e:
        print(f"Error saving unique categories: {e}")




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
    
    print(f"Processing complete!")
    


if __name__ == "__main__":
    main()
