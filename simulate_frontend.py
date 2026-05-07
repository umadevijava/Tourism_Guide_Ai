import requests
from pathlib import Path
import time

# Simulate frontend upload
test_file = Path(r'D:\rag-chatbot-main (1)\rag-chatbot-main\test_large.txt')

# Create a larger test file to check timeout
test_file.write_text('This is test content. ' * 1000)  # ~22KB

print("=" * 70)
print("SIMULATING FRONTEND UPLOAD")
print("=" * 70)

print(f"\n1. File Details:")
print(f"   - Filename: {test_file.name}")
print(f"   - Size: {test_file.stat().st_size / 1024:.1f} KB")

print(f"\n2. Testing Upload with Progress:")
start_time = time.time()

def upload_with_progress(filepath):
    with open(filepath, 'rb') as f:
        files = {'file': f}
        
        # Simulate progress callback like frontend does
        try:
            response = requests.post(
                'http://127.0.0.1:8000/documents',
                files=files,
                timeout=300,  # Long timeout like frontend might have
                # Note: requests doesn't show progress unless streamed,
                # but we can measure the total time
            )
            
            elapsed = time.time() - start_time
            print(f"   - Response received in {elapsed:.1f}s")
            print(f"   - Status: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"   - Document ID: {data['document_id'][:20]}...")
                print(f"   - Filename: {data['filename']}")
                return True, data
            else:
                print(f"   - Error: {response.status_code}")
                print(f"   - Response: {response.text[:200]}")
                return False, None
                
        except requests.exceptions.Timeout:
            print(f"   - TIMEOUT after {time.time() - start_time:.1f}s")
            return False, None
        except Exception as e:
            print(f"   - ERROR: {type(e).__name__}: {str(e)}")
            return False, None

success, data = upload_with_progress(test_file)

if success:
    print(f"\n3. Verifying Upload:")
    resp = requests.get('http://127.0.0.1:8000/documents')
    docs = resp.json()['documents']
    found = any(d['filename'] == test_file.name for d in docs)
    print(f"   - Document in list: {'YES ✓' if found else 'NO ✗'}")
    
print("\n" + "=" * 70)
