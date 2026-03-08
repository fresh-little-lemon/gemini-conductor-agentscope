# Technology Stack - Browser Agent Example

## Programming Languages
- **Python (3.10+):** Core logic for AgentScope, BrowserAgent, and backend services.
- **JavaScript / TypeScript:** Used for the Playwright MCP server and the React-based WebUI.

## Frameworks & Libraries
- **AgentScope:** The primary agent framework for building and orchestrating the BrowserAgent.
- **Playwright:** Provides the underlying browser automation capabilities.
- **FastAPI:** Orchestration layer for managing agent runs and event streaming.
- **Node.js:** Runtime for the Playwright MCP server and frontend build tools.
- **React:** Framework for the project's web interface (WebUI).
- **Zustand:** Lightweight state management for the React frontend.

## Key Technologies & Protocols
- **Model Context Protocol (MCP):** Standardizes the interaction between the agent and the browser tools.
- **OpenAI-Compatible APIs:** Primary interface for LLM interaction (e.g., DashScope, OpenAI).
- **WebSockets:** Bidirectional real-time streaming of events and CDP frames.
- **Web Automation & Interaction:** Advanced techniques for navigating and interacting with complex web interfaces.
- **Multimodal Data Capture:** Tools for recording video trajectories and granular interaction logs for reward model training.

## Development & Deployment
- **Git:** Version control for the project codebase.
- **Environment Management:** Python venv/conda and npm for managing dependencies across runtimes.
