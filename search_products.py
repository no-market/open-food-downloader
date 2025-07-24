#!/usr/bin/env python3
"""
Script to search existing products catalog in MongoDB by text search on search_string field.
Performs direct search with improved input string formatting:
- Splits camelCase format words
- Splits numbers from letters  
- Removes commas and semicolons
- Converts to lowercase
- Keeps spaces as separators
Results are stored in output file with input and scores.
"""

import json
import os
import sys
import argparse
import re
from datetime import datetime
from typing import Dict, Any, List


def format_search_string(input_string: str) -> str:
    """
    Format search string according to requirements:
    - Split camelCase format words  
    - Split numbers from letters
    - Remove "," and ";"
    - Convert to lowercase
    - Keep space " " as separator
    
    Args:
        input_string: The input search string
        
    Returns:
        Formatted search string
    """
    if not input_string:
        return ""
    
    # Step 1: Replace commas and semicolons with spaces first
    formatted = re.sub(r'[,;]', ' ', input_string)
    
    # Step 2: Split camelCase - handle both regular camelCase and consecutive uppercase letters
    # Split on lowercase letter followed by uppercase letter
    formatted = re.sub(r'([a-ząćęłńóśźż])([A-ZĄĆĘŁŃÓŚŹŻ])', r'\1 \2', formatted)
    # Split consecutive uppercase letters when followed by lowercase letter (e.g., XMLHttp -> XML Http)
    formatted = re.sub(r'([A-ZĄĆĘŁŃÓŚŹŻ])([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż])', r'\1 \2', formatted)
    
    # Step 3: Split numbers from letters - insert space between letters and numbers
    # Insert space before numbers that follow letters (including Unicode letters)
    formatted = re.sub(r'([a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ])(\d)', r'\1 \2', formatted)
    # Insert space after numbers that are followed by letters  
    formatted = re.sub(r'(\d)([a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ])', r'\1 \2', formatted)
    
    # Step 4: Convert to lowercase
    formatted = formatted.lower()
    
    # Step 5: Normalize spaces - replace multiple spaces with single space and strip
    formatted = re.sub(r'\s+', ' ', formatted).strip()
    
    return formatted


