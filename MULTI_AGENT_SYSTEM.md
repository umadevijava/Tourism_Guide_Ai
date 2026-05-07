# Multi-Agent System Documentation

## Overview

The RAG Chatbot has been extended with a sophisticated multi-agent system that enables:

- **Planning**: Breaking down complex goals into manageable steps
- **Reasoning**: Analyzing problems from multiple perspectives
- **Execution**: Executing tasks with tool support
- **Memory Management**: Maintaining context and learning from experience
- **Feedback Loops**: Continuous improvement through feedback

## Architecture

### Core Components

#### 1. **BaseAgent** (`chatbot/agents/base_agent.py`)
The foundation class for all agents with:
- `AgentRole`: PLANNER, REASONER, EXECUTOR, MEMORY_MANAGER, COORDINATOR
- `AgentState`: Tracking agent lifecycle (IDLE, PLANNING, REASONING, etc.)
- `AgentThought`: Recording reasoning steps
- `AgentAction`: Recording intended actions
- `AgentObservation`: Recording feedback from actions

#### 2. **Specialized Agents** (`chatbot/agents/specialized_agents.py`)

##### PlannerAgent
- **Role**: Break down goals into sub-tasks
- **Process**: 
  1. Analyzes user goal
  2. Creates detailed step-by-step plan
  3. Identifies dependencies and challenges
  4. Stores plan in shared memory

##### ReasonerAgent
- **Role**: Analyze options and make decisions
- **Process**:
  1. Reviews plan and current task
  2. Analyzes pros/cons of approaches
  3. Identifies risks and mitigations
  4. Provides decision recommendations
  5. Records reasoning in memory

##### ExecutorAgent
- **Role**: Execute planned tasks
- **Process**:
  1. Determines required actions
  2. Calls appropriate tools
  3. Collects and summarizes results
  4. Stores execution records

##### MemoryAgent
- **Role**: Manage shared memory and knowledge consolidation
- **Process**:
  1. Stores information in shared memory
  2. Retrieves past learnings
  3. Consolidates insights from execution
  4. Maintains memory coherence

#### 3. **Tool Registry** (`chatbot/agents/tool_registry.py`)

Provides tools available to agents:

```python
# Register a tool
tool = Tool(
    name="search_knowledge_base",
    description="Search documents for relevant information",
    parameters=[ToolParameter(...)],
    func=search_function,
    category="knowledge_retrieval"
)
registry.register(tool)

# Call a tool
result = await registry.call_tool("search_knowledge_base", query="...")
```

**Available Default Tools**:
- `search_knowledge_base`: Query vector database
- `generate_text`: Generate text with LLM
- `analyze_text`: Text analysis (summary, entities, etc.)
- `store_memory`: Store in agent memory
- `retrieve_memory`: Retrieve from agent memory

#### 4. **Agent Memory** (`chatbot/agents/memory.py`)

Multi-tiered memory system:

```python
class MemoryType:
    CONVERSATION   # Chat history
    TASK          # Task progress
    KNOWLEDGE     # Learned facts
    FEEDBACK      # User/system feedback
    GOAL          # Goal information
    DECISION      # Decision history
    TOOL_CALL     # Tool usage history
```

**Memory Operations**:
```python
# Store
memory.store(
    key="task_001",
    value={"status": "in_progress"},
    memory_type=MemoryType.TASK,
    source_agent="planner",
    importance=0.8
)

# Retrieve
value = memory.retrieve("task_001")

# Search
results = memory.search("planning", memory_type=MemoryType.TASK)

# Get typed memories
conversation = memory.get_conversation_history(limit=20)
```

#### 5. **Agent Orchestrator** (`chatbot/agents/orchestrator.py`)

Coordinates agents through structured workflows:

```python
orchestrator = AgentOrchestrator(llm_client, vector_db)

# Execute standard workflow
async for update in orchestrator.process_with_feedback(goal, query):
    # Update types:
    # - workflow_start
    # - phase_complete
    # - workflow_complete
    # - error
    handle_update(update)
```

