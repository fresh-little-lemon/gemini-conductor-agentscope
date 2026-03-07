# Specification: Plan+Explore Collaborative WebUI

## 1. Overview
Implement a comprehensive, real-time WebUI for the "Plan+Explore" agent pipeline. This interface will allow developers and researchers to monitor agent orchestration, visualize browser-based exploration, and perform manual takeovers when necessary, all while capturing high-fidelity interaction logs for training reward models.

## 2. Technical Architecture
- **Backend Service:** FastAPI (Python) serving as the orchestration and event-pushing layer.
- **Real-time Communication:** WebSockets for bidirectional frame streaming and control commands.
- **Frontend Framework:** React + Vite + TypeScript for a modern, high-performance UI.
- **Persistence:** Local file-based session management in a `sessions/` directory using JSON.
- **Browser Interaction:** Playwright via the Model Context Protocol (MCP) for CDP-based interaction and frame capture.

## 3. Functional Requirements
### 3.1 Layout & Navigation
- **Dual-Stage Layouts:**
  - **Plan Layout:** Focuses on the initial agent planning and interaction.
  - **Explore Layout:** Triggered automatically with smooth animations when moving to exploration.
- **Navigation Components:**
  - **Left Sidebar:** Session history based on local `sessions/` data.
  - **Center Area:** High-fidelity "Chrome-style" horizontal tabs for different sub-agent browser views.
  - **Right Panel:** Switchable panel between "Workspace" (Progress, Artifacts, Context) and "Chat".
- **File Previewing:** Read-only preview in the center area for Markdown, Text, Images, and Video (MP4).

### 3.2 Real-time Monitoring & Control
- **CDP Stream:** Real-time screen capture from Playwright-MCP browsers, default 5 FPS (configurable in settings).
- **Manual Takeover:**
  - **Lock/Unlock:** Users can unlock the browser to take manual control.
  - **Auto-Relock:** Automatic lock after 30s of inactivity (configurable).
  - **Interaction Logging:** Record granular events (clicks, inputs, etc.) during manual takeover to inject back into agent context.
- **Event Streaming:** Live updates for agent status, messages, progress milestones, and artifacts.

### 3.3 Session Management & History
- **Replay Mode:** Support for both static (default) and interactive step-by-step playback of historical runs.
- **Session Indexing:** Automatic discovery and summarization of local session files.

## 4. Non-Functional Requirements
- **Performance:** Smooth UI transitions and low-latency command forwarding.
- **Security:** Strict path validation for the file previewing service to prevent directory traversal.
- **Extensibility:** Modular "Right Switch Bar" to allow registration of future panels beyond Workspace/Chat.

## 5. Acceptance Criteria
- Successful end-to-end run from Plan to Explore with automatic layout migration.
- Real-time CDP frame streaming and manual input forwarding verified.
- Manual operations are correctly logged and summaries injected into agent context upon relock.
- Session history correctly displays past runs and supports replay modes.
- Code coverage for new components meets project standards (>80%).
