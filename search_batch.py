#!/usr/bin/env python3
"""
Script to search existing products catalog in MongoDB by text search for multiple products from a batch file.
Reads product names from batch.txt file and outputs results in CSV format.

Output CSV format: Number, Input string, Given Name, Score, ID, Categories, Product Names
- For each product: 1 MongoDB result + 1 RapidFuzz result (top scored from each)
- Number column: 1.Mongo, 1.Fuzzy, 2.Mongo, 2.Fuzzy, etc.
"""

import csv
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from search_products import search_products
from openai_assistant import process_openai_assistance


def display_csv_as_table(csv_file_path: str, max_rows: int = 200, max_col_width: int = 30) -> bool:
    """
    Display CSV file content in a nice table format.
    For GitHub Actions, writes markdown table to GITHUB_STEP_SUMMARY.
    For console, displays Unicode table format.
    
    Args:
        csv_file_path: Path to the CSV file
        max_rows: Maximum number of rows to display (excluding header)
        max_col_width: Maximum width for each column
        
    Returns:
        True if successfully displayed, False otherwise
    """
    try:
        if not os.path.exists(csv_file_path):
            print(f"❌ CSV file not found: {csv_file_path}")
            return False
        
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
        
        if not rows:
            print("❌ CSV file is empty")
            return False
        
        headers = rows[0]
        data_rows = rows[1:]
        
        # Check if running in GitHub Actions
        github_step_summary = os.environ.get('GITHUB_STEP_SUMMARY')
        is_github_actions = github_step_summary is not None
        
        if is_github_actions:
            # Display markdown table for GitHub Actions
            return _display_markdown_table(github_step_summary, csv_file_path, headers, data_rows, max_rows, max_col_width)
        else:
            # Display Unicode table for console
            return _display_console_table(headers, data_rows, max_rows, max_col_width)
        
    except Exception as e:
        print(f"❌ Error displaying CSV table: {e}")
        return False


