.PHONY: setup build test test-unit lint dev clean start stop

# Default target
all: build

# Setup: boots host environment by initializing configuration and installing packages
setup:
	@echo "=== Bootstrapping Host Environment ==="
	@if [ ! -f .env ]; then \
		echo "Initializing .env from .env.example..."; \
		if [ -f .env.example ]; then \
			cp .env.example .env; \
		else \
			echo "Creating default .env..."; \
			printf "# Supabase Configuration\nSUPABASE_URL=\nSUPABASE_ANON_KEY=\nSUPABASE_SERVICE_ROLE_KEY=\n\n# Gemini API Configuration\nGEMINI_API_KEY=\n\n# App Environment\nENV=development\nPORT=8000\n" > .env; \
		fi \
	fi
	@if [ -f backend/requirements.txt ]; then \
		echo "Installing Python backend dependencies..."; \
		pip3 install -r backend/requirements.txt; \
	fi
	@if [ -f frontend/package.json ]; then \
		echo "Installing React frontend dependencies..."; \
		cd frontend && npm install && npx playwright install; \
	fi

# Build: sets up directories, builds sandbox container image
build: setup
	@echo "=== Setting up project skeleton ==="
	mkdir -p backend frontend sandbox-lambda
	@touch backend/.gitkeep
	@touch frontend/.gitkeep
	@touch sandbox-lambda/.gitkeep
	@if [ -d sandbox-lambda ] && [ -f sandbox-lambda/Dockerfile ]; then \
		echo "Building sandbox-lambda container image..."; \
		docker build -t sandbox-lambda sandbox-lambda/; \
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

test-unit:
	@echo "=== Running unit tests ==="
	@FAILED=0; \
	if [ -d backend/tests ] || [ -f backend/requirements.txt ]; then \
		echo "Running backend unit tests..."; \
		python3 -m pytest backend/ --ignore=backend/tests/integration/ || FAILED=1; \
	fi; \
	if [ -f frontend/package.json ]; then \
		echo "Running frontend unit tests..."; \
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

start:
	@echo "=== Starting Supabase Local Emulator ==="
	@npx supabase start || (echo "\n[ERROR] npx supabase start failed to run or apply migrations.\nTraceback/Details:\n- Check if Docker is running.\n- Verify supabase configuration files.\n- Review supabase/migrations/ files for SQL errors." && exit 1)
	@echo "=== Building and Starting Docker Containers ==="
	@docker compose up -d --build || (echo "\n[ERROR] docker compose up -d --build failed to compile or start containers.\nTraceback/Details:\n- Check docker compose build logs.\n- Verify docker configuration and ports." && exit 1)
	@echo "=== Local Dev Environment Started Successfully ==="

stop:
	@echo "=== Stopping Local Dev Environment ==="
	@echo "Stopping Docker containers..."
	@docker compose down || true
	@echo "Stopping Supabase Local Emulator..."
	@npx supabase stop || true
	@echo "=== Local Dev Environment Stopped ==="

clean:
	@echo "=== Cleaning up build artifacts ==="
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
