# S3 Bucket for AI DriveThru File Storage

# Main S3 Bucket
resource "aws_s3_bucket" "main" {
  bucket = "${local.project_name}-files-${random_id.bucket_suffix.hex}"

  tags = local.common_tags
}

# Random ID for bucket suffix (to ensure uniqueness)
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Server Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = false  # Allow public policy for images/audio
  ignore_public_acls      = true
  restrict_public_buckets = false  # Allow public access for images/audio
}

# S3 Bucket CORS Configuration
resource "aws_s3_bucket_cors_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# S3 Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "delete_old_versions"
    status = "Enabled"
    
    filter {
      prefix = ""
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# S3 Bucket Policy for Public Read Access to Images and Audio
resource "aws_s3_bucket_policy" "main" {
  bucket = aws_s3_bucket.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = [
          "${aws_s3_bucket.main.arn}/restaurants/*/images/*",
          "${aws_s3_bucket.main.arn}/restaurants/*/audio/*"
        ]
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.main]
}
