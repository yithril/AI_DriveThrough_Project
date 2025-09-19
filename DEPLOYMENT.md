# AI DriveThru Deployment Guide

This guide will help you deploy your AI DriveThru application to AWS using Terraform and GitHub Actions.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Amplify)     │◄───┤   (App Runner)  │◄─┤   (RDS)         │
│   Next.js       │    │   FastAPI       │    │   PostgreSQL   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │    │   ECR           │    │   ElastiCache   │
│   (CDN)         │    │   (Docker)      │    │   Redis         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

### 1. AWS Account Setup
- AWS Account with billing enabled
- AWS CLI configured with appropriate permissions
- IAM user with the following permissions:
  - App Runner
  - RDS
  - ElastiCache
  - S3
  - Secrets Manager
  - ECR
  - Amplify
  - VPC
  - IAM

### 2. Local Tools
- **Terraform** (version 1.6.0+)
- **Docker** (for building images)
- **Git** (for version control)

### 3. GitHub Repository
- Your code in a GitHub repository
- GitHub Actions enabled

## 🚀 Step-by-Step Deployment

### Step 1: Create S3 Bucket for Terraform State

```bash
# Create the bucket for storing Terraform state
aws s3 mb s3://ai-drivethru-terraform-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ai-drivethru-terraform-state \
  --versioning-configuration Status=Enabled
```

### Step 2: Configure Terraform Variables

```bash
# Navigate to the terraform directory
cd infrastructure/terraform

# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit the variables
nano terraform.tfvars
```

**Required variables to set:**
```hcl
# GitHub Repository (replace with your actual repo)
github_repository_url = "https://github.com/yourusername/your-repo"

# Disable Redis to save costs (optional)
enable_redis = false
```

### Step 3: Set up GitHub Secrets

In your GitHub repository, go to **Settings → Secrets and variables → Actions**, and add:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | `wJalr...` |
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |

### Step 4: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Plan the deployment (review what will be created)
terraform plan

# Apply the configuration
terraform apply
```

**This will create:**
- VPC with public/private subnets
- RDS PostgreSQL database
- ElastiCache Redis (if enabled)
- S3 bucket for file storage
- ECR repository for Docker images
- App Runner service for backend
- Amplify app for frontend
- Secrets Manager for sensitive data

### Step 5: Configure Secrets

After the infrastructure is deployed, you need to set the secret values:

```bash
# Set OpenAI API key
aws secretsmanager update-secret \
  --secret-id ai-drivethru-openai-api-key \
  --secret-string "your-openai-api-key-here"

# JWT secret removed - not needed for demo
```

### Step 6: Build and Push Docker Image

```bash
# Get the ECR repository URL
terraform output ecr_repository_url

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ECR_REPOSITORY_URL>

# Build and push the image
cd backend
docker build -t ai-drivethru-backend .
docker tag ai-drivethru-backend:latest <ECR_REPOSITORY_URL>:latest
docker push <ECR_REPOSITORY_URL>:latest
```

### Step 7: Update App Runner Service

The App Runner service needs to be updated to use the new image. This can be done through the AWS Console or by updating the Terraform configuration.

## 🔄 Automated Deployment with GitHub Actions

The `.github/workflows/deploy.yml` file will automatically:

1. **Build** the backend Docker image
2. **Push** to ECR
3. **Deploy** infrastructure with Terraform
4. **Deploy** frontend to Amplify

**To enable automated deployment:**
1. Push your code to the `main` branch
2. GitHub Actions will automatically run
3. Check the Actions tab for deployment status

## 💰 Cost Management

### Monthly Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| App Runner | $5-15 | Scales with usage |
| RDS PostgreSQL | $12 | db.t3.micro |
| ElastiCache Redis | $30 | Optional - disable to save |
| S3 | $1-2 | File storage |
| Amplify | $1-2 | Frontend hosting |
| Secrets Manager | $0.40 | Per secret |
| **Total** | **$18-50** | Depending on Redis usage |

### Cost Optimization Tips

1. **Disable Redis**: Set `enable_redis = false` in `terraform.tfvars`
2. **Monitor usage**: Use AWS Cost Explorer
3. **Set up billing alerts**: Get notified when costs exceed budget
4. **Use smaller instances**: For development, use smaller RDS instances

## 🔧 Environment Variables

### Backend (App Runner)
```bash
DATABASE_URL=postgresql://postgres:password@endpoint:5432/ai_drivethru
REDIS_URL=redis://endpoint:6379  # Optional
S3_BUCKET_NAME=ai-drivethru-files-xxxx
S3_REGION=us-east-1
AWS_REGION=us-east-1
ENVIRONMENT=production
DEBUG=False
# JWT_SECRET removed - not needed for demo
OPENAI_API_KEY=your-openai-key
```

### Frontend (Amplify)
```bash
NEXT_PUBLIC_API_URL=https://your-app-runner-url.us-east-1.awsapprunner.com
NEXT_PUBLIC_ENVIRONMENT=production
# NEXTAUTH_URL removed - not needed for demo
# NEXTAUTH_SECRET removed - not needed for demo
```

## 🐛 Troubleshooting

### Common Issues

1. **Terraform state lock**
   ```bash
   # Wait a few minutes and try again
   terraform apply
   ```

2. **ECR repository not found**
   ```bash
   # Make sure the ECR repository is created first
   terraform apply
   ```

3. **App Runner deployment fails**
   - Check App Runner logs in AWS Console
   - Verify environment variables are set correctly
   - Check if Docker image exists in ECR

4. **Amplify build fails**
   - Check build logs in Amplify Console
   - Verify `package.json` and build scripts
   - Check environment variables

### Useful Commands

```bash
# View Terraform state
terraform show

# View outputs
terraform output

# Destroy infrastructure (careful!)
terraform destroy

# View App Runner logs
aws apprunner describe-service --service-arn <service-arn>

# View Amplify build logs
aws amplify list-jobs --app-id <app-id> --branch-name main
```

## 🔒 Security Notes

- All secrets are stored in AWS Secrets Manager
- Database is not publicly accessible
- S3 bucket has public access blocked
- All resources are in a VPC with proper security groups
- HTTPS is enforced for all services

## 📊 Monitoring

- **CloudWatch**: App Runner and RDS metrics
- **Amplify Console**: Frontend build and deployment status
- **AWS Cost Explorer**: Cost monitoring and alerts
- **App Runner Console**: Backend logs and metrics

## 🎯 Next Steps

1. **Custom Domain**: Configure a custom domain for your application
2. **SSL Certificates**: Set up SSL certificates for HTTPS
3. **Monitoring**: Set up CloudWatch alarms and dashboards
4. **Backup**: Configure automated backups for RDS
5. **Scaling**: Configure auto-scaling for App Runner

## 🆘 Support

If you encounter issues:

1. Check the AWS Console for error messages
2. Review the GitHub Actions logs
3. Check the Terraform state
4. Verify all secrets are set correctly
5. Check the application logs in CloudWatch

For more help, refer to the AWS documentation or create an issue in your repository.
