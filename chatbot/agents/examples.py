"""
Example: Using the Multi-Agent System
======================================

This file demonstrates how to use the multi-agent system programmatically.
"""

import asyncio
from pathlib import Path
from chatbot.agents.orchestrator import AgentOrchestrator
from chatbot.agents.tool_registry import Tool, ToolParameter
from chatbot.bot.client.lama_cpp_client import LamaCppClient
from chatbot.bot.model.model_registry import get_model_settings
from chatbot.helpers.log import get_logger

logger = get_logger(__name__)


async def example_1_basic_workflow():
    """Example 1: Execute a basic multi-agent workflow."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Multi-Agent Workflow")
    print("="*60)
    
    # Initialize LLM
    model_settings = get_model_settings("Llama-3.2-1B")
    model_folder = Path("models")
    llm_client = LamaCppClient(model_folder, model_settings)
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(llm_client)
    
    # Execute workflow
    goal = "Analyze the effectiveness of renewable energy solutions"
    query = "What are the key benefits and challenges of renewable energy?"
    
    async for update in orchestrator.process_with_feedback(goal, query):
        print(f"\nUpdate Type: {update['type']}")
        
        if update["type"] == "workflow_start":
            print(f"  Starting workflow iteration {update.get('iteration')}")
            print(f"  Goal: {update.get('goal')}")
        
        elif update["type"] == "phase_complete":
            print(f"  Phase Complete: {update.get('phase_name')}")
            results = update.get('phase_results', {})
            for agent_id, result in results.get('agents', {}).items():
                if result.get('status') == 'success':
                    print(f"    ✓ {agent_id} finished successfully")
                else:
                    print(f"    ✗ {agent_id} encountered an error")
        
        elif update["type"] == "workflow_complete":
            print(f"  ✓ Workflow Complete!")
            print(f"  Total iterations: {update.get('iterations')}")
            print(f"  Memory summary: {update.get('final_results', {}).get('memory_summary')}")
    
    # Print agent states
    print("\n--- Agent States ---")
    agent_states = orchestrator.get_agent_states()
    for agent_id, state in agent_states.items():
        print(f"\n{agent_id}:")
        print(f"  State: {state['state']}")
        print(f"  Thoughts: {len(state['thoughts'])}")
        print(f"  Actions: {len(state['actions'])}")


async def example_2_custom_tools():
    """Example 2: Register custom tools for agents."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Custom Tools Registration")
    print("="*60)
    
    # Initialize LLM
    model_settings = get_model_settings("Llama-3.2-1B")
    model_folder = Path("models")
    llm_client = LamaCppClient(model_folder, model_settings)
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(llm_client)
    
    # Define custom tool function
    async def calculate_renewable_percentage(total_energy: float, renewable_energy: float):
        """Calculate the percentage of renewable energy."""
        if total_energy == 0:
            return {"error": "Total energy cannot be zero"}
        percentage = (renewable_energy / total_energy) * 100
        return {"percentage": percentage, "renewable": renewable_energy, "total": total_energy}
    
    # Register custom tool
    orchestrator.add_tool(
        tool_name="calculate_renewable_percentage",
        tool_func=calculate_renewable_percentage,
        description="Calculate the percentage of renewable energy from total energy",
        parameters=[
            ToolParameter(
                name="total_energy",
                type="float",
                description="Total energy consumption",
                required=True
            ),
            ToolParameter(
                name="renewable_energy",
                type="float",
                description="Renewable energy portion",
                required=True
            ),
        ]
    )
    
    print("✓ Custom tool registered: calculate_renewable_percentage")
    print(f"  Available tools: {orchestrator.tool_registry.list_tools()}")


