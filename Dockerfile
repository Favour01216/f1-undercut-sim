# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy backend files
COPY backend/pyproject.toml ./
COPY backend/requirements.txt ./

# Create virtual environment
RUN uv venv .venv

# Install dependencies
RUN uv pip install -r requirements.txt

# Copy backend source code
COPY backend/ ./

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Create necessary directories
RUN mkdir -p features/model_params
RUN mkdir -p logs

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"
ENV ENV=production
ENV OFFLINE=0
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check (disable for Railway since it has its own health check)
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:8000/health || exit 1

# Use entrypoint script that handles Railway's PORT
CMD ["./entrypoint.sh"]