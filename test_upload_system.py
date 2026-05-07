#!/usr/bin/env python3
"""
Comprehensive test script for RAG Chatbot document upload and retrieval system.
Tests the complete workflow: upload → process → retrieve → chat
"""

import asyncio
import time
from pathlib import Path

import httpx

# Configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 300.0  # 5 minutes for document processing


async def test_health_check():
    """Test that the backend API is running"""
    print("\n" + "="*60)
    print("1. HEALTH CHECK")
    print("="*60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health", timeout=10)
            print(f"✓ Backend is running: {response.status_code}")
            print(f"  Response: {response.json()}")
            return True
    except Exception as e:
        print(f"✗ Backend not reachable: {e}")
        print(f"  Make sure backend is running on {API_BASE_URL}")
        return False


async def test_list_documents():
    """Test listing documents"""
    print("\n" + "="*60)
    print("2. LIST DOCUMENTS")
    print("="*60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/documents", timeout=10)
            print(f"✓ List documents endpoint: {response.status_code}")
            data = response.json()
            print(f"  Current documents: {len(data.get('documents', []))}")
            for doc in data.get('documents', []):
                print(f"    - {doc['filename']} (ID: {doc['document_id'][:8]}...)")
            return data.get('documents', [])
    except Exception as e:
        print(f"✗ Failed to list documents: {e}")
        return []


async def create_test_document(content: str, filename: str = "test_document.txt") -> Path:
    """Create a test document file"""
    test_file = Path("/tmp") / filename if Path("/tmp").exists() else Path(".") / filename
    test_file.write_text(content)
    print(f"✓ Created test file: {test_file}")
    return test_file


async def test_upload_document():
    """Test uploading a document"""
    print("\n" + "="*60)
    print("3. UPLOAD DOCUMENT")
    print("="*60)
    
    # Create test document
    content = """
    Tourism Guide: Paris

    Paris is the capital of France and one of the most beautiful cities in the world.
    It is known for its iconic landmarks, romantic atmosphere, and world-class cuisine.

    Major Attractions:
    - Eiffel Tower: The most iconic monument in Paris, built in 1889
    - Louvre Museum: Home to the Mona Lisa and thousands of artworks
    - Notre-Dame Cathedral: A masterpiece of Gothic architecture
    - Arc de Triomphe: A monumental arch at the center of Place Charles de Gaulle
    - Sacré-Cœur: A beautiful basilica with panoramic views

    Best Time to Visit:
    April to June and September to October offer pleasant weather and fewer crowds.

    Getting Around:
    The Paris Metro is an efficient way to navigate the city.
    Buses and taxis are also widely available.
    """
    
    test_file = await create_test_document(content, "paris_guide.txt")
    
    try:
        async with httpx.AsyncClient() as client:
            with open(test_file, "rb") as f:
                files = {"file": (test_file.name, f, "text/plain")}
                print(f"📤 Uploading file: {test_file.name} ({test_file.stat().st_size} bytes)")
                
                response = await client.post(
                    f"{API_BASE_URL}/documents",
                    files=files,
                    timeout=TIMEOUT,
                )
            
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"✓ Document uploaded successfully!")
                print(f"  Document ID: {data['document_id']}")
                print(f"  Filename: {data['filename']}")
                return data['document_id']
            else:
                print(f"✗ Upload failed with status {response.status_code}")
                print(f"  Response: {response.text}")
                return None
                
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return None
    finally:
        # Clean up
        test_file.unlink()


async def test_rag_query(query: str = "What are the major attractions in Paris?"):
    """Test RAG chat query"""
    print("\n" + "="*60)
    print("4. RAG QUERY")
    print("="*60)
    
    print(f"📝 Query: {query}")
    print(f"⏳ Waiting for response...")
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "text": query,
                "rag": True,
            }
            
            response = await client.post(
                f"{API_BASE_URL}/chat/",
                json=payload,
                timeout=TIMEOUT,
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Query successful!")
                print(f"  Response: {data.get('response', 'No response')[:200]}...")
                return True
            else:
                print(f"✗ Query failed with status {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"✗ Query error: {e}")
        return False


async def test_websocket_rag_query(query: str = "Tell me about Paris"):
    """Test WebSocket RAG streaming"""
    print("\n" + "="*60)
    print("5. WEBSOCKET STREAMING QUERY")
    print("="*60)
    
    print(f"📝 Query: {query}")
    
    try:
        import websockets
        
        uri = f"ws://localhost:8000/chat/stream"
        async with websockets.connect(uri) as websocket:
            # Send query with RAG enabled
            await websocket.send('{"text": "' + query + '", "rag": true}')
            
            print("📡 Receiving response...")
            response_text = ""
            chunk_count = 0
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    if isinstance(message, str):
                        response_text += message
                        chunk_count += 1
                        print(message, end="", flush=True)
                except asyncio.TimeoutError:
                    break
            
            print(f"\n✓ Received {chunk_count} chunks, total: {len(response_text)} chars")
            return True
            
    except ImportError:
        print("⚠ websockets library not installed, skipping WebSocket test")
        return None
    except Exception as e:
        print(f"✗ WebSocket error: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "🤖 RAG CHATBOT - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    # Test health
    is_healthy = await test_health_check()
    if not is_healthy:
        print("\n⚠ Backend is not running. Starting tests would fail.")
        print("Please start the backend with: python -m uvicorn backend.main:app --reload")
        return
    
    # List existing documents
    existing_docs = await test_list_documents()
    
    # Upload document
    doc_id = await test_upload_document()
    
    if not doc_id:
        print("\n⚠ Document upload failed. Cannot proceed with RAG tests.")
        return
    
    # Give system a moment to process
    print("\n⏳ Waiting for document indexing...")
    await asyncio.sleep(2)
    
    # Test RAG query
    await test_rag_query()
    
    # Test WebSocket streaming
    await test_websocket_rag_query()
    
    # Final status
    print("\n" + "="*60)
    print("✓ TEST SUITE COMPLETE")
    print("="*60)
    
    final_docs = await test_list_documents()
    print(f"\nFinal document count: {len(final_docs)}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