**Standard Workflow**:
1. **Planning Phase**: PlannerAgent creates plan
2. **Reasoning Phase**: ReasonerAgent analyzes approach
3. **Execution Phase**: ExecutorAgent executes tasks
4. **Memory Phase**: MemoryAgent consolidates learning

## Frontend Integration

### Components

#### **AgentWorkflowDisplay** (`frontend/src/components/chat/agent-workflow-display.tsx`)

Visualizes the multi-agent workflow with:
- Phase timeline (Planning → Reasoning → Execution → Memory)
- Real-time status updates
- Phase results viewing
- Error display
- Final results summary

```tsx
<AgentWorkflowDisplay 
  workflow={workflow}
  isLoading={isLoading}
/>
```

#### **ModeToggle** (Updated)

New "Agent Workflow" mode toggle alongside existing modes:
```tsx
{
  key: "agentWorkflow",
  icon: Zap,
  label: "Agent Workflow",
  description: "Multi-agent planning and execution",
}
```

### Hooks

#### **useAgentWorkflow** (`frontend/src/hooks/useAgentWorkflow.ts`)

Managing agent workflow execution:

```tsx
const { workflow, isLoading, startWorkflow } = useAgentWorkflow();

// Start workflow
await startWorkflow(goal, userQuery);

// Access results
console.log(workflow.phases);
console.log(workflow.finalResults);
```

### WebSocket Service

#### **AgentWorkflowWebSocket** (`frontend/src/services/agent-workflow.ts`)

Handles streaming workflow updates:

```typescript
const ws = new AgentWorkflowWebSocket(
  (update) => handleUpdate(update),
  (error) => handleError(error)
);

await ws.executeWorkflow("goal", "user query");
```

## Backend API Endpoints

### WebSocket Endpoints

#### `/agents/workflow`
**Streaming multi-agent workflow execution**

**Message Format**:
```json
{
  "goal": "Summarize the most important findings",
  "query": "What are the key insights from the documents?"
}
```

**Response Format**:
```json
{
  "type": "workflow_start|phase_complete|workflow_complete|error",
  "data": { /* detailed update data */ }
}
```

### REST Endpoints

#### `GET /agents/status`
Get current status of all agents

```json
{
  "status": "operational",
  "agents": {
    "planner_agent": { "state": "idle", ... },
    "reasoner_agent": { "state": "idle", ... },
    "executor_agent": { "state": "idle", ... },
    "memory_agent": { "state": "idle", ... }
  },
  "memory_summary": { ... }
}
```

#### `GET /agents/memory`
Retrieve shared memory state

#### `POST /agents/feedback`
Submit feedback for agent improvement

```json
{
  "feedback": "The plan was clear but execution took too long",
  "agent_id": "planner_agent"  // optional
}
```

#### `DELETE /agents/reset`
Reset all agents and memory

#### `GET /agents/workflow-history`
Get recent workflow execution history

```json
{
  "count": 5,
  "history": [
    {
      "timestamp": "2026-04-04T...",
      "goal": "...",
      "query": "...",
      "iterations": 1,
      "results": [...]
    }
  ]
}
```

## Usage Examples

### Example 1: Simple Agent Workflow

```tsx
// Frontend
const { workflow, isLoading, startWorkflow } = useAgentWorkflow();

const handleAgentWorkflow = async () => {
  await startWorkflow(
    "Extract key insights about climate change",
    "What are the main points about climate change?"
  );
};

// Display workflow progress
<AgentWorkflowDisplay workflow={workflow} isLoading={isLoading} />
```

### Example 2: Custom Tool Registration

```python
# Backend
def custom_search_function(query: str, limit: int = 5):
    # Your custom search logic
    return {"results": [...]}

orchestrator.add_tool(
    tool_name="custom_search",
    tool_func=custom_search_function,
    description="Search with custom logic",
    parameters=[
        ToolParameter(
            name="query",
            type="str",
            description="Search query",
            required=True
        ),
        ToolParameter(
            name="limit",
            type="int",
            description="Result limit",
            required=False,
            default=5
        )
    ]
)
```

### Example 3: Processing Workflow Updates

