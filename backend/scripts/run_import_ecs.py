#!/usr/bin/env python3
"""
Run restaurant import using ECS Exec
This script connects to your running ECS container and runs the import from inside the VPC
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

def run_import_via_ecs(task_id, excel_file_name="import_excel.xlsx", overwrite_existing=False):
    """Run import inside the ECS container"""
    try:
        print("🔄 Connecting to ECS container and running import...")
        
        # Use ECS execute-command to run import
        cmd = [
            "aws", "ecs", "execute-command",
            "--cluster", "ai-drivethru-cluster",
            "--task", task_id,
            "--container", "backend",
            "--interactive",
            "--command", f"python /app/scripts/import_restaurant.py /app/import/{excel_file_name} {'--overwrite' if overwrite_existing else ''}"
        ]
        
        print(f"📦 Running: python scripts/import_restaurant.py import/{excel_file_name}")
        if overwrite_existing:
            print("⚠️  Overwrite mode enabled")
        print("⏳ This may take a few minutes...")
        
        # Run the command and capture output
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Import completed successfully!")
            
            # Show the actual output for debugging
            if result.stdout:
                print("\n📋 Import Output:")
                print(result.stdout)
            
            # Try to extract restaurant ID from output
            output_lines = result.stdout.split('\n') if result.stdout else []
            restaurant_id = None
            
            for line in output_lines:
                if 'Restaurant ID:' in line:
                    try:
                        restaurant_id = line.split('Restaurant ID:')[1].strip()
                        break
                    except:
                        pass
            
            if restaurant_id:
                print(f"🏪 Restaurant ID: {restaurant_id}")
            else:
                print("⚠️  Could not determine restaurant ID from output")
            
            return True
        else:
            print("❌ Import failed with return code:", result.returncode)
            if result.stderr:
                print("Error output:", result.stderr)
            return False
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Import failed: {e}")
        return False
    except KeyboardInterrupt:
        print("\n❌ Import cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function to run import via ECS"""
    print("🚀 AI DriveThru Restaurant Import via ECS")
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
    
    # Get user input for import options
    print("\n📋 Import Options:")
    excel_file = input("Excel file name (default: import_excel.xlsx): ").strip() or "import_excel.xlsx"
    
    overwrite_input = input("Overwrite existing data? (y/N): ").strip().lower()
    overwrite_existing = overwrite_input in ['y', 'yes']
    
    # Run import
    print(f"\n🔄 Running import in task: {task_id}")
    success = run_import_via_ecs(task_id, excel_file, overwrite_existing)
    
    if success:
        print("\n🎉 Restaurant import completed successfully!")
        print("🌐 Your restaurant data should now be available in the application")
    else:
        print("\n💥 Import failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
