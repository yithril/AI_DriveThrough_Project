# AI DriveThru Infrastructure

This directory contains the Terraform configuration for deploying the AI DriveThru application to AWS.

## Architecture

- **Backend**: AWS App Runner (FastAPI)
- **Frontend**: AWS Amplify (Next.js)
- **Database**: RDS PostgreSQL
- **Cache**: ElastiCache Redis (optional)
- **Storage**: S3 Bucket
- **Secrets**: AWS Secrets Manager

## Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **Terraform** installed (version 1.6.0+)
3. **Docker** installed (for building images)
4. **GitHub repository** with your code

## Setup Instructions

### 1. Create S3 Bucket for Terraform State

```bash
# Create the bucket for storing Terraform state
aws s3 mb s3://ai-drivethru-terraform-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ai-drivethru-terraform-state \
  --versioning-configuration Status=Enabled
```

### 2. Configure Terraform Variables

```bash
# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit the variables
nano terraform.tfvars
```

### 3. Set up GitHub Secrets

In your GitHub repository, go to Settings → Secrets and variables → Actions, and add:

- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `OPENAI_API_KEY`: Your OpenAI API key
- `JWT_SECRET`: A random JWT secret (generate with `openssl rand -base64 32`)

### 4. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the configuration
terraform apply
```

### 5. Update App Runner with Latest Image

After the infrastructure is deployed, you need to update the App Runner service to use the latest Docker image:

```bash
# Get the ECR repository URL from Terraform output
terraform output ecr_repository_url

# Update the App Runner service configuration
# (This will be done automatically by GitHub Actions)
```

## Cost Estimation

### Monthly Costs (Approximate)

- **App Runner**: $5-15/month (scales with usage)
- **RDS PostgreSQL**: $12/month (db.t3.micro)
- **S3**: $1-2/month
- **Amplify**: $1-2/month
- **Secrets Manager**: $0.40/month per secret

**Total**: $18-20/month (Redis disabled to save costs)

### Cost Optimization

- **Disable Redis**: Set `enable_redis = false` to save $30/month
- **Use smaller RDS**: Change `db_instance_class` to `db.t3.nano` (not recommended for production)
- **Monitor usage**: Use AWS Cost Explorer to track expenses

## Environment Variables

The following environment variables are automatically configured:

### Backend (App Runner)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string (if enabled)
- `S3_BUCKET`: S3 bucket name
- `S3_REGION`: AWS region
- `AWS_REGION`: AWS region
- `ENVIRONMENT`: Environment name
- `DEBUG`: Set to "False"

### Frontend (Amplify)
- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_ENVIRONMENT`: Environment name

## Troubleshooting

### Common Issues

1. **Terraform state lock**: If you get a state lock error, wait a few minutes and try again
2. **ECR repository not found**: Make sure the ECR repository is created before building images
3. **App Runner deployment fails**: Check the App Runner logs in AWS Console
4. **Amplify build fails**: Check the build logs in Amplify Console

### Useful Commands

```bash
# View Terraform state
terraform show

# Destroy infrastructure (careful!)
terraform destroy

# View App Runner logs
aws apprunner describe-service --service-arn <service-arn>

# View Amplify build logs
aws amplify list-jobs --app-id <app-id> --branch-name main
```

## Security Notes

- All secrets are stored in AWS Secrets Manager
- Database is not publicly accessible
- S3 bucket has public access blocked
- All resources are in a VPC with proper security groups

## Monitoring

- **CloudWatch**: App Runner and RDS metrics
- **Amplify Console**: Frontend build and deployment status
- **AWS Cost Explorer**: Cost monitoring and alerts
