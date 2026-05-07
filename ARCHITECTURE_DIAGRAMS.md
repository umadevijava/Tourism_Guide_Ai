# Multi-Agent System Architecture Diagrams

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ React Frontend (TypeScript)                                  │  │
│  │  • Chat Interface                                            │  │
│  │  • Agent Workflow Display                                    │  │
│  │  • Mode Toggle (New: Agent Workflow)                         │  │
│  │  • Real-time Status Updates                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                          ↕ WebSocket & REST
                    (JSON messages, streaming)
┌─────────────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Agent Orchestrator (Main System)                            │   │
│  │ ┌──────────────────────────────────────────────────────┐   │   │
│  │ │ Workflow Execution Engine                            │   │   │
│  │ │  • Phase Management                                  │   │   │
│  │ │  • Streaming Updates                                 │   │   │
│  │ │  • Feedback Processing                               │   │   │
│  │ └──────────────────────────────────────────────────────┘   │   │
│  │ ┌──────────────┬──────────────┬──────────────────────────┐ │   │
│  │ │ Agents       │ Shared       │ Tool                     │ │   │
│  │ │              │ Memory       │ Registry                 │ │   │
│  │ │ • Planner    │              │                          │ │   │
│  │ │ • Reasoner   │ • Conv.      │ • Search KB              │ │   │
│  │ │ • Executor   │ • Task       │ • Generate Text          │ │   │
│  │ │ • Memory     │ • Knowledge  │ • Analyze Text           │ │   │
│  │ │   Manager    │ • Feedback   │ • Store Memory           │ │   │
│  │ │              │ • Goal       │ • Retrieve Memory        │ │   │
│  │ │              │ • Decision   │ • Custom Tools           │ │   │
│  │ └──────────────┴──────────────┴──────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          ↕ Services
│  ┌──────────────────┬──────────────────┬────────────────────┐      │
│  │ Chat Service     │ Vector Database  │ LLM Client         │      │
│  │                  │ (Chroma)         │ (LlamaCpp)         │      │
│  └──────────────────┴──────────────────┴────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent Workflow Execution Flow

```
START
  |
  v
┌──────────────────┐
│ WORKFLOW START   │
│ (goal + query)   │
└──────────────────┘
       |
       v
┌─────────────────────────────────────────┐
│       PHASE 1: PLANNING                  │
│  [PlannerAgent]                          │
│                                          │
│  Input: goal + user query                │
│  Process:                                │
│    1. Analyze goal                       │
│    2. Break into sub-tasks               │
│    3. Identify dependencies              │
│    4. Generate detailed plan             │
│  Output: Clear, structured plan          │
│  Memory: Store in GOAL & TASK types      │
│          Confidence: 0.8                 │
└─────────────────────────────────────────┘
       |
       v (context: plan)
┌─────────────────────────────────────────┐
│     PHASE 2: REASONING                   │
│  [ReasonerAgent]                         │
│                                          │
│  Input: plan + task                      │
│  Process:                                │
│    1. Review plan thoroughly             │
│    2. Analyze approach options           │
│    3. Evaluate pros and cons             │
│    4. Identify risks & mitigation        │
│    5. Make recommendations               │
│  Output: Reasoned decision               │
│  Memory: Store in DECISION type          │
│          Confidence: 0.75                │
└─────────────────────────────────────────┘
       |
       v (context: reasoning)
┌─────────────────────────────────────────┐
│     PHASE 3: EXECUTION                   │
│  [ExecutorAgent]                         │
│                                          │
│  Input: plan + reasoning                 │
│  Process:                                │
│    1. Determine tool requirements        │
│    2. Call relevant tools                │
│    3. Collect results                    │
│    4. Summarize findings                 │
│  Output: Execution results               │
│  Memory: Store in TASK & TOOL_CALL       │
│          Confidence: 0.7                 │
└─────────────────────────────────────────┘
       |
       v (context: results)
┌─────────────────────────────────────────┐
│     PHASE 4: MEMORY                      │
│  [MemoryAgent]                           │
│                                          │
│  Input: all results                      │
│  Process:                                │
│    1. Consolidate insights               │
│    2. Update shared memory               │
│    3. Remove obsolete entries            │
│    4. Maintain coherence                 │
│  Output: Memory state                    │
│  Memory: Store in KNOWLEDGE type         │
│          Confidence: 0.9                 │
└─────────────────────────────────────────┘
       |
       v
┌──────────────────────┐
│ WORKFLOW COMPLETE    │
│ Return results to    │
│ frontend for display │
└──────────────────────┘
       |
       v
┌──────────────────────────┐
│ FEEDBACK LOOP (optional) │
│                          │
│ User provides feedback → │
│ Stored in memory →       │
│ Can guide next iteration │
└──────────────────────────┘
       |
END or ITERATE
```

