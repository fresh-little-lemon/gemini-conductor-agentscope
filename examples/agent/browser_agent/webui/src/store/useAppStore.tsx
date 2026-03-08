/**
 * Global app state managed via React Context + useReducer.
 *
 * Centralises what was previously scattered across App.tsx useState calls.
 * Includes localStorage persistence for key slices.
 */

import {
    createContext,
    useContext,
    useReducer,
    useEffect,
    type Dispatch,
    type ReactNode,
} from 'react';
import type { AppState, AppAction } from './types';

// ---------------------------------------------------------------------------
// Initial state (hydrated from localStorage where possible)
// ---------------------------------------------------------------------------

function loadJSON<T>(key: string, fallback: T): T {
    try {
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
    } catch {
        return fallback;
    }
}

const initialState: AppState = {
    appMode: (localStorage.getItem('as_app_mode') as AppState['appMode']) || 'plan',
    activeCenterTab: 'plan',
    activeAgentId: null,
    activeRightTab: 'workspace',

    messages: loadJSON('as_messages', []),
    plan: loadJSON('as_plan', null),
    agentStates: loadJSON('as_agent_states', {}),
    artifacts: [],

    sessionList: [],
    activeSessionId: localStorage.getItem('as_active_session') || null,
    isHistoryView: localStorage.getItem('as_history_view') === 'true',

    connected: false,

    previewFiles: [],
    activePreviewIndex: null,
};

// ---------------------------------------------------------------------------
// Reducer
// ---------------------------------------------------------------------------

function appReducer(state: AppState, action: AppAction): AppState {
    switch (action.type) {
        case 'SET_MODE':
            return { ...state, appMode: action.mode };

        case 'SET_CENTER_TAB': {
            const next: Partial<AppState> = { activeCenterTab: action.tab };
            // Coordination: Plan tab → force Workspace
            if (action.tab === 'plan') next.activeRightTab = 'workspace';
            return { ...state, ...next };
        }

        case 'SET_AGENT_ID':
            return { ...state, activeAgentId: action.agentId };

        case 'SET_RIGHT_TAB':
            return { ...state, activeRightTab: action.tab };

        case 'SET_CONNECTED':
            return { ...state, connected: action.connected };

        case 'SET_PLAN':
            return { ...state, plan: action.plan };

        case 'ADD_MESSAGE': {
            // Deduplicate consecutive identical user messages
            const prev = state.messages;
            if (action.message.type === 'user' && prev.length > 0) {
                const last = prev[prev.length - 1];
                if (last.type === 'user' && last.message === action.message.message) {
                    return state;
                }
            }
            return { ...state, messages: [...prev, action.message] };
        }

        case 'SET_MESSAGES':
            return { ...state, messages: action.messages };

        case 'UPDATE_AGENT_STATE': {
            const existing = state.agentStates[action.agentId] || {
                agent_id: action.agentId,
                hostedUrl: null,
                snapshot: null,
                agentAction: null,
            };
            return {
                ...state,
                agentStates: {
                    ...state.agentStates,
                    [action.agentId]: { ...existing, ...action.patch },
                },
            };
        }

        case 'SET_AGENT_STATES':
            return { ...state, agentStates: action.states };

        case 'SET_SESSIONS':
            return { ...state, sessionList: action.sessions };

        case 'LOAD_SESSION':
            return {
                ...state,
                isHistoryView: true,
                activeSessionId: action.sessionId,
                plan: action.detail.plan,
                messages: action.detail.messages,
                agentStates: action.detail.agent_states,
                artifacts: action.detail.artifacts || [],
                appMode: 'explore',
                activeCenterTab: 'plan',
            };

        case 'NEW_TASK':
            return {
                ...state,
                isHistoryView: false,
                activeSessionId: null,
                plan: null,
                messages: [],
                agentStates: {},
                artifacts: [],
                appMode: 'plan',
                activeAgentId: null,
                previewFiles: [],
                activePreviewIndex: null,
            };

        case 'START_RUN':
            return {
                ...state,
                agentStates: {},
                activeAgentId: null,
                plan: null,
                messages: [
                    {
                        type: 'user',
                        agent_name: 'User',
                        message: action.htmlPath,
                        timestamp: new Date().toISOString(),
                    },
                ],
            };

        case 'SET_ARTIFACTS':
            return { ...state, artifacts: action.artifacts };

        case 'OPEN_PREVIEW': {
            const existing = state.previewFiles.findIndex(
                (f) => f.sessionId === action.sessionId && f.path === action.path
            );
            if (existing >= 0) {
                return { ...state, activePreviewIndex: existing };
            }
            const files = [...state.previewFiles, { sessionId: action.sessionId, path: action.path, name: action.name }];
            return { ...state, previewFiles: files, activePreviewIndex: files.length - 1 };
        }

        case 'CLOSE_PREVIEW': {
            const files = state.previewFiles.filter((_, i) => i !== action.index);
            let idx = state.activePreviewIndex;
            if (idx !== null) {
                if (idx === action.index) idx = files.length > 0 ? Math.min(idx, files.length - 1) : null;
                else if (idx > action.index) idx--;
            }
            return { ...state, previewFiles: files, activePreviewIndex: idx };
        }

        case 'SET_ACTIVE_PREVIEW':
            return { ...state, activePreviewIndex: action.index };

        default:
            return state;
    }
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AppStateContext = createContext<AppState>(initialState);
const AppDispatchContext = createContext<Dispatch<AppAction>>(() => { });

export function AppProvider({ children }: { children: ReactNode }) {
    const [state, dispatch] = useReducer(appReducer, initialState);

    // Persist key slices to localStorage
    useEffect(() => {
        localStorage.setItem('as_app_mode', state.appMode);
    }, [state.appMode]);

    useEffect(() => {
        if (!state.isHistoryView) {
            try { localStorage.setItem('as_messages', JSON.stringify(state.messages)); } catch { /* noop */ }
        }
    }, [state.messages, state.isHistoryView]);

    useEffect(() => {
        if (!state.isHistoryView) {
            try { localStorage.setItem('as_plan', JSON.stringify(state.plan)); } catch { /* noop */ }
        }
    }, [state.plan, state.isHistoryView]);

    useEffect(() => {
        try {
            const filtered = Object.fromEntries(
                Object.entries(state.agentStates).map(([id, s]) => [id, { ...s, snapshot: null, agentAction: null }])
            );
            localStorage.setItem('as_agent_states', JSON.stringify(filtered));
        } catch { /* noop */ }
    }, [state.agentStates]);

    useEffect(() => {
        localStorage.setItem('as_active_session', state.activeSessionId || '');
        localStorage.setItem('as_history_view', state.isHistoryView.toString());
    }, [state.activeSessionId, state.isHistoryView]);

    return (
        <AppStateContext.Provider value= { state } >
        <AppDispatchContext.Provider value={ dispatch }>
            { children }
            </AppDispatchContext.Provider>
            </AppStateContext.Provider>
  );
}

export function useAppState(): AppState {
    return useContext(AppStateContext);
}

export function useAppDispatch(): Dispatch<AppAction> {
    return useContext(AppDispatchContext);
}
