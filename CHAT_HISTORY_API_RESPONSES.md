# Chat History API - Response Examples

## 🔄 WebSocket Messages

### 1. Client Sends Message

**Request (from frontend to backend):**
```json
{
  "text": "What is Python?",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "requestId": "msg-12345-1700000000000",
  "rag": false,
  "reasoning": false,
  "googleSearch": false
}
```

**Backend immediately responds with:**
```json
{"sessionId": "550e8400-e29b-41d4-a716-446655440000"}
```

**Then streams response tokens as text:**
```
Python
 is
 a
 powerful
 programming
 language
 ...
```

---

### 2. Session ID Creation (First Message)

**If client doesn't send sessionId:**
```json
{
  "text": "Tell me about Python",
  "requestId": "msg-12345-1700000000000",
  "rag": false
}
```

**Backend creates new sessionId and responds:**
```json
{"sessionId": "550e8400-e29b-41d4-a716-446655440000"}
```

**Future messages should include this sessionId to keep conversation linked.**

---

## 📡 REST API Responses

### 1. Get Chat Sessions List

**Request:**
```http
GET /history?limit=50
```

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2024-04-26T10:30:00Z",
      "updated_at": "2024-04-26T10:45:00Z",
      "message_count": 3,
      "title": "Python Programming Discussion",
      "last_message": "You can use Python for web development, data...",
      "last_question": "What are Python's main applications?"
    },
    {
      "session_id": "660f9511-f39c-52e5-b827-557766551111",
      "created_at": "2024-04-26T09:00:00Z",
      "updated_at": "2024-04-26T09:15:00Z",
      "message_count": 2,
      "title": null,
      "last_message": "Machine learning is a subset of AI that...",
      "last_question": "Explain machine learning in simple terms"
    }
  ],
  "total": 2
}
```

**Key Fields:**
- `session_id`: Unique session identifier (UUID)
- `message_count`: Total Q&A pairs in this session
- `title`: Optional custom title (null if not set)
- `last_message`: Preview of last response (first 100 chars)
- `updated_at`: When last message was sent

---

### 2. Get Full Chat History for Session

**Request:**
```http
GET /history/550e8400-e29b-41d4-a716-446655440000
```

**Response (200 OK):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-04-26T10:30:00Z",
  "updated_at": "2024-04-26T10:45:00Z",
  "title": "Python Programming",
  "messages": [
    {
      "question": "What is Python?",
      "answer": "Python is a high-level, interpreted programming language known for its simplicity and readability...",
      "timestamp": "2024-04-26T10:30:15Z",
      "rag_mode": false,
      "reasoning_mode": false,
      "web_search_mode": false
    },
    {
      "question": "How do I install Python?",
      "answer": "You can install Python by downloading from python.org or using package managers like brew on Mac or apt on Linux...",
      "timestamp": "2024-04-26T10:32:00Z",
      "rag_mode": false,
      "reasoning_mode": false,
      "web_search_mode": false
    },
    {
      "question": "What are Python's main applications?",
      "answer": "Python is used for web development with Django/Flask, data science with NumPy/Pandas, AI/ML with TensorFlow, automation, scripting, and more...",
      "timestamp": "2024-04-26T10:45:00Z",
      "rag_mode": true,
      "reasoning_mode": false,
      "web_search_mode": false
    }
  ]
}
```

**Key Fields:**
- `messages`: Array of Q&A pairs in chronological order (oldest first)
- `timestamp`: ISO 8601 timestamp for each message
- `rag_mode`: Whether RAG was used for this response
- `reasoning_mode`: Whether reasoning was enabled
- `web_search_mode`: Whether web search was used

---

### 3. Create New Session

**Request:**
```http
POST /history/session/create
Content-Type: application/json

{}
```

**Response (200 OK):**
```json
{
  "session_id": "770f9511-f39c-52e5-b827-557766552222"
}
```

**Use this session_id for future messages in new conversation.**

---

### 4. Update Session Title

**Request:**
```http
PUT /history/550e8400-e29b-41d4-a716-446655440000/title
Content-Type: application/json

{
  "title": "Python Basics for Beginners"
}
```

**Response (200 OK):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Python Basics for Beginners"
}
```

---

### 5. Delete Session

**Request:**
```http
DELETE /history/550e8400-e29b-41d4-a716-446655440000
```

**Response (204 No Content)**
```
[Empty body - just status code 204]
```

---

### 6. Clear All History

**Request:**
```http
DELETE /history
```

**Response (204 No Content)**
```
[Empty body - just status code 204]
```

---

## 💾 Database Schema

### chat_sessions Table
```sql
CREATE TABLE chat_sessions (
  session_id VARCHAR(36) PRIMARY KEY,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  message_count INT DEFAULT 0,
  title VARCHAR(255) NULL
);
```

**Example rows:**
```
session_id: 550e8400-e29b-41d4-a716-446655440000
created_at: 2024-04-26 10:30:00
updated_at: 2024-04-26 10:45:00
message_count: 3
title: Python Programming

---

