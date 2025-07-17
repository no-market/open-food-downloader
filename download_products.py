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
        
        print("Downloading dataset from Hugging Face...")
        print("Dataset: openfoodfacts/product-database")
        
        # Load dataset in streaming mode for efficiency
        dataset = load_dataset('openfoodfacts/product-database', split='train', streaming=True)
        
        print("Dataset loaded successfully!")
        print("Extracting first 5 records...")
        
        records = []
        for i, record in enumerate(dataset):
            if i >= 5:
                break
            records.append(record)
            print(f"Record {i+1}: {len(record)} fields")
        
        print(f"Successfully downloaded {len(records)} records")
        return records
        
    except ImportError:
        print("Required packages not installed. Please run: pip install -r requirements.txt")
        return []
    except Exception as e:
        print(f"Error downloading from Hugging Face: {e}")
        return []


def print_records(records: List[Dict[str, Any]]) -> None:
    """Print records to console as raw data."""
    if not records:
        print("No records to display")
        return
    
    for i, record in enumerate(records, 1):
        print(f"RECORD {i}:")
        print(json.dumps(record, indent=2, ensure_ascii=False))
        print()


def main():
    """Main function to download and display food records."""
    print("OpenFoodFacts Product Downloader")
    print("Downloading first 5 food records from dataset")
    print("Source: https://huggingface.co/datasets/openfoodfacts/product-database")
    print()
    
    # Try to download from Hugging Face
    records = download_from_huggingface()
    
    # Print the records to console
    print_records(records)
    
    print(f"Processing complete! Displayed {len(records)} food product records")


if __name__ == "__main__":
    main()
