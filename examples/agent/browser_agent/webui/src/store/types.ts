export type AppMode = 'plan' | 'explore';
export type RightTab = 'chat' | 'workspace';
export type CenterTab = 'plan' | string; // 'plan' or agent_id

export interface ChatMessage {
    type: 'user' | 'assistant';
    agent_name: string;
    message: string;
    timestamp: string;
    agent_id?: string;
}

export interface AgentState {
    agent_id: string;
    status: 'idle' | 'initializing' | 'running' | 'done' | 'failed' | 'error';
    hostedUrl?: string | null;
    snapshot?: string | null;
    agentAction?: string | null;
    lastFrame?: string | null;
    isLocked?: boolean;
}

export interface AppState {
    appMode: AppMode;
    activeCenterTab: CenterTab;
    activeAgentId: string | null;
    activeRightTab: RightTab;

    messages: ChatMessage[];
    plan: any | null;
    agentStates: Record<string, AgentState>;
    artifacts: any[];

    sessionList: any[];
    activeSessionId: string | null;
    isHistoryView: boolean;

    connected: boolean;

    previewFiles: { sessionId: string; path: string; name: string }[];
    activePreviewIndex: number | null;
}

export type AppAction =
    | { type: 'SET_MODE'; mode: AppMode }
    | { type: 'SET_CENTER_TAB'; tab: CenterTab }
    | { type: 'SET_AGENT_ID'; agentId: string | null }
    | { type: 'SET_RIGHT_TAB'; tab: RightTab }
    | { type: 'SET_CONNECTED'; connected: boolean }
    | { type: 'SET_PLAN'; plan: any }
    | { type: 'ADD_MESSAGE'; message: ChatMessage }
    | { type: 'SET_MESSAGES'; messages: ChatMessage[] }
    | { type: 'UPDATE_AGENT_STATE'; agentId: string; patch: Partial<AgentState> }
    | { type: 'SET_AGENT_STATES'; states: Record<string, AgentState> }
    | { type: 'SET_SESSIONS'; sessions: any[] }
    | { type: 'LOAD_SESSION'; sessionId: string; detail: any }
    | { type: 'NEW_TASK' }
    | { type: 'START_RUN'; htmlPath: string }
    | { type: 'SET_ARTIFACTS'; artifacts: any[] }
    | { type: 'OPEN_PREVIEW'; sessionId: string; path: string; name: string }
    | { type: 'CLOSE_PREVIEW'; index: number }
    | { type: 'SET_ACTIVE_PREVIEW'; index: number | null };
