# syntax=docker/dockerfile:1
FROM python:3.11

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Poetry
RUN pip install poetry

# Copy Poetry files first for better caching
COPY pyproject.toml ./

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Install dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/poetry \
    poetry config virtualenvs.create false \
    && poetry install --only=main

# Copy application code (after dependencies for better caching)
COPY . .

# Change ownership to app user
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "main.py"]