async def example_3_memory_management():
    """Example 3: Access and manage agent memory."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Memory Management")
    print("="*60)
    
    # Initialize LLM
    model_settings = get_model_settings("Llama-3.2-1B")
    model_folder = Path("models")
    llm_client = LamaCppClient(model_folder, model_settings)
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(llm_client)
    
    # Execute a workflow
    goal = "Research renewable energy"
    query = "What's the latest in solar technology?"
    
    async for update in orchestrator.process_with_feedback(goal, query):
        if update["type"] == "workflow_complete":
            break
    
    # Access memory
    print("\n--- Memory State ---")
    memory_summary = orchestrator.shared_memory.get_summary()
    print(f"Memory Summary: {memory_summary}")
    
    # Retrieve conversation history
    print("\n--- Conversation History ---")
    conversation = orchestrator.shared_memory.get_conversation_history(limit=5)
    for entry in conversation:
        print(f"  [{entry['timestamp']}] {entry['memory_type']}: {entry['value'][:50]}...")
    
    # Search memory
    print("\n--- Memory Search ---")
    results = orchestrator.shared_memory.search("renewable energy")
    print(f"Found {len(results)} relevant entries")
    for entry in results[:3]:
        print(f"  - [{entry['source_agent']}] {entry['value'][:50]}...")


async def example_4_feedback_loop():
    """Example 4: Use feedback loops to improve agent performance."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Feedback Loops")
    print("="*60)
    
    # Initialize LLM
    model_settings = get_model_settings("Llama-3.2-1B")
    model_folder = Path("models")
    llm_client = LamaCppClient(model_folder, model_settings)
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(llm_client)
    
    goal = "Create a plan for a green energy transition"
    query = "How should a country transition to green energy?"
    
    # Execute workflow
    async for update in orchestrator.process_with_feedback(goal, query):
        if update["type"] == "workflow_complete":
            break
    
    # Provide feedback
    print("\n--- Providing Feedback ---")
    feedback_examples = [
        "The plan was too high-level, add more specific implementation details",
        "Consider economic impacts and transition costs",
        "Include timeline for policy changes",
    ]
    
    for feedback in feedback_examples:
        orchestrator.update_feedback(feedback)
        print(f"✓ Feedback submitted: {feedback[:50]}...")
    
    # Check feedback
    print("\n--- Stored Feedback ---")
    feedback_history = orchestrator.shared_memory.get_feedback_history(limit=5)
    for entry in feedback_history:
        print(f"  • {entry['value']}")


async def example_5_workflow_history():
    """Example 5: Access workflow execution history."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Workflow History")
    print("="*60)
    
    # Initialize LLM
    model_settings = get_model_settings("Llama-3.2-1B")
    model_folder = Path("models")
    llm_client = LamaCppClient(model_folder, model_settings)
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(llm_client)
    
    # Run multiple workflows
    workflows = [
        ("Summarize sustainability reports", "What are the main sustainability challenges?"),
        ("Analyze climate data", "What do recent climate trends show?"),
    ]
    
    for goal, query in workflows:
        async for update in orchestrator.process_with_feedback(goal, query):
            if update["type"] == "workflow_complete":
                print(f"✓ Completed: {goal}")
                break
    
    # Access history
    print("\n--- Workflow History ---")
    history = orchestrator.get_workflow_history(limit=10)
    for i, workflow in enumerate(history, 1):
        print(f"\nWorkflow {i}:")
        print(f"  Goal: {workflow['goal']}")
        print(f"  Query: {workflow['query'][:50]}...")
        print(f"  Iterations: {workflow['iterations']}")
        print(f"  Timestamp: {workflow['timestamp']}")


async def main():
    """Run all examples."""
    print("\n🤖 Multi-Agent System Examples")
    print("=" * 60)
    
    # Choose which example to run
    examples = {
        "1": ("Basic Workflow", example_1_basic_workflow),
        "2": ("Custom Tools", example_2_custom_tools),
        "3": ("Memory Management", example_3_memory_management),
        "4": ("Feedback Loops", example_4_feedback_loop),
        "5": ("Workflow History", example_5_workflow_history),
    }
    
    print("\nAvailable Examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}: {name}")
    
    # For automated demo, run all
    print("\nRunning all examples...\n")
    
    try:
        # Example 1: Basic workflow
        await example_1_basic_workflow()
        
        # Example 2: Custom tools
        await example_2_custom_tools()
        
        # Example 3: Memory management
        await example_3_memory_management()
        
        # Example 4: Feedback loops
        await example_4_feedback_loop()
        
        # Example 5: Workflow history
        await example_5_workflow_history()
        
        print("\n" + "="*60)
        print("✓ All examples completed successfully!")
        print("="*60)
    
    except KeyboardInterrupt:
        print("\n\n❌ Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
