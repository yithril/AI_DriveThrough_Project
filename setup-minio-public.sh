#!/bin/bash

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
sleep 10

# Set up MinIO client alias
echo "Setting up MinIO client alias..."
docker run --rm --network host minio/mc alias set local http://localhost:9000 minioadmin minioadmin123

# Create bucket
echo "Creating bucket ai-drivethru-files..."
docker run --rm --network host minio/mc mb local/ai-drivethru-files

# Set bucket policy to public download (read-only)
echo "Setting bucket policy to public download access..."
docker run --rm --network host minio/mc anonymous set download local/ai-drivethru-files

echo "MinIO setup complete! Bucket is now publicly readable."
