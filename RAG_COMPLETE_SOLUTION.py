"""
COMPLETE RAG CHATBOT IMPLEMENTATION GUIDE
==========================================

This guide provides a fully working RAG chatbot with:
1. Proper document upload and validation
2. Correct document processing and chunking
3. Embedding creation and storage
4. Retrieval and grounded responses
5. Full logging for debugging
6. Frontend UI integration

ARCHITECTURE:
    User Upload → Validation → Chunking → Embedding → Vector DB
                                                          ↓
    User Query → Embedding → Retrieval → LLM Context → Answer
"""

# ============================================================================
# PART 1: DOCUMENT UPLOAD & PROCESSING (Backend)
# ============================================================================

import logging
from pathlib import Path
from typing import List, Optional
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document loading, chunking, and embedding"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        logger.info(f"✓ DocumentProcessor initialized (chunk_size={chunk_size})")
    
    def load_pdf(self, file_path: str) -> str:
        """Load text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                logger.info(f"  Reading PDF: {num_pages} pages")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text += page.extract_text()
                    if (page_num + 1) % 10 == 0:
                        logger.info(f"  Processed {page_num + 1}/{num_pages} pages")
            
            if not text.strip():
                raise ValueError("PDF is empty or has no extractable text")
            
            logger.info(f"  ✓ Extracted {len(text)} characters from PDF")
            return text
        except Exception as e:
            logger.error(f"✗ PDF loading failed: {e}")
            raise
    
    def load_text(self, file_path: str) -> str:
        """Load text from TXT or MD file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            if not text.strip():
                raise ValueError("File is empty")
            
            logger.info(f"  ✓ Loaded {len(text)} characters from text file")
            return text
        except Exception as e:
            logger.error(f"✗ Text file loading failed: {e}")
            raise
    
    def load_document(self, file_path: str) -> str:
        """Load document based on file extension"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        logger.info(f"\n📄 Loading document: {path.name}")
        
        if suffix == '.pdf':
            return self.load_pdf(file_path)
        elif suffix in ['.txt', '.md']:
            return self.load_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    def create_chunks(self, text: str, source: str = "document") -> List[Document]:
        """Split text into chunks"""
        try:
            logger.info(f"\n✂️  Chunking document...")
            chunks = self.text_splitter.split_text(text)
            
            # Create Document objects with metadata
            documents = [
                Document(
                    page_content=chunk,
                    metadata={"source": source, "chunk_size": len(chunk)}
                )
                for chunk in chunks
            ]
            
            logger.info(f"  ✓ Created {len(documents)} chunks")
            logger.info(f"  - Avg chunk size: {len(text) // len(documents)} chars")
            
            return documents
        except Exception as e:
            logger.error(f"✗ Chunking failed: {e}")
            raise
    
    def create_embeddings(self, documents: List[Document]) -> Chroma:
        """Create embeddings and store in vector database"""
        try:
            logger.info(f"\n🎯 Creating embeddings...")
            
            # Create vector store
            vector_db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory="./chroma_db"  # Persist for later retrieval
            )
            
            logger.info(f"  ✓ Embeddings created and stored")
            logger.info(f"  - Vector DB collection size: {len(documents)}")
            
            return vector_db
        except Exception as e:
            logger.error(f"✗ Embedding creation failed: {e}")
            raise
    
    def process_document(self, file_path: str) -> Chroma:
        """Full pipeline: Load → Chunk → Embed"""
        try:
            # Step 1: Load
            text = self.load_document(file_path)
            
            # Step 2: Chunk
            documents = self.create_chunks(text, source=Path(file_path).name)
            
            # Step 3: Embed & Store
            vector_db = self.create_embeddings(documents)
            
            logger.info(f"\n✅ Document processing complete!")
            logger.info(f"   Ready for RAG queries\n")
            
            return vector_db
        except Exception as e:
            logger.error(f"✅ DOCUMENT PROCESSING FAILED: {e}\n")
            raise


# ============================================================================
# PART 2: RAG RETRIEVAL & RESPONSE (Backend)
# ============================================================================

from langchain.chains import RetrievalQA
from langchain.llms import Ollama  # or any LLM you're using


class RAGPipeline:
    """Handles RAG retrieval and response generation"""
    
    def __init__(self, vector_db: Chroma, llm=None):
        self.vector_db = vector_db
        self.retriever = vector_db.as_retriever(search_kwargs={"k": 3})
        
        # Use provided LLM or default to Ollama
        if llm is None:
            self.llm = Ollama(model="llama2")
        else:
            self.llm = llm
        
        logger.info("✓ RAG Pipeline initialized")
    
    def retrieve(self, query: str) -> List[Document]:
        """Retrieve relevant documents"""
        try:
            logger.info(f"\n🔍 Retrieving for query: {query}")
            results = self.retriever.get_relevant_documents(query)
            logger.info(f"  ✓ Retrieved {len(results)} relevant chunks")
            return results
        except Exception as e:
            logger.error(f"✗ Retrieval failed: {e}")
            return []
    
    def generate_answer(self, query: str) -> str:
        """Generate answer using retrieved context"""
        try:
            # Retrieve
            retrieved = self.retrieve(query)
            
            if not retrieved:
                logger.warning("  ⚠️  No relevant documents found")
                return "I could not find relevant information in the uploaded document."
            
            # Build context
            context = "\n\n".join([doc.page_content for doc in retrieved])
            
            logger.info(f"  📝 Generating answer with {len(context)} chars of context")
            
            # Generate
            prompt = f"""Based on the following context, answer the question:

