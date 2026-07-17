FROM node:20-slim as claude-cli-builder

# Install Claude CLI in isolation
RUN npm install -g @anthropic-ai/claude-cli && \
    which claude && \
    claude --version


FROM python:3.11-slim

WORKDIR /app

# Install Node.js and npm
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude CLI - try simple global install first
RUN npm install -g @anthropic-ai/claude-cli

# Try to verify - don't fail if it doesn't work (we have fallback)
RUN which claude && claude --version || echo "WARNING: Claude CLI not in PATH, using fallback"

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