def _display_markdown_table(github_step_summary: str, csv_file_path: str, headers: List[str], data_rows: List[List[str]], max_rows: int, max_col_width: int) -> bool:
    """
    Display CSV content as markdown table in GitHub Actions step summary.
    
    Args:
        github_step_summary: Path to GITHUB_STEP_SUMMARY file
        csv_file_path: Path to CSV file (for filename display)
        headers: CSV headers
        data_rows: CSV data rows
        max_rows: Maximum rows to display
        max_col_width: Maximum column width
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(github_step_summary, 'a', encoding='utf-8') as f:
            # Add table section header
            f.write("\n### 📊 Search Results Table\n\n")
            f.write(f"Showing {min(len(data_rows), max_rows)}/{len(data_rows)} rows from `{os.path.basename(csv_file_path)}`:\n\n")
            
            # Helper function to truncate text for markdown
            def format_cell_md(text: str) -> str:
                text = str(text).strip()
                if len(text) > max_col_width:
                    return text[:max_col_width-3] + "..."
                return text
            
            # Create markdown table header
            header_line = "| " + " | ".join([format_cell_md(header) for header in headers]) + " |"
            f.write(header_line + "\n")
            
            # Create separator line
            separator = "| " + " | ".join(["---" for _ in headers]) + " |"
            f.write(separator + "\n")
            
            # Add data rows
            displayed_rows = 0
            for row in data_rows:
                if displayed_rows >= max_rows:
                    break
                
                # Ensure row has same number of columns as headers
                padded_row = row + [""] * (len(headers) - len(row))
                row_line = "| " + " | ".join([format_cell_md(cell) for cell in padded_row[:len(headers)]]) + " |"
                f.write(row_line + "\n")
                displayed_rows += 1
            
            # Add note about remaining rows
            if len(data_rows) > max_rows:
                f.write(f"\n*... and {len(data_rows) - max_rows} more rows (showing first {max_rows})*\n")
            
            f.write("\n")
        
        print(f"📊 Table with {min(len(data_rows), max_rows)}/{len(data_rows)} rows added to GitHub job summary")
        return True
        
    except Exception as e:
        print(f"❌ Error writing markdown table to GitHub summary: {e}")
        return False


def _display_console_table(headers: List[str], data_rows: List[List[str]], max_rows: int, max_col_width: int) -> bool:
    """
    Display CSV content as Unicode table in console.
    
    Args:
        headers: CSV headers
        data_rows: CSV data rows
        max_rows: Maximum rows to display
        max_col_width: Maximum column width
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Calculate column widths
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in data_rows[:max_rows]:  # Only consider displayed rows
                if i < len(row):
                    content = str(row[i])
                    max_width = max(max_width, len(content))
            col_widths.append(min(max_width, max_col_width))
        
        # Helper function to truncate and pad text
        def format_cell(text: str, width: int) -> str:
            text = str(text)
            if len(text) > width:
                return text[:width-3] + "..."
            return text.ljust(width)
        
        # Display table
        print(f"\n📊 Batch Search Results (showing {min(len(data_rows), max_rows)}/{len(data_rows)} rows):")
        print("=" * (sum(col_widths) + len(headers) * 3 + 1))
        
        # Header row
        header_line = "│"
        for i, header in enumerate(headers):
            header_line += f" {format_cell(header, col_widths[i])} │"
        print(header_line)
        
        # Separator line
        sep_line = "├"
        for i, width in enumerate(col_widths):
            sep_line += "─" * (width + 2)
            if i < len(col_widths) - 1:
                sep_line += "┼"
            else:
                sep_line += "┤"
        print(sep_line)
        
        # Data rows
        displayed_rows = 0
        for row in data_rows:
            if displayed_rows >= max_rows:
                break
            
            row_line = "│"
            for i, col_width in enumerate(col_widths):
                cell_content = row[i] if i < len(row) else ""
                row_line += f" {format_cell(cell_content, col_width)} │"
            print(row_line)
            displayed_rows += 1
        
        # Bottom border
        bottom_line = "└"
        for i, width in enumerate(col_widths):
            bottom_line += "─" * (width + 2)
            if i < len(col_widths) - 1:
                bottom_line += "┴"
            else:
                bottom_line += "┘"
        print(bottom_line)
        
        if len(data_rows) > max_rows:
            print(f"... and {len(data_rows) - max_rows} more rows (showing first {max_rows})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error displaying console table: {e}")
        return False


def read_batch_file(batch_file: str) -> List[str]:
    """
    Read product names from batch file.
    
    Args:
        batch_file: Path to the batch file
        
    Returns:
        List of product names (strings)
    """
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"Read {len(lines)} product names from {batch_file}")
        return lines
        
    except FileNotFoundError:
        print(f"Error: Batch file '{batch_file}' not found")
        return []
    except Exception as e:
        print(f"Error reading batch file: {e}")
        return []


