"""Base agent class and agent state management."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class AgentRole(Enum):
    """Enumeration of agent roles."""
    PLANNER = "planner"
    REASONER = "reasoner"
    EXECUTOR = "executor"
    MEMORY_MANAGER = "memory_manager"
    COORDINATOR = "coordinator"


class AgentState(Enum):
    """Enumeration of agent states."""
    IDLE = "idle"
    PLANNING = "planning"
    REASONING = "reasoning"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentThought:
    """Represents a single thought/reasoning step from an agent."""
    agent_id: str
    agent_role: AgentRole
    timestamp: datetime
    thought: str
    confidence: float = 0.5  # 0-1 confidence score
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentAction:
    """Represents an action an agent intends to take."""
    agent_id: str
    agent_role: AgentRole
    timestamp: datetime
    action_type: str  # tool_call, message, decision, etc.
    action_description: str
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentObservation:
    """Represents an observation/feedback from an action."""
    agent_id: str
    timestamp: datetime
    observation: str
    observation_type: str  # success, failure, partial, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system."""

    def __init__(self, agent_id: str, role: AgentRole, llm_client: Any):
        """
        Initialize a base agent.
        
        Args:
            agent_id: Unique identifier for the agent
            role: The role/purpose of this agent
            llm_client: The language model client for reasoning
        """
        self.agent_id = agent_id
        self.role = role
        self.llm_client = llm_client
        self.state = AgentState.IDLE
        self.current_task = None
        self.task_history: List[Dict[str, Any]] = []
        self.thought_chain: List[AgentThought] = []
        self.action_chain: List[AgentAction] = []
        self.observations: List[AgentObservation] = []

    @abstractmethod
    async def process(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task. Must be implemented by subclasses.
        
        Args:
            task: The task to process
            context: Context information (chat history, memory, etc.)
            
        Returns:
            Result dictionary with output and status
        """
        pass

    @abstractmethod
    async def think(self, prompt: str) -> AgentThought:
        """
        Generate a thought/reasoning step.
        
        Args:
            prompt: The prompt to reason about
            
        Returns:
            AgentThought object with the reasoning
        """
        pass

    def add_thought(self, thought: AgentThought) -> None:
        """Add a thought to the thought chain."""
        self.thought_chain.append(thought)

    def add_action(self, action: AgentAction) -> None:
        """Add an action to the action chain."""
        self.action_chain.append(action)

    def add_observation(self, observation: AgentObservation) -> None:
        """Add an observation to the observations list."""
        self.observations.append(observation)

    def set_state(self, state: AgentState) -> None:
        """Update agent state."""
        self.state = state

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state and history."""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "state": self.state.value,
            "current_task": self.current_task,
            "thoughts": [
                {
                    "timestamp": t.timestamp.isoformat(),
                    "thought": t.thought,
                    "confidence": t.confidence,
                    "metadata": t.metadata,
                }
                for t in self.thought_chain
            ],
            "actions": [
                {
                    "timestamp": a.timestamp.isoformat(),
                    "action_type": a.action_type,
                    "action_description": a.action_description,
                    "tool_name": a.tool_name,
                    "metadata": a.metadata,
                }
                for a in self.action_chain
            ],
        }

    async def reset(self) -> None:
        """Reset agent state for a new task."""
        self.state = AgentState.IDLE
        self.current_task = None
        self.thought_chain = []
        self.action_chain = []
        self.observations = []
