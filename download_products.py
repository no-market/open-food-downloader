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
        dataset = load_dataset('openfoodfacts/product-database', split='food', streaming=True)
        
        print("Dataset loaded successfully!")
        print("Extracting first 5 records...")
        
        records = []
        for i, record in enumerate(dataset):
            if i >= 5:
                break
            records.append(record)
            print(f"Record {i+1}: {len(record)} fields")
        
        print(f"Successfully downloaded {len(records)} records")
        
        # Save the first record to a file
        if records:
            save_first_record(records[0])
        
        return records
        
    except ImportError:
        print("Required packages not installed. Please run: pip install -r requirements.txt")
        return []
    except Exception as e:
        print(f"Error downloading from Hugging Face: {e}")
        return []


def save_first_record(record: Dict[str, Any]) -> None:
    """Save the first record to a JSON file."""
    filename = "first_record.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        print(f"First record saved to '{filename}'")
    except Exception as e:
        print(f"Error saving first record: {e}")


def print_records(records: List[Dict[str, Any]]) -> None:
    """Print records to console in {index}: {code} format."""
    if not records:
        print("No records to display")
        return
    
    for i, record in enumerate(records):
        code = record.get('code', 'unknown')
        print(f"{i}: {code}")


def load_fallback_data() -> List[Dict[str, Any]]:
    """Load fallback data from first_record.json if available."""
    try:
        with open('first_record.json', 'r', encoding='utf-8') as f:
            record = json.load(f)
        print("Using fallback data from first_record.json")
        return [record]
    except Exception as e:
        print(f"Error loading fallback data: {e}")
        return []


def main():
    """Main function to download and display food records."""
    print("OpenFoodFacts Product Downloader")
    print("Downloading first 5 food records from dataset")
    print("Source: https://huggingface.co/datasets/openfoodfacts/product-database")
    print()
    
    # Try to download from Hugging Face
    records = download_from_huggingface()
    
    # If no records downloaded, try fallback data
    if not records:
        records = load_fallback_data()
    
    # Print the records to console
    print_records(records)
    
    print(f"Processing complete! Displayed {len(records)} food product records")
    


if __name__ == "__main__":
    main()
