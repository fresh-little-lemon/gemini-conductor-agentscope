import { describe, it, expect, beforeEach } from 'vitest';
import { useStore, RunEvent } from './useStore';

describe('useStore', () => {
  beforeEach(() => {
    // Reset store before each test (manually)
    useStore.setState({
      runId: null,
      currentStage: 'idle',
      messages: [],
      artifacts: [],
      activeTab: 'plan',
      frames: {},
      lockState: {},
    });
  });

  it('updates currentStage on run.stage event', () => {
    const event: RunEvent = {
      type: 'run.stage',
      ts: new Date().toISOString(),
      payload: { stage: 'planning' }
    };
    
    useStore.getState().handleEvent(event);
    expect(useStore.getState().currentStage).toBe('planning');
  });

  it('adds messages on agent.chat event', () => {
    const event: RunEvent = {
      type: 'agent.chat',
      ts: new Date().toISOString(),
      payload: { type: 'action', content: 'Click button' }
    };
    
    useStore.getState().handleEvent(event);
    expect(useStore.getState().messages).toHaveLength(1);
    expect(useStore.getState().messages[0].content).toBe('Click button');
  });

  it('updates frames on viewer.frame event', () => {
    const event: RunEvent = {
      type: 'viewer.frame',
      ts: new Date().toISOString(),
      payload: { tabId: 'agent1', frame: 'base64data' }
    };
    
    useStore.getState().handleEvent(event);
    expect(useStore.getState().frames['agent1']).toBe('base64data');
  });
});
