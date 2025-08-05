.PHONY: install run search search-batch test clean setup-local run-local search-local search-batch-local

install:
	@echo "Setting up virtual environment..."
	python3 -m venv venv
	@echo "Activating virtual environment and installing dependencies..."
	. venv/bin/activate && python -m pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "Setup complete! Run 'source venv/bin/activate' to activate the virtual environment."

run:
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make install' first."; exit 1; fi
	-. venv/bin/activate && python3 download_products.py

search:
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make install' first."; exit 1; fi
	@if [ -z "$(SEARCH_STRING)" ]; then echo "Usage: make search SEARCH_STRING='your search term'"; exit 1; fi
	@echo "🔍 Running search (set OPENAI_API_KEY for enhanced results)..."
	. venv/bin/activate && python3 search_products.py "$(SEARCH_STRING)"

search-batch:
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make install' first."; exit 1; fi
	@echo "🔍 Running batch search (set OPENAI_API_KEY for enhanced results)..."
	. venv/bin/activate && python3 search_batch.py

setup-local:
	@echo "🔧 Setting up local environment variables from .env file..."
	@if [ ! -f .env ]; then echo "❌ .env file not found. Create one with MONGO_URI=your_mongo_uri"; exit 1; fi
	@echo "✅ Environment variables ready to be loaded from .env"
	@echo "💡 Use 'make run-local' to run downloader with these environment variables"
	@echo "💡 Use 'make search-local SEARCH_STRING=\"your search\"' to run search with these environment variables"
	@echo "💡 Optional: Add OPENAI_API_KEY=your_api_key to .env for OpenAI-enhanced search results"

run-local: setup-local
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make install' first."; exit 1; fi
	@echo "🚀 Running downloader with local environment variables..."
	@export $$(cat .env | grep -v '^#' | xargs) && . venv/bin/activate && python3 download_products.py

search-local: setup-local
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make install' first."; exit 1; fi
	@if [ -z "$(SEARCH_STRING)" ]; then echo "Usage: make search-local SEARCH_STRING='your search term'"; exit 1; fi
	@echo "🔍 Running search with local environment variables..."
	@export $$(cat .env | grep -v '^#' | xargs) && . venv/bin/activate && python3 search_products.py "$(SEARCH_STRING)"

search-batch-local: setup-local
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make install' first."; exit 1; fi
	@echo "🔍 Running batch search with local environment variables..."
	@export $$(cat .env | grep -v '^#' | xargs) && . venv/bin/activate && python3 search_batch.py

test:
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make install' first."; exit 1; fi
	@echo "🧪 Running tests with pytest..."
	. venv/bin/activate && python -m pytest test_utils.py -v --tb=short

clean:
	@echo "Removing virtual environment..."
	rm -rf venv
	@echo "Virtual environment removed."