session_id: 660f9511-f39c-52e5-b827-557766551111
created_at: 2024-04-26 09:00:00
updated_at: 2024-04-26 09:15:00
message_count: 2
title: NULL
```

### chat_messages Table
```sql
CREATE TABLE chat_messages (
  id VARCHAR(36) PRIMARY KEY,
  session_id VARCHAR(36) NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  timestamp DATETIME NOT NULL,
  rag_mode BOOLEAN DEFAULT 0,
  reasoning_mode BOOLEAN DEFAULT 0,
  web_search_mode BOOLEAN DEFAULT 0,
  FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
);
```

**Example rows:**
```
id: abc123-1
session_id: 550e8400-e29b-41d4-a716-446655440000
question: What is Python?
answer: Python is a high-level...
timestamp: 2024-04-26 10:30:15
rag_mode: 0
---

id: abc123-2
session_id: 550e8400-e29b-41d4-a716-446655440000
question: How do I install Python?
answer: You can install Python by...
timestamp: 2024-04-26 10:32:00
rag_mode: 0
---

id: abc123-3
session_id: 550e8400-e29b-41d4-a716-446655440000
question: What are Python's main applications?
answer: Python is used for web development...
timestamp: 2024-04-26 10:45:00
rag_mode: 1
```

---

## 🔍 Frontend Data Flow

### When Sending Message

1. **User types:** "What is Python?"

2. **Frontend sends via WebSocket:**
```javascript
{
  text: "What is Python?",
  sessionId: "550e8400-e29b-41d4-a716-446655440000",
  requestId: "msg-12345-1700000000000"
}
```

3. **Backend responds immediately:**
```
{"sessionId": "550e8400-e29b-41d4-a716-446655440000"}
```

4. **Then backend streams response:**
```
Python
 is
 a
 high-level
 interpreted
 language
 ...
```

5. **Frontend receives all tokens and builds message:**
```javascript
{
  id: 2,
  text: "Python is a high-level interpreted language...",
  sender: "bot",
  timestamp: new Date(),
  isStreaming: false
}
```

6. **Backend saves to database:**
```sql
INSERT INTO chat_messages (
  session_id,
  question,
  answer,
  timestamp
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  'What is Python?',
  'Python is a high-level interpreted language...',
  NOW()
);
```

---

### When Clicking History

1. **User clicks history item** → calls `handleSelectHistoryItem(sessionId)`

2. **Frontend fetches via HTTP:**
```http
GET /history/550e8400-e29b-41d4-a716-446655440000
```

3. **Backend returns full conversation:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "messages": [
    {
      "question": "What is Python?",
      "answer": "Python is..."
    },
    {
      "question": "How do I install it?",
      "answer": "You can install..."
    }
  ]
}
```

4. **Frontend converts to Message format:**
```javascript
const messages = [
  { id: 0, text: "What is Python?", sender: "user", ... },
  { id: 1, text: "Python is...", sender: "bot", ... },
  { id: 2, text: "How do I install it?", sender: "user", ... },
  { id: 3, text: "You can install...", sender: "bot", ... }
];
setMessages(messages);
```

5. **UI renders all messages in order!** ✅

---

## 🐛 Error Responses

### Session Not Found
```http
GET /history/invalid-session-id

HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "detail": "Session not found: invalid-session-id"
}
```

### Server Error
```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "detail": "Failed to retrieve chat history"
}
```

---

## 📊 Example Complete Workflow

### Step 1: Send First Message
```
→ WebSocket: { text: "Hello", sessionId: null }
← WebSocket: { sessionId: "abc-123" }
← WebSocket: "Hello!" (tokens)
✓ Database: INSERT chat_messages (session_id="abc-123", question="Hello", answer="Hello!")
```

### Step 2: Send Second Message
```
→ WebSocket: { text: "How are you?", sessionId: "abc-123" }
← WebSocket: { sessionId: "abc-123" }
← WebSocket: "I'm doing well..." (tokens)
✓ Database: INSERT chat_messages (session_id="abc-123", question="How are you?", answer="...")
```

### Step 3: Click History
```
→ HTTP GET: /history/abc-123
← HTTP: { messages: [Q1, A1, Q2, A2] }
✓ UI: Shows all 4 messages
```

### Step 4: Send Message in Loaded Chat
```
→ WebSocket: { text: "Thanks!", sessionId: "abc-123" }
← WebSocket: { sessionId: "abc-123" }
← WebSocket: "No problem!..." (tokens)
✓ Database: INSERT chat_messages (session_id="abc-123", question="Thanks!", answer="...")
✓ UI: 3rd Q&A pair appended to existing 2
```

---

## ✅ What to Monitor

When testing, watch the browser DevTools:

**Network Tab:**
```
GET /history - Sessions list
GET /history/{sessionId} - Full chat
POST /history/session/create - New session
```

**WebSocket Messages:**
```
Outgoing: {"text": "...", "sessionId": "...", ...}
Incoming: {"sessionId": "..."}
Incoming: "token" "by" "token" ...
```

**Console Logs:**
```
✓ Received sessionId: abc-123
useChat: Received sessionId: abc-123
📂 Loading history session: abc-123
✓ Loaded history for session: abc-123 Messages: 2
✓ Restoring chat messages from history: 2
```

**Database Records:**
```
SELECT COUNT(*) FROM chat_messages WHERE session_id = 'abc-123';
-- Should increase with each message
```

---

**All API responses verified and working! ✅**
