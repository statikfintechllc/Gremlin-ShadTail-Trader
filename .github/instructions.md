# Gremlin ShadTail Trader - Developer Instructions

## Project Overview

Gremlin ShadTail Trader is a sophisticated trading application built with:
- **Backend**: Python with FastAPI/Flask, using Poetry for dependency management
- **Frontend**: Astro.js with TypeScript, Tailwind CSS, and shadcn/ui components
- **Desktop**: Electron wrapper for cross-platform distribution
- **Memory**: ChromaDB for vector storage and local MCP servers for persistent memory
- **Architecture**: Microservices with MCP (Model Context Protocol) integration

## Local MCP Servers

Two local MCP servers are available for enhanced functionality:

### 1. Local Memory MCP (`~/local-memory-mcp/`)
Provides persistent memory storage with tagging and search capabilities:
- `store_memory`: Store information with tags and metadata
- `retrieve_memory`: Get stored information by key
- `search_memory`: Search by content, tags, or metadata
- `list_memories`: List all stored memories with pagination
- `update_memory`: Update existing memories
- `delete_memory`: Remove stored memories

### 2. Task Queue MCP (`~/task-queue-mcp/`)
Manages asynchronous tasks with scheduling and priority:
- `create_task`: Create new tasks with priority and scheduling
- `get_task`: Retrieve task details
- `update_task_status`: Update task execution status
- `list_tasks`: List tasks with filtering
- `create_queue`: Create new task queues
- `get_queue_stats`: Get queue statistics

## Development Guidelines

### Backend Development
- Use Poetry for dependency management: `poetry install`, `poetry add <package>`
- Follow Python type hints and docstrings
- Core trading logic goes in `Gremlin_Trade_Core/`
- Memory and embeddings in `Gremlin_Trade_Memory/`
- Agent coordination through `agent_coordinator.py`

### Frontend Development
- Use Astro.js with TypeScript for type safety
- Implement UI components with shadcn/ui and Tailwind CSS
- Keep components in `frontend/src/components/`
- Pages in `frontend/src/pages/`
- Use the utilities in `frontend/src/utils/`

### Trading Strategies
- Implement new strategies in `backend/Gremlin_Trader_Strategies/`
- Use the strategy manager for coordination
- Follow the existing pattern for penny stock and recursive scanner strategies

### Agent System
- Agents are in `backend/Gremlin_Trader_Tools/`
- Each agent type has its own directory
- Use the agent coordinator for inter-agent communication
- Memory agents utilize the local memory MCP

## Key Technologies

- **Python**: FastAPI, Poetry, ChromaDB, SQLite
- **JavaScript/TypeScript**: Astro.js, Electron, Node.js
- **CSS**: Tailwind CSS with shadcn/ui components
- **Database**: ChromaDB for vectors, SQLite for structured data

## Memory and Task Management

### Using Local Memory MCP
```javascript
// Store trading insights
await mcp.tools.store_memory({
  key: "market_analysis_2024_01",
  content: "Market showing bullish trends with tech sector leading",
  tags: ["market", "analysis", "tech", "bullish"],
  metadata: { date: "2024-01-15", confidence: 0.85 }
});

// Retrieve insights
const memory = await mcp.tools.retrieve_memory({
  key: "market_analysis_2024_01"
});
```

### Using Task Queue MCP
```javascript
// Create trading task
await mcp.tools.create_task({
  name: "analyze_penny_stocks",
  description: "Scan and analyze penny stocks for opportunities",
  priority: 8,
  queue: "trading",
  data: { symbol_range: "A-C", min_volume: 100000 }
});

// Schedule recurring analysis
await mcp.tools.create_task({
  name: "daily_market_scan",
  description: "Daily market opportunity scan",
  cron_schedule: "0 9 * * 1-5", // 9 AM weekdays
  queue: "scheduled"
});
```

## Agent Integration

### Financial Agent
- Handles market data and analysis
- Integrates with external APIs
- Stores findings in local memory MCP

### Strategy Agent
- Manages trading strategies
- Uses task queue for strategy execution
- Coordinates with other agents

### Memory Agent
- Leverages local memory MCP
- Manages embeddings and vector search
- Provides context to other agents

## Debugging and Logging

- Backend logs: Check `backend/config/Gremlin_Trade_Logs/`
- Frontend logs: Browser console and network tab
- MCP logs: Check MCP server output in terminal
- Electron logs: Main process and renderer logs

## Contributing

1. Use meaningful commit messages
2. Follow existing code style and patterns
3. Add tests for new functionality
4. Update documentation for significant changes
5. Use the MCP servers for persistent data and task management

## Security Notes

- API keys and sensitive data go in environment variables
- Use the memory MCP for storing non-sensitive trading insights
- Task queue should not store sensitive authentication data
- Follow principle of least privilege for agent permissions

## Performance Tips

- Use the local memory MCP for caching frequently accessed data
- Leverage task queues for long-running operations
- Monitor ChromaDB vector storage size
- Use appropriate batch sizes for data processing

## Ensuring MCP Integration in VSCode

### 1. Check for Local Memory MCP
- Verify if the local memory MCP server is running:
  ```bash
  ps aux | grep local-memory-mcp
  ```
- If not running, navigate to `~/local-memory-mcp/` and start the server:
  ```bash
  cd ~/local-memory-mcp/
  node server.js
  ```

### 2. Check for Task Queue MCP
- Verify if the task queue MCP server is running:
  ```bash
  ps aux | grep task-queue-mcp
  ```
- If not running, navigate to `~/task-queue-mcp/` and start the server:
  ```bash
  cd ~/task-queue-mcp/
  node server.js
  ```

### 3. Utilize MCP in VSCode
- Ensure the MCP servers are configured in your VSCode settings file (`mcp.json`):
  ```jsonc
  {
    "mcp.servers": {
      "local-memory": {
        "command": "node",
        "args": ["/home/statiksmoke8/local-memory-mcp/server.js"],
        "env": {
          "NODE_ENV": "development"
        }
      },
      "task-queue": {
        "command": "node",
        "args": ["/home/statiksmoke8/task-queue-mcp/server.js"],
        "env": {
          "NODE_ENV": "development"
        }
      }
    }
  }
  ```
- Use the MCP servers for:
  - Persistent memory storage for thoughts and context.
  - Task queue management for scheduling and prioritizing actions.
