import requests
from pathlib import Path
import json

# Create a test document
test_file = Path(r'D:\rag-chatbot-main (1)\rag-chatbot-main\test_upload_debug.txt')
test_file.write_text('This is a test document to check upload functionality.')

print("=" * 70)
print("TESTING DOCUMENT UPLOAD API DIRECTLY")
print("=" * 70)

# Test upload
with open(test_file, 'rb') as f:
    files = {'file': f}
    try:
        resp = requests.post('http://localhost:8000/documents', files=files, timeout=120)
        print(f"\n✓ Response Status: {resp.status_code}")
        print(f"✓ Response Headers: {dict(resp.headers)}")
        print(f"✓ Response Content-Type: {resp.headers.get('content-type')}")
        
        if resp.status_code == 201:
            print(f"\n✅ UPLOAD SUCCESS!")
            print(f"Response JSON: {resp.json()}")
        else:
            print(f"\n❌ UPLOAD FAILED!")
            print(f"Response Text: {resp.text[:500]}")
            try:
                print(f"Response JSON: {resp.json()}")
            except:
                pass
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")

# Now check what documents are in the system
print("\n" + "=" * 70)
print("CHECKING DOCUMENTS IN SYSTEM")
print("=" * 70)
resp = requests.get('http://localhost:8000/documents')
docs = resp.json()['documents']
print(f"Documents found: {len(docs)}")
for doc in docs:
    print(f"  - {doc['filename']}")
