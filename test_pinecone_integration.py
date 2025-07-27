#!/usr/bin/env python3
"""
Tests for Pinecone integration functionality.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from pinecone_integration import (
    check_pinecone_enabled,
    get_pinecone_config,
    create_category_embeddings,
    upload_to_pinecone,
    process_categories_to_pinecone
)


class TestPineconeIntegration(unittest.TestCase):
    """Test Pinecone integration functions."""

    def test_check_pinecone_enabled_true(self):
        """Test Pinecone enabled detection with various true values."""
        test_values = ['true', 'True', '1', 'yes', 'YES', 'on', 'ON']
        
        for value in test_values:
            with patch.dict(os.environ, {'SAVE_TO_PINECONE': value}):
                self.assertTrue(check_pinecone_enabled(), f"Failed for value: {value}")

    def test_check_pinecone_enabled_false(self):
        """Test Pinecone enabled detection with various false values."""
        test_values = ['false', 'False', '0', 'no', 'NO', 'off', 'OFF', '']
        
        for value in test_values:
            with patch.dict(os.environ, {'SAVE_TO_PINECONE': value}):
                self.assertFalse(check_pinecone_enabled(), f"Failed for value: {value}")

    def test_check_pinecone_enabled_default(self):
        """Test Pinecone enabled detection with no environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(check_pinecone_enabled())

    def test_get_pinecone_config_success(self):
        """Test successful Pinecone configuration retrieval."""
        test_env = {
            'PINECONE_API_KEY': 'test-api-key',
            'PINECONE_ENVIRONMENT': 'test-env',
            'PINECONE_INDEX_NAME': 'test-index'
        }
        
        with patch.dict(os.environ, test_env):
            config = get_pinecone_config()
            self.assertEqual(config['api_key'], 'test-api-key')
            self.assertEqual(config['environment'], 'test-env')
            self.assertEqual(config['index_name'], 'test-index')

    def test_get_pinecone_config_default_index(self):
        """Test Pinecone configuration with default index name."""
        test_env = {
            'PINECONE_API_KEY': 'test-api-key'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = get_pinecone_config()
            self.assertEqual(config['index_name'], 'product-categories')

    def test_get_pinecone_config_missing_api_key(self):
        """Test Pinecone configuration with missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                get_pinecone_config()
            self.assertIn("Missing required Pinecone environment variables", str(context.exception))
            self.assertIn("api_key", str(context.exception))

    @patch('sentence_transformers.SentenceTransformer')
    def test_create_category_embeddings_success(self, mock_transformer_class):
        """Test successful category embedding creation."""
        # Mock the transformer and its encode method
        mock_transformer = MagicMock()
        mock_transformer.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_transformer_class.return_value = mock_transformer
        
        # Test data
        unique_last_categories = {
            'Instant noodles': 'Food > Pasta > Instant noodles',
            'Dark chocolate': 'Food > Sweets > Chocolate > Dark chocolate'
        }
        
        embeddings_data = create_category_embeddings(unique_last_categories)
        
        # Verify results
        self.assertEqual(len(embeddings_data), 2)
        
        # Check first embedding
        category_id1, embedding1, full_path1 = embeddings_data[0]
        self.assertEqual(category_id1, 'instant_noodles')
        self.assertEqual(embedding1, [0.1, 0.2, 0.3])
        self.assertEqual(full_path1, 'Food > Pasta > Instant noodles')
        
        # Check second embedding
        category_id2, embedding2, full_path2 = embeddings_data[1]
        self.assertEqual(category_id2, 'dark_chocolate')
        self.assertEqual(embedding2, [0.4, 0.5, 0.6])
        self.assertEqual(full_path2, 'Food > Sweets > Chocolate > Dark chocolate')
        
        # Verify transformer was called correctly
        mock_transformer_class.assert_called_once_with('all-MiniLM-L6-v2')
        mock_transformer.encode.assert_called_once()
        
        # Check that the encode method was called with the full paths
        encode_args = mock_transformer.encode.call_args[0][0]
        self.assertIn('Food > Pasta > Instant noodles', encode_args)
        self.assertIn('Food > Sweets > Chocolate > Dark chocolate', encode_args)

    def test_create_category_embeddings_empty_input(self):
        """Test category embedding creation with empty input."""
        embeddings_data = create_category_embeddings({})
        self.assertEqual(embeddings_data, [])

    @patch('sentence_transformers.SentenceTransformer')
    def test_create_category_embeddings_import_error(self, mock_transformer_class):
        """Test category embedding creation with import error."""
        mock_transformer_class.side_effect = ImportError("No module named 'sentence_transformers'")
        
        unique_last_categories = {'test': 'test > path'}
        embeddings_data = create_category_embeddings(unique_last_categories)
        
        self.assertEqual(embeddings_data, [])

    def test_category_id_normalization(self):
        """Test that category IDs are properly normalized."""
        with patch('sentence_transformers.SentenceTransformer') as mock_transformer_class:
            mock_transformer = MagicMock()
            mock_transformer.encode.return_value = [[0.1, 0.2, 0.3]]
            mock_transformer_class.return_value = mock_transformer
            
            # Test categories with special characters
            unique_last_categories = {
                'Chocolate & Sweets': 'Food > Chocolate & Sweets'
            }
            
            embeddings_data = create_category_embeddings(unique_last_categories)
            
            # Verify ID normalization
            category_id, _, _ = embeddings_data[0]
            self.assertEqual(category_id, 'chocolate_and_sweets')

    @patch('pinecone.Pinecone')
    @patch('pinecone_integration.get_pinecone_config')
    def test_upload_to_pinecone_success(self, mock_get_config, mock_pinecone_class):
        """Test successful upload to Pinecone."""
        # Mock configuration
        mock_get_config.return_value = {
            'api_key': 'test-key',
            'environment': 'test-env',
            'index_name': 'test-index'
        }
        
        # Mock Pinecone and index
        mock_pinecone = MagicMock()
        mock_index = MagicMock()
        mock_pinecone.Index.return_value = mock_index
        mock_pinecone_class.return_value = mock_pinecone
        
        # Test data
        embeddings_data = [
            ('instant_noodles', [0.1, 0.2, 0.3], 'Food > Pasta > Instant noodles')
        ]
        
        result = upload_to_pinecone(embeddings_data)
        
        # Verify success
        self.assertTrue(result)
        
        # Verify Pinecone was initialized correctly
        mock_pinecone_class.assert_called_once_with(api_key='test-key')
        mock_pinecone.Index.assert_called_once_with('test-index')
        
        # Verify upsert was called
        mock_index.upsert.assert_called_once()
        
        # Check the vector structure
        upsert_args = mock_index.upsert.call_args[1]['vectors']
        self.assertEqual(len(upsert_args), 1)
        
        vector = upsert_args[0]
        self.assertEqual(vector['id'], 'instant_noodles')
        self.assertEqual(vector['values'], [0.1, 0.2, 0.3])
        self.assertEqual(vector['metadata']['full_path'], 'Food > Pasta > Instant noodles')

    @patch('pinecone_integration.create_category_embeddings')
    @patch('pinecone_integration.upload_to_pinecone')
    def test_process_categories_to_pinecone_success(self, mock_upload, mock_create_embeddings):
        """Test successful end-to-end category processing."""
        # Mock embedding creation
        mock_embeddings_data = [
            ('instant_noodles', [0.1, 0.2, 0.3], 'Food > Pasta > Instant noodles')
        ]
        mock_create_embeddings.return_value = mock_embeddings_data
        
        # Mock upload success
        mock_upload.return_value = True
        
        # Test data
        unique_last_categories = {
            'Instant noodles': 'Food > Pasta > Instant noodles'
        }
        
        result = process_categories_to_pinecone(unique_last_categories)
        
        # Verify success
        self.assertTrue(result)
        
        # Verify functions were called correctly
        mock_create_embeddings.assert_called_once_with(unique_last_categories)
        mock_upload.assert_called_once_with(mock_embeddings_data)

    @patch('pinecone_integration.create_category_embeddings')
    def test_process_categories_to_pinecone_empty_input(self, mock_create_embeddings):
        """Test category processing with empty input."""
        result = process_categories_to_pinecone({})
        
        # Should return True (success) for empty input
        self.assertTrue(result)
        
        # Embedding creation should not be called
        mock_create_embeddings.assert_not_called()

    @patch('pinecone_integration.create_category_embeddings')
    @patch('pinecone_integration.upload_to_pinecone')
    def test_process_categories_to_pinecone_embedding_failure(self, mock_upload, mock_create_embeddings):
        """Test category processing with embedding creation failure."""
        # Mock embedding creation failure
        mock_create_embeddings.return_value = []
        
        unique_last_categories = {
            'Instant noodles': 'Food > Pasta > Instant noodles'
        }
        
        result = process_categories_to_pinecone(unique_last_categories)
        
        # Should return False due to embedding failure
        self.assertFalse(result)
        
        # Upload should not be called
        mock_upload.assert_not_called()


if __name__ == '__main__':
    unittest.main()