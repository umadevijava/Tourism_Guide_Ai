#!/usr/bin/env python3
"""
RAG CHATBOT - STEP-BY-STEP VERIFICATION SCRIPT
===============================================

This script guides you through verifying each component works.
Run this after applying fixes to confirm the system is operational.
"""

import sys
import time
import json
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}► {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_instruction(msg):
    print(f"{Colors.BOLD}→  {msg}{Colors.RESET}")

class RAGVerification:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def verify_python_packages(self):
        """Verify required Python packages are installed"""
        print_header("STEP 1: Python Packages Verification")
        
        packages = {
            'fastapi': 'FastAPI (Web Framework)',
            'unstructured': 'Unstructured (Document Parser)',
            'chromadb': 'Chroma (Vector DB)',
            'sentence_transformers': 'Sentence Transformers (Embeddings)',
            'sqlalchemy': 'SQLAlchemy (ORM)',
            'websockets': 'WebSockets (Streaming)',
        }
        
        for pkg, desc in packages.items():
            try:
                __import__(pkg)
                print_success(f"{desc} installed")
                self.passed.append(pkg)
            except ImportError:
                print_error(f"{desc} NOT installed")
                print_instruction(f"Run: pip install {pkg}")
                self.failed.append(pkg)
    
    def verify_database_setup(self):
        """Verify SQLite database and migrations"""
        print_header("STEP 2: Database Setup Verification")
        
        db_path = Path("vector_store/registry.db")
        
        if db_path.exists():
            print_success(f"Database file exists: {db_path}")
            
            try:
                import sqlite3
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Check tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                if tables:
                    print_success(f"Database tables: {', '.join(tables)}")
                    
                    if 'documents' in tables:
                        cursor.execute("SELECT COUNT(*) FROM documents;")
                        count = cursor.fetchone()[0]
                        print_success(f"Documents table has {count} documents")
                        self.passed.append("database_documents_table")
                    else:
                        print_error("'documents' table not found")
                        print_instruction("Run: python -m alembic upgrade head")
                        self.failed.append("database_documents_table")
                else:
                    print_error("No tables in database")
                    print_instruction("Run: python -m alembic upgrade head")
                    self.failed.append("database_tables")
                
                conn.close()
                
            except Exception as e:
                print_error(f"Database error: {e}")
                self.failed.append("database_check")
        else:
            print_warning(f"Database file not found at {db_path}")
            print_instruction("Run alembic migrations: python -m alembic upgrade head")
            self.warnings.append("database_missing")
    
    def verify_code_fixes(self):
        """Verify code fixes have been applied"""
        print_header("STEP 3: Code Fixes Verification")
        
        fixes = {
            'chatbot/bot/memory/vector_database/chroma.py': {
                'name': 'Chroma - clean() function fix',
                'search_for': 'clean(doc.page_content)',
                'should_contain': ['def from_chunks', 'clean_content'],
                'should_not_contain': ['no_emoji=True']
            },
            'backend/api/endpoints/documents.py': {
                'name': 'Documents API - database query fix',
                'search_for': 'def list_documents',
                'should_contain': ['registry.get_all', 'GET /documents'],
                'should_not_contain': []
            },
            'frontend/src/services/api.ts': {
                'name': 'Frontend API - timeout fix',
                'search_for': 'uploadDocument',
                'should_contain': ['timeout: 300000', 'multipart'],
                'should_not_contain': []
            }
        }
        
        for filepath, check in fixes.items():
            try:
                path = Path(filepath)
                if not path.exists():
                    print_warning(f"File not found: {filepath}")
                    self.warnings.append(f"file_missing_{filepath}")
                    continue
                
                content = path.read_text()
                
                found_search = check['search_for'] in content
                has_all_required = all(item in content for item in check['should_contain'])
                has_forbidden = any(item in content for item in check['should_not_contain'])
                
                if found_search and has_all_required and not has_forbidden:
                    print_success(f"{check['name']}")
                    self.passed.append(f"fix_{filepath}")
                else:
                    print_error(f"{check['name']}")
                    if not found_search:
                        print_instruction(f"  Missing: {check['search_for']}")
                    if not has_all_required:
                        print_instruction(f"  Missing required: {check['should_contain']}")
                    if has_forbidden:
                        print_instruction(f"  Remove: {check['should_not_contain']}")
                    self.failed.append(f"fix_{filepath}")
                    
            except Exception as e:
                print_error(f"Error checking {filepath}: {e}")
                self.failed.append(f"fix_{filepath}")
    
    def verify_vector_database(self):
        """Verify Chroma vector database"""
        print_header("STEP 4: Vector Database Verification")
        
        chroma_path = Path("chroma_db")
        
        if chroma_path.exists():
            print_success(f"Vector store directory exists: {chroma_path}")
            
            # Count files
            files = list(chroma_path.glob("**/*"))
            print_success(f"Contains {len(files)} files/directories")
            
            try:
                from chatbot.bot.memory.vector_database.chroma import Chroma
                from backend.core.config import settings
                
                idx = Chroma(db_path=settings.VECTOR_STORE_PATH)
                indexed = idx.get_indexed_documents()
                
                if len(indexed) > 0:
                    print_success(f"Vector database indexed: {len(indexed)} chunks")
                    self.passed.append("vector_db_indexed")
                else:
                    print_warning(f"Vector database empty - no documents indexed yet")
                    print_instruction("Upload a document to index embeddings")
                    self.warnings.append("vector_db_empty")
                    
            except Exception as e:
                print_error(f"Vector database error: {e}")
                self.failed.append("vector_db_access")
        else:
            print_warning(f"Vector store directory not found: {chroma_path}")
            print_instruction("Upload a document to initialize vector database")
            self.warnings.append("vector_db_missing")
    
    def verify_backend_running(self):
        """Check if backend is running"""
        print_header("STEP 5: Backend Service Check")
        
        try:
            import requests
            resp = requests.get("http://localhost:8000/health", timeout=5)
            
            if resp.status_code == 200:
                print_success("Backend is running at http://localhost:8000")
                
                # Check endpoints
                endpoints = [
                    ("/documents", "GET", "List documents"),
                    ("/chat", "GET", "Chat endpoint")
                ]
                
                for endpoint, method, desc in endpoints:
                    try:
                        if method == "GET":
                            r = requests.get(f"http://localhost:8000{endpoint}", timeout=2)
                            if r.status_code in [200, 405]:
                                print_success(f"Endpoint available: {desc}")
                    except:
                        pass
                
                self.passed.append("backend_running")
            else:
                print_error(f"Backend returned: {resp.status_code}")
                self.failed.append("backend_running")
                
        except requests.exceptions.ConnectionError:
            print_error("Backend not running on localhost:8000")
            print_instruction("Start backend: python -m uvicorn backend.main:app --reload --port 8000")
            self.failed.append("backend_running")
        except Exception as e:
            print_error(f"Backend check error: {e}")
            self.warnings.append("backend_check_error")
    
    def verify_frontend_ready(self):
        """Check if frontend is ready"""
        print_header("STEP 6: Frontend Build Check")
        
        frontend_path = Path("frontend")
        
        if frontend_path.exists():
            print_success("Frontend directory exists")
            
            pkg_json = frontend_path / "package.json"
            if pkg_json.exists():
                try:
                    import json
                    data = json.loads(pkg_json.read_text())
                    print_success(f"Frontend project: {data.get('name', 'Unknown')}")
                    print_info("Frontend ready to start with: npm run dev")
                    self.passed.append("frontend_setup")
                except:
                    print_warning("Could not parse package.json")
            else:
                print_error("package.json not found")
                self.failed.append("frontend_setup")
        else:
            print_error("Frontend directory not found")
            self.failed.append("frontend_setup")
    
    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        
        total_passed = len(self.passed)
        total_failed = len(self.failed)
        total_warnings = len(self.warnings)
        
        print(f"{Colors.GREEN}✅ Passed: {total_passed}{Colors.RESET}")
        print(f"{Colors.RED}❌ Failed: {total_failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}⚠️  Warnings: {total_warnings}{Colors.RESET}")
        
        if total_failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL CHECKS PASSED!{Colors.RESET}")
            print(f"Your RAG chatbot is ready to use!")
            return True
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}⚠️  SOME CHECKS FAILED{Colors.RESET}")
            print(f"Please fix the issues above and re-run this verification.")
            return False
    
    def run_all(self):
        """Run all verifications"""
        print(f"{Colors.BOLD}{Colors.BLUE}")
        print("""
╔══════════════════════════════════════════════════════════════════╗
║     RAG CHATBOT - COMPREHENSIVE VERIFICATION SCRIPT              ║
║                                                                  ║
║  This script checks all components and confirms fixes applied   ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        print(Colors.RESET)
        
        self.verify_python_packages()
        self.verify_database_setup()
        self.verify_code_fixes()
        self.verify_vector_database()
        self.verify_backend_running()
        self.verify_frontend_ready()
        
        success = self.print_summary()
        
        print("\n" + "="*70)
        print("NEXT STEPS")
        print("="*70)
        
        if success:
            print("""
1. Start backend (if not running):
   python -m uvicorn backend.main:app --reload --port 8000

2. Start frontend:
   cd frontend && npm run dev

3. Open browser:
   http://localhost:5173

4. Upload a document to test the RAG pipeline
            """)
        else:
            print("""
1. Review failed checks above
2. Apply necessary fixes from FIX_IMPLEMENTATIONS.py
3. Re-run this verification script
4. Check QUICK_FIX_GUIDE.md for troubleshooting
            """)
        
        return success


if __name__ == "__main__":
    verifier = RAGVerification()
    success = verifier.run_all()
    sys.exit(0 if success else 1)
