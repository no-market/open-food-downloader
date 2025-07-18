# open-food-downloader

A Python script to download and display food product records from the OpenFoodFacts dataset.

## Features

- Downloads the first 5 Polish food product records (lang = 'pl') from the [OpenFoodFacts dataset](https://huggingface.co/datasets/openfoodfacts/product-database) on Hugging Face
- Displays records in a formatted console output with key product information
- Includes fallback mock data for testing when internet access is not available
- GitHub Actions workflow for manual execution

## Usage

### Local execution

```bash
# Install dependencies
pip install -r requirements.txt

# Run the script
python3 download_products.py
```

### Using Make

```bash
# Set up virtual environment and install dependencies
make install

# Run the script
make run
```

### GitHub Actions

The repository includes a GitHub Action workflow that can be triggered manually:

1. Go to the "Actions" tab in your GitHub repository
2. Select "Download Food Records" workflow
3. Click "Run workflow" button
4. Optionally add a description for the run

## Output

The script displays 5 Polish food product records with the following information for each:
- Product Code
- Product Name  
- Brand
- Categories
- Countries
- Ingredients
- Nutrition Grade
- Main Category
- Created Date

## Dependencies

- `datasets>=4.0.0` - For downloading from Hugging Face
- `huggingface_hub>=0.33.0` - Hugging Face Hub integration
- `requests>=2.32.0` - HTTP requests

## Fallback Mode

When internet access is not available or the dataset cannot be downloaded, the script automatically falls back to displaying mock data that demonstrates the expected output format.