# =============================================================================
# MyLLM: Pure CPU-Only Docker Container
# Strict CPU execution — No CUDA, No ROCm, No GPU accelerators required
# =============================================================================

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU build explicitly from official wheel index
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy dependencies first for Docker caching
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and scripts
COPY src/ ./src/
COPY configs/ ./configs/
COPY scripts/ ./scripts/
COPY model_manifest.json ./

# Install package in editable mode
RUN pip install --no-cache-dir -e .

# Create volume mount points for model artifacts and data
RUN mkdir -p /app/models /app/data /app/logs /app/scratch

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

# Default execution: serve API on port 8000
# Mount external checkpoints to /app/models and tokenizer to /app/data
CMD ["python", "scripts/serve.py", "--host", "0.0.0.0", "--port", "8000", "--checkpoint", "/app/models/best.pt", "--tokenizer", "/app/data/tokenizer.json"]
