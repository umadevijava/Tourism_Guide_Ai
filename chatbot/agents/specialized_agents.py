"""Specialized agents for multi-agent system."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from chatbot.agents.base_agent import (
    BaseAgent,
    AgentRole,
    AgentState,
    AgentThought,
    AgentAction,
    AgentObservation,
)
from chatbot.agents.tool_registry import ToolRegistry
from chatbot.agents.memory import AgentMemory, MemoryType


class PlannerAgent(BaseAgent):
    """Agent responsible for planning and breaking down goals into steps."""
    
    def __init__(self, agent_id: str, llm_client: Any, tool_registry: ToolRegistry = None):
        """Initialize planner agent."""
        super().__init__(agent_id, AgentRole.PLANNER, llm_client)
        self.tool_registry = tool_registry or ToolRegistry()
        self.memory = AgentMemory()
    
    async def think(self, prompt: str) -> AgentThought:
        """Generate planning thoughts."""
        self.set_state(AgentState.PLANNING)
        
        planning_prompt = f"""
You are a strategic planner. Analyze the user's goal and create a detailed plan.
Goal: {prompt}

Provide:
1. Clear objective
2. Key sub-tasks in logical order
3. Dependencies between tasks
4. Potential challenges
5. Success criteria

Be concise and structured.
        """
        
        thought_text = await self.llm_client.async_generate_answer(
            planning_prompt, max_new_tokens=512
        )
        
        thought = AgentThought(
            agent_id=self.agent_id,
            agent_role=self.role,
            timestamp=datetime.now(),
            thought=thought_text,
            confidence=0.8,
        )
        
        self.add_thought(thought)
        return thought
    
    async def process(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a plan for achieving the goal.
        
        Args:
            task: Goal or task to plan for
            context: Additional context information
            
        Returns:
            Plan with steps and reasoning
        """
        self.set_state(AgentState.PLANNING)
        self.current_task = task
        
        goal = task.get("goal", "")
        
        # Generate planning thought
        plan_thought = await self.think(goal)
        
        # Parse plan into steps
        planning_action = AgentAction(
            agent_id=self.agent_id,
            agent_role=self.role,
            timestamp=datetime.now(),
            action_type="planning",
            action_description="Created detailed plan for goal achievement",
        )
        self.add_action(planning_action)
        
        # Store in memory
        self.memory.store(
            key=f"plan_{datetime.now().timestamp()}",
            value=plan_thought.thought,
            memory_type=MemoryType.GOAL,
            source_agent=self.agent_id,
            importance=0.9,
        )
        
        self.set_state(AgentState.COMPLETED)
        
        return {
            "status": "success",
            "agent": self.agent_id,
            "role": self.role.value,
            "plan": plan_thought.thought,
            "thoughts": [plan_thought],
        }


