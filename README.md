# open-food-downloader

A Python project to download and search food product records from the OpenFoodFacts dataset in MongoDB.

## Features

### Data Download
- Downloads food product records from the [OpenFoodFacts dataset](https://huggingface.co/datasets/openfoodfacts/product-database) on Hugging Face
- Stores product data directly in MongoDB in real-time (no intermediate mapping)
- Configurable MongoDB connection via environment variable
- **NEW**: Embeds product categories using SentenceTransformers and stores them in Pinecone for semantic search
- Includes fallback mock data for testing when internet access is not available
- GitHub Actions workflow for manual execution

### Product Search
- Search existing products catalog by text search on search_string field
- Improved direct search with advanced input string formatting:
  - Splits camelCase format words (e.g., "BorówkaAmeryk" → "Borówka Ameryk")
  - Splits numbers from letters (e.g., "500g" → "500 g")
  - Removes commas and semicolons 
  - Converts to lowercase
  - Keeps spaces as separators
- Results include relevance scores from MongoDB's text search
- Output saved to JSON files with timestamps and formatted input
- Command-line interface with flexible arguments
- GitHub Actions workflow for manual search triggers

## Prerequisites

- Python 3.x
- MongoDB database (local or cloud-hosted like MongoDB Atlas)
- MongoDB connection URI

## Usage

### Environment Variables

Set the MongoDB connection URI using the environment variable:
- `MONGO_URI`

Optional environment variables:
- `SAVE_TO_MONGO` - Set to `false` to disable MongoDB storage (default: `true`)
- `SAVE_TO_PINECONE` - Set to `true` to enable Pinecone category embedding storage (default: `false`)

#### Pinecone Configuration

When `SAVE_TO_PINECONE=true`, the following environment variables are required:
- `PINECONE_API_KEY` - Your Pinecone API key
- `PINECONE_INDEX_NAME` - The name of your Pinecone index (default: `product-categories`)

Example:
```bash
export MONGO_URI="mongodb://localhost:27017/openfooddb"
export SAVE_TO_PINECONE="true"
export PINECONE_API_KEY="your-pinecone-api-key"
export PINECONE_INDEX_NAME="product-categories"
# or for MongoDB Atlas:
export MONGO_URI="mongodb+srv://user:password@cluster.mongodb.net/openfooddb"
```

### Local execution

#### Download Products
```bash
# Install dependencies
pip install -r requirements.txt

# Set MongoDB URI
export MONGO_URI="mongodb://localhost:27017/openfooddb"

# Run the downloader
python3 download_products.py
```

#### Search Products
```bash
# Search products (requires MongoDB with existing data)
python3 search_products.py "chocolate cookies"

# Search with custom output file
python3 search_products.py "italian pasta" -o my_search_results.json
```

### Using Make

```bash
# Set up virtual environment and install dependencies
make install

# Set MongoDB URI
export MONGO_URI="mongodb://localhost:27017/openfooddb"

# Run the downloader
make run

# Search products
make search SEARCH_STRING='chocolate cookies'
```

### Local development with .env file

```bash
# Create .env file with your MongoDB URI
echo "MONGO_URI=mongodb://localhost:27017/openfooddb" > .env

# Run downloader with local environment
make run-local

# Search with local environment
make search-local SEARCH_STRING='pasta'
```

### GitHub Actions

The repository includes GitHub Action workflows:

#### Download Workflow
1. Go to the "Actions" tab in your GitHub repository
2. Select "Download Food Records" workflow  
3. Click "Run workflow" button
4. Optionally add a description for the run

#### Search Workflow
1. Go to the "Actions" tab in your GitHub repository
2. Select "Search Products Catalog" workflow
3. Click "Run workflow" button
4. Enter your search string (e.g., "chocolate cookies")
5. Optionally add a description for the search

Note: For GitHub Actions, you'll need to set the `MONGO_URI` as a repository secret.

## Data Storage

### Product Documents
The script stores product records directly in a MongoDB collection named `products-catalog`. Each product document contains:
- Product Code (_id)
- Product Name  
- Brand
- Categories
- Countries  
- Ingredients
- Nutrition Grade
- Main Category
- **Search String** - Concatenated searchable text from multiple fields
- And other OpenFoodFacts fields

### Search Results
Search results are saved as JSON files with the following structure:
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "input_string": "BorówkaAmeryk500g",
  "formatted_string": "borówka ameryk 500 g", 
  "direct_search": {
    "count": 15,
    "results": [...]
  }
}
```

## Dependencies

- `datasets>=4.0.0` - For downloading from Hugging Face
- `huggingface_hub>=0.33.0` - Hugging Face Hub integration
- `requests>=2.32.0` - HTTP requests
- `pymongo>=4.0.0` - MongoDB connectivity
- `sentence-transformers>=2.2.0` - For creating category embeddings (optional, required for Pinecone)
- `pinecone>=3.0.0` - Pinecone vector database integration (optional)

## Error Handling

The project includes robust error handling for:
- Missing MongoDB URI environment variable
- MongoDB connection failures
- Individual document insertion errors (continues processing)
- Network connectivity issues
- Empty search strings
- Invalid search parameters