---

## 3. Memory System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SHARED MEMORY                            │
│  (AgentMemory instance in AgentOrchestrator)                │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Memory Type Buckets                                  │  │
│  │                                                      │  │
│  │ ┌──────────┐  ┌──────────┐  ┌──────────────┐       │  │
│  │ │CONVERSA- │  │   TASK   │  │  KNOWLEDGE   │       │  │
│  │ │TION ID=5 │  │ ID=3     │  │ ID=8         │       │  │
│  │ │          │  │          │  │              │       │  │
│  │ │Chat turn │  │Progress: │  │Finding 1:    │       │  │
│  │ │1         │  │Step 2/4  │  │  Renewable   │       │  │
│  │ │Chat turn │  │          │  │  is 40%      │       │  │
│  │ │2         │  │Duration: │  │              │       │  │
│  │ │...       │  │2.5s      │  │Finding 2:    │       │  │
│  │ └──────────┘  └──────────┘  │  Grid issue  │       │  │
│  │                              │              │       │  │
│  │ ┌──────────┐  ┌──────────┐  │  ...         │       │  │
│  │ │ FEEDBACK │  │ DECISION │  └──────────────┘       │  │
│  │ │ ID=2     │  │ ID=6     │                         │  │
│  │ │          │  │          │  ┌──────────┐           │  │
│  │ │"Too slow"│  │Plan A vs │  │  GOAL    │           │  │
│  │ │"Complex" │  │Plan B    │  │  ID=1    │           │  │
│  │ │...       │  │Analysis  │  │          │           │  │
│  │ └──────────┘  └──────────┘  │Renewable │           │  │
│  │                              │energy    │           │  │
│  │                              │research  │           │  │
│  │                              └──────────┘           │  │
│  │                                                      │  │
│  │ ┌──────────────────────────┐  ┌─────────────────┐  │  │
│  │ │ TOOL_CALL                │  │    METADATA     │  │  │
│  │ │ ID=4,7,9,...             │  │                 │  │  │
│  │ │                          │  │ • Timestamps    │  │  │
│  │ │ Tool: search_kb          │  │ • Source agent  │  │  │
│  │ │ Tool: generate_text      │  │ • Importance    │  │  │
│  │ │ Tool: analyze_text       │  │ • Custom data   │  │  │
│  │ │                          │  │                 │  │  │
│  │ └──────────────────────────┘  └─────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Memory Operations                                    │  │
│  │                                                      │  │
│  │  • store(key, value, type, source, importance)      │  │
│  │  • retrieve(key) → value                            │  │
│  │  • search(query, type) → [matching entries]         │  │
│  │  • get_by_type(type) → [all of type]               │  │
│  │  • clear() | clear_by_type(type)                    │  │
│  │  • export() → full memory state                     │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Agent Interaction Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                             │
│                                                             │
│  for each agent in workflow_phase:                         │
│    1. agent.set_state(PLANNING/REASONING/EXECUTING)       │
│    2. await agent.process(task, context)                  │
│    3. Collect: thoughts, actions, observations            │
│    4. Store in shared memory                              │
│    5. Update frontend with phase_complete                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          |
         ┌────────────────┼────────────────┐
         |                |                |
         v                v                v
    ┌─────────┐      ┌─────────┐      ┌─────────┐
    │PLANNER  │      │REASONER │      │EXECUTOR │
    │AGENT    │      │AGENT    │      │AGENT    │
    │         │      │         │      │         │
    │ ┌─────┐ │      │ ┌─────┐ │      │ ┌─────┐ │
    │ │think│ │      │ │think│ │      │ │think│ │
    │ └────┘ │      │ └────┘ │      │ └────┘ │
    │   ↓    │      │   ↓    │      │   ↓    │
    │ ┌─────┐ │      │ ┌─────┐ │      │ ┌─────┐ │
    │ │proc.│ │      │ │proc.│ │      │ │proc.│ │
    │ └────┘ │      │ └────┘ │      │ └────┘ │
    │   ↓    │      │   ↓    │      │   ↓    │
    │ ┌─────┐ │      │ ┌─────┐ │      │ ┌─────┐ │
    │ │mem  │ │      │ │mem  │ │      │ │mem  │ │
    │ │store│ │      │ │store│ │      │ │store│ │
    │ └────┘ │      │ └────┘ │      │ └────┘ │
    └─────────┘      └─────────┘      └─────────┘
      Plan             Analysis          Results
      ↓                 ↓                  ↓
    SHARED MEMORY (consolidated by MemoryAgent)
      ↓
    WORKFLOW COMPLETE → FRONTEND DISPLAY
