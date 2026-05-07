# Tourism Guide Chatbot Integration

This document explains how to use the Tourism Guide Chatbot system prompt and templates that have been integrated into the RAG chatbot.

## Overview

The Tourism Guide system provides:
- ✅ Structured tourism responses with formatted sections
- ✅ Budget breakdown calculations
- ✅ Day-wise itinerary generation
- ✅ Accurate, context-only answers (no hallucinations)
- ✅ Multi-language support (detects user language)

## How to Enable Tourism Mode

### Option 1: Environment Variable
Set the `CHATBOT_MODE` environment variable:

```bash
export CHATBOT_MODE=tourism
# or on Windows:
set CHATBOT_MODE=tourism
```

### Option 2: .env File
Add to your `.env` file in the project root:

```
CHATBOT_MODE=tourism
```

### Option 3: Direct Configuration
Modify `backend/core/config.py` and update the Settings class:

```python
CHATBOT_MODE: str = "tourism"  # Change from "general" to "tourism"
```

## Response Format

When in tourism mode, the chatbot responds with this structure:

```
🔹 Location Overview  
[Brief description of the location]

🔹 Top Attractions  
- Attraction 1
- Attraction 2
- Attraction 3

🔹 Detailed Information  
[History, timings, entry fees]

🔹 Suggested Itinerary  
Day 1:
- Place A
- Place B

Day 2:
- Place C
- Place D

🔹 Budget Breakdown  
- Entry Fees: ₹200
- Food Cost: ₹500
- Transport Cost: ₹300
- Hotel Cost: ₹1500
- Total Budget: ₹2500

🔹 Travel Tips  
- Tip 1
- Tip 2

🔹 Sources  
[List of retrieved document sources]
```

## Query Examples

### Tourism Mode Queries

```
1. "Best places to visit in Jaipur"
2. "2-day trip plan to Goa under ₹5000"
3. "Budget travel guide for Rajasthan"
4. "Historical monuments in Delhi"
5. "Route planning for South India"
```

### Expected Behavior

- ✅ Uses only retrieved data from vector database
- ✅ Provides structured output with emoji section headers
- ✅ Includes budget breakdown for travel queries
- ✅ Suggests optimized day-wise itineraries
- ✅ Cites sources from retrieved documents
- ✅ Says "Not available based on retrieved data" if info is missing

### Non-Tourism Queries

For queries outside tourism domain:
```
Input: "How to build a web application?"
Output: "I am a Tourism Guide Chatbot. Please ask travel-related queries."
```

## System Prompt Details

**Location:** `chatbot/prompts/tourism_guide.txt`

The system prompt includes:
1. Core behavior rules emphasizing accuracy and RAG-only responses
2. Structured output format with specific sections
3. Budget estimation guidelines
4. Multi-language support instructions
5. Response style requirements
6. Failsafe for non-tourism queries

## Technical Implementation

### Files Modified/Created

1. **Created:**
   - `chatbot/prompts/tourism_guide.txt` - Tourism guide system prompt
   - `chatbot/helpers/prompt_loader.py` - Utility to load prompts from files

2. **Modified:**
   - `chatbot/bot/client/prompt.py` - Added TOURISM_SYSTEM_TEMPLATE and TOURISM_CTX_PROMPT_TEMPLATE
   - `chatbot/bot/client/lama_cpp_client.py` - Added tourism-specific methods
   - `chatbot/bot/conversation/ctx_strategy.py` - Added chatbot_mode parameter to synthesis strategies
   - `backend/core/config.py` - Added CHATBOT_MODE configuration option
   - `backend/api/services/chat_stream.py` - Pass chatbot_mode to synthesis strategy

### Key Methods

```python
# Get current system template based on mode
template = LamaCppClient.get_system_template(chatbot_mode="tourism")

# Generate context prompt with mode-aware template
prompt = llm_client.generate_ctx_prompt_with_mode(
    question="Best places in Jaipur",
    context="...",
    chatbot_mode="tourism"
)

# Load tourism guide prompt from file
from chatbot.helpers.prompt_loader import PromptLoader
tourism_guide = PromptLoader.load_tourism_guide()
```

## Testing

To test the tourism mode:

1. **Start backend in tourism mode:**
   ```bash
   export CHATBOT_MODE=tourism
   poetry run uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```

2. **Send a tourism query:**
   ```json
   {
     "text": "Plan 2-day Jaipur trip under ₹5000",
     "rag": true,
     "googleSearch": false,
     "reasoning": false
   }
   ```

3. **Expected response format:**
   - Structured sections with 🔹 emoji headers
   - Budget breakdown with cost estimates
   - Day-wise itinerary
   - Source attribution

## Switching Back to General Mode

To revert to general mode:

```bash
export CHATBOT_MODE=general
# or remove CHATBOT_MODE from .env
# or set it to "general" in the configuration
```

## Future Enhancements

Potential improvements:
- Multi-language response generation
- Real-time pricing integration
- Image-based attraction identification
- Personalized itinerary customization
- Weather-aware recommendations
- Accessibility information

## Troubleshooting

**Issue:** Tourism structure not appearing in responses

**Solution:** 
1. Verify CHATBOT_MODE is set to "tourism"
2. Check backend logs for synthesis strategy initialization
3. Ensure tourism_guide.txt file exists in `chatbot/prompts/`

**Issue:** "Not available" sections too frequent

**Solution:**
1. Improve training data in vector database
2. Ensure documents contain tourism-specific information
3. Adjust NUM_RETRIEVALS in config to get more context
