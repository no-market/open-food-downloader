#!/usr/bin/env python3
"""
Pinecone integration module for storing product embeddings.
Uses SentenceTransformers to embed products and stores them in Pinecone for semantic search.
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
        'index_name': os.getenv('PINECONE_INDEX_NAME', 'product-catalog')
    }
    
    missing_keys = [k for k, v in config.items() if not v and k != 'environment']
    if missing_keys:
        raise ValueError(f"Missing required Pinecone environment variables: {missing_keys}")
    
    return config

def create_product_embeddings(products: List[Dict[str, Any]]) -> List[Tuple[str, List[float], Dict[str, Any]]]:
    """
    Create embeddings for products using SentenceTransformers.
    
    Args:
        products: List of product dictionaries
        
    Returns:
        List of tuples (product_id, embedding, metadata)
    """
    try:
        from sentence_transformers import SentenceTransformer
        
        print("Loading SentenceTransformer model 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'...")
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        
        embeddings_data = []
        
        print(f"Creating embeddings for {len(products)} products...")
        
        # First pass: validate product IDs and create list of valid products
        valid_products = []
        skipped_products = []
        
        for product in products:
            product_id = product.get('_id')
            
            # Validate product ID - skip if empty (Pinecone requires ID length >= 1)
            if not product_id or len(str(product_id)) == 0:
                skipped_products.append(product)
                print(f"Warning: Skipping product with empty ID - product: {product}")
                continue
            
            # Convert product_id to string
            product_id = str(product_id)
            
            valid_products.append(product)
        
        # Log summary of skipped products
        if skipped_products:
            print(f"Skipped {len(skipped_products)} products with invalid IDs that would fail Pinecone validation")
        
        if not valid_products:
            print("No valid products to process after validation")
            return []
        
        print(f"Processing {len(valid_products)} valid products for embeddings...")
        
        # Prepare search strings for batch encoding (only valid products)
        search_strings = [product.get('search_string', '') for product in valid_products]
        
        # Create embeddings in batch for efficiency (only for valid products)
        embeddings = model.encode(search_strings, show_progress_bar=True)
        
        # Create embeddings data with validated products
        for i, product in enumerate(valid_products):
            product_id = str(product.get('_id'))
            
            # Get the embedding for this product
            embedding = embeddings[i]
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            else:
                embedding = list(embedding)
            
            # Extract product names as a list of strings
            product_names = []
            product_name_data = product.get('product_name', [])
            if isinstance(product_name_data, list):
                for name_obj in product_name_data:
                    if isinstance(name_obj, dict) and 'text' in name_obj:
                        text = name_obj.get('text', '')
                        if text:
                            product_names.append(text)
            
            # Create metadata with all search_string component fields
            # Ensure all values are valid for Pinecone (no null/None values)
            
            # Handle quantity - convert null to empty string
            quantity = product.get('quantity')
            quantity = str(quantity) if quantity is not None else ''
            
            # Handle brands - convert null to empty string
            brands = product.get('brands')
            brands = str(brands) if brands is not None else ''
            
            # Handle categories - ensure it's a list of strings with no null values
            categories = product.get('categories', [])
            if categories is None:
                categories = []
            elif not isinstance(categories, list):
                categories = [str(categories)] if categories is not None else []
            else:
                # Filter out any null values from the list
                categories = [str(cat) for cat in categories if cat is not None]
            
            # Handle labels - ensure it's a list of strings with no null values
            labels = product.get('labels', [])
            if labels is None:
                labels = []
            elif not isinstance(labels, list):
                labels = [str(labels)] if labels is not None else []
            else:
                # Filter out any null values from the list
                labels = [str(label) for label in labels if label is not None]
            
            # Handle search_string - convert null to empty string
            search_string = product.get('search_string')
            search_string = str(search_string) if search_string is not None else ''
            
            metadata = {
                'product_names': product_names,
                'quantity': quantity,
                'brands': brands,
                'categories': categories,
                'labels': labels,
                'search_string': search_string,
                '_id': product_id
            }
            
            embeddings_data.append((product_id, embedding, metadata))
        
        print(f"Successfully created {len(embeddings_data)} product embeddings")
        return embeddings_data
        
    except ImportError:
        print("Error: sentence-transformers not installed. Please run: pip install sentence-transformers")
        return []
    except Exception as e:
        print(f"Error creating embeddings: {e}")
        return []


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
        
        print("Loading SentenceTransformer model 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'...")
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        
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

def upload_to_pinecone(embeddings_data: List[Tuple[str, List[float], Any]], batch_size: int = 100) -> bool:
    """
    Upload product embeddings to Pinecone index.
    
    Args:
        embeddings_data: List of tuples (product_id, embedding, metadata) for products
                        or (category_id, embedding, full_path) for categories (legacy)
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
        for item in embeddings_data:
            product_id, embedding, metadata = item
            
            # Handle both new product format and legacy category format
            if isinstance(metadata, dict):
                # New product format - metadata is already a dict
                vector_metadata = metadata
            else:
                # Legacy category format - metadata is a string (full_path)
                vector_metadata = {
                    "full_path": metadata,
                    "category_name": product_id.replace('_', ' ').replace('and', '&')
                }
            
            vector = {
                "id": product_id,
                "values": embedding,
                "metadata": vector_metadata
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
        
        print(f"Successfully uploaded all {total_vectors} embeddings to Pinecone")
        return True
        
    except ImportError:
        print("Error: pinecone-client not installed. Please run: pip install pinecone-client")
        return False
    except Exception as e:
        print(f"Error uploading to Pinecone: {e}")
        return False

def search_pinecone(search_string: str, top_k: int = 10) -> List[Dict[str, any]]:
    """
    Search Pinecone index for similar products based on search string.
    
    Args:
        search_string: The search query string
        top_k: Number of top results to return
        
    Returns:
        List of search results with scores and metadata
    """
    try:
        from pinecone import Pinecone
        from sentence_transformers import SentenceTransformer
        
        # Import format_search_string to normalize input the same way as MongoDB
        from utils import format_search_string
        
        # Get Pinecone configuration
        config = get_pinecone_config()
        
        print("Connecting to Pinecone for search...")
        pc = Pinecone(api_key=config['api_key'])
        
        # Connect to the index
        index_name = config['index_name']
        index = pc.Index(index_name)
        
        print(f"Connected to Pinecone index: {index_name}")
        
        # Normalize the search string the same way as MongoDB search
        formatted_search_string = format_search_string(search_string)
        print(f"Normalized search string: '{formatted_search_string}'")
        
        # Create embedding for search string
        print("Loading SentenceTransformer model for search embedding...")
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        
        # Create embedding for the formatted search string
        search_embedding = model.encode([formatted_search_string])[0]
        if hasattr(search_embedding, 'tolist'):
            search_embedding = search_embedding.tolist()
        else:
            search_embedding = list(search_embedding)
        
        # Perform similarity search
        print(f"Searching for similar products to: '{formatted_search_string}'")
        search_results = index.query(
            vector=search_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Process results
        results = []
        for match in search_results.matches:
            metadata = match.metadata or {}
            
            # Handle both product and category results for backward compatibility
            if 'product_names' in metadata:
                # Product result
                product_names = metadata.get('product_names', [])
                given_name = product_names[0] if product_names else metadata.get('_id', '')
                text = metadata.get('search_string', '')
            else:
                # Legacy category result
                given_name = metadata.get('category_name', '')
                text = metadata.get('full_path', '')
            
            result = {
                'id': match.id,
                'score': float(match.score),
                'given_name': given_name,
                'text': text,
                'metadata': metadata
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


def process_products_to_pinecone(products: List[Dict[str, Any]]) -> bool:
    """
    Complete pipeline to process products and upload to Pinecone.
    
    Args:
        products: List of product dictionaries
        
    Returns:
        True if successful, False otherwise
    """
    if not products:
        print("No products to process for Pinecone")
        return True
    
    print(f"Processing {len(products)} products for Pinecone...")
    
    # Create embeddings
    embeddings_data = create_product_embeddings(products)
    if not embeddings_data:
        print("Failed to create embeddings")
        return False
    
    # Upload to Pinecone
    success = upload_to_pinecone(embeddings_data)
    if success:
        print("Successfully processed all products to Pinecone")
    else:
        print("Failed to upload products to Pinecone")
    
    return success


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