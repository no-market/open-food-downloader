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
        
        hierarchy = {}  # Build hierarchy incrementally to avoid memory issues
        unique_food_groups = set()  # Collect unique food group tags
        
        # Open products file for writing incrementally to avoid memory issues
        products_filename = "products.json"
        with open(products_filename, 'w', encoding='utf-8') as products_file:
            products_file.write("[\n")  # Start JSON array
            first_product = True
            
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
                
                # Write product to file incrementally
                if not first_product:
                    products_file.write(",\n")
                products_file.write("  ")
                json.dump(product, products_file, ensure_ascii=False)
                first_product = False

                # Process food groups hierarchy directly in the loop to avoid memory issues
                food_groups_tags = record.get('food_groups_tags', [])
                if food_groups_tags:
                    # Add all tags to unique set
                    unique_food_groups.update(food_groups_tags)
                    
                    # Build hierarchy: food_groups_tags[0] is child of food_groups_tags[1], etc.
                    for j in range(len(food_groups_tags)):
                        child = food_groups_tags[j]
                        
                        if child not in hierarchy:
                            hierarchy[child] = {'parent': None, 'children': []}
                        
                        # If there's a parent (next element in array)
                        if j + 1 < len(food_groups_tags):
                            parent = food_groups_tags[j + 1]
                            hierarchy[child]['parent'] = parent
                            
                            # Ensure parent exists in hierarchy
                            if parent not in hierarchy:
                                hierarchy[parent] = {'parent': None, 'children': []}
                            
                            # Add child to parent's children list if not already there
                            if child not in hierarchy[parent]['children']:
                                hierarchy[parent]['children'].append(child)

                lang = record.get('lang', "None_LANG_ATTRIBUTE")
                langs_map[lang] = langs_map.get(lang, 0) + 1

                print(f"Record {i + 1}: {lang}")

            # Close JSON array and file
            products_file.write("\n]")
        
        print("Language distribution:")
        for lang, count in langs_map.items():
            print(f" - {lang}: {count}")
        
        print(f"Successfully downloaded and saved {i + 1} records to '{products_filename}'")

        save_hierarchy_to_json(hierarchy)
        save_unique_food_groups_to_json(unique_food_groups)

    except ImportError:
        print("Required packages not installed. Please run: pip install -r requirements.txt")
        return []
    except Exception as e:
        print(f"Error downloading from Hugging Face: {e}")
        return []



def build_nested_hierarchy(flat_hierarchy):
    """
    Convert flat hierarchy to nested hierarchy structure.
    
    Args:
        flat_hierarchy: Dict with structure {tag: {'parent': parent_tag, 'children': [child_tags]}}
    
    Returns:
        Dict with nested structure where only root nodes are at top level
    """
    # Find root nodes (nodes with no parent)
    root_nodes = {tag: data for tag, data in flat_hierarchy.items() if data['parent'] is None}
    
    def build_children_tree(node_tag):
        """Recursively build the nested children structure for a node."""
        if node_tag not in flat_hierarchy:
            return {"children": []}
        
        children_list = []
        for child_tag in flat_hierarchy[node_tag]['children']:
            child_tree = build_children_tree(child_tag)
            children_list.append({child_tag: child_tree})
        
        return {"children": children_list}
    
    # Build the nested structure
    nested_hierarchy = {}
    for root_tag in root_nodes:
        nested_hierarchy[root_tag] = build_children_tree(root_tag)
    
    return nested_hierarchy


def save_hierarchy_to_json(flat_hierarchy: dict) -> None:
    """Save food groups hierarchy to a separate file in nested format."""
    filename = "food_groups_hierarchy.json"
    
    try:
        # Convert flat hierarchy to nested format
        nested_hierarchy = build_nested_hierarchy(flat_hierarchy)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(nested_hierarchy, f, indent=2, ensure_ascii=False)
        print(f"Food groups hierarchy saved to '{filename}'")
    except Exception as e:
        print(f"Error saving food groups hierarchy: {e}")


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
