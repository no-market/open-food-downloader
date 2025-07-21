#!/bin/bash
# Sample usage script for the MongoDB-enabled OpenFoodFacts downloader

echo "OpenFoodFacts MongoDB Integration Demo"
echo "======================================"
echo

# Check if MongoDB URI is set
if [ -z "$MONGO_URI" ] && [ -z "$MONGODB_URI" ]; then
    echo "❌ MongoDB URI not set!"
    echo
    echo "Please set one of these environment variables:"
    echo "  export MONGO_URI=\"mongodb://localhost:27017/openfoodfacts\""
    echo "  export MONGODB_URI=\"mongodb://localhost:27017/openfoodfacts\""
    echo
    echo "For MongoDB Atlas:"
    echo "  export MONGO_URI=\"mongodb+srv://user:password@cluster.mongodb.net/openfoodfacts\""
    echo
    echo "Then run this script again or run the downloader directly:"
    echo "  python3 download_products.py"
    exit 1
fi

echo "✅ MongoDB URI configured"
echo "URI: ${MONGO_URI:-$MONGODB_URI}"
echo

echo "Installing dependencies..."
pip install -r requirements.txt

echo
echo "Starting download and MongoDB storage process..."
echo "This will:"
echo "  1. Connect to MongoDB"
echo "  2. Download OpenFoodFacts Polish products"
echo "  3. Store each product directly in the 'products' collection"
echo "  4. Save unique food groups and categories to JSON files"
echo

python3 download_products.py

echo
echo "Process complete! Check your MongoDB collection for the stored products."