#!/usr/bin/env python3
"""
Deploy AI DriveThru Backend to AWS ECS
This script builds the Docker image, pushes to ECR, and updates the ECS service
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_aws_cli():
    """Check if AWS CLI is configured"""
    try:
        subprocess.run(["aws", "sts", "get-caller-identity"], 
                      capture_output=True, check=True)
        print("✅ AWS CLI is configured")
        return True
    except subprocess.CalledProcessError:
        print("❌ AWS CLI not configured. Please run 'aws configure'")
        return False

def get_aws_account_id():
    """Get AWS account ID"""
    try:
        result = subprocess.run(["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"], 
                               capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("❌ Could not get AWS account ID")
        return None

def build_docker_image():
    """Build the Docker image"""
    print("📦 Building Docker image...")
    try:
        result = subprocess.run(["docker", "build", "-t", "ai-drivethru-backend", "."], 
                               check=True, cwd=Path(__file__).parent.parent)
        print("✅ Docker image built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker build failed: {e}")
        return False

def login_to_ecr(account_id, region):
    """Login to Amazon ECR"""
    print("🔐 Logging into Amazon ECR...")
    try:
        cmd = f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{region}.amazonaws.com"
        subprocess.run(cmd, shell=True, check=True)
        print("✅ ECR login successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ECR login failed: {e}")
        return False

def tag_and_push_image(account_id, region):
    """Tag and push image to ECR"""
    print("🏷️ Tagging and pushing image to ECR...")
    try:
        ecr_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/ai-drivethru-backend:latest"
        
        # Tag the image
        subprocess.run(["docker", "tag", "ai-drivethru-backend:latest", ecr_uri], check=True)
        
        # Push the image
        subprocess.run(["docker", "push", ecr_uri], check=True)
        
        print("✅ Image pushed to ECR successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ECR push failed: {e}")
        return False

def update_ecs_service():
    """Update ECS service with new image"""
    print("🔄 Updating ECS service...")
    try:
        subprocess.run([
            "aws", "ecs", "update-service",
            "--cluster", "ai-drivethru-cluster",
            "--service", "ai-drivethru-backend-service",
            "--force-new-deployment"
        ], check=True)
        
        print("✅ ECS service updated successfully")
        print("⏳ Service is deploying... This may take a few minutes")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ECS update failed: {e}")
        return False

def get_service_status():
    """Get ECS service status"""
    try:
        result = subprocess.run([
            "aws", "ecs", "describe-services",
            "--cluster", "ai-drivethru-cluster",
            "--services", "ai-drivethru-backend-service"
        ], capture_output=True, text=True, check=True)
        
        data = json.loads(result.stdout)
        service = data["services"][0]
        
        running_count = service["runningCount"]
        desired_count = service["desiredCount"]
        
        print(f"📊 Service Status: {running_count}/{desired_count} tasks running")
        
        if running_count == desired_count:
            print("✅ All tasks are running!")
            return True
        else:
            print("⏳ Service is still deploying...")
            return False
            
    except subprocess.CalledProcessError:
        print("⚠️ Could not get service status")
        return False

def main():
    """Main deployment function"""
    print("🚀 AI DriveThru Backend Deployment")
    print("=" * 50)
    
    # Configuration
    region = "us-east-2"
    
    # Check prerequisites
    if not check_aws_cli():
        sys.exit(1)
    
    # Get AWS account ID
    account_id = get_aws_account_id()
    if not account_id:
        sys.exit(1)
    
    print(f"🔗 Using AWS Account: {account_id}")
    print(f"🌍 Using Region: {region}")
    
    # Build Docker image
    if not build_docker_image():
        sys.exit(1)
    
    # Login to ECR
    if not login_to_ecr(account_id, region):
        sys.exit(1)
    
    # Tag and push image
    if not tag_and_push_image(account_id, region):
        sys.exit(1)
    
    # Update ECS service
    if not update_ecs_service():
        sys.exit(1)
    
    # Check service status
    print("\n📊 Checking deployment status...")
    if get_service_status():
        print("\n🎉 Deployment completed successfully!")
        print("🌐 Your backend should be available at: http://your-alb-dns-name")
        
        # Try to get the ALB DNS name
        try:
            result = subprocess.run([
                "aws", "elbv2", "describe-load-balancers",
                "--names", "ai-drivethru-alb",
                "--query", "LoadBalancers[0].DNSName",
                "--output", "text"
            ], capture_output=True, text=True, check=True)
            
            alb_dns = result.stdout.strip()
            if alb_dns and alb_dns != "None":
                print(f"🔗 Backend URL: http://{alb_dns}")
        except:
            print("⚠️ Could not get ALB DNS name. Check AWS Console.")
    else:
        print("\n⏳ Deployment is in progress. Check AWS Console for status.")

if __name__ == "__main__":
    main()
