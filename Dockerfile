FROM node:20-slim as claude-cli-builder

# Install Claude CLI in isolation
RUN npm install -g @anthropic-ai/claude-cli && \
    which claude && \
    claude --version


FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm config set registry https://registry.npmjs.org/ \
    && npm install -g @anthropic-ai/claude-cli \
    && which claude && claude --version \
    && rm -rf /var/lib/apt/lists/*

# Set PATH for Claude CLI
ENV PATH="/usr/local/bin:${PATH}"

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
