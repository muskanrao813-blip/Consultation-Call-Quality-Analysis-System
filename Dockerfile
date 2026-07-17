FROM python:3.11-slim

WORKDIR /app

# Install system dependencies + Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm config set registry https://registry.npmjs.org/ \
    && rm -rf /var/lib/apt/lists/*

# Set NODE_PATH and extend PATH for npm global modules
ENV NODE_PATH=/usr/local/lib/node_modules
ENV PATH="/usr/local/lib/node_modules/.bin:/usr/local/bin:/usr/bin:/bin:${PATH}"

# Install Claude CLI
RUN npm install -g @anthropic-ai/claude-cli && \
    echo "NPM global prefix: $(npm config get prefix)" && \
    echo "Looking for claude..." && \
    find /usr -name "claude" -type f 2>/dev/null || echo "claude executable not found" && \
    ls -la /usr/local/lib/node_modules/.bin/ 2>/dev/null || echo "bin directory not found"

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app/ app/

# Expose port
EXPOSE 8000

# Run app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
