"""Tool registry and tool system for agent execution."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
import json


@dataclass
class ToolParameter:
    """Describes a parameter for a tool."""
    name: str
    type: str  # str, int, float, bool, list, dict
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None


@dataclass
class Tool:
    """Represents a tool that can be called by agents."""
    name: str
    description: str
    parameters: List[ToolParameter]
    func: Callable
    category: str = "general"  # knowledge_retrieval, computation, communication, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                    "enum": p.enum,
                }
                for p in self.parameters
            ],
        }


class ToolRegistry:
    """Registry for managing available tools for agents."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """
        Register a new tool.
        
        Args:
            tool: The Tool object to register
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
    
    def unregister(self, tool_name: str) -> None:
        """
        Unregister a tool.
        
        Args:
            tool_name: Name of the tool to unregister
        """
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        del self._tools[tool_name]
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool object or None if not found
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())
    
    def get_tool_specs(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get tool specifications.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of tool specification dictionaries
        """
        tools = self._tools.values()
        if category:
            tools = [t for t in tools if t.category == category]
        return [tool.to_dict() for tool in tools]
    
    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a registered tool.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Result from tool execution
            
        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        
        # Validate inputs
        required_params = {p.name for p in tool.parameters if p.required}
        provided_params = set(kwargs.keys())
        missing = required_params - provided_params
        
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")
        
        # Call the tool function
        result = tool.func(**kwargs)
        
        # Handle async functions
        if hasattr(result, '__await__'):
            result = await result
        
        return result


class DefaultTools:
    """Default tools available to all agents."""
    
    @staticmethod
    async def search_knowledge_base(query: str, top_k: int = 5, vector_db: Any = None) -> Dict[str, Any]:
        """
        Search the vector database for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            vector_db: Vector database instance
            
        Returns:
            Search results
        """
        if not vector_db:
            return {"error": "Vector database not available"}
        
        try:
            results = await vector_db.search(query, k=top_k)
            return {
                "query": query,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    async def generate_text(prompt: str, max_tokens: int = 256, llm_client: Any = None) -> Dict[str, Any]:
        """
        Generate text using the LLM.
        
        Args:
            prompt: The prompt to generate from
            max_tokens: Maximum tokens to generate
            llm_client: LLM client instance
            
        Returns:
            Generated text
        """
        if not llm_client:
            return {"error": "LLM client not available"}
        
        try:
            text = await llm_client.async_generate_answer(prompt, max_new_tokens=max_tokens)
            return {
                "prompt": prompt,
                "generated_text": text,
                "tokens_used": len(text.split()),
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    async def analyze_text(text: str, analysis_type: str = "summary") -> Dict[str, Any]:
        """
        Analyze text (extract entities, summarize, etc.).
        
        Args:
            text: Text to analyze
            analysis_type: Type of analysis (summary, entities, sentiment, etc.)
            
        Returns:
            Analysis results
        """
        # Placeholder for text analysis
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "analysis_type": analysis_type,
            "result": f"Analysis of type '{analysis_type}' completed",
        }
    
    @staticmethod
    async def store_memory(key: str, value: str, memory_type: str = "general") -> Dict[str, Any]:
        """
        Store information in agent memory.
        
        Args:
            key: Memory key
            value: Memory value
            memory_type: Type of memory
            
        Returns:
            Confirmation
        """
        return {
            "key": key,
            "memory_type": memory_type,
            "status": "stored",
        }
    
    @staticmethod
    async def retrieve_memory(key: str, memory_type: str = "general") -> Dict[str, Any]:
        """
        Retrieve information from agent memory.
        
        Args:
            key: Memory key
            memory_type: Type of memory
            
        Returns:
            Retrieved value or not found
        """
        return {
            "key": key,
            "memory_type": memory_type,
            "status": "not_found",
            "value": None,
        }
