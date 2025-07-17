#!/usr/bin/env python3
"""
Script to download and extract food records from OpenFoodFacts dataset.
Downloads first 5 records from the Hugging Face dataset and prints them to console.
"""

import json
import sys
import signal
import gc
from typing import List, Dict, Any



def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    print("Received termination signal. Exiting gracefully...")
    sys.exit(0)


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
            # Limit record size to prevent memory issues
            limited_record = {k: v for k, v in list(record.items())[:50]}  # Limit to first 50 fields
            records.append(limited_record)
            print(f"Record {i+1}: {len(limited_record)} fields")
            
            # Force garbage collection to free memory
            if i % 2 == 0:
                gc.collect()
        
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
        # Always return gracefully to avoid core dumps
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
    # Set up signal handlers to prevent core dumps
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("OpenFoodFacts Product Downloader")
        print("Downloading first 5 food records from dataset")
        print("Source: https://huggingface.co/datasets/openfoodfacts/product-database")
        print()
        
        # Try to download from Hugging Face
        records = download_from_huggingface()
        
        # Print the records to console
        print_records(records)
        
        print(f"Processing complete! Displayed {len(records)} food product records")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Script completed with errors but exiting gracefully.")
    except KeyboardInterrupt:
        print("Script interrupted by user.")
    finally:
        # Ensure we always exit cleanly
        sys.exit(0)
    


if __name__ == "__main__":
    main()
