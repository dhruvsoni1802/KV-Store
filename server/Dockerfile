FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY server/ ./server/

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8080

# Run the server
CMD ["python", "server/main.py"]