def search_products_direct(collection, search_string: str, formatted_string: str) -> List[Dict[str, Any]]:
    """
    Search products using direct text search on the formatted input string.
    
    Args:
        collection: MongoDB collection object
        search_string: The original search string
        formatted_string: The formatted search string to use for search
        
    Returns:
        List of matching products with scores
    """
    try:
        # Use MongoDB text search with scoring
        # Create text index if it doesn't exist (MongoDB will ignore if exists)
        try:
            collection.create_index([("search_string", "text")])
        except Exception:
            pass  # Index might already exist
        
        # Perform text search with scoring using the formatted string
        results = list(collection.find(
            {"$text": {"$search": formatted_string}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(50))
        
        return results
    except Exception as e:
        print(f"Error in direct search: {e}")
        return []



def search_products(search_string: str) -> Dict[str, Any]:
    """
    Main search function that performs only direct search with formatted input.
    
    Args:
        search_string: The input search string
        
    Returns:
        Dictionary containing search results and metadata
    """
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ConfigurationError
        
        # Get MongoDB URI from environment variable
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            print("Error: MONGO_URI environment variable not set")
            print("Please set the MongoDB connection URI in the MONGO_URI environment variable")
            return {"error": "MONGO_URI not set"}
        
        # Initialize MongoDB connection
        try:
            print(f"Connecting to MongoDB...")
            client = MongoClient(mongo_uri)
            # Test connection
            client.admin.command('ping')
            db = client.get_database()  # Use default database from URI
            collection = db['products-catalog']
            print("Successfully connected to MongoDB")
        except (ConnectionFailure, ConfigurationError) as e:
            print(f"Error connecting to MongoDB: {e}")
            return {"error": f"MongoDB connection failed: {e}"}
        
        # Format the search string
        formatted_string = format_search_string(search_string)
        print(f"Original input: '{search_string}'")
        print(f"Formatted input: '{formatted_string}'")
        
        # Perform direct search with formatted string
        print("Performing direct search with formatted input...")
        direct_results = search_products_direct(collection, search_string, formatted_string)
        
        # Prepare results
        results = {
            "timestamp": datetime.now().isoformat(),
            "input_string": search_string,
            "formatted_string": formatted_string,
            "direct_search": {
                "count": len(direct_results),
                "results": direct_results
            }
        }
        
        # Close MongoDB connection
        client.close()
        
        print(f"Direct search found {len(direct_results)} results")
        
        return results
        
    except ImportError:
        error_msg = "Required packages not installed. Please run: pip install -r requirements.txt"
        print(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Error during search: {e}"
        print(error_msg)
        return {"error": error_msg}


def extract_unique_product_names(product_name_data) -> List[str]:
    """
    Extract unique product names from product_name array.
    
    Args:
        product_name_data: The product_name field from MongoDB document
        
    Returns:
        List of unique product names
    """
    unique_product_names = []
    if isinstance(product_name_data, list):
        seen_texts = set()
        for name_obj in product_name_data:
            if isinstance(name_obj, dict) and 'text' in name_obj:
                text = name_obj['text']
                if text and text not in seen_texts:
                    unique_product_names.append(text)
                    seen_texts.add(text)
    return unique_product_names


def save_results(results: Dict[str, Any], output_file: str = None) -> str:
    """
    Save search results to a JSON file.
    
    Args:
        results: Search results dictionary
        output_file: Optional output filename
        
    Returns:
        The filename where results were saved
    """
    if not output_file:
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_input = re.sub(r'[^\w\s-]', '', results.get('input_string', 'search')).strip()
        safe_input = re.sub(r'[-\s]+', '_', safe_input)[:30]  # Limit length
        output_file = f"search_results_{safe_input}_{timestamp}.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Results saved to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error saving results: {e}")
        return ""


def main():
    """Main function to handle command line arguments and execute search."""
    parser = argparse.ArgumentParser(description='Search products catalog by text search on search_string field')
    parser.add_argument('search_string', help='Text to search for in product catalog')
    parser.add_argument('-o', '--output', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    if not args.search_string.strip():
        print("Error: Search string cannot be empty")
        sys.exit(1)
    
    print("Product Catalog Search Tool")
    print("=" * 40)
    print(f"Search string: {args.search_string}")
    print()
    
    # Perform search
    results = search_products(args.search_string)
    
    # Check for errors
    if "error" in results:
        print(f"Search failed: {results['error']}")
        sys.exit(1)
    
    # Save results
    output_file = save_results(results, args.output)
    
    # Print summary
    print("\nSearch Summary:")
    print(f"- Formatted input: '{results['formatted_string']}'")
    print(f"- Direct search: {results['direct_search']['count']} results")
    print(f"- Results saved to: {output_file}")
    
    # Print top 10 direct search results
    if results['direct_search']['results']:
        print("\nTop 10 direct search results:")
        for i, result in enumerate(results['direct_search']['results'][:10]):
            score = result.get('score', 0)
            product_id = result.get('_id', 'Unknown')
            
            # Extract unique product names
            unique_product_names = extract_unique_product_names(result.get('product_name', []))
            
            # Get other requested fields
            quantity = result.get('quantity', '')
            brands = result.get('brands', '')
            categories = result.get('categories', [])
            labels = result.get('labels', [])
            
            print(f"  {i+1}. Score: {score:.2f} - ID: {product_id}")
            print(f"     Product Names: {', '.join(unique_product_names) if unique_product_names else 'N/A'}")
            print(f"     Quantity: {quantity if quantity else 'N/A'}")
            print(f"     Brands: {brands if brands else 'N/A'}")
            print(f"     Categories: {', '.join(categories) if categories else 'N/A'}")
            print(f"     Labels: {', '.join(labels) if labels else 'N/A'}")
            print(f"     Text: {result.get('search_string', '')}")
            print()


if __name__ == "__main__":
    main()