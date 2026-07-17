FROM node:20-slim as claude-cli-builder

# Install Claude CLI in isolation
RUN npm install -g @anthropic-ai/claude-cli && \
    which claude && \
    claude --version


# Stage 1: Build Claude CLI in official Node image
FROM node:20 AS claude-builder

# Force rebuild (cache buster)
RUN echo "Build timestamp: $(date)"

RUN echo "=== npm version ===" && \
    npm --version && \
    echo "=== node version ===" && \
    node --version && \
    echo "=== npm config ===" && \
    npm config list && \
    echo "=== npm registry ===" && \
    npm config get registry && \
    echo "=== installing Claude CLI ===" && \
    npm install -g @anthropic-ai/claude-cli 2>&1 | tee /tmp/npm-install.log && \
    echo "=== verifying installation ===" && \
    which claude && \
    claude --version && \
    echo "=== Claude CLI built successfully ===" || \
    (echo "=== INSTALLATION FAILED ===" && cat /tmp/npm-install.log && exit 1)


# Stage 2: Python runtime with Claude copied from Stage 1
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Node.js and npm from node:20 image
COPY --from=node:20 /usr/local/bin/node /usr/local/bin/node
COPY --from=node:20 /usr/local/bin/npm /usr/local/bin/npm
COPY --from=node:20 /usr/local/bin/npx /usr/local/bin/npx
COPY --from=node:20 /usr/local/lib/node_modules /usr/local/lib/node_modules

# Copy Claude CLI from builder stage
COPY --from=claude-builder /usr/local/bin/claude /usr/local/bin/claude
COPY --from=claude-builder /usr/local/lib/node_modules/@anthropic-ai /usr/local/lib/node_modules/@anthropic-ai

# Verify Claude is available
RUN which claude && claude --version && echo "✓ Claude CLI ready"

# Set PATH
ENV PATH="/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
ENV NODE_PATH="/usr/local/lib/node_modules"

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
