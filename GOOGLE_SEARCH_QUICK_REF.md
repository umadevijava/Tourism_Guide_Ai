# Google Search Tool - Quick Reference

## Enable Web Search Mode

### Frontend (User Side)
```
1. Open the chat interface
2. Toggle "Web Search" button (globe icon)
3. Ask a question that needs current data
```

### Example Queries
```
✅ "What's the latest AI news?"         → Triggers search
✅ "Who won the recent World Cup?"      → Triggers search
✅ "What are current Bitcoin prices?"   → Triggers search
❌ "Explain photosynthesis"              → No search (general knowledge)
❌ "What is Python?"                     → No search (general knowledge)
```

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│  ┌───────────────────────────────────┐  │
│  │  Mode Toggle (RAG/Reasoning/Web)  │  │
│  └───────────┬───────────────────────┘  │
│              │ webSearch: true           │
└──────────────┼──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   WebSocket Service (TypeScript)        │
│  sends: {text, googleSearch: true}      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Backend WebSocket Handler             │
│   checks: if googleSearch flag          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  stream_google_search_response()         │
│  ┌─────────────────────────────────────┐│
│  │ ToolCallingHandler                  ││
│  │ ├─ detect_tool_need()               ││
│  │ ├─ handle_tool_call()               ││
│  │ └─ process_with_tool_calling()      ││
│  └──────────┬──────────────────────────┘│
└─────────────┼──────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│    GoogleSearchTool                     │
│  ├─ _custom_search() (Google API)       │
│  ├─ _duckduckgo_search() (DuckDuckGo)   │
│  └─ _mock_search() (Demo fallback)      │
└──────────────┬──────────────────────────┘
               │
               ▼
         Search Results
               │
               ▼
    Format and integrate into
        LLM context
               │
               ▼
         Stream response
               with citations
```

## Key Classes

### GoogleSearchTool
**File**: `chatbot/bot/tools/google_search.py`

```python
class GoogleSearchTool:
    async def search(self, query: str) -> List[Dict]
    async def search_and_get_summary(self, query: str) -> str
```

### ToolCallingHandler
**File**: `chatbot/bot/client/tool_calling.py`

```python
class ToolCallingHandler:
    async def detect_tool_need(self, prompt: str) -> bool
    async def process_with_tool_calling(self, prompt: str) -> Dict
    def get_available_tools(self) -> str
```

## WebSocket Message Format

### Request (Frontend → Backend)
```json
{
  "text": "What's the latest news about AI?",
  "googleSearch": true
}
```

### Response (Backend → Frontend)
```
[Tool Usage Info]
**[Using Google Search]** - Searched for: AI news (5 results)

[Response with search context integrated]
```

## Configuration

### Max Tool Calls (Prevent Loops)
```python
# In ToolCallingHandler
self.max_tool_calls = 3
```

### Search Keywords Detected
```python
"latest", "current", "recent", "today", "news", "find",
"statistics", "data", "when", "where", "who", "what is",
"how much", "tell me about"
```

## Response Flow

```
User: "What's the latest AI news?"
  │
  ├─→ ToolCallingHandler.detect_tool_need()
  │   └─→ Finds keyword "latest" → need search
  │
  ├─→ ToolCallingHandler.handle_tool_call("google_search")
  │   └─→ GoogleSearchTool.search("AI news")
  │
  ├─→ Search results formatted
  │   └─→ "**[Using Google Search]** - Searched for: AI news (5 results)"
  │
  ├─→ Results added to LLM context
  │   └─→ LLM generates response using fresh data
  │
  └─→ Stream response to user
      └─→ User sees response with search attribution
```

## Testing Scenarios

| Query | Expected | Status |
|-------|----------|--------|
| "What's happening in tech today?" | Search triggers | ✅ Auto |
| "Latest AI breakthroughs" | Search triggers | ✅ Auto |
| "Current Bitcoin price" | Search triggers | ✅ Auto |
| "Who won 2024 World Cup?" | Search triggers | ✅ Auto |
| "Explain machine learning" | No search | ✅ No trigger |
| "Python programming basics" | No search | ✅ No trigger |

## Common Use Cases

### 1. Current Events
```
User: "What happened in the news today?"
System: Automatically searches for today's news
Result: Latest news items integrated in response
```

### 2. Real-time Data
```
User: "What are current stock prices?"
System: Automatically searches for stock data
Result: Current pricing information provided
```

### 3. Recent Statistics
```
User: "What are the latest unemployment statistics?"
System: Automatically searches for recent stats
Result: Latest statistics included in response
```

### 4. Product Information
```
User: "Tell me about the latest iPhone model"
System: Automatically searches for recent info
Result: Latest product information provided
```

## Fallback Strategy

```
Try 1: Google Custom Search API
  ├─ Success? → Use results
  └─ Fail ↓

Try 2: DuckDuckGo API (No API Key)
  ├─ Success? → Use results
  └─ Fail ↓

Try 3: Mock Results (Demo Data)
  ├─ Success? → Use demo results
  └─ Graceful degradation
```

## Performance Metrics

| Component | Typical Duration |
|-----------|-----------------|
| Keyword detection | ~10ms |
| Google Search call | ~500-1000ms |
| Result formatting | ~50ms |
| **Total overhead** | **~600-1100ms** |

## Debugging

### Enable Logging
```python
# In any file using tool calling
import logging
logging.basicConfig(level=logging.DEBUG)

# Will show:
# - Keywords detected
# - Tools invoked
# - Search results
# - Formatting steps
```

### Check Tool Execution
```python
result = await handler.process_with_tool_calling(prompt)
print(result["tools_used"])      # Which tools ran
print(result["search_results"])  # What was found
print(result["response"])        # Final response
```

## Modes Combination

### Individual Modes
- **RAG Only**: Uses uploaded documents
- **Reasoning Only**: Step-by-step analysis
- **Web Search Only**: Real-time internet data

### Combined Modes
- **RAG + Web Search**: Documents + current data
- **Reasoning + Web Search**: Analysis with fresh data
- **RAG + Reasoning**: Document analysis with steps
- **All Three**: Full-featured response

## API Key Configuration (Production)

To use real Google Search API:

```bash
export GOOGLE_API_KEY="your-key-here"
export GOOGLE_SEARCH_ENGINE_ID="your-cse-id"
```

Then restart backend - system will auto-use real API.

## Support

### FAQ

**Q: Why isn't Google Search triggering?**
A: Check if "Web Search" mode is enabled and query has trigger keywords.

**Q: Can I customize trigger keywords?**
A: Yes, edit `SEARCH_KEYWORDS` in `tool_calling.py`

**Q: What if search fails?**
A: System falls back to DuckDuckGo, then mock data.

**Q: How many searches per request?**
A: Max 3 to prevent infinite loops. Customizable via `max_tool_calls`.

**Q: Is it free?**
A: Yes - uses DuckDuckGo (free, no API key). Google API optional for production.
