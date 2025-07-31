# Name of the virtual environment directory
VENV_DIR := venv

# Python interpreter
PYTHON := python3
PIP := $(VENV_DIR)/bin/pip

# Default target
all: venv install

# Create virtual environment if it doesn't exist
venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "✅ Virtual environment created"; \
	fi

# Install dependencies
install: venv packages.txt
	@$(PIP) install --upgrade pip
	@$(PIP) install -r packages.txt
	@echo "✅ Dependencies installed"

# Activate the virtual environment (prints the command to run)
activate:
	@echo "Run: source $(VENV_DIR)/bin/activate"

# Clean up
clean:
	rm -rf $(VENV_DIR)
	@echo "🧹 Virtual environment removed"

.PHONY: all venv install activate clean
