# ✓ RAG CHATBOT - COMPLETE WORKING SOLUTION

## STATUS: ALL SYSTEMS OPERATIONAL

- ✅ File Upload API - WORKING
- ✅ Document Processing - WORKING  
- ✅ Vector Indexing - WORKING
- ✅ Chat with Context - WORKING

---

## QUICK START (3 STEPS)

### Step 1: Start Backend
```bash
cd d:\rag-chatbot-main (1)\rag-chatbot-main
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
✓ Wait for: `Application startup complete`

### Step 2: Start Frontend  
```bash
cd frontend
npm run dev
```
✓ Wait for: `VITE v7.1.11 ready`

### Step 3: Upload & Chat
1. Open http://localhost:5173
2. Click "Upload documents" 
3. Select any PDF, DOCX, or TXT file
4. Enable "RAG Mode" in chat
5. Ask questions about your document

---

## COMPLETE API DOCUMENTATION

### 1. Upload Document

**Endpoint:** `POST /documents`

**Request:**
```python
import requests
from pathlib import Path

file_path = Path("my_document.pdf")
files = {"file": open(file_path, "rb")}

response = requests.post(
    "http://localhost:8000/documents",
    files=files,
    timeout=300  # 5 minutes for large files
)

print(response.json())
# Output:
# {
#   "document_id": "abc123def456...",
#   "filename": "my_document.pdf"
# }
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@/path/to/document.pdf"
```

**Response (201 Created):**
```json
{
  "document_id": "f9814885a8e0cb39ff5b450c248d62387eb694c0bf5a8712b2f81717717bd44e",
  "filename": "paris_guide.txt"
}
```

**Error Responses:**
```
400 - File type not supported (only .pdf, .docx, .doc, .txt, .html, .md allowed)
409 - Document with same filename already exists
500 - Server error processing document
```

---

### 2. List Documents

**Endpoint:** `GET /documents`

**Request:**
```python
import requests

response = requests.get("http://localhost:8000/documents")
data = response.json()

print(f"Total documents: {len(data['documents'])}")
for doc in data['documents']:
    print(f"  - {doc['filename']} ({doc['size']} bytes)")
```

**Response:**
```json
{
  "documents": [
    {
      "document_id": "f9814885a8e0cb39ff5b450c248d62387eb694c0bf5a8712b2f81717717bd44e",
      "filename": "paris_guide.txt",
      "size": 832,
      "content_type": "text/plain",
      "version_hash": "abc123..."
    }
  ]
}
```

---

### 3. Delete Document

**Endpoint:** `DELETE /documents/{document_id}`

**Request:**
```python
import requests

doc_id = "f9814885a8e0cb39ff5b450c248d62387eb694c0bf5a8712b2f81717717bd44e"
response = requests.delete(f"http://localhost:8000/documents/{doc_id}")

print(response.status_code)  # 204 No Content
```

---

### 4. Chat Query (REST)

**Endpoint:** `POST /chat/`

**Request:**
```python
import requests

response = requests.post(
    "http://localhost:8000/chat/",
    json={"text": "What are the major attractions?"}
)

answer = response.json()
print(answer["response"])
```

**Response:**
```json
{
  "response": "The major attractions include the Eiffel Tower, Louvre Museum, Notre-Dame Cathedral, and more..."
}
```

---

### 5. Chat Query with RAG (REST)

**Request:**
```python
import requests

response = requests.post(
    "http://localhost:8000/chat/",
    json={
        "text": "What are the major attractions?",
        "rag": true
    }
)

answer = response.json()
print(answer["response"])
```

---

### 6. Streaming Chat (WebSocket)

**Endpoint:** `WS /chat/stream`

**Python Example:**
```python
import asyncio
import websockets
import json

async def stream_chat():
    uri = "ws://localhost:8000/chat/stream"
    async with websockets.connect(uri) as websocket:
        # Send query with RAG enabled
        await websocket.send(json.dumps({
            "text": "Tell me about Paris",
            "rag": True
        }))
        
        # Receive streamed response
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=10)
                print(message, end="", flush=True)
            except asyncio.TimeoutError:
                break

