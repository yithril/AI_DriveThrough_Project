FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Create non-root user first
RUN useradd --create-home --shell /bin/bash app

# Install dependencies directly to system Python (no virtual env)
RUN poetry config virtualenvs.create false
RUN poetry install --only=main

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "main.py"]
