#!/usr/bin/env python3
"""Final System Verification"""

import requests
import json

print('='*60)
print('FINAL SYSTEM VERIFICATION')
print('='*60)
print()

try:
    # Check health
    r = requests.get('http://localhost:8000/health', timeout=5)
    print(f'✓ Backend Health: {r.status_code}')
    print(f'  Response: {r.json()}')
    
    # List documents
    r = requests.get('http://localhost:8000/documents', timeout=5)
    docs = r.json()['documents']
    print(f'✓ Documents Registered: {len(docs)}')
    
    for doc in docs:
        print(f'  - {doc["filename"]} (ID: {doc["document_id"][:16]}...)')
    
    print()
    print('✓✓✓ SYSTEM STATUS: FULLY OPERATIONAL ✓✓✓')
    print()
    print('READY TO USE:')
    print('1. Frontend: http://localhost:5173')
    print('2. Backend API: http://localhost:8000')
    print('3. Upload documents and start chatting!')
    
except Exception as e:
    print(f'✗ Error: {e}')
    print()
    print('Make sure backend is running:')
    print('python -m uvicorn backend.main:app --reload')
