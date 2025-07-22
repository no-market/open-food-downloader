#!/usr/bin/env python3
"""
Script to search existing products catalog in MongoDB by text search on search_string field.
Supports both direct search and word-by-word search with special character removal.
Results are stored in output file with input and scores.
"""

import json
import os
import sys
import argparse
import re
from datetime import datetime
from typing import List, Dict, Any


def clean_search_words(input_string: str) -> List[str]:
    """
    Remove special characters from input string and return list of words.
    
    Args:
        input_string: The input search string
        
    Returns:
        List of cleaned words (lowercase, no special chars)
    """
    # Remove special characters, keep only letters, numbers, and spaces
    cleaned = re.sub(r'[^\w\s]', ' ', input_string)
    # Split into words and filter out empty strings
    words = [word.lower().strip() for word in cleaned.split() if word.strip()]
    return words


def search_products_direct(collection, search_string: str) -> List[Dict[str, Any]]:
    """
    Search products using direct text search on the full input string.
    
    Args:
        collection: MongoDB collection object
        search_string: The search string to look for
        
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
        
        # Perform text search with scoring
        results = list(collection.find(
            {"$text": {"$search": search_string}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(50))
        
        return results
    except Exception as e:
        print(f"Error in direct search: {e}")
        return []


def search_products_by_words(collection, search_words: List[str]) -> List[Dict[str, Any]]:
    """
    Search products using individual words from the input string.
    
    Args:
        collection: MongoDB collection object
        search_words: List of individual words to search for
        
    Returns:
        List of matching products with scores
    """
    try:
        if not search_words:
            return []
            
        # Create combined search string for MongoDB text search
        words_query = " ".join(search_words)
        
        # Use MongoDB text search with scoring
        results = list(collection.find(
            {"$text": {"$search": words_query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(50))
        
        return results
    except Exception as e:
        print(f"Error in word-based search: {e}")
        return []


def search_products(search_string: str) -> Dict[str, Any]:
    """
    Main search function that performs both direct and word-based searches.
    
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
        
        # Perform searches
        print(f"Searching for: '{search_string}'")
        
        # 1. Direct search
        print("Performing direct search...")
        direct_results = search_products_direct(collection, search_string)
        
        # 2. Word-based search
        search_words = clean_search_words(search_string)
        print(f"Performing word-based search with words: {search_words}")
        word_results = search_products_by_words(collection, search_words)
        
        # Prepare results
        results = {
            "timestamp": datetime.now().isoformat(),
            "input_string": search_string,
            "search_words": search_words,
            "direct_search": {
                "count": len(direct_results),
                "results": direct_results
            },
            "word_search": {
                "count": len(word_results),
                "results": word_results
            }
        }
        
        # Close MongoDB connection
        client.close()
        
        print(f"Direct search found {len(direct_results)} results")
        print(f"Word-based search found {len(word_results)} results")
        
        return results
        
    except ImportError:
        error_msg = "Required packages not installed. Please run: pip install -r requirements.txt"
        print(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Error during search: {e}"
        print(error_msg)
        return {"error": error_msg}


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
    print(f"- Direct search: {results['direct_search']['count']} results")
    print(f"- Word search: {results['word_search']['count']} results")
    print(f"- Results saved to: {output_file}")
    
    # Print top results
    if results['direct_search']['results']:
        print("\nTop direct search results:")
        for i, result in enumerate(results['direct_search']['results'][:3]):
            score = result.get('score', 0)
            product_id = result.get('_id', 'Unknown')
            search_text = result.get('search_string', '')[:100] + ('...' if len(result.get('search_string', '')) > 100 else '')
            print(f"  {i+1}. Score: {score:.2f} - ID: {product_id}")
            print(f"     Text: {search_text}")
    
    if results['word_search']['results']:
        print("\nTop word-based search results:")
        for i, result in enumerate(results['word_search']['results'][:3]):
            score = result.get('score', 0)
            product_id = result.get('_id', 'Unknown')
            search_text = result.get('search_string', '')[:100] + ('...' if len(result.get('search_string', '')) > 100 else '')
            print(f"  {i+1}. Score: {score:.2f} - ID: {product_id}")
            print(f"     Text: {search_text}")


if __name__ == "__main__":
    main()