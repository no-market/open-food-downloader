#!/usr/bin/env python3
"""
Script to download and extract food records from OpenFoodFacts dataset.
Downloads records from the Hugging Face dataset and stores them in MongoDB.
"""

import json
import os
import sys


def is_valid_product(record):
    """
    Check if a product meets the validation criteria:
    - Has at least 1 not blank product_name[].text
    - Has at least 1 not blank category which does not contain ":" or starts with "pl:" (case insensitive)
    
    Args:
        record: The product record from the dataset
        
    Returns:
        bool: True if product is valid, False if it should be skipped
    """
    # Check product names
    product_names = record.get('product_name', [])
    has_valid_name = False
    
    if isinstance(product_names, list):
        for name_obj in product_names:
            if isinstance(name_obj, dict) and 'text' in name_obj:
                text = name_obj['text']
                if text and text.strip():  # Not blank
                    has_valid_name = True
                    break
    
    if not has_valid_name:
        return False
    
    # Check categories
    categories = record.get('categories', '')
    has_valid_category = False
    
    if categories:
        # Split by comma and check each category
        category_list = [c.strip() for c in categories.split(',') if c.strip()]
        for category in category_list:
            if category:
                # Check if category starts with "pl:" (case insensitive) or has no colon
                if category.lower().startswith('pl:'):
                    pl_category = category[3:]  # Remove "pl:" prefix
                    if pl_category:  # Only consider valid if non-empty after prefix removal
                        has_valid_category = True
                        break
                elif ':' not in category:
                    has_valid_category = True
                    break
    
    return has_valid_category


def download_from_huggingface():
    """Download records from the OpenFoodFacts dataset on Hugging Face and optionally store in MongoDB."""
    try:
        from datasets import load_dataset
        
        # Check if we should save to MongoDB (default: true)
        save_to_mongo = os.getenv('SAVE_TO_MONGO', 'true').lower() in ('true', '1', 'yes', 'on')
        
        save_to_mongo = os.getenv('SAVE_TO_MONGO', 'true').lower() in ('true', '1', 'yes', 'on')
        
        client = None
        collection = None
        
        if save_to_mongo:
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure, ConfigurationError
            
            # Get MongoDB URI from environment variable
            mongo_uri = os.getenv('MONGO_URI')
            if not mongo_uri:
                print("Error: MONGO_URI environment variable not set")
                print("Please set the MongoDB connection URI in the MONGO_URI environment variable")
                return []
            
            # Initialize MongoDB connection
            try:
                print(f"Connecting to MongoDB...")
                client = MongoClient(mongo_uri)
                # Test connection
                client.admin.command('ping')
                db = client.get_database()  # Use default database from URI or 'test'
                collection = db['products-catalog']
                print("Successfully connected to MongoDB")
            except (ConnectionFailure, ConfigurationError) as e:
                print(f"Error connecting to MongoDB: {e}")
                return []
        else:
            print("SAVE_TO_MONGO is disabled - data will be processed but not stored in MongoDB")
        
        print("Downloading dataset from Hugging Face...")
        print("Dataset: openfoodfacts/product-database")
        
        # Load dataset in streaming mode for efficiency
        dataset = load_dataset('openfoodfacts/product-database', split='food', streaming=True)
        
        # Filter dataset to only include Polish records using built-in filter method
        dataset = dataset.filter(lambda record: record.get('lang') == 'pl')
        
        print("Dataset loaded successfully!")
        if save_to_mongo:
            print("Extracting and storing records in MongoDB...")
        else:
            print("Extracting records (MongoDB storage disabled)...")
        langs_map = {}
        
        unique_food_groups = set()  # Collect unique food group tags
        unique_categories = set()  # Collect unique category tags
        unique_last_categories = {}  # Collect unique last category mapping to full path
        
        # Process records and optionally store directly in MongoDB
        skipped_count = 0
        for i, record in enumerate(dataset):
            # if i >= 5:
            #     break
            
            # Validate product before processing
            if not is_valid_product(record):
                skipped_count += 1
                if skipped_count <= 10:  # Log first 10 skipped products for debugging
                    print(f"Skipped product {record.get('code', 'unknown')}: Missing valid product name or category without ':'")
                continue
            
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
            
            # Create space-separated search string (lowercase)
            search_string = ' '.join(search_components).lower().replace(',', ' ')

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
            
            # Store product directly in MongoDB (upsert to handle duplicates) if enabled
            if save_to_mongo and collection is not None:
                try:
                    collection.replace_one({'_id': product['_id']}, product, upsert=True)
                except Exception as e:
                    print(f"Error upserting product {product.get('_id')}: {e}")
                    continue

            # Collect unique food groups tags
            food_groups_tags = record.get('food_groups_tags', [])
            if food_groups_tags:
                # Add all tags to unique set
                unique_food_groups.update(food_groups_tags)

            # Collect unique categories from categories field
            categories = record.get('categories', '')
            if categories:
                # Split by comma and add each category to unique set
                category_list = [c.strip() for c in categories.split(',') if c.strip()]
                unique_categories.update(category_list)
                
                # Build mapping from last category to full path, skipping categories with ":"
                if category_list:
                    # Filter out categories containing ":"
                    filtered_categories = [cat for cat in category_list if ':' not in cat]
                    
                    if filtered_categories:
                        # Get the last category
                        last_category = filtered_categories[-1]
                        
                        # Build full path using ">" separator
                        full_path = " > ".join(filtered_categories)
                        
                        # Store the mapping
                        unique_last_categories[last_category] = full_path

            lang = record.get('lang', "None_LANG_ATTRIBUTE")
            langs_map[lang] = langs_map.get(lang, 0) + 1

            if save_to_mongo:
                print(f"Record {i + 1}: {product.get('_id')} - Stored in MongoDB")
            else:
                print(f"Record {i + 1}: {product.get('_id')} - Processed (MongoDB storage disabled)")
            

        print("Language distribution:")
        for lang, count in langs_map.items():
            print(f" - {lang}: {count}")
        
        processed_count = i + 1 - skipped_count  # Total processed minus skipped
        if save_to_mongo:
            print(f"Successfully processed and stored {processed_count} records in MongoDB")
        else:
            print(f"Successfully processed {processed_count} records (MongoDB storage was disabled)")
        
        if skipped_count > 0:
            print(f"Skipped {skipped_count} invalid products (missing valid name or categories with ':')")

        save_unique_food_groups_to_json(unique_food_groups)
        save_unique_categories_to_json(unique_categories)
        save_unique_last_categories_to_json(unique_last_categories)
        
        # Store categories in separate collection if MongoDB is enabled
        if save_to_mongo and collection is not None:
            store_categories_collection(client.get_database(), unique_last_categories)
        
        # Close MongoDB connection if it was opened
        if client:
            client.close()

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




