#!/usr/bin/env python3
"""
Run database migrations using ECS Exec
This script connects to your running ECS container and runs migrations from inside the VPC
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def get_ecs_task_id():
    """Get the ECS task ID for the backend service"""
    try:
        result = subprocess.run([
            "aws", "ecs", "list-tasks", 
            "--cluster", "ai-drivethru-cluster",
            "--service", "ai-drivethru-backend-service"
        ], capture_output=True, text=True, check=True)
        
        data = json.loads(result.stdout)
        tasks = data.get("taskArns", [])
        
        if not tasks:
            print("❌ No running tasks found for ai-drivethru-backend-service")
            print("Make sure your ECS service is running")
            return None
        
        # Extract task ID from ARN (format: arn:aws:ecs:region:account:task/cluster/task-id)
        task_arn = tasks[0]
        task_id = task_arn.split("/")[-1]
        
        print(f"✅ Found running task: {task_id}")
        return task_id
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting ECS tasks: {e.stderr}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_migrations_via_ecs(task_id):
    """Run migrations inside the ECS container"""
    try:
        print("🔄 Connecting to ECS container and running migrations...")
        
        # Use ECS execute-command to run migrations
        cmd = [
            "aws", "ecs", "execute-command",
            "--cluster", "ai-drivethru-cluster",
            "--task", task_id,
            "--container", "backend",
            "--interactive",
            "--command", "poetry run alembic upgrade head"
        ]
        
        print("📦 Running: poetry run alembic upgrade head")
        print("⏳ This may take a few minutes...")
        
        # Run the command
        result = subprocess.run(cmd, check=True)
        
        print("✅ Migrations completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        return False
    except KeyboardInterrupt:
        print("\n❌ Migration cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function to run migrations via ECS"""
    print("🚀 AI DriveThru Database Migrations via ECS")
    print("=" * 50)
    
    # Check if AWS CLI is configured
    try:
        subprocess.run(["aws", "sts", "get-caller-identity"], 
                      capture_output=True, check=True)
        print("✅ AWS CLI is configured")
    except subprocess.CalledProcessError:
        print("❌ AWS CLI not configured. Please run 'aws configure'")
        sys.exit(1)
    
    # Get ECS task ID
    print("\n🔍 Looking for running ECS tasks...")
    task_id = get_ecs_task_id()
    if not task_id:
        sys.exit(1)
    
    # Run migrations
    print(f"\n🔄 Running migrations in task: {task_id}")
    success = run_migrations_via_ecs(task_id)
    
    if success:
        print("\n🎉 Database migrations completed successfully!")
        print("🌐 Your application should now be updated with the latest schema")
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
