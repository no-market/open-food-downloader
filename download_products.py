#!/usr/bin/env python3
"""
Script to download and extract food records from OpenFoodFacts dataset.
Downloads records from the Hugging Face dataset and stores them in MongoDB.
"""

import json
import os
import sys
from dataclasses import dataclass
from typing import Optional


POLISH_LANGUAGE_LABEL = 'pol_Latn'
CATEGORY_LANGUAGE_MODEL_REPO = 'facebook/fasttext-language-identification'
CATEGORY_LANGUAGE_MODEL_FILE = 'model.bin'


class CategoryLanguageError(RuntimeError):
    """Raised when category language cannot be determined reliably."""


@dataclass(frozen=True)
class ProductAssessment:
    eligible: bool
    reason: Optional[str]
    direct_category: Optional[str] = None
    detected_category_language: Optional[str] = None
    detected_category_language_score: Optional[float] = None
    product_name_for_language_detection: Optional[str] = None
    detected_product_name_language: Optional[str] = None
    detected_product_name_language_score: Optional[float] = None


def _parse_categories(record):
    categories = record.get('categories', '')
    if not isinstance(categories, str):
        return []
    return [category.strip() for category in categories.split(',') if category.strip()]


def _get_basic_rejection_reason(record):
    product_names = record.get('product_name', [])
    has_valid_name = isinstance(product_names, list) and any(
        isinstance(name, dict)
        and isinstance(name.get('text'), str)
        and name['text'].strip()
        for name in product_names
    )
    if not has_valid_name:
        return 'missing_product_name'

    category_list = _parse_categories(record)
    has_valid_category = any(
        ':' not in category
        or (category.lower().startswith('pl:') and bool(category[3:]))
        for category in category_list
    )
    if not has_valid_category:
        return 'missing_valid_category'

    return None


def is_valid_product(record):
    """Return whether a product has a usable name and category."""
    return _get_basic_rejection_reason(record) is None


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


def get_preferred_product_name(product_names):
    """Return the `pl` name, then `main`, then the first non-empty name."""
    if not isinstance(product_names, list):
        return None

    valid_names = [
        name
        for name in product_names
        if isinstance(name, dict)
        and isinstance(name.get('text'), str)
        and name['text'].strip()
    ]
    for preferred_language in ('pl', 'main'):
        for name in valid_names:
            if name.get('lang') == preferred_language:
                return name['text'].strip()

    if valid_names:
        return valid_names[0]['text'].strip()
    return None


class ProductEligibilityFilter:
    """Accept products with a Polish direct category or preferred product name."""

    def __init__(self, language_model):
        self._language_model = language_model
        self._language_prediction_by_text = {}

    def _predict_language(self, text, field_name):
        prediction = self._language_prediction_by_text.get(text)
        if prediction is not None:
            return prediction

        try:
            labels, scores = self._language_model.predict(text, k=1)
            if not labels or not scores:
                raise ValueError('language model returned no prediction')
            prediction = (
                labels[0].replace('__label__', ''),
                float(scores[0]),
            )
        except Exception as exc:
            raise CategoryLanguageError(
                f"Could not determine language for {field_name} '{text}'"
            ) from exc

        self._language_prediction_by_text[text] = prediction
        return prediction

    def assess(self, record):
        rejection_reason = _get_basic_rejection_reason(record)
        if rejection_reason:
            return ProductAssessment(False, rejection_reason)

        if record.get('lang') != 'pl':
            return ProductAssessment(False, 'non_polish_record_language')

        category_list = _parse_categories(record)
        direct_category = get_direct_category(category_list)
        if direct_category is None:
            return ProductAssessment(False, 'missing_direct_category')

        product_name = get_preferred_product_name(record.get('product_name', []))
        category_language, category_language_score = self._predict_language(
            direct_category,
            'direct category',
        )
        product_name_language, product_name_language_score = self._predict_language(
            product_name,
            'product name',
        )
        eligible = (
            category_language == POLISH_LANGUAGE_LABEL
            or product_name_language == POLISH_LANGUAGE_LABEL
        )

        return ProductAssessment(
            eligible=eligible,
            reason=None if eligible else 'non_polish_direct_category',
            direct_category=direct_category,
            detected_category_language=category_language,
            detected_category_language_score=category_language_score,
            product_name_for_language_detection=product_name,
            detected_product_name_language=product_name_language,
            detected_product_name_language_score=product_name_language_score,
        )


def write_rejected_product_jsonl(stream, record, assessment):
    """Write one rejected-product diagnostic as a JSON Lines record."""
    rejection = {
        'code': record.get('code'),
        'reason': assessment.reason,
        'record_language': record.get('lang'),
        'product_name': record.get('product_name'),
        'direct_category': assessment.direct_category,
        'detected_category_language': assessment.detected_category_language,
        'detected_category_language_score': assessment.detected_category_language_score,
        'product_name_for_language_detection': assessment.product_name_for_language_detection,
        'detected_product_name_language': assessment.detected_product_name_language,
        'detected_product_name_language_score': assessment.detected_product_name_language_score,
        'categories': _parse_categories(record),
    }
    json.dump(rejection, stream, ensure_ascii=False)
    stream.write('\n')


def write_eligible_product_jsonl(stream, product):
    """Write one filtered product document as a JSON Lines record."""
    json.dump(product, stream, ensure_ascii=False)
    stream.write('\n')


def get_rejection_output_group(reason):
    """Separate language rejections from all other rejection reasons."""
    if reason == 'non_polish_direct_category':
        return 'non_polish_direct_category'
    return 'other'