def get_top_results(search_results: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Extract the top MongoDB result and top RapidFuzz result.
    
    Args:
        search_results: Search results from search_products function
        
    Returns:
        Tuple of (top_mongo_result, top_rapidfuzz_result)
    """
    # Get top MongoDB result (first in direct_search results)
    top_mongo = None
    if (search_results.get('direct_search', {}).get('results')):
        top_mongo = search_results['direct_search']['results'][0]
    
    # Get top RapidFuzz result (first in rapidfuzz_search results) 
    top_rapidfuzz = None
    if (search_results.get('rapidfuzz_search', {}).get('results')):
        top_rapidfuzz = search_results['rapidfuzz_search']['results'][0]
    
    return top_mongo, top_rapidfuzz


def format_csv_row(product_num: int, search_type: str, input_string: str, result: Optional[Dict]) -> List[str]:
    """
    Format a single CSV row from search result.
    
    Args:
        product_num: Product number (1, 2, 3, etc.)
        search_type: 'Mongo' or 'Fuzzy'
        input_string: Original input search string
        result: Search result dictionary or None
        
    Returns:
        List of strings for CSV row: [Number, Input string, Given Name, Score, ID, Categories, Product Names]
    """
    if not result:
        return [f"{product_num}.{search_type}", input_string, "", "0", "", "", ""]
    
    # Extract required fields
    given_name = result.get('given_name', '')
    product_id = result.get('_id', '')
    
    # Get score based on search type
    if search_type == 'Mongo':
        score = result.get('score', 0)
    else:  # Fuzzy
        score = result.get('rapidfuzz_score', 0)
    
    # Extract categories field
    categories = result.get('categories', '')
    
    # Extract product names from product_name array
    product_names = []
    product_name_array = result.get('product_name', [])
    if isinstance(product_name_array, list):
        for item in product_name_array:
            if isinstance(item, dict) and 'text' in item:
                text = item['text']
                if text and text.strip():
                    product_names.append(text.strip())
    
    # Join product names with semicolon separator
    product_names_str = '; '.join(product_names) if product_names else ''
    
    return [
        f"{product_num}.{search_type}",
        input_string,
        given_name,
        f"{score:.2f}",
        str(product_id),
        categories,
        product_names_str
    ]


def format_openai_csv_row(product_num: int, search_type: str, input_string: str, openai_result) -> List[str]:
    """
    Format a single CSV row from OpenAI result.
    
    Args:
        product_num: Product number (1, 2, 3, etc.)
        search_type: 'gpt-3.5' or 'gpt-4'
        input_string: Original input search string
        openai_result: OpenAI result dictionary or None
        
    Returns:
        List of strings for CSV row: [Number, Input string, Given Name, Score, ID, Categories, Product Names]
    """
    if not openai_result:
        return [f"{product_num}.{search_type}", input_string, "", "0", "", "", ""]
    
    # For OpenAI results, we use decision as "given name" and confidence as score
    decision = openai_result.get('decision', 'no_match_found')
    confidence = openai_result.get('confidence', 0.0)
    rephrased_query = openai_result.get('rephrased_query', '')
    reasoning = openai_result.get('reasoning', '')
    
    # Format the result to show decision and rephrased query if available
    given_name = decision
    if rephrased_query:
        given_name = f"{decision}: {rephrased_query}"
    
    return [
        f"{product_num}.{search_type}",
        input_string,
        given_name,
        f"{confidence * 100:.1f}",  # Convert to percentage
        "AI",  # ID field shows this is AI result
        reasoning[:50] + "..." if len(reasoning) > 50 else reasoning,  # Categories field shows reasoning
        rephrased_query or ""  # Product names field shows rephrased query
    ]
    """
    Format a single CSV row from search result.
    
    Args:
        product_num: Product number (1, 2, 3, etc.)
        search_type: 'Mongo' or 'Fuzzy'
        input_string: Original input search string
        result: Search result dictionary or None
        
    Returns:
        List of strings for CSV row: [Number, Input string, Given Name, Score, ID, Categories, Product Names]
    """
    if not result:
        return [f"{product_num}.{search_type}", input_string, "", "0", "", "", ""]
    
    # Extract required fields
    given_name = result.get('given_name', '')
    product_id = result.get('_id', '')
    
    # Get score based on search type
    if search_type == 'Mongo':
        score = result.get('score', 0)
    else:  # Fuzzy
        score = result.get('rapidfuzz_score', 0)
    
    # Extract categories field
    categories = result.get('categories', '')
    
    # Extract product names from product_name array
    product_names = []
    product_name_array = result.get('product_name', [])
    if isinstance(product_name_array, list):
        for item in product_name_array:
            if isinstance(item, dict) and 'text' in item:
                text = item['text']
                if text and text.strip():
                    product_names.append(text.strip())
    
    # Join product names with semicolon separator
    product_names_str = '; '.join(product_names) if product_names else ''
    
    return [
        f"{product_num}.{search_type}",
        input_string,
        given_name,
        f"{score:.2f}",
        str(product_id),
        categories,
        product_names_str
    ]


def search_batch_products(batch_file: str = "batch.txt", output_file: str = None) -> str:
    """
    Main function to search multiple products and generate CSV output.
    
    Args:
        batch_file: Path to input batch file
        output_file: Optional output CSV filename
        
    Returns:
        Path to generated CSV file or empty string on error
    """
    # Read batch file
    product_names = read_batch_file(batch_file)
    if not product_names:
        return ""
    
    # Generate output filename if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"batch_search_results_{timestamp}.csv"
    
    # Prepare CSV data
    csv_rows = []
    csv_headers = ["Number", "Input string", "Given Name", "Score", "ID", "Categories", "Product Names"]
    
    print(f"\nStarting batch search for {len(product_names)} products...")
    print("=" * 50)
    
    # Process each product
    for i, product_name in enumerate(product_names, 1):
        print(f"Searching product {i}/{len(product_names)}: '{product_name}'")
        
        # Perform search
        search_results = search_products(product_name)
        
        # Check for errors
        if "error" in search_results:
            print(f"  Error: {search_results['error']}")
            # Add empty rows for failed search
            csv_rows.append(format_csv_row(i, "Mongo", product_name, None))
            csv_rows.append(format_csv_row(i, "Fuzzy", product_name, None))
            continue
        
        # Get top results
        top_mongo, top_rapidfuzz = get_top_results(search_results)
        
        # Log results summary
        mongo_score = top_mongo.get('score', 0) if top_mongo else 0
        fuzzy_score = top_rapidfuzz.get('rapidfuzz_score', 0) if top_rapidfuzz else 0
        print(f"  MongoDB top score: {mongo_score:.2f}")
        print(f"  RapidFuzz top score: {fuzzy_score:.2f}")
        
        # Add CSV rows (Mongo, Fuzzy, then OpenAI if available)
        csv_rows.append(format_csv_row(i, "Mongo", product_name, top_mongo))
        csv_rows.append(format_csv_row(i, "Fuzzy", product_name, top_rapidfuzz))
        
        # Add OpenAI results if available
        if 'openai_gpt35' in search_results:
            gpt35_result = search_results['openai_gpt35']
            csv_rows.append(format_openai_csv_row(i, "gpt-3.5", product_name, gpt35_result))
            print(f"  GPT-3.5 decision: {gpt35_result.get('decision', 'unknown')}")
        
        if 'openai_gpt4' in search_results:
            gpt4_result = search_results['openai_gpt4']
            csv_rows.append(format_openai_csv_row(i, "gpt-4", product_name, gpt4_result))
            print(f"  GPT-4 decision: {gpt4_result.get('decision', 'unknown')}")
    
    # Write CSV file
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(csv_headers)
            writer.writerows(csv_rows)
        
        print(f"\n✅ Batch search completed!")
        print(f"📁 Results saved to: {output_file}")
        print(f"📊 Total rows: {len(csv_rows)} (including headers)")
        print(f"🔍 Products processed: {len(product_names)}")
        
        # Display the results in a nice table format
        display_csv_as_table(output_file, max_col_width=25)
        
        return output_file
        
    except Exception as e:
        print(f"Error writing CSV file: {e}")
        return ""


def main():
    """Main function to handle command line arguments and execute batch search."""
    parser = argparse.ArgumentParser(description='Search products catalog for multiple products from batch file')
    parser.add_argument('-b', '--batch', default='batch.txt', 
                       help='Input batch file path (default: batch.txt)')
    parser.add_argument('-o', '--output', help='Output CSV file path (optional)')
    
    args = parser.parse_args()
    
    print("Product Catalog Batch Search Tool")
    print("=" * 40)
    print(f"Batch file: {args.batch}")
    print()
    
    # Check if batch file exists
    if not os.path.exists(args.batch):
        print(f"Error: Batch file '{args.batch}' not found")
        sys.exit(1)
    
    # Perform batch search
    output_file = search_batch_products(args.batch, args.output)
    
    if not output_file:
        print("Batch search failed")
        sys.exit(1)
    
    print(f"\n📋 Summary:")
    print(f"- Input file: {args.batch}")
    print(f"- Output file: {output_file}")
    print("- Format: CSV with columns: Number, Input string, Given Name, Score, ID, Categories, Product Names")
    print("- Each product has 2-4 rows: N.Mongo, N.Fuzzy, N.gpt-3.5 (if triggered), N.gpt-4 (if triggered)")


if __name__ == "__main__":
    main()