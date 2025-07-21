.PHONY: install run test clean setup-local run-local

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

setup-local:
	@echo "🔧 Setting up local environment variables from .env file..."
	@if [ ! -f .env ]; then echo "❌ .env file not found. Create one with MONGO_URI=your_mongo_uri"; exit 1; fi
	@echo "✅ Environment variables ready to be loaded from .env"
	@echo "💡 Use 'make run-local' to run with these environment variables"

run-local: setup-local
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make install' first."; exit 1; fi
	@echo "🚀 Running bot with local environment variables..."
	@export $$(cat .env | grep -v '^#' | xargs) && . venv/bin/activate && python3 download_products.py

test:
	# No tests yet
	echo "No tests yet"

clean:
	@echo "Removing virtual environment..."
	rm -rf venv
	@echo "Virtual environment removed."
