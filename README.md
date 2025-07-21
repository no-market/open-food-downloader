# open-food-downloader

A Python script to download and store food product records from the OpenFoodFacts dataset in MongoDB.

## Features

- Downloads food product records from the [OpenFoodFacts dataset](https://huggingface.co/datasets/openfoodfacts/product-database) on Hugging Face
- Stores product data directly in MongoDB in real-time (no intermediate mapping)
- Configurable MongoDB connection via environment variable
- Includes fallback mock data for testing when internet access is not available
- GitHub Actions workflow for manual execution

## Prerequisites

- Python 3.x
- MongoDB database (local or cloud-hosted like MongoDB Atlas)
- MongoDB connection URI

## Usage

### Environment Variables

Set the MongoDB connection URI using one of these environment variables:
- `MONGO_URI` (preferred)
- `MONGODB_URI` (alternative)

Example:
```bash
export MONGO_URI="mongodb://localhost:27017/openfooddb"
# or for MongoDB Atlas:
export MONGO_URI="mongodb+srv://user:password@cluster.mongodb.net/openfooddb"
```

### Local execution

```bash
# Install dependencies
pip install -r requirements.txt

# Set MongoDB URI
export MONGO_URI="mongodb://localhost:27017/openfooddb"

# Run the script
python3 download_products.py
```

### Using Make

```bash
# Set up virtual environment and install dependencies
make install

# Set MongoDB URI
export MONGO_URI="mongodb://localhost:27017/openfooddb"

# Run the script
make run
```

### GitHub Actions

The repository includes a GitHub Action workflow that can be triggered manually:

1. Go to the "Actions" tab in your GitHub repository
2. Select "Download Food Records" workflow
3. Click "Run workflow" button
4. Optionally add a description for the run

Note: For GitHub Actions, you'll need to set the `MONGO_URI` as a repository secret.

## Data Storage

The script stores product records directly in a MongoDB collection named `products`. Each product document contains:
- Product Code (_id)
- Product Name  
- Brand
- Categories
- Countries
- Ingredients
- Nutrition Grade
- Main Category
- Search String
- And other OpenFoodFacts fields

The unique food groups and categories are still saved as JSON files (`unique_food_groups.json` and `unique_categories.json`) for reference.

## Dependencies

- `datasets>=4.0.0` - For downloading from Hugging Face
- `huggingface_hub>=0.33.0` - Hugging Face Hub integration
- `requests>=2.32.0` - HTTP requests
- `pymongo>=4.0.0` - MongoDB connectivity

## Error Handling

The script includes robust error handling for:
- Missing MongoDB URI environment variable
- MongoDB connection failures
- Individual document insertion errors (continues processing)
- Network connectivity issues