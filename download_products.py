#!/usr/bin/env python3
"""
Script to download and extract food records from OpenFoodFacts dataset.
Downloads records from the Hugging Face dataset and stores them in MongoDB.
"""

import json
import os
import sys


def get_download_limit():
    """Read optional download limit from DOWNLOAD_LIMIT."""
    raw_limit = os.getenv('DOWNLOAD_LIMIT', '').strip()
    if not raw_limit:
        return None

    try:
        limit = int(raw_limit)
    except ValueError:
        print(f"Warning: DOWNLOAD_LIMIT='{raw_limit}' is not a valid integer. Processing all records.")
        return None

    if limit <= 0:
        return None

    return limit


def get_download_limit_type():
    """Read whether DOWNLOAD_LIMIT applies to products or categories."""
    limit_type = os.getenv('DOWNLOAD_LIMIT_TYPE', 'products').strip().lower()
    if limit_type not in ('products', 'categories'):
        print(f"Warning: DOWNLOAD_LIMIT_TYPE='{limit_type}' is invalid. Using 'products'.")
        return 'products'
    return limit_type


def limit_mapping_items(mapping: dict, limit):
    """Return mapping capped to the first limit items, or unchanged when no limit is set."""
    if not limit:
        return mapping
    return dict(list(mapping.items())[:limit])


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


def get_direct_category(category_list):
    """
    Return the direct product category from a parsed category path.

    The direct category is the last non-tag category in the product's category
    path. Parent categories are not counted here.
    """
    filtered_categories = [cat for cat in category_list if ':' not in cat]
    if not filtered_categories:
        return None
    return filtered_categories[-1]


def load_category_language_model():
    """Load the Hugging Face fastText language identification model."""
    if os.getenv('CATEGORY_LANGUAGE_DETECTION', 'true').lower() not in ('true', '1', 'yes', 'on'):
        print("Category language detection is disabled")
        return None

    repo_id = os.getenv('CATEGORY_LANGUAGE_MODEL_REPO', 'facebook/fasttext-language-identification')
    filename = os.getenv('CATEGORY_LANGUAGE_MODEL_FILE', 'model.bin')

    try:
        import fasttext
        from huggingface_hub import hf_hub_download

        print(f"Loading category language model from {repo_id}/{filename}...")
        model_path = hf_hub_download(repo_id=repo_id, filename=filename)
        return fasttext.load_model(model_path)
    except Exception as e:
        print(f"Warning: Could not load category language model: {e}")
        return None


def predict_category_language(model, category_name, category_path):
    """Predict language for a category using its name plus full path."""
    if model is None:
        return None, None

    text = f"{category_name} {category_path}".replace("\n", " ").strip()
    if not text:
        return None, None

    labels, scores = model.predict(text, k=1)
    if not labels:
        return None, None

    language = labels[0].replace('__label__', '')
    return language, float(scores[0])


def build_direct_category_details(unique_last_categories, direct_category_product_counts, model=None):
    """Build direct category details with path, product count, and language prediction."""
    details = {}
    for category_name, category_path in sorted(unique_last_categories.items()):
        language, language_score = predict_category_language(model, category_name, category_path)
        details[category_name] = {
            'path': category_path,
            'product_count': direct_category_product_counts.get(category_name, 0),
            'language': language,
            'language_score': language_score,
        }
    return details


def save_category_output_files(unique_food_groups, unique_categories, unique_last_categories, direct_category_product_counts):
    """Save all category-related output files."""
    direct_category_details = build_direct_category_details(
        unique_last_categories,
        direct_category_product_counts,
        load_category_language_model(),
    )

    save_unique_food_groups_to_json(unique_food_groups)
    save_unique_categories_to_json(unique_categories)
    save_unique_last_categories_to_json(unique_last_categories)
    save_direct_category_product_counts_to_json(direct_category_product_counts)
    save_direct_category_details_to_json(direct_category_details)


