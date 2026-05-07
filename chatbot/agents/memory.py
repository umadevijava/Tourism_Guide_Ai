"""Agent memory management system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
import json


class MemoryType(Enum):
    """Types of agent memory."""
    CONVERSATION = "conversation"  # Chat history and interactions
    TASK = "task"  # Current task information and progress
    KNOWLEDGE = "knowledge"  # Facts and information learned
    FEEDBACK = "feedback"  # Feedback from observations
    GOAL = "goal"  # Goal-related information
    DECISION = "decision"  # Decision history and reasoning
    TOOL_CALL = "tool_call"  # Tool usage history


@dataclass
class MemoryEntry:
    """A single entry in agent memory."""
    key: str
    value: Any
    memory_type: MemoryType
    timestamp: datetime
    source_agent: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5  # 0-1 importance score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory entry to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source_agent": self.source_agent,
            "importance": self.importance,
            "metadata": self.metadata,
        }


class AgentMemory:
    """Manages memory for agents."""
    
    def __init__(self, max_entries_per_type: int = 100):
        """
        Initialize agent memory.
        
        Args:
            max_entries_per_type: Maximum entries to keep per memory type
        """
        self.memory: Dict[MemoryType, List[MemoryEntry]] = {
            mem_type: [] for mem_type in MemoryType
        }
        self.max_entries_per_type = max_entries_per_type
        self.memories_index: Dict[str, MemoryEntry] = {}  # key -> entry mapping
    
    def store(
        self,
        key: str,
        value: Any,
        memory_type: MemoryType,
        source_agent: str,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store information in memory.
        
        Args:
            key: Unique key for this memory entry
            value: The value to store
            memory_type: Type of memory
            source_agent: ID of the agent storing this
            importance: Importance score (0-1)
            metadata: Optional metadata
        """
        entry = MemoryEntry(
            key=key,
            value=value,
            memory_type=memory_type,
            timestamp=datetime.now(),
            source_agent=source_agent,
            metadata=metadata or {},
            importance=importance,
        )
        
        # Store in memory list
        self.memory[memory_type].append(entry)
        self.memories_index[key] = entry
        
        # Enforce max entries per type (keep most important)
        if len(self.memory[memory_type]) > self.max_entries_per_type:
            # Sort by importance and timestamp, keep top entries
            self.memory[memory_type].sort(
                key=lambda x: (-x.importance, -x.timestamp.timestamp())
            )
            removed_entries = self.memory[memory_type][self.max_entries_per_type:]
            self.memory[memory_type] = self.memory[memory_type][:self.max_entries_per_type]
            
            # Remove from index
            for entry in removed_entries:
                if entry.key in self.memories_index:
                    del self.memories_index[entry.key]
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from memory by key.
        
        Args:
            key: The memory key
            
        Returns:
            The stored value or None if not found
        """
        entry = self.memories_index.get(key)
        return entry.value if entry else None
    
    def retrieve_by_type(self, memory_type: MemoryType, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve all memories of a specific type.
        
        Args:
            memory_type: Type of memory to retrieve
            limit: Maximum number to return
            
        Returns:
            List of memory entries
        """
        entries = self.memory[memory_type][-limit:]
        return [entry.to_dict() for entry in entries]
    
    def search(self, query: str, memory_type: Optional[MemoryType] = None) -> List[Dict[str, Any]]:
        """
        Search memory by key or content.
        
        Args:
            query: Search query
            memory_type: Optional type filter
            
        Returns:
            List of matching memory entries
        """
        results = []
        query_lower = query.lower()
        
        types_to_search = [memory_type] if memory_type else list(MemoryType)
        
        for mem_type in types_to_search:
            for entry in self.memory[mem_type]:
                if (query_lower in entry.key.lower() or
                    (isinstance(entry.value, str) and query_lower in entry.value.lower())):
                    results.append(entry.to_dict())
        
        # Sort by importance and timestamp
        results.sort(key=lambda x: (-x["importance"], -datetime.fromisoformat(x["timestamp"]).timestamp()))
        return results
    
    def get_conversation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.retrieve_by_type(MemoryType.CONVERSATION, limit)
    
    def get_task_context(self) -> Dict[str, Any]:
        """Get current task context from memory."""
        entries = self.memory[MemoryType.TASK]
        if not entries:
            return {}
        
        return {
            "current_task": entries[-1].value if entries else None,
            "task_history": [e.to_dict() for e in entries],
        }
    
    def get_recent_decisions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent decisions made by agents."""
        return self.retrieve_by_type(MemoryType.DECISION, limit)
    
    def get_feedback_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get feedback history."""
        return self.retrieve_by_type(MemoryType.FEEDBACK, limit)
    
    def clear(self) -> None:
        """Clear all memory."""
        for mem_type in MemoryType:
            self.memory[mem_type] = []
        self.memories_index = {}
    
    def clear_by_type(self, memory_type: MemoryType) -> None:
        """Clear memory of a specific type."""
        entries_to_remove = self.memory[memory_type]
        for entry in entries_to_remove:
            if entry.key in self.memories_index:
                del self.memories_index[entry.key]
        self.memory[memory_type] = []
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary of memory usage."""
        return {
            mem_type.value: len(entries)
            for mem_type, entries in self.memory.items()
        }
    
    def export(self) -> Dict[str, Any]:
        """Export all memory as dictionary."""
        return {
            "memory": {
                mem_type.value: [e.to_dict() for e in entries]
                for mem_type, entries in self.memory.items()
            },
            "summary": self.get_summary(),
        }