```

---

## 5. Frontend WebSocket Update Flow

```
Frontend                          Backend
  |                                |
  | PUT: goal + query              |
  |---[WebSocket Message]--------->|
  |                                | Orchestrator processes
  |                                |   Phase 1: Planning
  | GET: workflow_start           |
  |<--[JSON]------------------------|
  |                                |
  | UPDATE: Show Phase 1 UI        |
  |                                |
  |                                | Phase 2: Reasoning starts
  | GET: phase_complete           |
  | (phase: Planning, results)    |
  |<--[JSON]------------------------|
  |                                |
  | UPDATE: Planning done          |
  | START: Show Phase 2           |
  |                                |
  |                                | Phase 3: Execution starts
  | GET: phase_complete           |
  | (phase: Reasoning, results)   |
  |<--[JSON]------------------------|
  |                                |
  | UPDATE: Reasoning done         |
  | START: Show Phase 3           |
  |                                |
  |                                | Phase 4: Memory consolidation
  | GET: phase_complete           |
  | (phase: Execution, results)   |
  |<--[JSON]------------------------|
  |                                |
  | UPDATE: Execution done         |
  | START: Show Phase 4           |
  |                                |
  | GET: workflow_complete        |
  | (final_results, iterations)   |
  |<--[JSON]------------------------|
  |                                |
  | UPDATE: Complete             |
  | DISPLAY: Final results        |
  |                                |
  | SHOW: Memory summary          |
  | (conversation, task, ...)     |
  |                                |
```

---

## 6. Tool Registry Architecture

```
┌─────────────────────────────────────────────────────┐
│                 TOOL REGISTRY                       │
│                                                     │
│  _tools: Dict[str, Tool]                           │
│  ├─ "search_knowledge_base"                        │
│  │  ├─ name: "search_knowledge_base"               │
│  │  ├─ description: "Search documents..."          │
│  │  ├─ category: "knowledge_retrieval"             │
│  │  ├─ func: async_search_function()               │
│  │  ├─ parameters:                                 │
│  │  │  ├─ "query" (str, required)                  │
│  │  │  └─ "top_k" (int, default=5)                 │
│  │  └─ to_dict() → tool spec                       │
│  │                                                  │
│  ├─ "generate_text"                                │
│  │  ├─ func: to LLM                                │
│  │  └─ parameters: [prompt, max_tokens, ...]       │
│  │                                                  │
│  ├─ "analyze_text"                                 │
│  │  ├─ func: text analysis                         │
│  │  └─ parameters: [text, analysis_type]           │
│  │                                                  │
│  ├─ "store_memory"                                 │
│  │  ├─ func: memory.store()                        │
│  │  └─ parameters: [key, value, type]              │
│  │                                                  │
│  ├─ "retrieve_memory"                              │
│  │  ├─ func: memory.retrieve()                     │
│  │  └─ parameters: [key]                           │
│  │                                                  │
│  └─ [Custom tools registered by user]              │
│                                                     │
│  Methods:                                          │
│  ├─ register(tool)                                 │
│  ├─ unregister(tool_name)                          │
│  ├─ get_tool(tool_name)                            │
│  ├─ list_tools() → [names]                         │
│  ├─ call_tool(tool_name, **kwargs) → result        │
│  └─ get_tool_specs(category) → [{specs}]           │
│                                                     │
└─────────────────────────────────────────────────────┘
                       ↑
            All agents can access tools
         via orchestrator.tool_registry
