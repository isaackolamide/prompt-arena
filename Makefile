.PHONY: build test lint dev clean

# Default target
all: build

# Build: sets up directories, checks env file, installs dependencies if manifests exist
build:
	@echo "=== Setting up project skeleton ==="
	mkdir -p backend frontend sandbox-lambda
	@touch backend/.gitkeep
	@touch frontend/.gitkeep
	@touch sandbox-lambda/.gitkeep
	@if [ ! -f .env ]; then \
		echo "Initializing .env from .env.example..."; \
		if [ -f .env.example ]; then \
			cp .env.example .env; \
		else \
			echo "Creating default .env..."; \
			printf "# Supabase Configuration\nSUPABASE_URL=\nSUPABASE_ANON_KEY=\nSUPABASE_SERVICE_ROLE_KEY=\n\n# Gemini API Configuration\nGEMINI_API_KEY=\n\n# App Environment\nENV=development\nPORT=8000\n" > .env; \
		fi \
	fi
	@echo "=== Installing dependencies if available ==="
	@if [ -f backend/requirements.txt ]; then \
		echo "Installing Python backend dependencies..."; \
		pip3 install -r backend/requirements.txt; \
	fi
	@if [ -f frontend/package.json ]; then \
		echo "Installing React frontend dependencies..."; \
		cd frontend && npm install; \
	fi

test:
	@echo "=== Running all tests ==="
	@FAILED=0; \
	if [ -d backend/tests ] || [ -f backend/requirements.txt ]; then \
		echo "Running backend tests..."; \
		python3 -m pytest backend/ || FAILED=1; \
	fi; \
	if [ -f frontend/package.json ]; then \
		echo "Running frontend tests..."; \
		cd frontend && npm run test -- --run || FAILED=1; \
	fi; \
	exit $$FAILED

lint:
	@echo "=== Linting all modules ==="
	@FAILED=0; \
	if [ -d backend ]; then \
		echo "Linting backend with ruff..."; \
		if python3 -m ruff --version >/dev/null 2>&1; then \
			python3 -m ruff check backend/ || FAILED=1; \
		else \
			echo "ruff not installed, skipping backend lint."; \
		fi; \
	fi; \
	if [ -f frontend/package.json ]; then \
		echo "Linting frontend..."; \
		cd frontend && npm run lint || FAILED=1; \
	fi; \
	exit $$FAILED

dev:
	@echo "=== Starting dev environment ==="
	@echo "To run backend: uvicorn app.main:app --reload --port 8000"
	@echo "To run frontend: cd frontend && npm run dev"

clean:
	@echo "=== Cleaning up build artifacts ==="
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
