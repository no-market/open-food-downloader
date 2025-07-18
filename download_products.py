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
        
        print("Dataset loaded successfully!")
        # print("Extracting first 5 records...")
        print("Extracting records...")
        langs_map = {}
        
        # records = []
        for i, record in enumerate(dataset):
            # if i >= 5000:
            #     break
            
            lang = record.get('lang', "None_LANG_ATTRIBUTE")
            langs_map[lang] = langs_map.get(lang, 0) + 1

            if (i + 1) % 1000 == 0:
                print(f"Record {i+1}: {lang}")


        print("Language distribution:")
        for lang, count in langs_map.items():
            print(f" - {lang}: {count}")
        
        print(f"Successfully downloaded {i} records")

        # Save the first record to a file
        # if records:
        #     save_first_record(records[0])
        
    except ImportError:
        print("Required packages not installed. Please run: pip install -r requirements.txt")
        return []
    except Exception as e:
        print(f"Error downloading from Hugging Face: {e}")
        return []


# def save_first_record(record: Dict[str, Any]) -> None:
#     """Save the first record to a JSON file."""
#     filename = "first_record.json"
#     try:
#         with open(filename, 'w', encoding='utf-8') as f:
#             json.dump(record, f, indent=2, ensure_ascii=False)
#         print(f"First record saved to '{filename}'")
#     except Exception as e:
#         print(f"Error saving first record: {e}")


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
