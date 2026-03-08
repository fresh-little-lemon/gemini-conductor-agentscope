# Implementation Plan: Plan+Explore Collaborative WebUI

## Phase 1: Backend Foundation & Event Streaming
- [x] Task: Implement Central Event System
    - [ ] Write unit tests for the event bus and emitter logic
    - [ ] Implement the `EventSink` and `ControlHub` in the orchestration layer
- [x] Task: Set up FastAPI WebSocket Service
    - [ ] Write tests for real-time message streaming via WebSockets
    - [ ] Implement the FastAPI server and WebSocket endpoint for `RunEvent` broadcasting
- [ ] Task: Conductor - User Manual Verification 'Backend Foundation & Event Streaming' (Protocol in workflow.md)

## Phase 2: Agent Control & CDP Bridge
- [x] Task: Implement Agent Control Gate
    - [ ] Write tests for the `AgentControlGate` pause/resume mechanism
    - [ ] Update `BrowserAgent` and `ExploringAgent` to support execution gating
- [x] Task: Implement CDP Bridge & Frame Capture
    - [ ] Write tests for CDP frame acquisition and input forwarding
    - [ ] Implement the `CDPBridge` to stream frames and handle `viewer.input` commands
- [ ] Task: Conductor - User Manual Verification 'Agent Control & CDP Bridge' (Protocol in workflow.md)

## Phase 3: Frontend Infrastructure & Global State
- [x] Task: Scaffold React/Vite Project
    - [ ] Set up the UI project structure with TypeScript and Tailwind CSS
    - [ ] Implement the core theme tokens and CSS animations for layout switching
- [x] Task: Implement Global State & Event Reducer
    - [ ] Write unit tests for state transitions based on `RunEvent` types
    - [ ] Implement the Zustand/Redux store and event handling logic
- [ ] Task: Conductor - User Manual Verification 'Frontend Infrastructure & Global State' (Protocol in workflow.md)

## Phase 4: Core UI Components
- [x] Task: Implement Session Sidebar & History
    - [ ] Write tests for session indexing and listing
    - [ ] Implement `SessionSidebar` with local persistence integration
- [x] Task: Implement Chrome-style Agent Tabs
    - [ ] Write tests for dynamic tab creation and switching
    - [ ] Implement the horizontal `AgentTabs` component
- [x] Task: Implement LiveViewer & File Preview
    - [ ] Write tests for CDP frame rendering and read-only file previews
    - [ ] Implement `LiveViewer` and the multi-format file previewer
- [ ] Task: Conductor - User Manual Verification 'Core UI Components' (Protocol in workflow.md)

## Phase 5: Interaction & Layout Logic
- [x] Task: Implement Animated Layout Switching
    - [ ] Write tests for layout migration triggers (Plan <-> Explore)
    - [ ] Implement the smooth transition logic between stages
- [x] Task: Implement Manual Takeover & Lock Logic
    - [ ] Write tests for the 30s auto-relock timeout and manual unlock
    - [ ] Implement the lock/unlock UI controls and background timers
- [x] Task: Implement Operation Logging & Context Injection
    - [ ] Write tests for granular event logging during manual takeover
    - [ ] Implement the logic to inject logged summaries back into the agent context
- [ ] Task: Conductor - User Manual Verification 'Interaction & Layout Logic' (Protocol in workflow.md)

## Phase 6: Persistence & Replay Mode
- [x] Task: Implement Session Persistence & Indexer
    - [ ] Write tests for session IO and aggregation from `sessions/`
    - [ ] Implement the `SessionIndexer` service
- [x] Task: Implement Static & Interactive Replay
    - [ ] Write tests for step-by-step log playback
    - [ ] Implement the Replay mode UI and settings-based mode switching
- [ ] Task: Conductor - User Manual Verification 'Persistence & Replay Mode' (Protocol in workflow.md)

## Phase 7: Final Integration & Acceptance
- [x] Task: End-to-End Acceptance Testing
    - [ ] Perform a full run from Plan to Explore, verifying layout transitions and monitoring
    - [ ] Verify manual takeover, operation injection, and session replay
- [ ] Task: Conductor - User Manual Verification 'Final Integration & Acceptance' (Protocol in workflow.md)

## Phase: Review Fixes
- [x] Task: Apply review suggestions (fix build errors in webui) f87c5ba
- [x] Task: Implement interactive message input in ChatInterface d1a862a
