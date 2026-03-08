import { create } from 'zustand';

export interface RunEvent {
  type: string;
  runId?: string;
  ts: string;
  payload: Record<string, any>;
}

interface Message {
  id: string;
  type: 'action' | 'api_request' | 'api_response' | 'system';
  content: string;
  ts: string;
}

interface Artifact {
  id: string;
  name: string;
  path: string;
  type: string;
}

interface AppState {
  runId: string | null;
  currentStage: 'idle' | 'planning' | 'dispatching' | 'aggregation' | 'done';
  messages: Message[];
  artifacts: Artifact[];
  activeTab: string; // 'plan' or agent_id
  tabs: string[];
  frames: Record<string, string>; // tabId -> base64 frame
  lockState: Record<string, boolean>; // tabId -> isLocked
  
  // Actions
  handleEvent: (event: RunEvent) => void;
  setRunId: (id: string | null) => void;
  setActiveTab: (id: string) => void;
}

export const useStore = create<AppState>((set) => ({
  runId: null,
  currentStage: 'idle',
  messages: [],
  artifacts: [],
  activeTab: 'plan',
  tabs: ['plan'],
  frames: {},
  lockState: {},

  setRunId: (id) => set({ runId: id }),
  setActiveTab: (id) => set({ activeTab: id }),

  handleEvent: (event) => {
    const { type, payload } = event;

    switch (type) {
      case 'run.stage':
        if (payload.stage === 'planning') {
          set({
            currentStage: payload.stage,
            tabs: ['plan'],
            activeTab: 'plan',
            messages: [],
            artifacts: [],
            frames: {},
            lockState: {}
          });
        } else {
          set({ currentStage: payload.stage });
        }
        break;
      
      case 'plan.chat.chunk':
      case 'agent.chat':
        set((state) => ({
          messages: [...state.messages, {
            id: Math.random().toString(36).substr(2, 9),
            type: type === 'plan.chat.chunk' ? 'system' : payload.type,
            content: payload.content,
            ts: event.ts
          }]
        }));
        break;

      case 'workspace.artifacts':
        set((state) => ({
          artifacts: [...state.artifacts, ...payload.artifacts]
        }));
        break;

      case 'viewer.frame':
        set((state) => {
          const tabId = payload.tabId || 'default';
          const newTabs = state.tabs.includes(tabId) 
            ? state.tabs 
            : [...state.tabs, tabId];
          return {
            tabs: newTabs,
            frames: {
              ...state.frames,
              [tabId]: payload.frame
            }
          };
        });
        break;

      case 'viewer.lock_state':
        set((state) => ({
          lockState: {
            ...state.lockState,
            [payload.tabId]: payload.locked
          }
        }));
        break;

      default:
        console.warn('Unhandled event type:', type);
    }
  }
}));
