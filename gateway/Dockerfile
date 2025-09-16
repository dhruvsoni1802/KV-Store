FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install build dependencies for psutil
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the gateway code
COPY gateway/ ./

# Expose port
EXPOSE 8000

# Run the API Gateway
CMD ["python", "main.py"]
