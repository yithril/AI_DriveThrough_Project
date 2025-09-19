# AI DriveThru Lambda Deployment Guide

This guide explains how to deploy the AI DriveThru FastAPI application to AWS Lambda using AWS SAM.

## 📋 Prerequisites

### Required Tools
1. **AWS CLI** - Install and configure with your credentials
2. **AWS SAM CLI** - For building and deploying serverless applications
3. **Docker** - Required for SAM build process
4. **Python 3.11** - Lambda runtime version

### AWS Setup
1. **AWS Account** with appropriate permissions
2. **S3 Bucket** for deployment artifacts
3. **RDS PostgreSQL** database (or use serverless Aurora)

## 🚀 Quick Deployment

### 1. Install Prerequisites

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install SAM CLI
pip install aws-sam-cli

# Verify installations
aws --version
sam --version
```

### 2. Configure AWS Credentials

```bash
aws configure
# Enter your Access Key ID, Secret Access Key, and region
```

### 3. Deploy Application

```bash
# From backend directory
cd backend

# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

## 🔧 Manual Deployment Steps

### 1. Build Application

```bash
# Build with Docker (required for dependencies)
sam build --use-container
```

### 2. Deploy Application

```bash
# Guided deployment (first time)
sam deploy --guided

# Subsequent deployments
sam deploy
```

### 3. Configure Parameters

During guided deployment, you'll be prompted for:

- **Stack Name**: `ai-drivethru-stack`
- **AWS Region**: `us-east-1` (or your preferred region)
- **Parameter DatabaseUrl**: Your PostgreSQL connection string
- **Parameter OpenAIApiKey**: Your OpenAI API key
- **Parameter JwtSecret**: Your JWT secret for authentication
- **Confirm changes**: `Y`
- **Allow SAM CLI IAM role creation**: `Y`

## 📊 Infrastructure Overview

### AWS Resources Created

1. **Lambda Function**: `ai-drivethru-api`
   - Runtime: Python 3.11
   - Memory: 1024 MB
   - Timeout: 30 seconds

2. **API Gateway**: REST API with CORS enabled
   - Custom domain support
   - Automatic scaling

3. **CloudWatch Logs**: Application logging
   - Automatic log group creation
   - Log retention policies

### Environment Variables

The Lambda function receives these environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `JWT_SECRET`: JWT secret for authentication
- `DEBUG`: Set to "False" for production

## 🔍 Testing Deployment

### 1. Get API Gateway URL

```bash
# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name ai-drivethru-stack \
  --query 'Stacks[0].Outputs'
```

### 2. Test Health Endpoint

```bash
# Test the health endpoint
curl https://your-api-gateway-url/restaurants/health

# Expected response
{
  "status": "healthy",
  "service": "restaurant_api",
  "message": "Restaurant API is running"
}
```

### 3. Test Menu Endpoint

```bash
# Test menu endpoint (after importing data)
curl https://your-api-gateway-url/restaurants/1/menu
```

## 🗄️ Database Setup

### Option 1: RDS PostgreSQL

```bash
# Create RDS instance (via AWS Console or CLI)
aws rds create-db-instance \
  --db-instance-identifier ai-drivethru-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password YourPassword123 \
  --allocated-storage 20
```

### Option 2: Aurora Serverless

```bash
# Create Aurora Serverless cluster
aws rds create-db-cluster \
  --db-cluster-identifier ai-drivethru-aurora \
  --engine aurora-postgresql \
  --engine-mode serverless \
  --master-username admin \
  --master-user-password YourPassword123
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS Lambda

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install SAM CLI
        run: pip install aws-sam-cli
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build application
        run: cd backend && sam build --use-container
      
      - name: Deploy application
        run: cd backend && sam deploy --no-confirm-changeset
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          JWT_SECRET: ${{ secrets.JWT_SECRET }}
```

## 🛠️ Local Development

### Run Locally with SAM

```bash
# Start local API Gateway
sam local start-api

# Test locally
curl http://localhost:3000/restaurants/health
```

### Environment Variables for Local Development

```bash
# Create .env file
DATABASE_URL="postgresql://user:password@localhost:5432/ai_drivethru"
OPENAI_API_KEY="your-openai-key"
JWT_SECRET="your-jwt-secret"
DEBUG="True"
```

## 📝 Monitoring and Logs

### CloudWatch Logs

```bash
# View logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/ai-drivethru"

# Stream logs
aws logs tail /aws/lambda/ai-drivethru-api --follow
```

### CloudWatch Metrics

Monitor these key metrics:
- **Duration**: Function execution time
- **Errors**: Function errors and exceptions
- **Throttles**: Concurrent execution limits
- **Invocations**: Total function calls

## 🔧 Troubleshooting

### Common Issues

**Build Failures:**
```bash
# Clear SAM cache
sam build --use-container --force-upload
```

**Deployment Failures:**
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name ai-drivethru-stack
```

**Runtime Errors:**
```bash
# Check Lambda logs
aws logs tail /aws/lambda/ai-drivethru-api --follow
```

**Database Connection Issues:**
- Verify RDS security groups allow Lambda access
- Check VPC configuration
- Validate connection string format

### Performance Optimization

1. **Memory Allocation**: Increase if function times out
2. **Timeout Settings**: Adjust based on operation complexity
3. **Database Connection Pooling**: Use connection pooling for better performance
4. **Cold Start Optimization**: Consider provisioned concurrency for critical functions

## 💰 Cost Optimization

### Lambda Costs
- **Free Tier**: 1M requests/month, 400,000 GB-seconds
- **Pricing**: $0.20 per 1M requests + $0.0000166667 per GB-second

### RDS Costs
- **RDS**: ~$15-20/month for db.t3.micro
- **Aurora Serverless**: Pay per use, scales to zero

### API Gateway Costs
- **Free Tier**: 1M requests/month
- **Pricing**: $3.50 per million requests

## 🔐 Security Best Practices

1. **Environment Variables**: Use AWS Secrets Manager for sensitive data
2. **VPC Configuration**: Deploy Lambda in VPC for database access
3. **IAM Roles**: Use least privilege principle
4. **API Gateway**: Enable request validation and throttling
5. **Database Security**: Use SSL connections and proper security groups

For more information, see the [AWS SAM documentation](https://docs.aws.amazon.com/serverless-application-model/).
