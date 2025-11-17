FROM python:3.11-slim

LABEL maintainer="Camera API"
LABEL description="MindVision 47MP GigE Vision Camera API"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # OpenCV dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    # Network tools
    iputils-ping \
    net-tools \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY camera_api.py .
COPY mvsdk.py .

# Create directory for captured images
RUN mkdir -p /app/images

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "camera_api:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
