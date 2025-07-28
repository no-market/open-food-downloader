#!/usr/bin/env python3
"""
Test for multilingual model functionality.
Tests that the new paraphrase-multilingual-MiniLM-L12-v2 model can handle Polish sentences.
"""

import unittest
from unittest.mock import patch, MagicMock
from pinecone_integration import create_category_embeddings, search_pinecone


class TestMultilingualModel(unittest.TestCase):
    """Test cases for multilingual model functionality."""

    def test_model_name_in_create_embeddings(self):
        """Test that create_category_embeddings uses the correct multilingual model."""
        test_categories = {
            "Czekolada": "path/to/czekolada",
            "Słodycze": "path/to/slodycze"
        }
        
        with patch('sentence_transformers.SentenceTransformer') as mock_st:
            # Mock the model and its encode method
            mock_model = MagicMock()
            mock_model.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            mock_st.return_value = mock_model
            
            # Call the function
            result = create_category_embeddings(test_categories)
            
            # Verify the correct model was used
            mock_st.assert_called_once_with('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            
            # Verify we got results
            self.assertEqual(len(result), 2)
            self.assertTrue(all(len(item) == 3 for item in result))  # Each item should have (id, embedding, path)

    def test_model_name_in_search(self):
        """Test that search_pinecone uses the correct multilingual model."""
        polish_search = "czekolada mleczna"
        
        with patch('sentence_transformers.SentenceTransformer') as mock_st, \
             patch('pinecone.Pinecone') as mock_pc, \
             patch('pinecone_integration.get_pinecone_config') as mock_config:
            
            # Mock the config
            mock_config.return_value = {
                'api_key': 'test-key',
                'environment': 'test-env',
                'index_name': 'test-index'
            }
            
            # Mock the model and its encode method
            mock_model = MagicMock()
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
            mock_st.return_value = mock_model
            
            # Mock Pinecone index
            mock_index = MagicMock()
            mock_index.query.return_value = MagicMock(matches=[])
            mock_pc.return_value.Index.return_value = mock_index
            
            # Call the function
            result = search_pinecone(polish_search)
            
            # Verify the correct model was used
            mock_st.assert_called_once_with('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            
            # Verify the search was performed
            self.assertIsInstance(result, list)

    def test_polish_category_names_are_handled(self):
        """Test that Polish category names are properly processed."""
        polish_categories = {
            "Czekolada": "Słodycze/Czekolada",
            "Mleko": "Nabiał/Mleko", 
            "Chleb": "Pieczywo/Chleb",
            "Owoce": "Świeże/Owoce"
        }
        
        with patch('sentence_transformers.SentenceTransformer') as mock_st:
            # Mock the model and its encode method
            mock_model = MagicMock()
            # Return embeddings that match the number of categories
            mock_model.encode.return_value = [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6], 
                [0.7, 0.8, 0.9],
                [0.2, 0.3, 0.4]
            ]
            mock_st.return_value = mock_model
            
            # Call the function
            result = create_category_embeddings(polish_categories)
            
            # Verify all Polish categories were processed
            self.assertEqual(len(result), 4)
            
            # Verify the model was called with the correct texts (full paths)
            mock_model.encode.assert_called_once()
            call_args = mock_model.encode.call_args[0][0]  # First positional argument
            expected_paths = ["Słodycze/Czekolada", "Nabiał/Mleko", "Pieczywo/Chleb", "Świeże/Owoce"]
            self.assertEqual(sorted(call_args), sorted(expected_paths))

    def test_polish_search_string_encoding(self):
        """Test that Polish search strings are properly encoded."""
        polish_searches = [
            "czekolada mleczna",
            "świeże owoce", 
            "chleb żytni",
            "mleko krowie"
        ]
        
        with patch('sentence_transformers.SentenceTransformer') as mock_st, \
             patch('pinecone.Pinecone') as mock_pc, \
             patch('pinecone_integration.get_pinecone_config') as mock_config:
            
            # Mock the config
            mock_config.return_value = {
                'api_key': 'test-key',
                'environment': 'test-env', 
                'index_name': 'test-index'
            }
            
            # Mock the model
            mock_model = MagicMock()
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
            mock_st.return_value = mock_model
            
            # Mock Pinecone
            mock_index = MagicMock()
            mock_index.query.return_value = MagicMock(matches=[])
            mock_pc.return_value.Index.return_value = mock_index
            
            # Test each Polish search string
            for search_string in polish_searches:
                with self.subTest(search_string=search_string):
                    result = search_pinecone(search_string)
                    
                    # Verify the search string was encoded
                    mock_model.encode.assert_called_with([search_string])
                    self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()