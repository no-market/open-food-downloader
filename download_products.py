#!/usr/bin/env python3
"""
Script to extract a specific record from OpenFoodFacts JSONL file
and save it as a formatted JSON file for easier inspection.
"""

import json
import os
import sys

def extract_record(index=0):
    """Extract a specific record from the JSONL file by index (0-based)."""
    
    # Define file paths
    downloads_path = os.path.expanduser("~/Downloads")
    input_file = os.path.join(downloads_path, "openfoodfacts-products.jsonl")
    output_file = f"products_short_{index}.json"
    
    print(f"🔍 Looking for file: {input_file}")
    print(f"📍 Extracting record at index: {index}")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        print("📁 Please make sure 'openfoodfacts-products.jsonl' is in your Downloads folder")
        return False
    
    try:
        print(f"📖 Reading from: {input_file}")
        
        record_count = 0
        with open(input_file, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                try:
                    # Parse JSON from line
                    record = json.loads(line)
                    
                    # Check if this is the record we want
                    if record_count == index:
                        # Save the record
                        with open(output_file, 'w', encoding='utf-8') as out_file:
                            json.dump(record, out_file, indent=2, ensure_ascii=False)
                        
                        print(f"✅ Successfully extracted record {index} (line {line_num})")
                        print(f"💾 Saved to: {output_file}")
                        
                        # Print some info about the record
                        print(f"📊 Record contains {len(record)} fields")
                        if 'product_name' in record:
                            print(f"🏷️  Product name: {record.get('product_name', 'N/A')}")
                        if 'code' in record:
                            print(f"🔢 Product code: {record.get('code', 'N/A')}")
                        
                        return True
                    
                    record_count += 1
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️  Skipping invalid JSON on line {line_num}: {e}")
                    continue
        
        print(f"❌ Record at index {index} not found. File contains {record_count} valid records.")
        return False
        
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

if __name__ == "__main__":
    print("🍕 OpenFoodFacts Product Extractor")
    print("=" * 40)
    
    # Get index from command line argument or default to 0
    index = 0
    if len(sys.argv) > 1:
        try:
            index = int(sys.argv[1])
            if index < 0:
                print("❌ Index must be 0 or greater")
                sys.exit(1)
        except ValueError:
            print("❌ Index must be a valid integer")
            print("📝 Usage: python3 extract_product.py [index]")
            print("📝 Example: python3 extract_product.py 5")
            sys.exit(1)
    
    success = extract_record(index)
    
    if success:
        print(f"\n🎉 Done! You can now inspect 'products_short_{index}.json'")
    else:
        print("\n💥 Failed to extract record")
