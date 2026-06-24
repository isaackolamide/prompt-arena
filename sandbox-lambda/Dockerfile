FROM python:3.11-slim

# Install system dependencies, including curl for Node.js setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js v22.x from NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
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

# Create a custom 'json' reporter package in node_modules to support --test-reporter=json
RUN python -c 'import os; os.makedirs("/node_modules/json", exist_ok=True); open("/node_modules/json/package.json", "w").write("{\"name\": \"json\", \"version\": \"1.0.0\", \"main\": \"index.js\"}"); open("/node_modules/json/index.js", "w").write("async function* customReporter(source) { for await (const event of source) { yield JSON.stringify(event) + \"\\n\"; } }; module.exports = customReporter; module.exports.default = customReporter;\n")'

RUN groupadd -g 1000 sandbox && useradd -r -u 1000 -g sandbox sandbox \
    && mkdir -p /tmp/sandbox \
    && chown -R sandbox:sandbox /tmp/sandbox /app /node_modules
USER sandbox

# Set entrypoint to run the runner script
ENTRYPOINT ["python", "/app/runner.py"]