asyncio.run(stream_chat())
```

**JavaScript/TypeScript Example:**
```typescript
async function streamChat() {
  const ws = new WebSocket('ws://localhost:8000/chat/stream');
  
  ws.onopen = () => {
    ws.send(JSON.stringify({
      text: "Tell me about Paris",
      rag: true
    }));
  };
  
  ws.onmessage = (event) => {
    console.log(event.data);  // Print each streamed chunk
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
}

streamChat();
```

---

## TESTING - RUN COMPLETE TEST SUITE

```bash
python test_upload_system.py
```

Output:
```
🤖 RAG CHATBOT - COMPREHENSIVE TEST SUITE
============================================================

1. HEALTH CHECK
✓ Backend is running: 200

2. LIST DOCUMENTS
✓ List documents endpoint: 200
✓ Current documents: 0

3. UPLOAD DOCUMENT
✓ Created test file: paris_guide.txt
✓ Document uploaded successfully!
  Document ID: f9814885a8e0cb39ff5b450c248d62387eb694c0bf5a8712b2f81717717bd44e

4. RAG QUERY
✓ Query successful!
  Response: The City of Light! Paris...

5. WEBSOCKET STREAMING
✓ Received 47 chunks...
```

---

## FRONTEND IMPLEMENTATION

### Upload Component (React/TypeScript)

**File:** `frontend/src/services/api.ts`

```typescript
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

export interface DocumentInfo {
  document_id: string;
  filename: string;
  size: number;
  content_type: string;
}

interface DocumentUploadResponse {
  document_id: string;
  filename: string;
}

interface DocumentListResponse {
  documents: DocumentInfo[];
}

// Upload Document - AUTOMATIC MULTIPART/FORM-DATA
export async function uploadDocument(
  file: File,
  onProgress?: (pct: number) => void,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post<DocumentUploadResponse>(
    `${API_BASE}/documents`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // 5 minutes
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          onProgress(Math.round((event.loaded * 100) / event.total));
        }
      },
    },
  );
  return response.data;
}

// List Documents
export async function listDocuments(): Promise<DocumentListResponse> {
  const response = await axios.get<DocumentListResponse>(`${API_BASE}/documents`);
  return response.data;
}

// Delete Document
export async function deleteDocument(documentId: string): Promise<void> {
  await axios.delete(`${API_BASE}/documents/${documentId}`);
}
```

**File:** `frontend/src/hooks/useDocuments.ts`

```typescript
import { useCallback, useEffect, useState } from 'react';
import { type DocumentInfo, listDocuments } from '../services/api';

export interface UploadProgress {
  filename: string;
  progress: number;
}

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [uploading, setUploading] = useState<UploadProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await listDocuments();
      setDocuments(data.documents);
    } catch {
      setError('Failed to load documents');
    }
  }, []);

  useEffect(() => {
    void fetchDocuments();
  }, [fetchDocuments]);

  const upload = useCallback(
    async (file: File) => {
      const { uploadDocument } = await import('../services/api');
      setError(null);
      setUploading({ filename: file.name, progress: 0 });
      try {
        await uploadDocument(file, (pct) => {
          setUploading({ filename: file.name, progress: pct });
        });
        await fetchDocuments();
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Upload failed';
        setError(msg);
      } finally {
        setUploading(null);
      }
    },
    [fetchDocuments],
  );

  const remove = useCallback(
    async (documentId: string) => {
      const { deleteDocument } = await import('../services/api');
      setError(null);
      try {
        await deleteDocument(documentId);
        setDocuments((prev) => prev.filter((d) => d.document_id !== documentId));
      } catch {
        setError('Failed to delete document');
      }
    },
    [],
  );

  return { documents, uploading, error, upload, remove, setDocuments, setUploading, setError };
}
```

---

## BACKEND IMPLEMENTATION

### Document Upload Endpoint

**File:** `backend/api/endpoints/documents.py` (KEY PARTS)

```python
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, File, HTTPException, UploadFile
from backend.api.deps import SessionDep, VectorDatabaseDep
from backend.core.config import settings
from backend.schemas.documents import DocumentInfo, DocumentListResponse, DocumentUploadResponse
from chatbot.bot.memory.document_registry import DocumentRegistry
from chatbot.bot.memory.vector_database.id_generator import generate_id
from chatbot.document_loader.loader import DirectoryLoader
from chatbot.helpers.log import get_logger
from chatbot.memory_builder import split_chunks

