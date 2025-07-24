#!/usr/bin/env python3
"""
Test the CSV table display functionality.
"""

import csv
import os
import tempfile
from io import StringIO
import sys
from contextlib import redirect_stdout

from search_batch import display_csv_as_table


def test_display_csv_as_table_basic():
    """Test basic CSV table display functionality."""
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['Number', 'Input string', 'Given Name', 'Score', 'ID'])
        writer.writerow(['1.Mongo', 'nutella chocolate', 'Hazelnut Spreads', '15.42', '507f1f77bcb8218b39000001'])
        writer.writerow(['1.Fuzzy', 'nutella chocolate', 'Chocolate Spreads', '125.75', '507f1f77bcb8218b39000002'])
        temp_file = f.name
    
    try:
        # Capture output
        output = StringIO()
        with redirect_stdout(output):
            result = display_csv_as_table(temp_file, max_rows=10, max_col_width=25)
        
        # Check return value
        assert result == True, "Function should return True for successful display"
        
        # Check output content
        output_str = output.getvalue()
        assert "📊 Batch Search Results" in output_str, "Should contain results header"
        assert "1.Mongo" in output_str, "Should contain first row data"
        assert "nutella chocolate" in output_str, "Should contain input string"
        assert "Hazelnut Spreads" in output_str, "Should contain given name"
        assert "15.42" in output_str, "Should contain score"
        assert "│" in output_str, "Should contain table borders"
        assert "├" in output_str, "Should contain table separators"
        assert "└" in output_str, "Should contain table bottom border"
        
    finally:
        # Clean up
        os.unlink(temp_file)


def test_display_csv_as_table_empty_file():
    """Test table display with empty CSV file."""
    # Create an empty CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_file = f.name
    
    try:
        # Capture output
        output = StringIO()
        with redirect_stdout(output):
            result = display_csv_as_table(temp_file, max_rows=10, max_col_width=25)
        
        # Check return value
        assert result == False, "Function should return False for empty file"
        
        # Check output content
        output_str = output.getvalue()
        assert "❌ CSV file is empty" in output_str, "Should show empty file message"
        
    finally:
        # Clean up
        os.unlink(temp_file)


def test_display_csv_as_table_nonexistent_file():
    """Test table display with non-existent file."""
    nonexistent_file = "/tmp/this_file_does_not_exist.csv"
    
    # Capture output
    output = StringIO()
    with redirect_stdout(output):
        result = display_csv_as_table(nonexistent_file, max_rows=10, max_col_width=25)
    
    # Check return value
    assert result == False, "Function should return False for non-existent file"
    
    # Check output content
    output_str = output.getvalue()
    assert "❌ CSV file not found" in output_str, "Should show file not found message"


def test_display_csv_as_table_truncation():
    """Test table display with long content that should be truncated."""
    # Create a CSV file with long content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['Number', 'Input string', 'Given Name', 'Score', 'ID'])
        writer.writerow(['1.Mongo', 'very long product name that should be truncated', 
                        'Very Long Category Name That Should Be Truncated Too', 
                        '15.42', '507f1f77bcb8218b39000001'])
        temp_file = f.name
    
    try:
        # Capture output
        output = StringIO()
        with redirect_stdout(output):
            result = display_csv_as_table(temp_file, max_rows=10, max_col_width=20)
        
        # Check return value
        assert result == True, "Function should return True for successful display"
        
        # Check output content
        output_str = output.getvalue()
        assert "..." in output_str, "Should contain truncation indicator"
        
    finally:
        # Clean up
        os.unlink(temp_file)


def test_display_csv_as_table_row_limit():
    """Test table display with row limit."""
    # Create a CSV file with many rows
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['Number', 'Input string', 'Given Name', 'Score', 'ID'])
        for i in range(1, 11):  # Create 10 rows
            writer.writerow([f'{i}.Mongo', f'product{i}', f'Category{i}', f'{i}.50', f'id{i}'])
        temp_file = f.name
    
    try:
        # Capture output
        output = StringIO()
        with redirect_stdout(output):
            result = display_csv_as_table(temp_file, max_rows=5, max_col_width=25)
        
        # Check return value
        assert result == True, "Function should return True for successful display"
        
        # Check output content
        output_str = output.getvalue()
        assert "showing 5/10 rows" in output_str, "Should show correct row count"
        assert "and 5 more rows" in output_str, "Should indicate remaining rows"
        
    finally:
        # Clean up
        os.unlink(temp_file)


def test_display_csv_as_table_polish_characters():
    """Test table display with Polish characters."""
    # Create a CSV file with Polish characters
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Number', 'Input string', 'Given Name', 'Score', 'ID'])
        writer.writerow(['1.Mongo', 'chleb żytni', 'Pieczywo żytnie', '15.42', '507f1f77bcb8218b39000001'])
        writer.writerow(['1.Fuzzy', 'śmietana 18%', 'Nabiał świeży', '125.75', '507f1f77bcb8218b39000002'])
        temp_file = f.name
    
    try:
        # Capture output
        output = StringIO()
        with redirect_stdout(output):
            result = display_csv_as_table(temp_file, max_rows=10, max_col_width=25)
        
        # Check return value
        assert result == True, "Function should return True for successful display"
        
        # Check output content
        output_str = output.getvalue()
        assert "chleb żytni" in output_str, "Should contain Polish characters"
        assert "Pieczywo żytnie" in output_str, "Should contain Polish characters"
        assert "śmietana 18%" in output_str, "Should contain Polish characters"
        assert "Nabiał świeży" in output_str, "Should contain Polish characters"
        
    finally:
        # Clean up
        os.unlink(temp_file)


if __name__ == "__main__":
    test_display_csv_as_table_basic()
    test_display_csv_as_table_empty_file()
    test_display_csv_as_table_nonexistent_file()
    test_display_csv_as_table_truncation()
    test_display_csv_as_table_row_limit()
    test_display_csv_as_table_polish_characters()
    print("✅ All table display tests passed!")