"""Agent orchestrator for coordinating multi-agent workflows."""

from typing import Any, Dict, List, Optional, AsyncIterator
from datetime import datetime
import json

from chatbot.agents.base_agent import BaseAgent, AgentRole
from chatbot.agents.specialized_agents import (
    PlannerAgent,
    ReasonerAgent,
    ExecutorAgent,
    MemoryAgent,
)
from chatbot.agents.tool_registry import ToolRegistry
from chatbot.agents.memory import AgentMemory, MemoryType
from chatbot.helpers.log import get_logger

logger = get_logger(__name__)


class WorkflowPhase:
    """Represents a phase in the agent workflow."""
    
    def __init__(self, name: str, agents: List[BaseAgent]):
        """
        Initialize workflow phase.
        
        Args:
            name: Name of the phase
            agents: List of agents to execute in this phase
        """
        self.name = name
        self.agents = agents
        self.results: Dict[str, Any] = {}
        self.completed = False


class AgentOrchestrator:
    """Orchestrates multi-agent workflows for complex task solving."""
    
    def __init__(self, llm_client: Any, vector_db: Any = None):
        """
        Initialize agent orchestrator.
        
        Args:
            llm_client: Language model client for agents
            vector_db: Vector database for knowledge retrieval
        """
        self.llm_client = llm_client
        self.vector_db = vector_db
        
        # Initialize shared resources
        self.tool_registry = ToolRegistry()
        self.shared_memory = AgentMemory()
        
        # Initialize agents
        self.agents: Dict[str, BaseAgent] = {}
        self._initialize_agents()
        
        # Workflow configuration
        self.current_workflow: Optional[List[WorkflowPhase]] = None
        self.workflow_history: List[Dict[str, Any]] = []
        self.feedback_loop_enabled = True
        self.max_iterations = 3
        
        logger.info("Agent orchestrator initialized")
    
    def _initialize_agents(self) -> None:
        """Initialize all specialized agents."""
        self.agents = {
            "planner": PlannerAgent("planner_agent", self.llm_client, self.tool_registry),
            "reasoner": ReasonerAgent("reasoner_agent", self.llm_client, self.tool_registry),
            "executor": ExecutorAgent("executor_agent", self.llm_client, self.tool_registry),
            "memory": MemoryAgent("memory_agent", self.llm_client, self.shared_memory),
        }
        
        logger.info("Initialized agents: " + ", ".join(self.agents.keys()))
    
    def create_standard_workflow(self) -> List[WorkflowPhase]:
        """Create the standard workflow: Plan -> Reason -> Execute."""
        return [
            WorkflowPhase("Planning", [self.agents["planner"]]),
            WorkflowPhase("Reasoning", [self.agents["reasoner"]]),
            WorkflowPhase("Execution", [self.agents["executor"]]),
            WorkflowPhase("Memory", [self.agents["memory"]]),
        ]
    
    async def execute_phase(
        self,
        phase: WorkflowPhase,
        task: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a workflow phase.
        
        Args:
            phase: Workflow phase to execute
            task: Current task
            context: Context from previous phases
            
        Returns:
            Phase results
        """
        logger.info(f"Executing phase: {phase.name}")
        phase_results = {"phase": phase.name, "agents": {}}
        
        for agent in phase.agents:
            logger.info(f"  Running agent: {agent.agent_id}")
            
            try:
                result = await agent.process(task, context)
                phase_results["agents"][agent.agent_id] = result
                
                # Store thought chain in memory
                for thought in agent.thought_chain:
                    self.shared_memory.store(
                        key=f"{agent.agent_id}_thought_{datetime.now().timestamp()}",
                        value=thought.thought,
                        memory_type=MemoryType.DECISION,
                        source_agent=agent.agent_id,
                        importance=thought.confidence,
                    )
                
            except Exception as e:
                logger.error(f"Error in agent {agent.agent_id}: {str(e)}")
                phase_results["agents"][agent.agent_id] = {
                    "status": "error",
                    "error": str(e),
                }
        
        return phase_results
    
    async def process_with_feedback(
        self,
        goal: str,
        user_query: str,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process a task with feedback loops until goal is achieved.
        
        Args:
            goal: The main goal to achieve
            user_query: The user's initial query
            
        Yields:
            Workflow progress updates
        """
        logger.info(f"Starting workflow for goal: {goal}")
        
        task = {
            "goal": goal,
            "prompt": user_query,
        }
        context = {}
        iteration = 0
        
        # Main workflow loop
        self.current_workflow = self.create_standard_workflow()
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Workflow iteration: {iteration}")
            
            yield {
                "type": "workflow_start",
                "iteration": iteration,
                "goal": goal,
            }
            
            # Execute workflow phases
            phase_results = []
            for phase in self.current_workflow[:-1]:  # Skip memory phase for now
                result = await self.execute_phase(phase, task, context)
                phase_results.append(result)
                
                # Update context for next phase
                context = {
                    **context,
                    f"{phase.name.lower()}": result,
                }
                
                # Stream phase results
                yield {
                    "type": "phase_complete",
                    "phase_name": phase.name,
                    "phase_results": result,
                    "iteration": iteration,
                }
            
            # Check if goal achieved (in a real system, this would be more sophisticated)
            # For now, we'll do one iteration
            if iteration >= 1:
                break
        
        # Final memory consolidation
        memory_task = {
            "action": "consolidate",
        }
        memory_result = await self.agents["memory"].process(memory_task, context)
        
        yield {
            "type": "workflow_complete",
            "final_results": {
                "phases": phase_results,
                "memory_summary": self.shared_memory.get_summary(),
            },
            "iterations": iteration,
        }
        
        # Store workflow in history
        self.workflow_history.append({
            "timestamp": datetime.now().isoformat(),
            "goal": goal,
            "query": user_query,
            "iterations": iteration,
            "results": phase_results,
        })
    
    def get_agent_states(self) -> Dict[str, Dict[str, Any]]:
        """Get current state of all agents."""
        return {
            agent_id: agent.get_state()
            for agent_id, agent in self.agents.items()
        }
    
    def get_shared_memory(self) -> Dict[str, Any]:
        """Get shared memory state."""
        return self.shared_memory.export()
    
    def get_workflow_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow history."""
        return self.workflow_history[-limit:]
    
    async def reset(self) -> None:
        """Reset orchestrator state."""
        for agent in self.agents.values():
            await agent.reset()
        self.shared_memory.clear()
        self.current_workflow = None
        logger.info("Orchestrator reset")
    
    def add_tool(self, tool_name: str, tool_func, description: str, parameters: List[Any]) -> None:
        """
        Add a tool to the registry accessible by all agents.
        
        Args:
            tool_name: Name of the tool
            tool_func: Function to call
            description: Tool description
            parameters: List of ToolParameter objects
        """
        from chatbot.agents.tool_registry import Tool
        
        tool = Tool(
            name=tool_name,
            description=description,
            parameters=parameters,
            func=tool_func,
        )
        self.tool_registry.register(tool)
        logger.info(f"Tool registered: {tool_name}")
    
    def update_feedback(self, feedback: str, agent_id: Optional[str] = None) -> None:
        """
        Process user feedback to improve future iterations.
        
        Args:
            feedback: Feedback message
            agent_id: Optional specific agent to give feedback to
        """
        self.shared_memory.store(
            key=f"feedback_{datetime.now().timestamp()}",
            value=feedback,
            memory_type=MemoryType.FEEDBACK,
            source_agent=agent_id or "user",
            importance=0.8,
        )
        logger.info(f"Feedback stored: {feedback[:100]}")
