#!/usr/bin/env python
"""Test script to verify backend imports"""

import sys
import traceback

print("Testing FemCare AI Backend...")

try:
    print("1. Testing config import...")
    from app.config import settings
    print(f"   ✓ Config loaded: {settings.APP_NAME}")
    
    print("2. Testing database import...")
    from app.database import engine, SessionLocal, get_db
    print("   ✓ Database configured")
    
    print("3. Testing models import...")
    from app import models
    print("   ✓ Models loaded")
    
    print("4. Testing schemas import...")
    from app import schemas
    print("   ✓ Schemas loaded")
    
    print("5. Testing security import...")
    from app.security import get_password_hash, verify_password
    print("   ✓ Security utilities loaded")
    
    print("6. Testing routers import...")
    from app.routers import auth, cycles, symptoms, insights, chat
    print("   ✓ All routers loaded")
    
    print("7. Testing main app import...")
    from app.main import app
    print("   ✓ FastAPI app created")
    
    print("\n✅ All imports successful! Backend is ready.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