```

---

## 7. Data Flow: Query to Results

```
1. User Input
   "Summarize benefits of renewable energy"
   ↓

2. Frontend Processing
   • Enables "Agent Workflow" mode
   • Creates WebSocket connection
   • Sends goal + query to backend
   ↓

3. Orchestrator Initialization
   • Parse goal and query
   • Create standard workflow (4 phases)
   • Initialize shared memory
   ↓

4. Planning Phase
   PlannerAgent.process()
   ├─ LLM thinks about goal: "PlannerAgent.think()"
   ├─ LLM generates plan with steps
   ├─ AgentThought recorded (confidence: 0.8)
   ├─ AgentAction recorded
   └─ Plan stored in memory (GOAL + TASK types)
   ↓

5. Reasoning Phase
   ReasonerAgent.process()
   ├─ Receives plan from context
   ├─ LLM analyzes pros/cons
   ├─ AgentThought recorded (confidence: 0.75)
   ├─ Reasoning stored (DECISION type)
   └─ Frontend shows "Reasoning complete"
   ↓

6. Execution Phase
   ExecutorAgent.process()
   ├─ Determines which tools to call
   ├─ Calls tool_registry.call_tool()
   ├─ Tool executes (e.g., search_knowledge_base)
   ├─ Results collected
   ├─ Stored in memory (TASK + TOOL_CALL types)
   └─ Frontend shows "Execution complete"
   ↓

7. Memory Phase
   MemoryAgent.process()
   ├─ Consolidates all learned info
   ├─ Updates memory entries
   ├─ Generates memory summary
   └─ Frontend shows "Memory updated"
   ↓

8. Workflow Complete
   ├─ All phases yielded results
   ├─ Final results assembled
   ├─ Memory summary included
   └─ Frontend displays complete workflow
   ↓

9. Frontend Display
   AgentWorkflowDisplay shows:
   ├─ All 4 phases (completed ✓)
   ├─ Duration of each phase
   ├─ Phase results (expandable)
   ├─ Memory summary
   └─ Option to provide feedback
```

---

## 8. Class Hierarchy

```
BaseAgent (abstract)
├── PlannerAgent
│   ├── Responsibility: Break down goals
│   ├── Output: Detailed plan
│   └── Confidence: 0.8
│
├── ReasonerAgent
│   ├── Responsibility: Analyze decisions
│   ├── Output: Reasoning + recommendations
│   └── Confidence: 0.75
│
├── ExecutorAgent
│   ├── Responsibility: Execute tasks
│   ├── Output: Execution results
│   └── Confidence: 0.7
│
└── MemoryAgent
    ├── Responsibility: Memory management
    ├── Output: Consolidated memory
    └── Confidence: 0.9

AgentOrchestrator
├── Composes: All agents, shared memory, tool registry
├── Manages: Workflow execution, phase management
└── Provides: Streaming updates, feedback handling

Tool
├── name: str
├── description: str
├── parameters: List[ToolParameter]
├── func: Callable
└── category: str (knowledge_retrieval, computation, etc.)

MemoryEntry
├── key: str
├── value: Any
├── memory_type: MemoryType (7 types)
├── timestamp: datetime
├── source_agent: str
└── importance: float (0-1)
```

---

## 9. State Transitions

```
Agent Lifecycle:
IDLE
 ↓ (process() called)
PLANNING/REASONING/EXECUTING
 ↓ (thinking)
REASONING/EXECUTING (continued)
 ↓ (complete)
COMPLETED
 ↓ (reset() called)
IDLE

Error Path:
IDLE → [PLANNING/REASONING/EXECUTING] → ERROR → IDLE (on reset)

Memory Lifecycle:
[] (empty)
 ↑
 v
[Entry 1]
 ↑
 v
[Entry 1, 2, 3, ...] (grows)
 ↑
 v
[Entry 1, 3, 5, ...] (pruned, important ones kept)
```

---

This documentation provides visual understanding of the system architecture
at different levels of abstraction, from high-level user flow to low-level
class hierarchies.
