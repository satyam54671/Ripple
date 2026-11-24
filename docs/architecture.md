# RIPPLE System Architecture

## Design Principles

1. **Dependency-First Modeling:** Travel commitments are stored as typed nodes (`FLIGHT`, `TRANSFER`, `HOTEL`, `MEETING`) connected by directed temporal dependency edges with explicit buffer requirements.
2. **Protocol-Standardized Tooling (MCP):** Agents never hardcode third-party HTTP calls. Every external read/write flows through `RippleMCPClient` into `MCPServer("ripple-travel-tools")`, making mock-to-live swaps isolated to adapter implementations.
3. **Deterministic Mathematical Optimization:** Candidate re-routings are evaluated with Google OR-Tools CP-SAT rather than heuristic LLM guessing, ensuring hard deadlines and corporate budget policies are provably respected.
4. **Human-in-the-Loop Safety:** LangGraph checkpoints pause execution right at `human_approval` before any airline booking, cancellation, or reservation update is dispatched.

## Module Breakdown

```text
backend/app/
├── api/routes.py                  # FastAPI endpoints (/trips, /disruptions, /workflows/{id}/approve, /mcp/tools)
├── core/config.py                 # Pydantic-settings environment configuration
├── core/database.py               # SQLAlchemy engine (SQLite default, PostgreSQL-ready)
├── models/trip.py                 # ORM tables (trips, trip_nodes, trip_edges, recovery_workflow_runs)
├── schemas/trip.py                # Domain Pydantic v2 schemas
├── graph/trip_dependency_graph.py # DAG builder and BFS cascade impact tracer
├── optimisation/recovery_optimizer.py # OR-Tools CP-SAT constraint solver
├── integrations/
│   ├── mcp/server.py              # Official MCP SDK server exposing 9 tools
│   ├── mcp/client.py              # In-process MCP client wrapper
│   ├── gmail/adapter.py           # GmailAdapter + MockGmailAdapter
│   ├── calendar/adapter.py        # GoogleCalendarAdapter + MockGoogleCalendarAdapter
│   ├── flight_status/adapter.py   # FlightStatusAdapter + MockFlightStatusAdapter
│   └── travel_provider/adapter.py # TravelProviderAdapter + MockTravelProviderAdapter
├── agents/                        # Single-responsibility agent modules
└── workflows/recovery_workflow.py # LangGraph StateGraph orchestrator
```

## Database Portability

`backend/app/core/database.py` configures SQLAlchemy 2.x using `DATABASE_URL`:
- Local development defaults to `sqlite:///./ripple.db`.
- Production / Docker Compose (`docker-compose.yml`) switches seamlessly to `postgresql+psycopg://...` without changing application queries.
