#!/usr/bin/env python3
"""
Complete troubleshooting script for document upload.
This tests the entire flow and identifies any remaining issues.
"""

import requests
import time
from pathlib import Path
import json

print("\n" + "=" * 80)
print("DOCUMENT UPLOAD TROUBLESHOOTING & VERIFICATION")
print("=" * 80)

# Test 1: Backend Check
print("\n[TEST 1] BACKEND HEALTH CHECK")
print("-" * 80)
try:
    resp = requests.get('http://localhost:8000/health', timeout=5)
    if resp.status_code == 200:
        print("✓ Backend is RUNNING")
    else:
        print(f"✗ Backend returned status {resp.status_code}")
except Exception as e:
    print(f"✗ Backend is NOT running: {e}")
    print("  FIX: Run: cd 'd:\\rag-chatbot-main (1)\\rag-chatbot-main' && python -m uvicorn backend.main:app --reload --port 8000")
    exit(1)

# Test 2: Database Check
print("\n[TEST 2] DATABASE AVAILABILITY")
print("-" * 80)
from backend.core.config import settings
import sqlite3

db_path = settings.DATABASE_URL.replace('sqlite:///', '')
try:
    conn = sqlite3.connect(db_path)
    conn.execute("SELECT 1")
    print(f"✓ Database accessible at: {db_path}")
    conn.close()
except Exception as e:
    print(f"✗ Database error: {e}")

# Test 3: Document Upload
print("\n[TEST 3] DOCUMENT UPLOAD")
print("-" * 80)

# Create test file
test_file = Path(r'D:\rag-chatbot-main (1)\rag-chatbot-main\test_comprehensive.txt')
test_file.write_text('Test document for troubleshooting. ' * 10)

print(f"  File: {test_file.name} ({test_file.stat().st_size / 1024:.1f} KB)")
print(f"  Uploading... (this may take 30-60 seconds)")

start = time.time()
try:
    with open(test_file, 'rb') as f:
        resp = requests.post(
            'http://localhost:8000/documents',
            files={'file': f},
            timeout=300
        )
    elapsed = time.time() - start
    
    if resp.status_code == 201:
        print(f"✓ Upload successful in {elapsed:.1f}s")
        data = resp.json()
        print(f"  - Document ID: {data['document_id'][:16]}...")
    else:
        print(f"✗ Upload failed: {resp.status_code}")
        print(f"  Response: {resp.text[:200]}")
except requests.exceptions.Timeout:
    print(f"✗ Upload TIMED OUT after {time.time() - start:.1f}s")
    print("  This should NOT happen after the fix (timeout is set to 5 minutes)")
except Exception as e:
    print(f"✗ Upload error: {type(e).__name__}: {e}")

# Test 4: Document Listing
print("\n[TEST 4] DOCUMENT RETRIEVAL")
print("-" * 80)
try:
    resp = requests.get('http://localhost:8000/documents')
    if resp.status_code == 200:
        docs = resp.json()['documents']
        print(f"✓ Retrieved {len(docs)} documents from backend")
        if docs:
            for doc in docs[-3:]:  # Show last 3
                print(f"  - {doc['filename']} ({doc['size']} bytes)")
    else:
        print(f"✗ Failed to get documents: {resp.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Vector Database
print("\n[TEST 5] VECTOR DATABASE CHECK")
print("-" * 80)
try:
    from chatbot.bot.memory.vector_database.chroma import Chroma
    index = Chroma(embedding_model=settings.EMBEDDING_MODEL, db_path=settings.VECTOR_STORE_PATH)
    indexed = index.get_indexed_documents()
    print(f"✓ Vector database has {len(indexed)} document chunks indexed")
except Exception as e:
    print(f"✗ Vector database error: {e}")

# Test 6: RAG Query
print("\n[TEST 6] RAG QUERY TEST")
print("-" * 80)
try:
    import asyncio
    import websockets
    
    async def test_rag():
        try:
            uri = "ws://localhost:8000/chat/stream"
            async with websockets.connect(uri, timeout=10) as ws:
                msg = {
                    "text": "What documents are available?",
                    "rag": True
                }
                await ws.send(json.dumps(msg))
                token_count = 0
                async for token in ws:
                    token_count += 1
                    if token_count > 100:  # Limit output
                        break
                if token_count > 0:
                    print(f"✓ RAG query returned {token_count} response tokens")
                    return True
        except Exception as e:
            print(f"✗ RAG error: {e}")
            return False
    
    result = asyncio.run(test_rag())
    
except Exception as e:
    print(f"⚠ Skipping RAG test (asyncio issue): {e}")

print("\n" + "=" * 80)
print("✅ TROUBLESHOOTING COMPLETE")
print("=" * 80)
print("\nIF YOU STILL SEE UPLOAD ERRORS:")
print("1. Check the browser console (F12) for any errors")
print("2. Check the backend terminal for error messages")
print("3. Verify the backend is running one of the following commands:")
print("   - python -m uvicorn backend.main:app --reload --port 8000")
print("\n4. If documents disappear after upload:")
print("   - Refresh the page (Ctrl+R)")
print("   - Check browser Network tab to see if upload returned 201")
print("\n5. If upload takes too long:")
print("   - Try a smaller file first")
print("   - The fix now waits up to 5 minutes for uploads")
print("\nFor debugging, check these files:")
print(f"- Backend logs: Application startup messages")
print(f"- Database: {db_path}")
print(f"- Vector store: {settings.VECTOR_STORE_PATH}")
print("=" * 80 + "\n")