def load_category_language_model():
    """Load the fastText language model used for direct-category filtering."""
    try:
        import fasttext
        from huggingface_hub import hf_hub_download

        print(
            "Loading category language model from "
            f"{CATEGORY_LANGUAGE_MODEL_REPO}/{CATEGORY_LANGUAGE_MODEL_FILE}..."
        )
        model_path = hf_hub_download(
            repo_id=CATEGORY_LANGUAGE_MODEL_REPO,
            filename=CATEGORY_LANGUAGE_MODEL_FILE,
        )
        return fasttext.load_model(model_path)
    except Exception as exc:
        raise CategoryLanguageError(
            "Could not load category language model from "
            f"{CATEGORY_LANGUAGE_MODEL_REPO}/{CATEGORY_LANGUAGE_MODEL_FILE}"
        ) from exc


def download_from_huggingface():
    """Download records from the OpenFoodFacts dataset on Hugging Face and optionally store in MongoDB."""
    client = None
    eligible_products_file = None
    rejected_products_files = {}
    try:
        from datasets import load_dataset
        
        # Check if we should save to MongoDB (default: true)
        save_to_mongo = os.getenv('SAVE_TO_MONGO', 'true').lower() in ('true', '1', 'yes', 'on')
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

        product_filter = ProductEligibilityFilter(load_category_language_model())
        eligible_products_file = open('eligible_products.jsonl', 'w', encoding='utf-8')
        rejected_products_files['non_polish_direct_category'] = open(
            'non_polish_direct_category_rejections.jsonl',
            'w',
            encoding='utf-8',
        )
        rejected_products_files['other'] = open(
            'other_rejections.jsonl',
            'w',
            encoding='utf-8',
        )
        
        print("Dataset loaded successfully!")
        if save_to_mongo:
            print("Extracting and storing records in MongoDB...")
        else:
            print("Extracting records (MongoDB storage disabled)...")
        langs_map = {}
        
        unique_food_groups = set()  # Collect unique food group tags
        unique_categories = set()  # Collect unique category tags
        unique_last_categories = {}  # Collect unique last category mapping to full path
        direct_category_product_counts = {}  # Count products by their direct category only
        
        # Process records and optionally store directly in MongoDB
        rejected_counts = {
            'non_polish_direct_category': 0,
            'other': 0,
        }
        processed_count = 0
        for i, record in enumerate(dataset):
            # if i >= 5:
            #     break
            
            assessment = product_filter.assess(record)
            if not assessment.eligible:
                rejection_group = get_rejection_output_group(assessment.reason)
                rejected_counts[rejection_group] += 1
                write_rejected_product_jsonl(
                    rejected_products_files[rejection_group],
                    record,
                    assessment,
                )
                if sum(rejected_counts.values()) <= 10:
                    print(
                        f"Rejected product {record.get('code', 'unknown')}: "
                        f"{assessment.reason}"
                    )
                continue

            processed_count += 1
            category_list = _parse_categories(record)
            
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
                'categories': category_list,
                'direct_category': assessment.direct_category,
                'detected_category_language': assessment.detected_category_language,
                'detected_category_language_score': assessment.detected_category_language_score,
                'product_name_for_language_detection': assessment.product_name_for_language_detection,
                'detected_product_name_language': assessment.detected_product_name_language,
                'detected_product_name_language_score': assessment.detected_product_name_language_score,
                'labels_tags': record.get('labels_tags'),
                'labels': [l.strip() for l in record.get('labels', '').split(',') if record.get('labels')] if record.get('labels') else [],
                'popularity_key': record.get('popularity_key'),
                'popularity_tags': record.get('popularity_tags'),
                'nutriscore_grade': record.get('nutriscore_grade'),
                'nutriscore_score': record.get('nutriscore_score'),
                'search_string': search_string,
            }

            # Preserve every product that passed eligibility filtering, even when
            # optional MongoDB storage is disabled or an upsert later fails.
            write_eligible_product_jsonl(eligible_products_file, product)
            
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
            if category_list:
                # Add each category to the unique set
                unique_categories.update(category_list)
                
                # Build mapping from last category to full path, skipping categories with ":"
                if category_list:
                    last_category = assessment.direct_category
                        
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
            

        print("Language distribution:")
        for lang, count in langs_map.items():
            print(f" - {lang}: {count}")
        
        if save_to_mongo:
            print(f"Successfully processed and stored {processed_count} records in MongoDB")
        else:
            print(f"Successfully processed {processed_count} records (MongoDB storage was disabled)")
        
        rejected_count = sum(rejected_counts.values())
        if rejected_count > 0:
            print(
                f"Rejected {rejected_count} products: "
                f"{rejected_counts['non_polish_direct_category']} language rejections "
                "saved to 'non_polish_direct_category_rejections.jsonl', and "
                f"{rejected_counts['other']} other rejections saved to "
                "'other_rejections.jsonl'"
            )

        save_unique_food_groups_to_json(unique_food_groups)
        save_unique_categories_to_json(unique_categories)
        save_unique_last_categories_to_json(unique_last_categories)
        save_direct_category_product_counts_to_json(direct_category_product_counts)
        
        # Store categories in separate collection if MongoDB is enabled
        if save_to_mongo and collection is not None:
            store_categories_collection(client.get_database(), unique_last_categories)
        
    except ImportError:
        print("Required packages not installed. Please run: pip install -r requirements.txt")
        return []
    except CategoryLanguageError:
        raise
    except Exception as e:
        print(f"Error downloading from Hugging Face: {e}")
        return []
    finally:
        if eligible_products_file:
            eligible_products_file.close()
        for rejected_products_file in rejected_products_files.values():
            rejected_products_file.close()
        if client:
            client.close()




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
