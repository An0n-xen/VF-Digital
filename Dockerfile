# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and other libraries
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies (exclude Windows-specific packages)
RUN grep -v "pywin32" requirements.txt > requirements-docker.txt && \
    pip install --no-cache-dir -r requirements-docker.txt && \
    rm requirements-docker.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/uploads \
    && mkdir -p data/videos \
    && chmod -R 755 data

# Expose Flask port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Run the Flask application
CMD ["python", "app.py"]
