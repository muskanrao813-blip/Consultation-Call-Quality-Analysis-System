FROM node:20-slim as claude-cli-builder

# Install Claude CLI in isolation
RUN npm install -g @anthropic-ai/claude-cli && \
    which claude && \
    claude --version


FROM node:20-alpine AS node-base

# Install Claude CLI in Node base image
RUN npm install -g @anthropic-ai/claude-cli


FROM python:3.11-slim

WORKDIR /app

# Install Node.js runtime only (no npm needed after install)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest \
    && npm install -g @anthropic-ai/claude-cli 2>&1 && \
    echo "=== Verifying Claude installation ===" && \
    which claude && \
    claude --version && \
    echo "=== Claude CLI successfully installed ===" \
    || echo "=== Warning: Claude CLI installation may have failed ===" && \
    rm -rf /var/lib/apt/lists/*

# Set proper PATH for Node global bins
ENV PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH}"

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app/ app/

# Verify Claude CLI is available
RUN which claude && claude --version

# Expose port
EXPOSE 8000

# Run app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
