# Quick Integration Guide

## For Developers: How to Use the Multi-Agent System

### Backend Integration

#### 1. Initialize Orchestrator (in your backend service)

```python
from chatbot.agents.orchestrator import AgentOrchestrator
from chatbot.bot.client.lama_cpp_client import LamaCppClient

# During startup
llm_client = LamaCppClient(model_folder, model_settings)
vector_db = ...  # Your vector database instance

orchestrator = AgentOrchestrator(llm_client, vector_db)
```

#### 2. Register Custom Tools

```python
from chatbot.agents.tool_registry import Tool, ToolParameter

async def my_search_function(query: str, limit: int = 5) -> dict:
    # Your implementation
    return {"results": [...]}

orchestrator.add_tool(
    tool_name="my_search",
    tool_func=my_search_function,
    description="Search function description",
    parameters=[
        ToolParameter("query", "str", "Search query", required=True),
        ToolParameter("limit", "int", "Result limit", required=False, default=5),
    ]
)
```

#### 3. Use Orchestrator in Endpoints

```python
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/agents/workflow")
async def agent_workflow(websocket: WebSocket):
    await websocket.accept()
    
    data = await websocket.receive_json()
    goal = data.get("goal")
    query = data.get("query")
    
    async for update in orchestrator.process_with_feedback(goal, query):
        await websocket.send_json({"type": update["type"], "data": update})
```

#### 4. Access Agent Information

```python
# Get agent states
states = orchestrator.get_agent_states()

# Get shared memory
memory_state = orchestrator.shared_memory.export()

# Get workflow history
history = orchestrator.get_workflow_history(limit=10)

# Store feedback
orchestrator.update_feedback("User feedback here", agent_id="planner_agent")
```

---

### Frontend Integration

#### 1. Use Agent Workflow Hook

```tsx
import { useAgentWorkflow } from '@/hooks/useAgentWorkflow';

function MyComponent() {
  const { workflow, isLoading, startWorkflow } = useAgentWorkflow();
  
  const handleStartWorkflow = async () => {
    await startWorkflow(
      "My goal here",
      "User query here"
    );
  };
  
  return (
    <>
      <button onClick={handleStartWorkflow} disabled={isLoading}>
        Start Agent Workflow
      </button>
      <AgentWorkflowDisplay workflow={workflow} isLoading={isLoading} />
    </>
  );
}
```

#### 2. Enable Agent Workflow Mode

```tsx
import { type ChatModes } from '@/components/chat';

const [modes, setModes] = useState<ChatModes>({
  rag: false,
  reasoning: false,
  webSearch: false,
  agentWorkflow: false,
});

// Toggle agent workflow
if (modes.agentWorkflow) {
  startWorkflow(goal, query);
}
```

#### 3. Display Workflow Progress

```tsx
import { AgentWorkflowDisplay } from '@/components/chat/agent-workflow-display';

<AgentWorkflowDisplay 
  workflow={workflow}
  isLoading={isLoading}
/>
```

---

## File Structure Reference

```
Backend:
├── chatbot/agents/                        # Core agent system
│   ├── __init__.py                       # Module exports
│   ├── base_agent.py                     # Base classes
│   ├── tool_registry.py                  # Tool system
│   ├── memory.py                         # Memory management
│   ├── specialized_agents.py             # Planner, Reasoner, Executor, Memory
│   ├── orchestrator.py                   # Main orchestrator
│   └── examples.py                       # Runnable examples
├── backend/api/endpoints/
│   └── agents.py                         # WebSocket + REST endpoints
└── backend/api/
    └── routes.py                         # Router includes agents

Frontend:
├── src/services/
│   └── agent-workflow.ts                 # WebSocket service
├── src/hooks/
│   └── useAgentWorkflow.ts               # React hook
├── src/components/chat/
│   ├── agent-workflow-display.tsx        # Display component
│   └── mode-toggle.tsx                   # Updated with new mode
└── src/
    └── App.tsx                           # Updated mode state
```

---

## Typical Usage Flow

### 1. User Perspective
```
User enables "Agent Workflow" mode → Types question → Click Send
       ↓
Frontend sends to /agents/workflow WebSocket with {goal, query}
       ↓
Real-time workflow visualization shows Planning → Reasoning → Execution
       ↓
Results displayed in workflow panel
```

### 2. Developer Perspective
```python
# In orchestrator.py
async for update in self.process_with_feedback(goal, query):
    # Phase 1: Planning
    await execute_phase(planning_phase, task, context)
    yield {"type": "phase_complete", "phase_name": "Planning", ...}
    
    # Phase 2: Reasoning
    await execute_phase(reasoning_phase, task, context)
    yield {"type": "phase_complete", "phase_name": "Reasoning", ...}
    
    # Phase 3: Execution
    await execute_phase(execution_phase, task, context)
    yield {"type": "phase_complete", "phase_name": "Execution", ...}
    
    # Phase 4: Memory
    await execute_phase(memory_phase, task, context)
    
    # Final
    yield {"type": "workflow_complete", "final_results": {...}}
```

