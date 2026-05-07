# Quick Start: Document Upload Testing

## 5-Minute Quick Test

### Prerequisites
- Backend running: `http://localhost:8000`
- Frontend running: `http://localhost:5174` (or 5173)

### Step 1: Create Test Document
Create a file named `test_travel.txt` in your Downloads folder:

```
PARIS TRAVEL GUIDE

Paris is the capital of France and the most visited city in the world.
Known as the "City of Light" or "La Ville Lumière" in French, it attracts
millions of tourists annually.

MAIN ATTRACTIONS:
- Eiffel Tower: Opened in 1889, stands 330 meters tall
- Louvre Museum: World's most visited art museum, home to Mona Lisa
- Notre-Dame Cathedral: Gothic masterpiece being restored
- Arc de Triomphe: Monument built by Napoleon
- Sacré-Cœur Basilica: White domed church in Montmartre

GETTING AROUND:
- Metro: 16 lines, fastest way to travel
- Buses: Extensive network covering entire city
- Bikes: Vélib' is Paris's bike-sharing system
- Walking: City is very walkable

BEST TIME TO VISIT:
Spring (April-May): Mild weather, fewer tourists
Summer (June-August): Warm but crowded
Fall (September-October): Pleasant weather, fewer crowds
Winter (November-March): Cold but fewer tourists, festive atmosphere

FOOD & DINING:
French cuisine is world-famous. Try:
- Croissants and pastries
- French bread (baguettes)
- Cheese varieties
- Wine from different regions

VISA & TRAVEL INFO:
- Currency: Euro (EUR)
- Language: French (English spoken in tourist areas)
- Time Zone: Europe/Paris (CET/CEST)
- Best for: History, art, food, romance
```

### Step 2: Upload the Document
1. Open: `http://localhost:5174`
2. In the chat area, find "Upload documents" button
3. Click to expand upload area
4. Either:
   - Drag `test_travel.txt` into the upload zone
   - OR Click and select from file browser
5. Watch for progress bar (0% → 100%)
6. Verify: File appears in "Ready" state below upload area

### Step 3: Query the Uploaded Document
1. In the chat input, type: `"What are the main attractions in Paris?"`
2. Press Send or click the Send button
3. Wait for response (showing "Thinking..." indicator)
4. Verify:
   - Response mentions Eiffel Tower, Louvre, etc.
   - "Source Documents:" section shows your uploaded file
   - Content preview shows text from your document

### Step 4: Multiple Queries
Try these queries to test different retrieval aspects:

**Query 1:** "What's the best time to visit Paris?"
- Expected: Should find BEST TIME TO VISIT section

**Query 2:** "How do I get around on public transportation?"
- Expected: Should find the GETTING AROUND section with Metro info

**Query 3:** "Tell me about French food"
- Expected: Should find FOOD & DINING section

**Query 4:** "What visa do I need?"
- Expected: Should find VISA & TRAVEL INFO section

### Step 5: Test Error Handling
1. Try uploading file with `.exe` extension
   - Expected: Error message "File type '.exe' not supported"
2. Try uploading the same file again
   - Expected: Error message "already exists"

### Step 6: Clean Up (Optional)
1. Hover over the uploaded document in the list
2. Click the X (delete) button
3. Verify: Document removed from list and no longer used in queries

---

## What's Happening Behind the Scenes

### Upload Flow:
```
File Selected
    ↓
Client: Validate size & type
    ↓
Client: Send FormData to POST /documents
    ↓
Backend: Validate file extension
    ↓
Backend: Check for duplicates
    ↓
Backend: Save file to disk (docs/)
    ↓
Backend: Extract text using unstructured library
    ↓
Backend: Split into chunks (500 chars each)
    ↓
Backend: Generate embeddings (all-MiniLM-L6-v2 model)
    ↓
Backend: Store embeddings in Chroma vector DB
    ↓
Backend: Register document in SQLite
    ↓
Client: Display file as "Ready"
```

### Query Flow:
```
User Types: "What are main attractions?"
    ↓
Client: Send via WebSocket
    ↓
Backend: Refine the query
    ↓
Backend: Search vector DB for similar chunks
    ├─ Searches BOTH:
    │  • Original tourism knowledge base
    │  • ALL uploaded documents
    │
Backend: Retrieve top 3 matching chunks
    ↓
Backend: Limit context to 2000 characters
    ↓
Backend: Send to LLM with context
    ↓
Backend: Stream response token-by-token
    ↓
Client: Display answer with source doc shown
```