def save_unique_last_categories_to_json(unique_last_categories: dict) -> None:
    """Save unique last category mappings to a separate file."""
    filename = "unique_last_categories.json"
    
    try:
        # Save as dictionary with sorted keys for consistent output
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(unique_last_categories, f, indent=2, ensure_ascii=False, sort_keys=True)
        print(f"Unique last categories ({len(unique_last_categories)} items) saved to '{filename}'")
    except Exception as e:
        print(f"Error saving unique last categories: {e}")


def store_categories_collection(db, unique_last_categories: dict) -> None:
    """
    Store valid unique categories into separate "categories" collection.
    
    Structure: {
        "_id": ObjectId,
        "name": "Chocolate Spreads", 
        "ancestors": ["Food", "Spreads"]
    }
    
    Before storing, checks if standard index on "name" exists, if not - creates it.
    
    Args:
        db: MongoDB database instance
        unique_last_categories: Dictionary mapping last category to full path
    """
    try:
        collection = db['categories']
        print(f"\nProcessing categories collection...")
        
        # Check if index on "name" exists, create if not
        existing_indexes = list(collection.list_indexes())
        name_index_exists = any(
            'name' in index.get('key', {}) 
            for index in existing_indexes
        )
        
        if not name_index_exists:
            print("Creating index on 'name' field...")
            collection.create_index('name')
            print("Index on 'name' field created successfully")
        else:
            print("Index on 'name' field already exists")
        
        # Process each category mapping
        categories_processed = 0
        categories_updated = 0
        
        for category_name, full_path in unique_last_categories.items():
            if not category_name or not full_path:
                continue
                
            # Parse the full path to extract ancestors
            # Example: "Food > Spreads > Chocolate Spreads" -> ancestors: ["Food", "Spreads"]
            path_parts = [part.strip() for part in full_path.split(' > ') if part.strip()]
            
            # The ancestors are all parts except the last one (which is the category name itself)
            ancestors = path_parts[:-1] if len(path_parts) > 1 else []
            
            # Verify the last part matches the category name
            if path_parts and path_parts[-1] != category_name:
                print(f"Warning: Category name mismatch: '{category_name}' vs '{path_parts[-1]}' in path '{full_path}'")
                continue
            
            # Create category document
            category_doc = {
                'name': category_name,
                'ancestors': ancestors
            }
            
            # Upsert the category (update if exists, insert if not)
            result = collection.replace_one(
                {'name': category_name}, 
                category_doc, 
                upsert=True
            )
            
            categories_processed += 1
            if result.upserted_id:
                categories_updated += 1
                if categories_processed <= 5:  # Log first 5 for debugging
                    print(f"  Inserted category: '{category_name}' with ancestors: {ancestors}")
            else:
                if categories_processed <= 5:  # Log first 5 for debugging
                    print(f"  Updated category: '{category_name}' with ancestors: {ancestors}")
        
        print(f"Categories collection processing complete:")
        print(f"  Total categories processed: {categories_processed}")
        print(f"  New categories inserted: {categories_updated}")
        print(f"  Existing categories updated: {categories_processed - categories_updated}")
        
    except Exception as e:
        print(f"Error storing categories collection: {e}")




def main():
    """Main function to download and optionally store food records in MongoDB."""
    print("OpenFoodFacts Product Downloader")
    save_to_mongo = os.getenv('SAVE_TO_MONGO', 'true').lower() in ('true', '1', 'yes', 'on')
    
    if save_to_mongo:
        print("Downloading food records from dataset and storing in MongoDB")
    else:
        print("Downloading food records from dataset (MongoDB storage disabled)")
    
    print("Source: https://huggingface.co/datasets/openfoodfacts/product-database")
    print()
    
    # Try to download from Hugging Face
    download_from_huggingface()
    
    print(f"Processing complete!")
    


if __name__ == "__main__":
    main()