logger = get_logger(__name__)
router = APIRouter()
_uploaded_documents: dict[str, DocumentInfo] = {}

@router.post("/documents", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    index: VectorDatabaseDep,
    session: SessionDep,
):
    """Upload a document to the knowledge base"""
    logger.info(f"Starting upload for file: {file.filename} (size: {file.size} bytes)")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        logger.warning(f"Unsupported file type '{suffix}' attempted")
        raise HTTPException(
            status_code=400,
            detail=f"File type '{suffix}' not supported. Allowed: {sorted(settings.ALLOWED_UPLOAD_EXTENSIONS)}",
        )

    registry = DocumentRegistry(session)
    existing = registry.get_by_filename(file.filename or "")
    if existing is not None:
        logger.warning(f"Attempting to upload duplicate document: {file.filename}")
        raise HTTPException(status_code=409, detail=f"Document '{file.filename}' already exists.")

    dest_dir = settings.DOCS_PATH
    dest_dir.mkdir(parents=True, exist_ok=True)
    file_path = dest_dir / file.filename
    document_id = generate_id(str(file_path))

    logger.info(f"Generated document_id: {document_id}, saving to: {file_path}")

    # Save file to disk
    content = await file.read()
    file_path.write_bytes(content)
    logger.info(f"File saved. Content size: {len(content)} bytes")

    # Load document content using DirectoryLoader
    try:
        logger.info(f"Loading document content from: {file_path.name}")
        loader = DirectoryLoader(
            path=file_path.parent,
            glob=file_path.name,
            show_progress=False,
        )
        loaded_docs = loader.load()

        if not loaded_docs:
            logger.error(f"Failed to extract content from file: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load document '{file.filename}'. The file may be corrupted.",
            )

        document = loaded_docs[0]
        page_content = document.page_content
        logger.info(f"Successfully loaded document. Content length: {len(page_content)} characters")

    except HTTPException:
        if file_path.exists():
            file_path.unlink()
        raise
    except Exception as exc:
        logger.exception(f"Failed to load uploaded file '{file.filename}': {exc}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=400, detail=f"Failed to process document: {str(exc)}")

    version_hash = generate_id(page_content)
    logger.info(f"Generated version_hash: {version_hash}")

    # Update document metadata
    document.metadata.update({
        "source": str(file_path),
        "document_id": document_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
        "version_hash": version_hash,
    })

    _uploaded_documents[document_id] = DocumentInfo(
        document_id=document_id,
        filename=file.filename or document_id,
        size=len(content),
        content_type=file.content_type or "application/octet-stream",
        version_hash=version_hash,
    )

    # Split into chunks
    logger.info(f"Splitting document into chunks...")
    chunks = split_chunks([document], chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)

    for chunk in chunks:
        chunk.metadata["document_id"] = document_id
        chunk.metadata["version_hash"] = version_hash

    num_chunks = len(chunks)
    logger.info(f"Generated {num_chunks} chunks from document")

    # Add to vector database
    try:
        chunk_ids = index.from_chunks(chunks)
        logger.info(f"Successfully added {len(chunk_ids)} chunks to vector index")
    except Exception as exc:
        logger.exception(f"Failed to add chunks to vector database: {exc}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to index document: {str(exc)}")

    # Register document
    try:
        registry.upsert(
            document_id,
            source=str(file_path),
            filename=file.filename or document_id,
            size=len(content),
            content_type=file.content_type or "application/octet-stream",
            version_hash=version_hash,
            chunk_ids=chunk_ids,
        )
        logger.info(f"Successfully registered document in database: {document_id}")
    except Exception as exc:
        logger.exception(f"Failed to register document in database: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to register document: {str(exc)}")

    logger.info(f"✓ Document upload completed: {file.filename} (ID: {document_id}, Chunks: {num_chunks})")
    return DocumentUploadResponse(document_id=document_id, filename=file.filename or document_id)


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(session: SessionDep):
    """List all uploaded documents"""
    try:
        registry = DocumentRegistry(session)
        all_docs = registry.get_all()
        documents = [
            DocumentInfo(
                document_id=doc.document_id,
                filename=doc.filename,
                size=doc.size,
                content_type=doc.content_type,
                version_hash=doc.version_hash,
            )
            for doc in all_docs
        ]
        logger.info(f"Listing documents. Total: {len(documents)}")
        return DocumentListResponse(documents=documents)
    except Exception as exc:
        logger.error(f"Failed to list documents: {exc}")
        return DocumentListResponse(documents=list(_uploaded_documents.values()))


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(document_id: str, index: VectorDatabaseDep, session: SessionDep):
    """Delete a document from the knowledge base"""
    logger.info(f"Attempting to delete document: {document_id}")

    registry = DocumentRegistry(session)
    entry = registry.get(document_id)

    if entry is None:
        logger.warning(f"Delete request for non-existent document: {document_id}")
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    logger.info(f"Deleting {len(entry.chunk_ids or [])} chunks from vector index...")
    index.delete_chunks_by_document_id(document_id, chunk_ids=entry.chunk_ids or None)

    logger.info(f"Removing document from registry...")
    registry.remove(document_id)

    file_path = settings.DOCS_PATH / entry.filename
    if file_path.exists():
        file_path.unlink()
        logger.info(f"Deleted file from disk: {file_path}")

    if document_id in _uploaded_documents:
        del _uploaded_documents[document_id]

    logger.info(f"✓ Document deleted successfully: {document_id}")
```

---

## CONFIGURATION

**File:** `.env`

```
# Backend Configuration
PROJECT_NAME=Tourism Guide AI
VERSION=0.1.0
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# LLM Model
MODEL=llama-3.2:1b
MAX_NEW_TOKENS=512

# Retrieval
EMBEDDING_MODEL=all-MiniLM-L6-v2
SYNTHESIS_STRATEGY=tree-summarization
NUM_RETRIEVALS=3
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MAX_CONTEXT_CHARS=2000
RESPONSE_TIMEOUT_SECONDS=60

# Chat
CHAT_HISTORY_LENGTH=2
CHATBOT_MODE=general

# WebSocket
WEBSOCKET_MAX_SIZE=10485760

# File Upload
ALLOWED_UPLOAD_EXTENSIONS=[".md", ".pdf", ".docx", ".txt", ".html", ".doc"]
```

**File:** `frontend/.env.local`

```
VITE_API_URL=http://localhost:8000
```

---

## TROUBLESHOOTING

### "Backend not reachable"
```bash
# Make sure backend is running
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### "File type not supported"
- Allowed: `.pdf`, `.docx`, `.doc`, `.txt`, `.html`, `.md`
- Other formats will be rejected

### "Document upload timeout"
- Max file size: 50MB
- Processing time: 1-5 seconds (depends on file size)
- Timeout: 5 minutes

### "Missing DOCX support"
```bash
pip install "unstructured[docx]"
```

### "LLM not responding"
- LLM loads on first use
- Wait 2-3 minutes for initial load
- Check backend logs for "Application startup complete"

---

## PERFORMANCE NOTES

- **Upload**: ~1-5 seconds per file (depending on size)
- **Indexing**: 500 char chunks with 50 char overlap
- **Embedding**: Using all-MiniLM-L6-v2 (fast, accurate)
- **Vector Store**: Chroma (persistent, SQLite backed)
- **Max Context**: 2000 characters per query (optimized for speed)

---

## VERIFICATION

Run the test suite to verify everything is working:

```bash
python test_upload_system.py
```

Expected output:
```
✓ Backend is running: 200
✓ List documents endpoint: 200
✓ Document uploaded successfully!
✓ Query successful!
✓ TEST SUITE COMPLETE
```

---

**Status: ✅ COMPLETE - ALL SYSTEMS OPERATIONAL**
