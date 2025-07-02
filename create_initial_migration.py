#!/usr/bin/env python3
"""
Create initial database migration for the chat_history table.
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {command}")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {command}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Error running command '{command}': {e}")
        return False

def main():
    print("🚀 Creating initial database migration...")
    print("=" * 50)
    
    # Check if alembic is available
    if not run_command("alembic --version"):
        print("❌ Alembic not found. Please install it with: pip install alembic")
        sys.exit(1)
    
    # Create initial migration
    print("\n📝 Creating initial migration...")
    if run_command('alembic revision --autogenerate -m "Initial migration - create chat_history table"'):
        print("✅ Initial migration created successfully!")
        
        print("\n📋 To apply the migration, run:")
        print("   alembic upgrade head")
        
        print("\n📋 To see migration status, run:")
        print("   alembic current")
        print("   alembic history")
    else:
        print("❌ Failed to create migration")
        sys.exit(1)

if __name__ == "__main__":
    main()