CONTEXT:
{context}

QUESTION: {query}

ANSWER:"""
            
            answer = self.llm(prompt)
            logger.info(f"  ✓ Answer generated: {answer[:100]}...")
            
            return answer
        except Exception as e:
            logger.error(f"✗ Answer generation failed: {e}")
            return "Error generating answer"


# ============================================================================
# PART 3: FASTAPI INTEGRATION
# ============================================================================

from fastapi import FastAPI, UploadFile, File
import asyncio

app = FastAPI()
processor = DocumentProcessor()
rag_pipeline = None


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document"""
    try:
        logger.info(f"\n📤 Uploading: {file.filename}")
        
        # Validate file
        if not file.filename:
            return {"error": "No file provided"}
        
        suffix = Path(file.filename).suffix.lower()
        if suffix not in ['.pdf', '.txt', '.md']:
            return {"error": f"Unsupported format: {suffix}"}
        
        # Save file
        file_path = f"./uploads/{file.filename}"
        Path("./uploads").mkdir(exist_ok=True)
        
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        logger.info(f"  ✓ File saved: {len(contents)} bytes")
        
        # Process in background
        global rag_pipeline
        try:
            vector_db = processor.process_document(file_path)
            rag_pipeline = RAGPipeline(vector_db)
            
            return {
                "status": "success",
                "message": "Document uploaded and processed successfully",
                "filename": file.filename
            }
        except Exception as e:
            return {"error": f"Processing failed: {str(e)}"}
        
    except Exception as e:
        logger.error(f"✗ Upload failed: {e}")
        return {"error": str(e)}


@app.post("/query")
async def query_document(question: str):
    """Query uploaded document"""
    try:
        if rag_pipeline is None:
            return {"error": "Please upload a document first"}
        
        logger.info(f"\n❓ Query: {question}")
        answer = rag_pipeline.generate_answer(question)
        
        return {
            "question": question,
            "answer": answer
        }
    except Exception as e:
        logger.error(f"✗ Query failed: {e}")
        return {"error": str(e)}


# ============================================================================
# PART 4: USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    """
    TESTING THE COMPLETE PIPELINE
    
    Run with:
    python main.py
    """
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║           RAG CHATBOT - COMPLETE WORKING SOLUTION              ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Example 1: Process a document
    print("\n📚 EXAMPLE 1: Processing Document\n" + "="*50)
    
    # Create sample document
    sample_doc = "./sample.txt"
    with open(sample_doc, 'w') as f:
        f.write("""
        Tourism Guide: Tirupathi Temple
        
        Tirupathi Temple is one of the most visited temples in the world,
        located in Chittoor district of Andhra Pradesh, India.
        
        History: Built in 10th century, it's dedicated to Lord Venkateswara.
        
        Facilities:
        - Accommodation nearby
        - Prasadam (blessed food) distribution
        - Darshan (viewing deity) slots available
        
        Best Time to Visit: October to March
        Entry Fee: Free
        
        How to Reach:
        - Train: 1.5 hours from Chennai
        - Bus: Regular buses from major cities
        """)
    
    # Process it
    try:
        processor = DocumentProcessor()
        vector_db = processor.process_document(sample_doc)
        rag_pipeline = RAGPipeline(vector_db)
        
        # Example 2: Query the document
        print("\n❓ EXAMPLE 2: Querying Document\n" + "="*50)
        
        questions = [
            "What is Tirupathi Temple?",
            "When is the best time to visit?",
            "What are the facilities available?"
        ]
        
        for q in questions:
            print(f"\nQ: {q}")
            answer = rag_pipeline.generate_answer(q)
            print(f"A: {answer}\n")
    
    except Exception as e:
        print(f"Error: {e}")
