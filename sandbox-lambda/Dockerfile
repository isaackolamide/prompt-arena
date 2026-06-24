FROM python:3.11-slim

# Install system dependencies, including curl for Node.js setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js v20.x from NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python testing dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-json-report

# Set working directory
WORKDIR /app

# Copy sandbox runner script
COPY runner.py /app/runner.py

# Set entrypoint to run the runner script
ENTRYPOINT ["python", "/app/runner.py"]
