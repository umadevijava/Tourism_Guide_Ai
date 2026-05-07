from pathlib import Path
from chatbot.document_loader.loader import DirectoryLoader

# Create test file
test_file_path = Path(r'D:\rag-chatbot-main (1)\rag-chatbot-main\docs\test_doc.md')
test_file_path.parent.mkdir(parents=True, exist_ok=True)
test_file_path.write_text('# Test Document\n\nThis is a test for Tirupathi temple tourism guide.')

try:
    loader = DirectoryLoader(
        path=test_file_path.parent,
        glob=test_file_path.name,
        show_progress=False,
    )
    docs = loader.load()
    print(f"Successfully loaded {len(docs)} documents")
    if docs:
        print(f"First doc content length: {len(docs[0].page_content)}")
        print(f"First doc metadata: {docs[0].metadata}")
except Exception as e:
    print(f"Error loading document: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
