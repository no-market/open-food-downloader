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

from utils import format_search_string, compute_rapidfuzz_score, extract_product_names, compute_given_name



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


def apply_rapidfuzz_scoring(search_string: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply RapidFuzz scoring to search results and sort by RapidFuzz score.
    
    Args:
        search_string: The original search string
        results: List of MongoDB search results
        
    Returns:
        List of results with RapidFuzz scores, sorted by RapidFuzz score descending
    """
    if not results:
        return results
    
    # Add RapidFuzz scores to each result
    for result in results:
        rapidfuzz_score = compute_rapidfuzz_score(search_string, result)
        result['rapidfuzz_score'] = rapidfuzz_score
    
    # Sort by RapidFuzz score in descending order
    results.sort(key=lambda x: x.get('rapidfuzz_score', 0), reverse=True)
    
    return results



def search_products(search_string: str) -> Dict[str, Any]:
    """
    Main search function that performs MongoDB searches.
    
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
        
        # Initialize OpenAI assistant (singleton pattern)
        from openai_assistant import OpenAIAssistant, SCORE_THRESHOLD
        assistant = OpenAIAssistant()
        
        # Initialize variables for the search loop
        current_search_string = search_string
        current_formatted_string = formatted_string
        level1_result = None
        level2_result = None
        iteration = 0
        max_iterations = 3  # Prevent infinite loops
        
        # Search loop: try original string, then Level 1 rephrased, then Level 2 rephrased
        while iteration < max_iterations:
            iteration += 1
            print(f"\n=== Search Iteration {iteration} ===")
            print(f"Search string: '{current_search_string}'")
            print(f"Formatted string: '{current_formatted_string}'")
            
            # Perform direct search with current formatted string
            print("Performing MongoDB search...")
            direct_results = search_products_direct(collection, current_search_string, current_formatted_string)
            
            # Add given_name field to direct results
            for result in direct_results:
                result['given_name'] = compute_given_name(result)
            
            # Apply RapidFuzz scoring to the results
            print("Computing RapidFuzz scores...")
            direct_results_with_rapidfuzz = apply_rapidfuzz_scoring(current_search_string, direct_results.copy())
            
            # Add given_name field to rapidfuzz results 
            for result in direct_results_with_rapidfuzz:
                result['given_name'] = compute_given_name(result)
            
            # Check if we have good results
            if direct_results_with_rapidfuzz:
                best_score = direct_results_with_rapidfuzz[0].get('rapidfuzz_score', 0)
                print(f"Best RapidFuzz score: {best_score:.1f}")
                
                # If score is good enough, we're done
                if best_score >= SCORE_THRESHOLD:
                    print(f"Score {best_score:.1f} is above threshold {SCORE_THRESHOLD}, search successful!")
                    break
                
                # If we have results but score is low, try AI assistance
                print(f"Score {best_score:.1f} is below threshold {SCORE_THRESHOLD}")
                
                # Get top result name for AI context
                top_result_name = direct_results_with_rapidfuzz[0].get('given_name') if direct_results_with_rapidfuzz else None
                
                # Try Level 1 model on first iteration
                if iteration == 1:
                    print("Using Level 1 model for query analysis...")
                    level1_result = assistant.process_with_level1(current_search_string, top_result_name)
                    
                    if level1_result.decision == "rephrased_successfully" and level1_result.rephrased_query:
                        print(f"Level 1 model suggested: '{level1_result.rephrased_query}'")
                        current_search_string = level1_result.rephrased_query
                        current_formatted_string = format_search_string(current_search_string)
                        continue  # Try search again with rephrased query
                    elif level1_result.decision == "not_a_product":
                        print("Level 1 model determined this is not a food product")
                        break
                    elif level1_result.decision == "valid_product":
                        print("Level 1 model confirmed this is a valid food product")
                        break
                    else:
                        print("Level 1 model could not improve the query, trying Level 2 model...")
                        # Immediately try Level 2 model without another MongoDB query
                        print("Using Level 2 model for advanced analysis...")
                        level2_result = assistant.process_with_level2(current_search_string, top_result_name, level1_result)
                        
                        if level2_result.decision == "rephrased_successfully" and level2_result.rephrased_query:
                            print(f"Level 2 model suggested: '{level2_result.rephrased_query}'")
                            current_search_string = level2_result.rephrased_query
                            current_formatted_string = format_search_string(current_search_string)
                            continue  # Try search again with rephrased query
                        elif level2_result.decision == "not_a_product":
                            print("Level 2 model determined this is not a food product")
                            break
                        else:
                            print("Level 2 model could not improve the query further")
                            break
                
                # Try Level 2 model on second iteration (if Level 1 wasn't called in first iteration)
                elif iteration == 2 and not level1_result:
                    print("Using Level 2 model for advanced analysis...")
                    level2_result = assistant.process_with_level2(current_search_string, top_result_name, level1_result)
                    
                    if level2_result.decision == "rephrased_successfully" and level2_result.rephrased_query:
                        print(f"Level 2 model suggested: '{level2_result.rephrased_query}'")
                        current_search_string = level2_result.rephrased_query
                        current_formatted_string = format_search_string(current_search_string)
                        continue  # Try search again with rephrased query
                    elif level2_result.decision == "not_a_product":
                        print("Level 2 model determined this is not a food product")
                        break
                    else:
                        print("Level 2 model could not improve the query further")
                        break
                else:
                    # No more AI assistance available
                    print("No further AI assistance available")
                    break
            else:
                # No results found at all
                print("No results found")
                if iteration == 1:
                    # Try Level 1 model even without results
                    print("Trying Level 1 model without search results...")
                    level1_result = assistant.process_with_level1(current_search_string, None)
                    
                    if level1_result.decision == "rephrased_successfully" and level1_result.rephrased_query:
                        current_search_string = level1_result.rephrased_query
                        current_formatted_string = format_search_string(current_search_string)
                        continue
                    elif level1_result.decision in ["not_a_product", "valid_product"]:
                        # Stop processing if Level 1 model has made a definitive decision
                        break
                break
        
        # Use the final results from the last iteration
        final_direct_results = direct_results if 'direct_results' in locals() else []
        final_rapidfuzz_results = direct_results_with_rapidfuzz if 'direct_results_with_rapidfuzz' in locals() else []
        
        # Prepare results
        results = {
            "timestamp": datetime.now().isoformat(),
            "input_string": search_string,
            "formatted_string": formatted_string,
            "direct_search": {
                "count": len(final_direct_results),
                "results": final_direct_results
            },
            "rapidfuzz_search": {
                "count": len(final_rapidfuzz_results),
                "results": final_rapidfuzz_results
            }
        }
        
        # Add OpenAI results if available
        if level1_result:
            results["openai_level1"] = {
                "model": level1_result.model,
                "decision": level1_result.decision,
                "rephrased_query": level1_result.rephrased_query,
                "error": level1_result.error
            }
        
        if level2_result:
            results["openai_level2"] = {
                "model": level2_result.model,
                "decision": level2_result.decision,
                "rephrased_query": level2_result.rephrased_query,
                "error": level2_result.error
            }
        
        # Close MongoDB connection
        client.close()
        
        # Export OpenAI conversations if AI was used
        if level1_result or level2_result:
            print("Exporting OpenAI conversation histories...")
            conversation_files = assistant.export_conversations()
            if conversation_files:
                print(f"Conversation files exported: {list(conversation_files.values())}")
        
        print(f"Direct search found {len(final_direct_results)} results")
        print(f"RapidFuzz scoring applied to {len(final_rapidfuzz_results)} results")
        
        # Log OpenAI results
        if level1_result:
            print(f"Level 1 model decision: {level1_result.decision}")
            if level1_result.rephrased_query:
                print(f"Level 1 model suggested query: '{level1_result.rephrased_query}'")
        
        if level2_result:
            print(f"Level 2 model decision: {level2_result.decision}")
            if level2_result.rephrased_query:
                print(f"Level 2 model suggested query: '{level2_result.rephrased_query}'")
        
        # Add match status to results for programmatic access
        if final_rapidfuzz_results:
            best_result = final_rapidfuzz_results[0]
            best_score = best_result.get('rapidfuzz_score', 0)
            
            if best_score >= SCORE_THRESHOLD:
                results["match_status"] = "successful"
                results["match_confidence"] = "high"
                results["best_match"] = {
                    "score": best_score,
                    "threshold": SCORE_THRESHOLD,
                    "product": best_result
                }
            else:
                results["match_status"] = "low_confidence"
                results["match_confidence"] = "low"
                results["best_match"] = {
                    "score": best_score,
                    "threshold": SCORE_THRESHOLD,
                    "product": best_result
                }
        else:
            results["match_status"] = "no_match"
            results["match_confidence"] = "none"
            results["best_match"] = None
        
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
    print(f"- Formatted input: '{results['formatted_string']}'")
    print(f"- Direct search: {results['direct_search']['count']} results")
    print(f"- RapidFuzz search: {results['rapidfuzz_search']['count']} results")
    
    # Print OpenAI summary
    if 'openai_level1' in results:
        level1 = results['openai_level1']
        print(f"- Level 1 model decision: {level1['decision']}")
        if level1.get('rephrased_query'):
            print(f"  Suggested query: '{level1['rephrased_query']}'")
    
    if 'openai_level2' in results:
        level2 = results['openai_level2']
        print(f"- Level 2 model decision: {level2['decision']}")
        if level2.get('rephrased_query'):
            print(f"  Suggested query: '{level2['rephrased_query']}'")
    
    print(f"- Results saved to: {output_file}")
    
    # Print top 3 direct search results
    if results['direct_search']['results']:
        print("\nTop 3 direct search results (MongoDB scoring):")
        for i, result in enumerate(results['direct_search']['results'][:3]):
            score = result.get('score', 0)
            product_id = result.get('_id', 'Unknown')
            
            # Extract unique product names
            unique_product_names = extract_product_names(result.get('product_name', []))
            
            # Get other requested fields
            quantity = result.get('quantity', '')
            brands = result.get('brands', '')
            categories = result.get('categories', [])
            labels = result.get('labels', [])
            
            print(f"  {i+1}. MongoDB Score: {score:.2f} - ID: {product_id}")
            print(f"     Given Name: {result.get('given_name', 'N/A')}")
            print(f"     Product Names: {', '.join(unique_product_names) if unique_product_names else 'N/A'}")
            print(f"     Quantity: {quantity if quantity else 'N/A'}")
            print(f"     Brands: {brands if brands else 'N/A'}")
            print(f"     Categories: {', '.join(categories) if categories else 'N/A'}")
            print(f"     Labels: {', '.join(labels) if labels else 'N/A'}")
            print(f"     Text: {result.get('search_string', '')}")
            print()
    
    # Print top 3 RapidFuzz results
    if results['rapidfuzz_search']['results']:
        print("\nTop 3 RapidFuzz search results (Custom relevance scoring):")
        for i, result in enumerate(results['rapidfuzz_search']['results'][:3]):
            mongo_score = result.get('score', 0)
            rapidfuzz_score = result.get('rapidfuzz_score', 0)
            product_id = result.get('_id', 'Unknown')
            
            # Extract unique product names
            unique_product_names = extract_product_names(result.get('product_name', []))
            
            # Get other requested fields
            quantity = result.get('quantity', '')
            brands = result.get('brands', '')
            categories = result.get('categories', [])
            labels = result.get('labels', [])
            
            print(f"  {i+1}. RapidFuzz Score: {rapidfuzz_score:.2f} (MongoDB: {mongo_score:.2f}) - ID: {product_id}")
            print(f"     Given Name: {result.get('given_name', 'N/A')}")
            print(f"     Product Names: {', '.join(unique_product_names) if unique_product_names else 'N/A'}")
            print(f"     Quantity: {quantity if quantity else 'N/A'}")
            print(f"     Brands: {brands if brands else 'N/A'}")
            print(f"     Categories: {', '.join(categories) if categories else 'N/A'}")
            print(f"     Labels: {', '.join(labels) if labels else 'N/A'}")
            print(f"     Text: {result.get('search_string', '')}")
            print()
    
    # Print final search result summary
    print("=" * 60)
    print("SEARCH RESULT SUMMARY")
    print("=" * 60)
    
    # Get match status from results
    match_status = results.get('match_status', 'unknown')
    best_match = results.get('best_match')
    
    if match_status == "successful":
        print("✅ SUCCESSFUL MATCH FOUND")
        if best_match:
            print(f"Score: {best_match['score']:.1f} (threshold: {best_match['threshold']})")
            best_result = best_match['product']
            print(f"Matched Product: {best_result.get('given_name', 'N/A')}")
            
            # Show key matching details
            unique_product_names = extract_product_names(best_result.get('product_name', []))
            if unique_product_names:
                print(f"Product Names: {', '.join(unique_product_names)}")
            
            brands = best_result.get('brands', '')
            if brands:
                print(f"Brand: {brands}")
                
            quantity = best_result.get('quantity', '')
            if quantity:
                print(f"Quantity: {quantity}")
                
    elif match_status == "low_confidence":
        print("⚠️  LOW CONFIDENCE MATCH")
        if best_match:
            print(f"Score: {best_match['score']:.1f} (threshold: {best_match['threshold']})")
            best_result = best_match['product']
            print(f"Best Match: {best_result.get('given_name', 'N/A')}")
        print("Recommendation: The search found results but confidence is low.")
        
        # Show AI assistance results if available
        if 'openai_level1' in results or 'openai_level2' in results:
            print("AI assistance was used but could not improve the match quality.")
            
    else:  # no_match
        print("❌ NO MATCH FOUND")
        print("No products were found matching the search criteria.")
        
        # Show AI assistance results if available
        if 'openai_level1' in results:
            level1 = results['openai_level1']
            if level1['decision'] == 'not_a_product':
                print("AI Analysis: This query does not appear to be a food product.")
            elif level1.get('rephrased_query'):
                print(f"AI suggested alternative search: '{level1['rephrased_query']}'")
        
        if 'openai_level2' in results:
            level2 = results['openai_level2']
            if level2['decision'] == 'not_a_product':
                print("AI Analysis: This query does not appear to be a food product.")
            elif level2.get('rephrased_query'):
                print(f"AI suggested alternative search: '{level2['rephrased_query']}'")
    
    print("=" * 60)

if __name__ == "__main__":
    main()