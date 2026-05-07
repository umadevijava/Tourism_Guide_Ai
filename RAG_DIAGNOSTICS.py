"""
DEBUGGING & VERIFICATION GUIDE FOR RAG CHATBOT
===============================================

This guide helps verify and fix the entire document upload → retrieval → answer pipeline
"""

import logging
import requests
import json
from pathlib import Path
import asyncio
import websockets

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGChatbotDiagnostics:
    """Comprehensive diagnostics for RAG chatbot"""
    
    def __init__(self, backend_url="http://localhost:8000"):
        self.backend_url = backend_url
        self.ws_url = backend_url.replace("http", "ws") + "/chat/stream"
    
    # ========================================================================
    # STEP 1: VERIFY BACKEND COMPONENTS
    # ========================================================================
    
    def test_backend_health(self):
        """Check if backend is running"""
        print("\n" + "="*70)
        print("STEP 1: BACKEND HEALTH CHECK")
        print("="*70)
        try:
            resp = requests.get(f"{self.backend_url}/health", timeout=5)
            if resp.status_code == 200:
                print("✅ Backend is RUNNING")
                return True
            else:
                print(f"❌ Backend returned: {resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend ERROR: {e}")
            return False
    
    # ========================================================================
    # STEP 2: TEST DOCUMENT UPLOAD
    # ========================================================================
    
    def test_document_upload(self):
        """Test file upload"""
        print("\n" + "="*70)
        print("STEP 2: DOCUMENT UPLOAD TEST")
        print("="*70)
        
        # Create test document
        test_file = Path("test_upload.txt")
        test_content = """
        Tourism Guide: Taj Mahal
        
        The Taj Mahal is an ivory-white marble mausoleum located in Agra, India.
        It was commissioned by Mughal emperor Shah Jahan in memory of his wife Mumtaz.
        
        Key Facts:
        - Built between 1632 and 1653
        - Recognized as one of the seven wonders of the world
        - Located on right bank of River Yamuna
        - One of the most visited monuments in India
        
        Architecture:
        - Main dome with four minarets
        - Built with white marble from Makrana
        - Inlaid with semi-precious stones
        
        Visitor Information:
        - Entry Fee: ₹250 for Indian citizens
        - Open: Sunrise to Sunset
        - Best Time: October to February
        """
        
        test_file.write_text(test_content)
        print(f"  📄 Test file created: {test_file.name} ({test_file.stat().st_size} bytes)")
        
        try:
            with open(test_file, 'rb') as f:
                files = {'file': f}
                resp = requests.post(
                    f"{self.backend_url}/documents",
                    files=files,
                    timeout=300  # 5 minutes
                )
            
            print(f"  Status: {resp.status_code}")
            
            if resp.status_code == 201:
                data = resp.json()
                print(f"✅ Upload SUCCESS")
                print(f"   Document ID: {data['document_id'][:16]}...")
                print(f"   Filename: {data['filename']}")
                return True, data['document_id']
            else:
                print(f"❌ Upload FAILED: {resp.status_code}")
                print(f"   Response: {resp.text[:200]}")
                return False, None
                
        except Exception as e:
            print(f"❌ Upload ERROR: {e}")
            return False, None
    
    # ========================================================================
    # STEP 3: VERIFY DOCUMENT STORAGE
    # ========================================================================
    
    def test_document_listing(self):
        """Check if document is stored in database"""
        print("\n" + "="*70)
        print("STEP 3: DOCUMENT STORAGE VERIFICATION")
        print("="*70)
        
        try:
            resp = requests.get(
                f"{self.backend_url}/documents",
                timeout=10
            )
            
            if resp.status_code == 200:
                docs = resp.json()['documents']
                print(f"✅ Database query SUCCESS")
                print(f"   Documents found: {len(docs)}")
                
                if docs:
                    print(f"\n   Recent documents:")
                    for doc in docs[-3:]:
                        print(f"   - {doc['filename']} ({doc['size']} bytes)")
                    return True
                else:
                    print(f"⚠️  No documents in database")
                    return False
            else:
                print(f"❌ Query FAILED: {resp.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Query ERROR: {e}")
            return False
    
    # ========================================================================
    # STEP 4: TEST VECTOR EMBEDDINGS
    # ========================================================================
    
    def test_embeddings(self):
        """Check if documents are embedded in vector store"""
        print("\n" + "="*70)
        print("STEP 4: VECTOR EMBEDDINGS CHECK")
        print("="*70)
        
        try:
            from backend.core.config import settings
            from chatbot.bot.memory.vector_database.chroma import Chroma
            
            print(f"  Vector DB Path: {settings.VECTOR_STORE_PATH}")
            
            index = Chroma(db_path=settings.VECTOR_STORE_PATH)
            indexed = index.get_indexed_documents()
            
            print(f"✅ Vector database accessible")
            print(f"   Total chunks indexed: {len(indexed)}")
            
            if len(indexed) > 0:
                print(f"✅ Embeddings FOUND - Ready for retrieval")
                return True
            else:
                print(f"⚠️  No embeddings found")
                return False
                
        except Exception as e:
            print(f"❌ Vector DB ERROR: {e}")
            print(f"   This might mean Chroma isn't initialized properly")
            return False
    
    # ========================================================================
    # STEP 5: TEST RAG RETRIEVAL
    # ========================================================================
    
    def test_rag_retrieval(self):
        """Test if RAG retrieves relevant documents"""
        print("\n" + "="*70)
        print("STEP 5: RAG RETRIEVAL TEST")
        print("="*70)
        
        query = "What is the Taj Mahal?"
        print(f"  Testing query: {query}")
        
        try:
            from backend.api.deps import get_index
            from backend.database import SessionLocal
            
            # Get vector database
            gen = get_index()
            index = next(gen)
            
            # Test retrieval
            contents, sources = index.similarity_search_with_threshold(query, k=3)
            
            if contents:
                print(f"✅ Retrieval SUCCESS")
                print(f"   Retrieved {len(contents)} chunks")
                print(f"   Top match score: {sources[0] if sources else 'N/A'}")
                return True
            else:
                print(f"⚠️  No chunks retrieved")
                return False
                
        except Exception as e:
            print(f"❌ Retrieval ERROR: {e}")
            print(f"   This might mean retrieval is not set up correctly")
            return False
    
    # ========================================================================
    # STEP 6: TEST WEBSOCKET CONNECTION
    # ========================================================================
    
    async def test_websocket_connection(self):
        """Test WebSocket connection for streaming"""
        print("\n" + "="*70)
        print("STEP 6: WEBSOCKET CONNECTION TEST")
        print("="*70)
        
        try:
            async with websockets.connect(self.ws_url, timeout=10) as ws:
                print(f"✅ WebSocket connected")
                
                # Send test message
                msg = {
                    "text": "What information do you have about Taj Mahal?",
                    "rag": True
                }
                await ws.send(json.dumps(msg))
                print(f"  Query sent: {msg['text']}")
                
                # Receive response
                tokens = 0
                async for response in ws:
                    tokens += 1
                    if tokens <= 3:
                        print(f"  Response chunk {tokens}: {response[:50]}...")
                    if tokens > 50:
                        print(f"  ... (total {tokens} tokens received)")
                        break
                
                print(f"✅ WebSocket streaming works ({tokens} tokens)")
                return True
                
        except Exception as e:
            print(f"❌ WebSocket ERROR: {e}")
            print(f"   Make sure backend is running and accessible")
            return False
    
    # ========================================================================
    # STEP 7: FULL END-TO-END TEST
    # ========================================================================
    
    def test_full_pipeline(self):
        """Full end-to-end test"""
        print("\n" + "="*70)
        print("STEP 7: FULL END-TO-END TEST")
        print("="*70)
        
        # Checklist
        checks = {
            "Backend Running": self.test_backend_health(),
            "Document Upload": self.test_document_upload()[0],
            "Document Storage": self.test_document_listing(),
            "Vector Embeddings": self.test_embeddings(),
            "RAG Retrieval": self.test_rag_retrieval(),
        }
        
        print(f"\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        
        for check, result in checks.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {check}")
        
        print(f"\nTotal: {passed}/{total} checks passed")
        
        if passed == total:
            print("\n🎉 YOUR RAG CHATBOT IS WORKING PERFECTLY!")
        else:
            print("\n⚠️  Some components need fixing. See failures above.")
        
        return passed == total
    
    # ========================================================================
    # COMMON FIXES
    # ========================================================================
    
    def suggest_fixes(self):
        """Suggest fixes for common issues"""
        print("\n" + "="*70)
        print("COMMON ISSUES & FIXES")
        print("="*70)
        
        issues = {
            "Backend not running": [
                "cd d:\\rag-chatbot-main\\ (1)\\rag-chatbot-main",
                "python -m uvicorn backend.main:app --reload --port 8000"
            ],
            "Upload timeout": [
                "Frontend axios timeout is set to 5 minutes (300000ms)",
                "Backend document processing can take 20-60 seconds",
                "If still slow, try uploading smaller documents first"
            ],
            "Documents disappear after upload": [
                "Refresh the page (Ctrl+R)",
                "Check browser Network tab for 201 status",
                "Documents are saved in SQLite database",
                "They persist across server restarts"
            ],
            "No embeddings created": [
                "Ensure unstructured[md] is installed",
                "Check Chroma database is initialized",
                "Verify VECTOR_STORE_PATH exists"
            ],
            "RAG returns 'No documents found'": [
                "Verify document was uploaded successfully",
                "Check retrieval similarity threshold is not too high",
                "Try a simpler query first"
            ]
        }
        
        for issue, fixes in issues.items():
            print(f"\n❓ {issue}")
            for fix in fixes:
                print(f"   • {fix}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║         RAG CHATBOT - DIAGNOSTIC & VERIFICATION TOOL              ║
    ║                                                                   ║
    ║  This tool helps identify and fix issues in your RAG chatbot     ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    diagnostics = RAGChatbotDiagnostics()
    
    # Run all tests
    print("\n🔍 Running comprehensive diagnostics...\n")
    
    success = diagnostics.test_full_pipeline()
    
    # Test WebSocket (async)
    try:
        print("\n" + "="*70)
        print("Testing WebSocket (async)...")
        asyncio.run(diagnostics.test_websocket_connection())
    except Exception as e:
        print(f"WebSocket test skipped: {e}")
    
    # Suggest fixes
    diagnostics.suggest_fixes()
    
    print("\n" + "="*70)
    if success:
        print("✅ All systems operational!")
    else:
        print("⚠️  Please review failures above and apply fixes")
    print("="*70 + "\n")
