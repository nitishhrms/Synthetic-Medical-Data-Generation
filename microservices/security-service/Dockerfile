FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create non-root user and switch to it
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER 10001

# Change to src directory
WORKDIR /app/src

# Expose port
EXPOSE 8005

# Run the application
CMD ["python", "main.py"]
