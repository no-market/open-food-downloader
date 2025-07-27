#!/usr/bin/env python3
"""
Integration test for the complete Pinecone workflow with mock data.
"""

import os
import tempfile
from unittest.mock import patch, MagicMock
from pinecone_integration import process_categories_to_pinecone


def test_end_to_end_pinecone_integration():
    """Test the complete Pinecone integration workflow with mock data."""
    
    # Mock data similar to what would be extracted from OpenFoodFacts
    unique_last_categories = {
        'Instant noodles': 'Food > Pasta > Instant noodles',
        'Dark chocolate': 'Food > Sweets > Chocolate > Dark chocolate',
        'Greek yogurt': 'Food > Dairy > Yogurt > Greek yogurt',
        'Olive oil': 'Food > Oils > Olive oil',
        'Sourdough bread': 'Food > Bakery > Bread > Sourdough bread'
    }
    
    print("Testing Pinecone integration with sample categories:")
    for category, path in unique_last_categories.items():
        print(f"  - {category}: {path}")
    
    # Test with mocked dependencies
    with patch('sentence_transformers.SentenceTransformer') as mock_transformer_class:
        with patch('pinecone.Pinecone') as mock_pinecone_class:
            with patch('pinecone_integration.get_pinecone_config') as mock_get_config:
                
                # Mock SentenceTransformer
                mock_transformer = MagicMock()
                # Create mock embeddings (384-dimensional like all-MiniLM-L6-v2)
                mock_embeddings = [[0.1] * 384 for _ in range(len(unique_last_categories))]
                mock_transformer.encode.return_value = mock_embeddings
                mock_transformer_class.return_value = mock_transformer
                
                # Mock Pinecone configuration
                mock_get_config.return_value = {
                    'api_key': 'test-api-key',
                    'environment': 'test-env',
                    'index_name': 'product-categories'
                }
                
                # Mock Pinecone client and index
                mock_pinecone = MagicMock()
                mock_index = MagicMock()
                mock_pinecone.Index.return_value = mock_index
                mock_pinecone_class.return_value = mock_pinecone
                
                # Test the complete workflow
                result = process_categories_to_pinecone(unique_last_categories)
                
                # Verify success
                assert result == True, "Pinecone integration should succeed"
                
                # Verify SentenceTransformer was used correctly
                mock_transformer_class.assert_called_once_with('all-MiniLM-L6-v2')
                mock_transformer.encode.assert_called_once()
                
                # Verify the inputs to the transformer
                encode_args = mock_transformer.encode.call_args[0][0]
                assert len(encode_args) == 5, "Should encode 5 category paths"
                assert 'Food > Pasta > Instant noodles' in encode_args
                assert 'Food > Sweets > Chocolate > Dark chocolate' in encode_args
                
                # Verify Pinecone was configured correctly
                mock_pinecone_class.assert_called_once_with(api_key='test-api-key')
                mock_pinecone.Index.assert_called_once_with('product-categories')
                
                # Verify upsert was called
                mock_index.upsert.assert_called_once()
                
                # Check the vectors that were uploaded
                upsert_call = mock_index.upsert.call_args
                vectors = upsert_call[1]['vectors']
                
                assert len(vectors) == 5, "Should upload 5 vectors"
                
                # Check each vector structure
                expected_ids = ['instant_noodles', 'dark_chocolate', 'greek_yogurt', 'olive_oil', 'sourdough_bread']
                uploaded_ids = [v['id'] for v in vectors]
                
                for expected_id in expected_ids:
                    assert expected_id in uploaded_ids, f"Should include vector for {expected_id}"
                
                # Check vector structure
                for vector in vectors:
                    assert 'id' in vector, "Vector should have id"
                    assert 'values' in vector, "Vector should have values"
                    assert 'metadata' in vector, "Vector should have metadata"
                    assert 'full_path' in vector['metadata'], "Metadata should include full_path"
                    assert 'category_name' in vector['metadata'], "Metadata should include category_name"
                    assert len(vector['values']) == 384, "Embedding should be 384-dimensional"
                
                print("\n✅ All Pinecone integration tests passed!")
                print(f"✅ Created embeddings for {len(unique_last_categories)} categories")
                print(f"✅ Uploaded {len(vectors)} vectors to Pinecone")
                print("✅ All vector structures are correct")


def test_pinecone_integration_with_environment_variables():
    """Test that environment variables properly control Pinecone integration."""
    
    unique_last_categories = {
        'Test category': 'Food > Test category'
    }
    
    # Test with SAVE_TO_PINECONE=false
    with patch.dict(os.environ, {'SAVE_TO_PINECONE': 'false'}):
        from pinecone_integration import check_pinecone_enabled
        assert check_pinecone_enabled() == False, "Should be disabled when SAVE_TO_PINECONE=false"
    
    # Test with SAVE_TO_PINECONE=true but missing config
    with patch.dict(os.environ, {'SAVE_TO_PINECONE': 'true'}, clear=True):
        from pinecone_integration import check_pinecone_enabled, get_pinecone_config
        
        assert check_pinecone_enabled() == True, "Should be enabled when SAVE_TO_PINECONE=true"
        
        try:
            get_pinecone_config()
            assert False, "Should raise error when Pinecone config is missing"
        except ValueError as e:
            assert "Missing required Pinecone environment variables" in str(e)
    
    print("✅ Environment variable tests passed!")


if __name__ == '__main__':
    print("Running Pinecone integration tests...")
    test_end_to_end_pinecone_integration()
    test_pinecone_integration_with_environment_variables()
    print("\n🎉 All integration tests completed successfully!")