---

## Expected File Size & Performance

| File Type | Max Size | Typical Chunks | Process Time |
|-----------|----------|---|---|
| PDF (Pages) | 10 pages | 50-100 | < 5 sec |
| DOCX | 20 pages | 80-150 | < 5 sec |
| TXT | 50KB | 30-80 | < 3 sec |
| HTML | 100KB | 100-200 | < 5 sec |

**Speed Tip:** Only upload 2-3 documents for testing. Large libraries take longer to search.

---

## Troubleshooting Quick Fixes

### ❌ Upload Button Not Appearing
- Frontend doesn't load document component
- **Fix:** Reload page (Ctrl+F5 or Cmd+Shift+R)

### ❌ File Upload Hangs at 0% or 50%
- WebSocket connection issue
- **Fix:** 
  - Check backend is running: `http://localhost:8000/health`
  - Check console (F12) for errors
  - Restart both frontend and backend

### ❌ Upload Succeeds but File Not Used in Queries
- Chunks not added to vector DB
- **Fix:**
  - Check backend logs for error messages
  - Try uploading a simple .txt file first
  - Restart backend

### ❌ File Uploaded but Error "Already Exists"
- Same filename was uploaded before
- **Fix:**
  - Delete the existing file via UI
  - OR rename file and upload again

### ❌ "File Type Not Supported" Error
- File extension not in allowed list
- **Fix:**
  - Supported: .pdf, .docx, .doc, .txt, .html, .md
  - Convert file to supported format
  - Check backend config: `ALLOWED_UPLOAD_EXTENSIONS`

---

## Advanced: Check What's Stored

### See Uploaded Documents (API)
```bash
curl http://localhost:8000/documents
```

Returns:
```json
{
  "documents": [
    {
      "document_id": "abc123...",
      "filename": "test_travel.txt",
      "size": 1234,
      "content_type": "text/plain",
      "version_hash": "xyz789..."
    }
  ]
}
```

### Check Backend Logs
Look for lines like:
```
✓ Document upload completed successfully: test_travel.txt (ID: abc123..., Chunks: 45)
```

### Check Files on Disk
Navigate to project folder → `docs` directory
- Should see: `test_travel.txt`

### Check Vector Store
Navigate to project folder → `vector_store/docs_index`
- Should contain Chroma database files
- Vector embeddings are stored here

---

## Expected Results Summary

✅ **File uploads successfully** → See progress bar to 100%  
✅ **File appears in list** → "Ready" status shown  
✅ **Queries use file content** → Response includes relevant info  
✅ **Source document shown** → "Source Documents:" displays filename  
✅ **Multiple files work** → All searchable together  
✅ **Delete removes file** → No longer in queries afterward  
✅ **Errors handled gracefully** → Clear error messages  

---

## Next Steps

Once basic testing works:

1. **Test Different Formats:**
   - Upload PDF, DOCX, HTML alongside TXT
   - Verify all work correctly

2. **Test Large Documents:**
   - Try 20+ page PDF
   - Monitor processing time and chunk count

3. **Test Edge Cases:**
   - Upload file with special characters in name
   - Upload file with mixed languages
   - Upload file with tables/charts (PDF)

4. **Performance Testing:**
   - Upload 10 documents with 50KB average
   - Run 20 different queries
   - Measure average response time
   - Verify caching improves subsequent queries

5. **Integration Testing:**
   - Test with RAG mode ON vs OFF in chat settings
   - Test switching between uploaded docs and base knowledge
   - Test chat history with document queries

---

## Support Checklist

Before reporting issues:
- [ ] Ran complete 5-minute test above
- [ ] Confirmed both servers running and accessible
- [ ] Checked browser console for JS errors (F12)
- [ ] Checked backend logs for Python errors
- [ ] Tried with simple .txt file first
- [ ] Restarted both frontend and backend
- [ ] Cleared browser cache (Ctrl+Shift+Delete)
- [ ] Verified file is readable on local machine

---

**Ready to test! Good luck! 🚀**