---

## Common Operations

### To Add a New Agent Type

```python
# 1. Create class in specialized_agents.py
class MyCustomAgent(BaseAgent):
    def __init__(self, ...):
        super().__init__(agent_id, AgentRole.MY_ROLE, llm_client)
    
    async def think(self, prompt: str) -> AgentThought:
        # Your thinking logic
        pass
    
    async def process(self, task, context) -> Dict[str, Any]:
        # Your processing logic
        pass

# 2. Register in orchestrator
self.agents["my_agent"] = MyCustomAgent(...)

# 3. Add to workflow
workflow.append(WorkflowPhase("MyPhase", [self.agents["my_agent"]]))
```

### To Add Memory Access

```python
# Store
self.shared_memory.store(
    key="important_finding",
    value=finding_data,
    memory_type=MemoryType.KNOWLEDGE,
    source_agent="my_agent",
    importance=0.9
)

# Retrieve
finding = self.shared_memory.retrieve("important_finding")

# Search
results = self.shared_memory.search("keyword", MemoryType.KNOWLEDGE)
```

### To Get Workflow Results

```python
# Access via orchestrator
history = orchestrator.get_workflow_history(limit=1)
latest = history[0]
print(latest["goal"])
print(latest["results"])
print(latest["iterations"])

# Or via REST API
import requests
response = requests.get("http://localhost:8000/agents/workflow-history")
```

---

## Testing the System

### 1. Test via Frontend
- Enable "Agent Workflow" mode
- Type: "Summarize the benefits of renewable energy"
- Watch the workflow execute in real-time

### 2. Test via REST API
```bash
# Check status
curl http://localhost:8000/agents/status

# Get memory
curl http://localhost:8000/agents/memory

# Submit feedback
curl -X POST http://localhost:8000/agents/feedback \
  -d "feedback=System%20is%20working%20well"

# Get history
curl http://localhost:8000/agents/workflow-history
```

### 3. Test via Python
```python
import asyncio
from chatbot.agents.orchestrator import AgentOrchestrator

async def test():
    orchestrator = AgentOrchestrator(llm, vector_db)
    
    async for update in orchestrator.process_with_feedback(
        goal="Test goal",
        query="Test query"
    ):
        print(f"Update: {update['type']}")
        if update["type"] == "workflow_complete":
            break

asyncio.run(test())
```

---

## Configuration Checklist

- [ ] Backend `/agents/workflow` endpoint is accessible
- [ ] Frontend WebSocket connection to backend is working
- [ ] LLM model is loaded and accessible to orchestrator
- [ ] Vector database is initialized (if using RAG tools)
- [ ] "Agent Workflow" mode appears in mode toggle
- [ ] Agent status endpoint returns valid JSON

---

## Monitoring

### Real-time Monitoring
```python
# Check agent states
states = orchestrator.get_agent_states()
for agent_id, state in states.items():
    print(f"{agent_id}: {state['state']}")
    print(f"  Thoughts: {len(state['thoughts'])}")
    print(f"  Actions: {len(state['actions'])}")
```

### Memory Monitoring
```python
# Check memory usage
summary = orchestrator.shared_memory.get_summary()
print(f"Memory usage: {summary}")
# Output: {'conversation': 10, 'task': 5, 'feedback': 2, ...}
```

### Workflow Analysis
```python
# Analyze patterns
history = orchestrator.get_workflow_history(limit=100)
avg_iterations = sum(w['iterations'] for w in history) / len(history)
avg_complexity = ...  # your metric
```

---

## Debugging

### If agents aren't responding:
1. Check `/agents/status` for agent states
2. Verify LLM model is loaded
3. Check backend logs for errors
4. Test with REST calls first

### If memory is growing too large:
1. Reduce `max_entries_per_type` in AgentMemory
2. Implement periodic cleanup
3. Monitor `get_memory()` endpoint

### If WebSocket disconnects:
1. Check browser console for errors
2. Verify backend is serving `/agents/workflow`
3. Check firewall/proxy settings
4. Restart dev servers

---

## Performance Tips

1. **Reduce Token Generation**: Adjust `max_new_tokens` in agent prompts
2. **Optimize Tool Calls**: Make tool functions as fast as possible
3. **Memory Pruning**: Adjust `max_entries_per_type` based on load
4. **Parallel Execution**: Consider running non-dependent phases in parallel
5. **Caching**: Cache LLM responses for common queries

---

## Next Steps

1. ✅ **Installation**: Files are already in place
2. **Customization**: Register your own tools and agents
3. **Integration**: Connect to your databases/APIs
4. **Monitoring**: Set up logging and metrics
5. **Optimization**: Profile and optimize for your use case
6. **Deployment**: Test in production-like environment

---

For detailed documentation, see:
- `MULTI_AGENT_SYSTEM.md` - Full API documentation
- `AGENT_SYSTEM_SUMMARY.md` - Architecture overview
- `chatbot/agents/examples.py` - Working examples
