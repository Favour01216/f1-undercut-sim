# Dockerfile for Render deployment
# This uses Python runtime to run the FastAPI backend

FROM python:3.11-slim

WORKDIR /app

# Copy backend files
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Expose port
EXPOSE 10000

# Start the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
