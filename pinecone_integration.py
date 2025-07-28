#!/usr/bin/env python3
"""
Pinecone integration module for storing product category embeddings.
Uses SentenceTransformers to embed categories and stores them in Pinecone for semantic search.
"""

import os
import logging
from typing import Dict, List, Tuple, Any
import time

def check_pinecone_enabled() -> bool:
    """Check if Pinecone integration is enabled via environment variable."""
    return os.getenv('SAVE_TO_PINECONE', 'false').lower() in ('true', '1', 'yes', 'on')

def get_pinecone_config() -> Dict[str, str]:
    """Get Pinecone configuration from environment variables."""
    config = {
        'api_key': os.getenv('PINECONE_API_KEY'),
        'environment': os.getenv('PINECONE_ENVIRONMENT', ''),
        'index_name': os.getenv('PINECONE_INDEX_NAME', 'product-categories')
    }
    
    missing_keys = [k for k, v in config.items() if not v and k != 'environment']
    if missing_keys:
        raise ValueError(f"Missing required Pinecone environment variables: {missing_keys}")
    
    return config

def create_category_embeddings(unique_last_categories: Dict[str, str]) -> List[Tuple[str, List[float], str]]:
    """
    Create embeddings for categories using SentenceTransformers.
    
    Args:
        unique_last_categories: Dictionary mapping category name to full path
        
    Returns:
        List of tuples (category_id, embedding, full_path)
    """
    try:
        from sentence_transformers import SentenceTransformer
        
        print("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        embeddings_data = []
        
        print(f"Creating embeddings for {len(unique_last_categories)} categories...")
        
        # First pass: validate category names and create list of valid categories
        valid_categories = []
        skipped_categories = []
        
        for category_name, full_path in unique_last_categories.items():
            # Create unique category ID from category name
            category_id = category_name.lower().replace(' ', '_').replace('&', 'and')
            # Convert non-ASCII characters to ASCII equivalent
            import unicodedata
            category_id = unicodedata.normalize('NFKD', category_id).encode('ascii', 'ignore').decode('ascii')
            # Remove any special characters that might cause issues
            category_id = ''.join(c for c in category_id if c.isalnum() or c in '_-')
            
            # Validate category ID - skip if empty (Pinecone requires ID length >= 1)
            if not category_id or len(category_id) == 0:
                skipped_categories.append((category_name, full_path))
                print(f"Warning: Skipping category with empty ID - original name: '{category_name}'")
                continue
            
            valid_categories.append((category_name, full_path, category_id))
        
        # Log summary of skipped categories
        if skipped_categories:
            print(f"Skipped {len(skipped_categories)} categories with invalid IDs that would fail Pinecone validation")
            print("Skipped categories:")
            for category_name, full_path in skipped_categories:
                print(f"  - '{category_name}' (path: {full_path})")
        
        if not valid_categories:
            print("No valid categories to process after validation")
            return []
        
        print(f"Processing {len(valid_categories)} valid categories for embeddings...")
        
        # Prepare texts for batch encoding (only valid categories)
        full_paths = [item[1] for item in valid_categories]
        
        # Create embeddings in batch for efficiency (only for valid categories)
        embeddings = model.encode(full_paths, show_progress_bar=True)
        
        # Create embeddings data with validated categories
        for i, (category_name, full_path, category_id) in enumerate(valid_categories):
            # Get the embedding for this category
            embedding = embeddings[i]
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            else:
                embedding = list(embedding)
            
            embeddings_data.append((category_id, embedding, full_path))
        
        print(f"Successfully created {len(embeddings_data)} category embeddings")
        return embeddings_data
        
    except ImportError:
        print("Error: sentence-transformers not installed. Please run: pip install sentence-transformers")
        return []
    except Exception as e:
        print(f"Error creating embeddings: {e}")
        return []

def upload_to_pinecone(embeddings_data: List[Tuple[str, List[float], str]], batch_size: int = 100) -> bool:
    """
    Upload category embeddings to Pinecone index.
    
    Args:
        embeddings_data: List of tuples (category_id, embedding, full_path)
        batch_size: Number of vectors to upload per batch
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from pinecone import Pinecone
        
        # Get Pinecone configuration
        config = get_pinecone_config()
        
        print("Connecting to Pinecone...")
        pc = Pinecone(api_key=config['api_key'])
        
        # Connect to the index
        index_name = config['index_name']
        index = pc.Index(index_name)
        
        print(f"Connected to Pinecone index: {index_name}")
        
        # Prepare vectors for upload
        vectors = []
        for category_id, embedding, full_path in embeddings_data:
            vector = {
                "id": category_id,
                "values": embedding,
                "metadata": {
                    "full_path": full_path,
                    "category_name": category_id.replace('_', ' ').replace('and', '&')
                }
            }
            vectors.append(vector)
        
        # Upload in batches
        total_vectors = len(vectors)
        print(f"Uploading {total_vectors} vectors in batches of {batch_size}...")
        
        for i in range(0, total_vectors, batch_size):
            batch = vectors[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_vectors + batch_size - 1) // batch_size
            
            print(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} vectors)...")
            
            try:
                index.upsert(vectors=batch)
                print(f"Batch {batch_num} uploaded successfully")
                
                # Small delay between batches to avoid rate limiting
                if i + batch_size < total_vectors:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"Error uploading batch {batch_num}: {e}")
                return False
        
        print(f"Successfully uploaded all {total_vectors} category embeddings to Pinecone")
        return True
        
    except ImportError:
        print("Error: pinecone-client not installed. Please run: pip install pinecone-client")
        return False
    except Exception as e:
        print(f"Error uploading to Pinecone: {e}")
        return False

def search_pinecone(search_string: str, top_k: int = 10) -> List[Dict[str, any]]:
    """
    Search Pinecone index for similar categories based on search string.
    
    Args:
        search_string: The search query string
        top_k: Number of top results to return
        
    Returns:
        List of search results with scores and metadata
    """
    try:
        from pinecone import Pinecone
        from sentence_transformers import SentenceTransformer
        
        # Get Pinecone configuration
        config = get_pinecone_config()
        
        print("Connecting to Pinecone for search...")
        pc = Pinecone(api_key=config['api_key'])
        
        # Connect to the index
        index_name = config['index_name']
        index = pc.Index(index_name)
        
        print(f"Connected to Pinecone index: {index_name}")
        
        # Create embedding for search string
        print("Loading SentenceTransformer model for search embedding...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create embedding for the search string
        search_embedding = model.encode([search_string])[0]
        if hasattr(search_embedding, 'tolist'):
            search_embedding = search_embedding.tolist()
        else:
            search_embedding = list(search_embedding)
        
        # Perform similarity search
        print(f"Searching for similar categories to: '{search_string}'")
        search_results = index.query(
            vector=search_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Process results
        results = []
        for match in search_results.matches:
            result = {
                'id': match.id,
                'score': float(match.score),
                'category_name': match.metadata.get('category_name', ''),
                'full_path': match.metadata.get('full_path', ''),
                'given_name': match.metadata.get('category_name', ''),  # Use category_name as given_name
                'text': match.metadata.get('full_path', '')  # Use full_path as text
            }
            results.append(result)
        
        print(f"Found {len(results)} Pinecone search results")
        return results
        
    except ImportError as e:
        print(f"Error: Required package not installed. {e}")
        return []
    except Exception as e:
        print(f"Error searching Pinecone: {e}")
        return []


def process_categories_to_pinecone(unique_last_categories: Dict[str, str]) -> bool:
    """
    Complete pipeline to process categories and upload to Pinecone.
    
    Args:
        unique_last_categories: Dictionary mapping category name to full path
        
    Returns:
        True if successful, False otherwise
    """
    if not unique_last_categories:
        print("No categories to process for Pinecone")
        return True
    
    print(f"Processing {len(unique_last_categories)} unique categories for Pinecone...")
    
    # Create embeddings
    embeddings_data = create_category_embeddings(unique_last_categories)
    if not embeddings_data:
        print("Failed to create embeddings")
        return False
    
    # Upload to Pinecone
    success = upload_to_pinecone(embeddings_data)
    if success:
        print("Successfully processed all categories to Pinecone")
    else:
        print("Failed to upload categories to Pinecone")
    
    return success