```tsx
const handleWorkflowUpdate = (update: AgentWorkflowUpdate) => {
  switch (update.type) {
    case 'workflow_start':
      console.log("Starting iteration", update.iteration);
      break;
    
    case 'phase_complete':
      console.log(`Completed ${update.phase_name}`);
      console.log("Results:", update.phase_results);
      break;
    
    case 'workflow_complete':
      console.log("Workflow done in", update.iterations, "iterations");
      console.log("Final results:", update.final_results);
      break;
    
    case 'error':
      console.error("Workflow error:", update.message);
      break;
  }
};
```

## Configuration

### Memory Limits

In `AgentMemory.__init__`:
```python
AgentMemory(max_entries_per_type=100)  # Adjust entry limits
```

### Feedback Loop Settings

In `AgentOrchestrator.__init__`:
```python
orchestrator.feedback_loop_enabled = True  # Enable/disable loops
orchestrator.max_iterations = 3  # Max workflow iterations
```

## Advanced Features

### Memory Persistence

Current memory is session-based. To add persistence:

```python
async def save_memory(orchestrator: AgentOrchestrator, filepath: str):
    memory_data = orchestrator.shared_memory.export()
    with open(filepath, 'w') as f:
        json.dump(memory_data, f)

async def load_memory(orchestrator: AgentOrchestrator, filepath: str):
    with open(filepath, 'r') as f:
        memory_data = json.load(f)
    # Restore memory items
    for entry in memory_data["memory"]["conversation"]:
        orchestrator.shared_memory.store(**entry)
```

### Custom Workflow Phases

```python
custom_workflow = [
    WorkflowPhase("Analysis", [analyzer_agent]),
    WorkflowPhase("Validation", [validator_agent]),
    WorkflowPhase("Documentation", [doc_agent]),
]

orchestrator.current_workflow = custom_workflow
# Then execute manually with orchestrator.execute_phase()
```

### Agent-Specific Feedback

```python
# Give feedback to specific agent
orchestrator.update_feedback(
    "Execution was slow, optimize tool calls",
    agent_id="executor_agent"
)
```

## Monitoring and Debugging

### View Agent States

```bash
# Endpoint
GET /agents/status

# Response shows real-time agent states, thoughts, and actions
```

### Access Workflow History

```python
history = orchestrator.get_workflow_history(limit=10)
for workflow in history:
    print(f"Goal: {workflow['goal']}")
    print(f"Iterations: {workflow['iterations']}")
    print(f"Results: {workflow['results']}")
```

### Memory Analytics

```python
summary = orchestrator.shared_memory.get_summary()
# {
#   "conversation": 15,
#   "task": 8,
#   "feedback": 3,
#   "decision": 12,
#   ...
# }
```

## Future Enhancements

1. **Long-term Memory**: Persist memory across sessions
2. **Multi-user Collaboration**: Coordinate agents for multiple users
3. **Tool Integration**: Connect to external APIs and services
4. **Learning**: Update agent behavior based on feedback
5. **Grounding**: Real-world fact verification
6. **Hierarchical Agents**: Define agent teams for complex tasks
7. **Performance Optimization**: Parallel agent execution
8. **Visualization Dashboard**: Real-time agent metrics and analytics

## Troubleshooting

### WebSocket Connection Error

**Frontend Error**: "WebSocket connection error"
- Ensure backend is running on configured port
- Check environment variable `VITE_API_URL`
- Verify no firewall blocking WebSocket connections

### Agent Timeout

**Issue**: Workflow takes too long
- Increase `max_iterations` in orchestrator
- Optimize tool functions for faster execution
- Reduce `max_entries_per_type` for memory

### Memory Growth

**Issue**: Memory consuming too much RAM
- Reduce `max_entries_per_type` in AgentMemory
- Implement memory cleanup in `MemoryAgent.process()`
- Clear less important entries periodically

## Support and Contributing

For issues, feature requests, or contributions:
1. Check existing documentation
2. Review workflow history for patterns
3. Check agent states with `/agents/status`
4. Submit with relevant error messages and workflow examples
