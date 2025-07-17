.PHONY: install run test clean

install:
	@echo "Setting up virtual environment..."
	python3 -m venv venv
	@echo "Activating virtual environment and installing dependencies..."
	. venv/bin/activate && python -m pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "Setup complete! Run 'source venv/bin/activate' to activate the virtual environment."

run:
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make install' first."; exit 1; fi
	venv/bin/python3 download_products.py

test:
	# No tests yet
	echo "No tests yet"

clean:
	@echo "Removing virtual environment..."
	rm -rf venv
	@echo "Virtual environment removed."
