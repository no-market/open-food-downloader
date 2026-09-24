# open-food-downloader

A Python project to download and search food product records from the OpenFoodFacts dataset in MongoDB.

## Features

### Data Download
- Downloads food product records from the [OpenFoodFacts dataset](https://huggingface.co/datasets/openfoodfacts/product-database) on Hugging Face
- Stores product data directly in MongoDB in real-time (no intermediate mapping)
- Configurable MongoDB connection via environment variable
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
- RapidFuzz scoring for improved relevance ranking
- **OpenAI assistance** for challenging queries:
  - Two-stage GPT-3.5 and GPT-4 processing when RapidFuzz scores are low (< 550)
  - Intelligent query rephrasing and product recognition
  - Decision outputs: `valid_product`, `rephrased_successfully`, `not_a_product`, `no_match_found`
  - Requires `OPENAI_API_KEY` environment variable
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
- `OPENAI_API_KEY` - OpenAI API key for enhanced search assistance (optional)

Example:
```bash
export MONGO_URI="mongodb://localhost:27017/openfooddb"
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
# Set MongoDB URI
export MONGO_URI="mongodb://localhost:27017/openfooddb"

# Optional: Set OpenAI API key for enhanced search
export OPENAI_API_KEY="your-openai-api-key"

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

# Optional: Set OpenAI API key for enhanced search
export OPENAI_API_KEY="your-openai-api-key"

# Run the downloader
make run

# Search products
make search SEARCH_STRING='chocolate cookies'
```

### Local development with .env file

```bash
# Create .env file with your MongoDB URI and optional OpenAI key
echo "MONGO_URI=mongodb://localhost:27017/openfooddb" > .env
echo "OPENAI_API_KEY=your-openai-api-key" >> .env

# Run downloader with local environment
make run-local

# Search with local environment
make search-local SEARCH_STRING='pasta'
```

### GitHub Actions

The repository includes GitHub Action workflows:

#### Download Workflow
1. Add an `HF_TOKEN` repository secret containing a Hugging Face access token
2. Go to the "Actions" tab in your GitHub repository
3. Select "Download Food Records" workflow
4. Click "Run workflow" button
5. Optionally add a description for the run

#### Search Workflow
1. Go to the "Actions" tab in your GitHub repository
2. Select "Search Products Catalog" workflow
3. Click "Run workflow" button
4. Enter your search string (e.g., "chocolate cookies")
5. Optionally add a description for the search

Note: The download workflow requires the `HF_TOKEN` repository secret. It also
requires `MONGO_URI` when MongoDB storage is enabled. `OPENAI_API_KEY` remains
optional for the search workflows.

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

### Category Output Files
The download workflow uploads product and category output files as artifacts:

- `eligible_products.jsonl` - one complete product document per line for every product that passed eligibility filtering
- `categories_hierarchy.json` - nested category tree merged from eligible product paths, excluding language-prefixed tags
- `categories_hierarchy_with_direct_counts.json` - the same nested tree with `_direct_product_count` on categories that have products assigned directly to them; child counts are not rolled up into parents
- `unique_categories.json` - all unique category names found in eligible products
- `unique_last_categories.json` - each direct category mapped to its full category path
- `direct_category_product_counts.json` - each direct category mapped to the number of products assigned directly to that category

Products are eligible when their OpenFoodFacts record language is `pl` and the
fastText language model classifies either the direct category or the preferred
product name as `pol_Latn`. The preferred name is the first non-empty `pl` name,
then `main`, then the first remaining non-empty name. Language predictions are
cached by text for the duration of the download.

The workflow separates rejected products into two JSONL files:

- `non_polish_direct_category_rejections.jsonl` - products for which both the
  direct category and preferred product name were classified as non-Polish
- `other_rejections.jsonl` - missing or invalid data and all other rejection reasons

Each rejected-product line includes its code, product names, selected name for
language detection, rejection reason, record language, detected category and
product-name languages with confidence scores, and category path. Existing
MongoDB records are not deleted when a product is rejected by a later run.

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
  },
  "rapidfuzz_search": {
    "count": 15,
    "results": [...]
  },
  "openai_gpt35": {
    "model": "gpt-3.5-turbo",
    "decision": "rephrased_successfully",
    "rephrased_query": "blueberry american 500g"
  },
  "openai_gpt4": {
    "model": "gpt-4",
    "decision": "valid_product", 
    "rephrased_query": "american blueberry 500 grams"
  }
}
```

## Dependencies

- `datasets>=4.0.0` - For downloading from Hugging Face
- `huggingface_hub>=0.33.0` - Hugging Face Hub integration
- `requests>=2.32.0` - HTTP requests
- `pymongo>=4.0.0` - MongoDB connectivity
- `rapidfuzz>=3.0.0` - Text similarity scoring
- `openai>=1.0.0` - OpenAI API for enhanced search assistance

## Error Handling

The project includes robust error handling for:
- Missing MongoDB URI environment variable
- Missing OpenAI API key (graceful degradation)
- MongoDB connection failures
- OpenAI API call failures
- Individual document insertion errors (continues processing)
- Network connectivity issues
- Empty search strings
- Invalid search parameters
