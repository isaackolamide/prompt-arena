FROM python:3.11-slim

# Install system dependencies, compile dependencies for awslambdaric, and Node.js v22.x
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    g++ \
    make \
    cmake \
    unzip \
    libcurl4-openssl-dev \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && pip install --no-cache-dir \
        pytest \
        pytest-json-report \
        awslambdaric \
    && apt-get purge -y --auto-remove \
        g++ \
        make \
        cmake \
        unzip \
        libcurl4-openssl-dev \
        curl \
        gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy sandbox runner script
COPY runner.py /app/runner.py

# Create a custom CommonJS test reporter for Node.js
RUN printf 'async function* customReporter(source) { for await (const event of source) { yield JSON.stringify(event) + "\\n"; } }; module.exports = customReporter; module.exports.default = customReporter;\n' > /app/reporter.cjs

RUN groupadd -g 1000 sandbox && useradd -r -u 1000 -g sandbox sandbox \
    && mkdir -p /tmp/sandbox \
    && chown -R sandbox:sandbox /tmp/sandbox
USER sandbox

# Set entrypoint to run the Lambda Runtime Interface Client (RIC)
ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["runner.lambda_handler"]
