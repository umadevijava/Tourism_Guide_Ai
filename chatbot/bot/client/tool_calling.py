"""Tool calling integration for LLM with Google Search."""

import json
import re
from typing import Any, Optional, Dict, List
from chatbot.bot.tools.google_search import get_google_search_tool
from chatbot.helpers.log import get_logger

logger = get_logger(__name__)

# Search result cache to avoid duplicate searches
_SEARCH_CACHE = {}


class ToolCallingHandler:
    """Handles automatic tool calling for LLM responses."""
    
    def __init__(self, llm_client: Any):
        """
        Initialize tool calling handler.
        
        Args:
            llm_client: LlamaCppClient instance
        """
        self.llm_client = llm_client
        self.google_search = get_google_search_tool()
        self.max_tool_calls = 2  # Allow 2 searches for comprehensive answers
        self.call_count = 0
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "google_search",
                    "description": "Search Google for current information when you need data from external sources",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to send to Google"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "Number of results to return (1-10)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    async def handle_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a tool call.
        
        Args:
            tool_name: Name of the tool to call
            tool_input: Input parameters for the tool
            
        Returns:
            Tool output as string
        """
        if tool_name == "google_search":
            query = tool_input.get("query", "")
            num_results = tool_input.get("num_results", 5)
            
            logger.info(f"Calling Google Search: {query}")
            
            results = await self.google_search.search(query, num_results)
            
            if results.get("success"):
                # Format results nicely
                formatted = f"Found {len(results.get('results', []))} results for '{query}':\n\n"
                for i, result in enumerate(results.get("results", []), 1):
                    formatted += f"{i}. **{result.get('title', 'No title')}**\n"
                    formatted += f"   Source: {result.get('url', 'No URL')}\n"
                    formatted += f"   {result.get('snippet', 'No description')}\n\n"
                return formatted
            else:
                return f"Search failed: {results.get('error', 'Unknown error')}"
        
        return f"Unknown tool: {tool_name}"
    
    def detect_tool_need(self, prompt: str) -> bool:
        """
        Detect if the prompt needs external search for accurate information.

        Triggers search for current information, factual queries, and specific data.

        Args:
            prompt: User prompt

        Returns:
            True if search is likely needed for accurate information
        """
        prompt_lower = prompt.lower()
        
        # Keywords that definitely need search
        search_keywords = [
            "latest", "current", "recent", "today", "2024", "2025", "2026",
            "what happened", "news", "search for", "find",
            "where", "who", "when", "statistics", "data",
            "how much", "price", "rate", "weather", "stock",
            "temple", "landmark", "monument", "location", "district", "city", "place",
            "country", "region", "address", "located"
        ]
        
        # Factual query patterns that benefit from search
        factual_patterns = [
            "tell me about", "what is", "who is", "information about",
            "capital of", "location of", "population of", "known for",
            "i want to know", "can you tell", "about the"
        ]
        
        # Check if any search keyword is present
        for keyword in search_keywords:
            if keyword in prompt_lower:
                return True
        
        # Check factual patterns - these benefit from web search for accuracy
        for pattern in factual_patterns:
            if pattern in prompt_lower:
                return True
        
        return False
    
    async def process_with_tool_calling(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        use_tools: bool = True,
    ) -> Dict[str, Any]:
        """
        Process prompt with automatic tool calling support - OPTIMIZED for speed.
        
        Args:
            prompt: User prompt
            max_new_tokens: Max tokens to generate
            use_tools: Whether to use tools
            
        Returns:
            Dictionary with response and tool usage info
        """
        self.call_count = 0
        tool_results = []
        
        # Quick path: Skip tool calling if not needed (for speed)
        if use_tools and self.detect_tool_need(prompt):
            logger.info(f"Tool calling triggered for: {prompt[:50]}...")
            
            # Extract search terms and execute tools
            search_terms = self._extract_search_terms(prompt)
            
            if search_terms:
                # Use cached result if available (avoid duplicate searches)
                search_term = search_terms[0]
                cache_key = search_term.lower()
                
                if cache_key in _SEARCH_CACHE:
                    logger.info(f"Using cached search for: {search_term}")
                    result = _SEARCH_CACHE[cache_key]
                else:
                    logger.info(f"Executing Google Search for: {search_term}")
                    result = await self.google_search.search(search_term, num_results=5)
                    _SEARCH_CACHE[cache_key] = result  # Cache for future use
                
                tool_results.append({
                    "tool": "google_search",
                    "input": {"query": search_term},
                    "output": result,
                })
                
                # Add search results to context
                tool_context = self._format_tool_context(tool_results)
                prompt = f"{prompt}\n\n[Recent Web Results]\n{tool_context}"
        
        # Generate response (uses streaming internally for speed)
        response = await self.llm_client.async_generate_answer(prompt, max_new_tokens)
        
        return {
            "response": response,
            "tools_used": tool_results,
            "has_tool_calls": len(tool_results) > 0,
        }
    
    async def _detect_and_execute_tools(
        self,
        prompt: str,
        messages: List[Dict],
        tools: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Detect and execute tools based on model instruction.
        
        Args:
            prompt: Original prompt
            messages: Message history
            tools: Available tools
            
        Returns:
            List of tool execution results
        """
        tool_results = []
        
        # Strategy: Analyze the user prompt to determine what tools are needed
        # This is a heuristic approach since the model may not explicitly request tools
        
        search_terms = self._extract_search_terms(prompt)
        
        if search_terms:
            for search_term in search_terms[:self.max_tool_calls]:
                logger.info(f"Auto-executing Google Search for: {search_term}")
                
                result = await self.google_search.search(search_term, num_results=5)
                
                tool_results.append({
                    "tool": "google_search",
                    "input": {"query": search_term},
                    "output": result,
                })
                
                self.call_count += 1
                if self.call_count >= self.max_tool_calls:
                    break
        
        return tool_results
    
    def _extract_search_terms(self, prompt: str) -> List[str]:
        """
        Extract potential search terms from prompt for accurate web search.
        
        Args:
            prompt: User prompt
            
        Returns:
            List of search terms
        """
        search_terms = []
        
        # Look for common question patterns - IMPROVED with more patterns
        patterns = [
            (r"who is (.+?)\?", 1),  # Who is X?
            (r"what is (.+?)\?", 1),  # What is X?
            (r"where is (.+?)\?", 1),  # Where is X?
            (r"tell me about (.+?)[\.\?]", 1),  # Tell me about X
            (r"information about (.+?)[\.\?]", 1),  # Information about X
            (r"give.*?information about (.+?)[\.\?]", 1),  # Give me information about X
            (r"find (.+?)[\.\?]", 1),  # Find X
            (r"search for (.+?)[\.\?]", 1),  # Search for X
            (r"latest ([^\.]+)", 1),  # Latest X
            (r"current ([^\.]+)", 1),  # Current X
            (r"what about (.+?)[\.\?]", 1),  # What about X
            (r"details about (.+?)[\.\?]", 1),  # Details about X
        ]
        
        for pattern, group in patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            search_terms.extend([m.strip() for m in matches])
        
        # If no specific patterns found, but keywords suggest search needed
        if not search_terms:
            # Use entire prompt if it's a question
            if "?" in prompt:
                # Extract main topic from the question
                words = [w for w in prompt.split() if len(w) > 3]
                if words:
                    search_terms = [" ".join(words[:5])]  # First 5 words
        
        # Clean and validate search terms
        search_terms = [term.strip() for term in search_terms if term.strip()]
        return search_terms
    
    def _format_tool_context(self, tool_results: List[Dict]) -> str:
        """
        Format tool results as context for the model.
        
        Args:
            tool_results: List of tool execution results
            
        Returns:
            Formatted string for the model
        """
        context = ""
        
        for result in tool_results:
            tool_name = result.get("tool", "unknown")
            output = result.get("output", {})
            
            if tool_name == "google_search":
                context += f"**Search Results for '{result['input'].get('query')}':**\n"
                
                if output.get("success"):
                    for item in output.get("results", []):
                        context += f"- {item.get('title', 'No title')}: {item.get('snippet', 'No description')}\n"
                        context += f"  Source: {item.get('url', 'No URL')}\n"
                else:
                    context += f"Search failed: {output.get('error', 'Unknown error')}\n"
                
                context += "\n"
        
        return context
    
    @staticmethod
    def _get_system_prompt() -> str:
        """System prompt: Help and accuracy with search results priority for factual queries."""
        return """You are a helpful, knowledgeable AI assistant.

CRITICAL FOR ACCURACY - FACTUAL QUERIES:
When search results are provided about locations, temples, districts, cities, or specific places:
ALWAYS use search results as your authoritative source.
Do NOT rely on training data that may be outdated.

EXAMPLES:
Q: "Where is Indrakiladri Temple?" 
Search result: "In Vijayawada, Krishna district"
Answer: "Indrakiladri Temple is located in Vijayawada, Krishna district, Andhra Pradesh. (based on current information)"

Q: "Tell me about Indrakiladri Temple"
Search results: [information about the temple in Vijayawada]
Answer: "Indrakiladri Temple is prominently located in Vijayawada, Krishna district. It is dedicated to Goddess Durga..."

YOUR GUIDELINES:
1. Always provide complete, helpful answers
2. For location/landmark/district queries: Search results are AUTHORITATIVE
3. If search results conflict with knowledge: Prioritize search (more current)
4. Be direct, comprehensive, conversational
5. Never say "I don't know" - always provide answers
6. For factual claims from search: Say "According to information found..."
7. Always cite location and district correctly based on search results

Be accurate. Be helpful. Be current."""


def process_response_with_tools(
    response: str,
    tool_results: Dict[str, Any],
) -> str:
    """
    Process model response and integrate tool results.
    
    Args:
        response: Model-generated response
        tool_results: Tool execution results
        
    Returns:
        Final response with tool results integrated
    """
    if not tool_results.get("tools_used"):
        return response
    
    # Enhance response with tool results
    enhanced = response
    
    for tool_result in tool_results.get("tools_used", []):
        if tool_result["tool"] == "google_search":
            query = tool_result["input"].get("query", "")
            output = tool_result["output"]
            
            if output.get("success"):
                enhanced += f"\n\n**Source:** Search results for '{query}'"
    
    return enhanced