def download_from_huggingface():
    """Download records from the OpenFoodFacts dataset on Hugging Face and optionally store in MongoDB."""
    unique_food_groups = set()
    unique_categories = set()
    unique_last_categories = {}
    direct_category_product_counts = {}

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
                print("Warning: MONGO_URI environment variable not set")
                print("Continuing without MongoDB storage so artifact files can still be generated")
                save_to_mongo = False
            
            # Initialize MongoDB connection
            if save_to_mongo:
                try:
                    print(f"Connecting to MongoDB...")
                    client = MongoClient(mongo_uri)
                    # Test connection
                    client.admin.command('ping')
                    db = client.get_database()  # Use default database from URI or 'test'
                    collection = db['products-catalog']
                    print("Successfully connected to MongoDB")
                except (ConnectionFailure, ConfigurationError) as e:
                    print(f"Warning: Error connecting to MongoDB: {e}")
                    print("Continuing without MongoDB storage so artifact files can still be generated")
                    save_to_mongo = False
                    client = None
                    collection = None
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
        download_limit = get_download_limit()
        download_limit_type = get_download_limit_type()
        if download_limit:
            print(f"Download limit: {download_limit} {download_limit_type}")

        langs_map = {}
        
        unique_food_groups = set()  # Collect unique food group tags
        unique_categories = set()  # Collect unique category tags
        unique_last_categories = {}  # Collect unique last category mapping to full path
        direct_category_product_counts = {}  # Count products by their direct category only
        
        # Process records and optionally store directly in MongoDB
        skipped_count = 0
        processed_count = 0
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
                    last_category = get_direct_category(category_list)
                        
                    if last_category:
                        # Build full path using ">" separator
                        filtered_categories = [cat for cat in category_list if ':' not in cat]
                        full_path = " > ".join(filtered_categories)
                        
                        # Store the mapping
                        unique_last_categories[last_category] = full_path
                        direct_category_product_counts[last_category] = direct_category_product_counts.get(last_category, 0) + 1

            lang = record.get('lang', "None_LANG_ATTRIBUTE")
            langs_map[lang] = langs_map.get(lang, 0) + 1

            if save_to_mongo:
                print(f"Record {i + 1}: {product.get('_id')} - Stored in MongoDB")
            else:
                print(f"Record {i + 1}: {product.get('_id')} - Processed (MongoDB storage disabled)")

            processed_count += 1
            if download_limit and download_limit_type == 'products' and processed_count >= download_limit:
                print(f"Reached product download limit ({download_limit}). Stopping early.")
                break
            if download_limit and download_limit_type == 'categories' and len(unique_last_categories) >= download_limit:
                print(f"Reached category download limit ({download_limit}). Stopping early.")
                break


        print("Language distribution:")
        for lang, count in langs_map.items():
            print(f" - {lang}: {count}")
        
        if save_to_mongo:
            print(f"Successfully processed and stored {processed_count} records in MongoDB")
        else:
            print(f"Successfully processed {processed_count} records (MongoDB storage was disabled)")
        
        if skipped_count > 0:
            print(f"Skipped {skipped_count} invalid products (missing valid name or categories with ':')")

        if download_limit and download_limit_type == 'categories':
            unique_last_categories = limit_mapping_items(unique_last_categories, download_limit)
            direct_category_product_counts = {
                category: direct_category_product_counts[category]
                for category in unique_last_categories
                if category in direct_category_product_counts
            }

        save_category_output_files(
            unique_food_groups,
            unique_categories,
            unique_last_categories,
            direct_category_product_counts,
        )
        
        # Store categories in separate collection if MongoDB is enabled
        if save_to_mongo and collection is not None:
            store_categories_collection(client.get_database(), unique_last_categories)
        
        # Close MongoDB connection if it was opened
        if client:
            client.close()

    except ImportError:
        print("Required packages not installed. Please run: pip install -r requirements.txt")
        save_category_output_files(
            unique_food_groups,
            unique_categories,
            unique_last_categories,
            direct_category_product_counts,
        )
        return []
    except Exception as e:
        print(f"Error downloading from Hugging Face: {e}")
        save_category_output_files(
            unique_food_groups,
            unique_categories,
            unique_last_categories,
            direct_category_product_counts,
        )
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


def save_direct_category_product_counts_to_json(direct_category_product_counts: dict) -> None:
    """Save product counts grouped by direct category to a separate file."""
    filename = "direct_category_product_counts.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(direct_category_product_counts, f, indent=2, ensure_ascii=False, sort_keys=True)
        print(f"Direct category product counts ({len(direct_category_product_counts)} items) saved to '{filename}'")
    except Exception as e:
        print(f"Error saving direct category product counts: {e}")


def save_direct_category_details_to_json(direct_category_details: dict) -> None:
    """Save direct category path, product count, and language details to a separate file."""
    filename = "direct_category_details.json"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(direct_category_details, f, indent=2, ensure_ascii=False, sort_keys=True)
        print(f"Direct category details ({len(direct_category_details)} items) saved to '{filename}'")
    except Exception as e:
        print(f"Error saving direct category details: {e}")


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