class ReasonerAgent(BaseAgent):
    """Agent responsible for reasoning, analysis, and decision-making."""
    
    def __init__(self, agent_id: str, llm_client: Any, tool_registry: ToolRegistry = None):
        """Initialize reasoner agent."""
        super().__init__(agent_id, AgentRole.REASONER, llm_client)
        self.tool_registry = tool_registry or ToolRegistry()
        self.memory = AgentMemory()
    
    async def think(self, prompt: str) -> AgentThought:
        """Generate reasoning thoughts."""
        self.set_state(AgentState.REASONING)
        
        reasoning_prompt = f"""
You are a critical reasoner and analyst. Analyze the following carefully:

{prompt}

Provide:
1. Key insights
2. Pros and cons of different approaches
3. Potential risks and mitigations
4. Recommended approach with justification
5. Confidence level (0-1)

Be thorough but concise.
        """
        
        thought_text = await self.llm_client.async_generate_answer(
            reasoning_prompt, max_new_tokens=512
        )
        
        thought = AgentThought(
            agent_id=self.agent_id,
            agent_role=self.role,
            timestamp=datetime.now(),
            thought=thought_text,
            confidence=0.75,
        )
        
        self.add_thought(thought)
        return thought
    
    async def process(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze and reason about a task.
        
        Args:
            task: Task to reason about
            context: Context information including plan
            
        Returns:
            Reasoning output and decisions
        """
        self.set_state(AgentState.REASONING)
        self.current_task = task
        
        prompt = task.get("prompt", "")
        plan = context.get("plan", "")
        
        combined_prompt = f"Plan:\n{plan}\n\nTask:\n{prompt}"
        
        # Generate reasoning thought
        reasoning_thought = await self.think(combined_prompt)
        
        # Record action
        reasoning_action = AgentAction(
            agent_id=self.agent_id,
            agent_role=self.role,
            timestamp=datetime.now(),
            action_type="reasoning",
            action_description="Analyzed task and generated reasoning",
        )
        self.add_action(reasoning_action)
        
        # Store in memory
        self.memory.store(
            key=f"reasoning_{datetime.now().timestamp()}",
            value=reasoning_thought.thought,
            memory_type=MemoryType.DECISION,
            source_agent=self.agent_id,
            importance=0.85,
        )
        
        self.set_state(AgentState.COMPLETED)
        
        return {
            "status": "success",
            "agent": self.agent_id,
            "role": self.role.value,
            "reasoning": reasoning_thought.thought,
            "thoughts": [reasoning_thought],
        }


class ExecutorAgent(BaseAgent):
    """Agent responsible for executing tasks and calling tools."""
    
    def __init__(self, agent_id: str, llm_client: Any, tool_registry: ToolRegistry):
        """Initialize executor agent."""
        super().__init__(agent_id, AgentRole.EXECUTOR, llm_client)
        self.tool_registry = tool_registry
        self.memory = AgentMemory()
    
    async def think(self, prompt: str) -> AgentThought:
        """Generate execution thoughts."""
        self.set_state(AgentState.EXECUTING)
        
        execution_prompt = f"""
You are an execution manager. Determine the best tools/actions to execute this task:

{prompt}

Provide:
1. Actions to take
2. Order of execution
3. Tools needed from available: {', '.join(self.tool_registry.list_tools())}
4. Expected outcomes

Be specific and actionable.
        """
        
        thought_text = await self.llm_client.async_generate_answer(
            execution_prompt, max_new_tokens=512
        )
        
        thought = AgentThought(
            agent_id=self.agent_id,
            agent_role=self.role,
            timestamp=datetime.now(),
            thought=thought_text,
            confidence=0.7,
        )
        
        self.add_thought(thought)
        return thought
    
    async def process(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task.
        
        Args:
            task: Task to execute
            context: Context including plan and reasoning
            
        Returns:
            Execution results
        """
        self.set_state(AgentState.EXECUTING)
        self.current_task = task
        
        prompt = task.get("prompt", "")
        
        # Generate execution thought
        execution_thought = await self.think(prompt)
        
        # Record action
        execution_action = AgentAction(
            agent_id=self.agent_id,
            agent_role=self.role,
            timestamp=datetime.now(),
            action_type="execution",
            action_description="Executed task and collected results",
        )
        self.add_action(execution_action)
        
        # Store execution record in memory
        self.memory.store(
            key=f"execution_{datetime.now().timestamp()}",
            value={
                "task": prompt,
                "execution_plan": execution_thought.thought,
            },
            memory_type=MemoryType.TASK,
            source_agent=self.agent_id,
            importance=0.8,
        )
        
        self.set_state(AgentState.COMPLETED)
        
        return {
            "status": "success",
            "agent": self.agent_id,
            "role": self.role.value,
            "execution_plan": execution_thought.thought,
            "thoughts": [execution_thought],
        }


class MemoryAgent(BaseAgent):
    """Agent responsible for memory management and knowledge consolidation."""
    
    def __init__(self, agent_id: str, llm_client: Any, shared_memory: AgentMemory):
        """Initialize memory agent."""
        super().__init__(agent_id, AgentRole.MEMORY_MANAGER, llm_client)
        self.shared_memory = shared_memory
        self.memory = AgentMemory()
    
    async def think(self, prompt: str) -> AgentThought:
        """Generate memory management thoughts."""
        thought = AgentThought(
            agent_id=self.agent_id,
            agent_role=self.role,
            timestamp=datetime.now(),
            thought=f"Consolidating and organizing memory: {prompt}",
            confidence=0.9,
        )
        self.add_thought(thought)
        return thought
    
    async def process(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage and consolidate agent memory.
        
        Args:
            task: Memory management task
            context: Context information
            
        Returns:
            Memory management results
        """
        self.set_state(AgentState.EXECUTING)
        self.current_task = task
        
        action_type = task.get("action", "consolidate")  # store, retrieve, consolidate
        
        if action_type == "store":
            key = task.get("key", "")
            value = task.get("value", "")
            mem_type = MemoryType(task.get("type", "general"))
            
            self.shared_memory.store(
                key=key,
                value=value,
                memory_type=mem_type,
                source_agent=self.agent_id,
                importance=task.get("importance", 0.5),
            )
            
            result = f"Stored memory: {key}"
        
        elif action_type == "retrieve":
            key = task.get("key", "")
            value = self.shared_memory.retrieve(key)
            result = f"Retrieved: {value}"
        
        elif action_type == "consolidate":
            # Analyze memory and consolidate insights
            summary = self.shared_memory.get_summary()
            result = f"Memory consolidation complete. Summary: {summary}"
        
        else:
            result = f"Unknown action: {action_type}"
        
        memory_action = AgentAction(
            agent_id=self.agent_id,
            agent_role=self.role,
            timestamp=datetime.now(),
            action_type="memory_management",
            action_description=result,
        )
        self.add_action(memory_action)
        
        self.set_state(AgentState.COMPLETED)
        
        return {
            "status": "success",
            "agent": self.agent_id,
            "role": self.role.value,
            "result": result,
            "memory_summary": self.shared_memory.get_summary(),
        }
