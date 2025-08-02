# Backend Architecture Purpose and Agent Roles

## Overview
The Gremlin ShadTail Trader backend is a sophisticated multi-agent trading system that coordinates 15 specialized agents through a centralized orchestration system with persistent memory capabilities.

## Core Architecture Components

### 1. Agent Coordinator (`agent_coordinator.py`)
**Purpose**: Master orchestrator that coordinates all trading agents with memory-based learning

**Key Responsibilities**:
- Initialize and manage all 15 trading agents
- Coordinate trading decisions using consensus-based approach
- Integrate memory system for learning from past decisions
- Apply risk management across all trading activities
- Track performance and adjust coordination strategies

**Memory Integration**:
- Stores all coordination decisions as embeddings
- Retrieves relevant historical patterns for decision-making
- Learns from successful and failed trading outcomes

### 2. Global Routing System (`globals.py`)
**Purpose**: Central configuration and dependency management for all backend components

**Key Responsibilities**:
- Centralized configuration loading (CFG, MEM dictionaries)
- Standardized logging setup for all modules
- Database path management (ChromaDB, SQLite metadata)
- Utility functions for embedding generation and market data
- Trading helper functions (penny stock scanning, signal rules)

**Configuration Management**:
- Memory system settings (embedding models, vector store paths)
- Agent configurations (IBKR, scanner, risk management)
- Strategy parameters (scanning criteria, signal filters)
- API keys and authentication settings

### 3. Memory System Architecture

#### Embedder (`embedder.py`)
**Purpose**: Vector embedding storage and retrieval with autonomous trading capabilities

**Key Responsibilities**:
- Generate embeddings using SentenceTransformers
- Store embeddings in ChromaDB with SQLite metadata
- Provide similarity search capabilities
- Autonomous trading system with live market data
- Performance tracking and strategy learning

**Autonomous Features**:
- Live market data collection via yfinance
- Technical analysis and signal generation
- Automated trade execution (simulation mode)
- Position monitoring and risk management

#### Agent Input Handler (`Agent_in.py`)
**Purpose**: Central hub for memory retrieval and agent data distribution

**Key Responsibilities**:
- Retrieve relevant memories for specific agents
- Filter memories by relevance and importance
- Cache frequently accessed data
- Track retrieval statistics and performance
- Route data to appropriate agents

**Query Types Supported**:
- Trading signals
- Market analysis
- Risk assessment
- Strategy performance
- Coordination decisions

#### Agent Output Handler (`Agents_out.py`)
**Purpose**: Process all agent outputs and integrate with memory system

**Key Responsibilities**:
- Process logs from all 15 agents
- Create memory embeddings for important events
- Route data between agents via Agent_in
- Generate strategy insights from trading data
- Track communication statistics

**Integration Flow**:
- Agents → Agents_out → Memory/Embedder → Agent_in → Agents

## The 15 Trading Agents

### Core Trading Agents
1. **Memory Agent** (`base_memory_agent.py`)
   - Base class for all agents with memory capabilities
   - Stores and retrieves agent-specific memories

2. **Strategy Agent** (`strategy_agent.py`)
   - Generates trading strategies based on market analysis
   - Evaluates strategy performance and adapts

3. **Signal Generator** (`signal_generator.py`)
   - Creates trading signals from market data
   - Applies technical analysis indicators

4. **Rule Set Agent** (`rule_set_agent.py`)
   - Enforces trading rules and constraints
   - Validates trades before execution

5. **Rules Engine** (`rules_engine.py`)
   - Processes complex trading rule logic
   - Dynamic rule evaluation system

### Market Analysis Agents
6. **Market Timing Agent** (`market_timing.py`)
   - Determines optimal entry/exit timing
   - Analyzes market cycles and patterns

7. **Market Data Service** (`market_data_service.py`)
   - Collects real-time market data
   - Provides data feeds to other agents

8. **Simple Market Service** (`simple_market_service.py`)
   - Lightweight market data collection
   - Backup data source for reliability

9. **Stock Scraper** (`stock_scraper.py`)
   - Web scraping for additional market intelligence
   - News and sentiment analysis

### Management Agents
10. **Runtime Agent** (`runtime_agent.py`)
    - Manages agent lifecycle and health
    - Monitors system performance

11. **Portfolio Tracker** (`portfolio_tracker.py`)
    - Tracks positions and performance
    - Calculates P&L and risk metrics

12. **Tool Control Agent** (`tool_control_agent.py`)
    - Coordinates tool usage across agents
    - Resource allocation and scheduling

13. **Tax Estimator** (`tax_estimator.py`)
    - Calculates tax implications of trades
    - Optimizes for tax efficiency

### Trading Execution Agents
14. **IBKR Trader** (`IBKR-API.trader.py`)
    - Interactive Brokers API integration
    - Live trading execution

15. **Kalshi Trader** (`Kalshi-API.trader.py`)
    - Kalshi prediction market integration
    - Event-based trading strategies

## Inter-Agent Communication Flow

### Data Flow Architecture
```
Market Data → Agents → Agents_out → Memory/Embedder
                 ↓                      ↓
            Agent_in ← Memory Retrieval ←
                 ↓
            Agent Coordinator → Trading Decisions
```

### Communication Patterns
1. **Signal Generation**: Market data agents → Signal generator → Strategy agent
2. **Risk Assessment**: Trading signals → Rule agents → Risk management
3. **Decision Making**: All inputs → Agent coordinator → Final decisions
4. **Memory Learning**: All activities → Agents_out → Embedder → Future retrieval

### Memory Integration Points
- **Storage**: All significant events stored as embeddings
- **Retrieval**: Context-aware memory queries for decision support
- **Learning**: Pattern recognition from historical outcomes
- **Adaptation**: Strategy adjustment based on performance

## Performance Tracking and Learning

### Coordination Performance Metrics
- Total decisions made
- Success/failure rates
- P&L tracking
- Risk-adjusted returns
- Agent contribution weights

### Memory System Metrics
- Embedding count and quality
- Retrieval accuracy
- Cache hit rates
- Agent notification success

### Adaptive Learning
- Agent weight adjustment based on performance
- Strategy refinement from historical patterns
- Risk parameter optimization
- Market condition adaptation

## Build and Deployment Integration

### Poetry Environment
- All dependencies managed via `pyproject.toml`
- Virtual environment isolation
- Comprehensive dependency resolution

### Testing Framework
- Unit tests for individual agents
- Integration tests for agent communication
- Memory system validation
- Performance benchmarking

### Electron Integration
- Backend packaged as executable
- Frontend dashboard integration
- Desktop application deployment
- Cross-platform compatibility

## Future Extensions

### Planned Enhancements
- Machine learning model integration
- Real-time news sentiment analysis
- Options trading strategies
- Multi-exchange support
- Advanced risk modeling

### Scalability Considerations
- Microservices architecture migration
- Distributed agent deployment
- Cloud-based memory storage
- API-first design patterns

This architecture provides a robust foundation for autonomous trading while maintaining human oversight and control through the coordination layer and memory-based learning system.