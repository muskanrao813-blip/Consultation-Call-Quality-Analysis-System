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

# Install Claude CLI with explicit error checking
RUN npm install -g @anthropic-ai/claude-cli --verbose && \
    which claude || (echo "Claude CLI not found in PATH after installation!" && exit 1) && \
    claude --version

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
