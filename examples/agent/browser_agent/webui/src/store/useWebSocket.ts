import { useEffect, useRef } from 'react';
import { useAppDispatch } from './useAppStore';

export function useWebSocket() {
    const dispatch = useAppDispatch();
    const socketRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host || 'localhost:8000';
        const wsUrl = `${protocol}//${host}/ws`;

        const connect = () => {
            const socket = new WebSocket(wsUrl);
            socketRef.current = socket;

            socket.onopen = () => {
                console.log('WS Connected');
                dispatch({ type: 'SET_CONNECTED', connected: true });
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleEvent(data);
            };

            socket.onclose = () => {
                console.log('WS Disconnected, retrying...');
                dispatch({ type: 'SET_CONNECTED', connected: false });
                setTimeout(connect, 3000);
            };

            socket.onerror = (err) => {
                console.error('WS Error:', err);
                socket.close();
            };
        };

        const handleEvent = (event: any) => {
            const { type, payload } = event;

            switch (type) {
                case 'run.stage':
                    if (payload.stage === 'planning') {
                        dispatch({ type: 'SET_MODE', mode: 'plan' });
                        dispatch({ type: 'SET_CENTER_TAB', tab: 'plan' });
                    } else if (payload.stage === 'dispatching') {
                        dispatch({ type: 'SET_MODE', mode: 'explore' });
                    }
                    break;

                case 'plan.chat.chunk':
                    dispatch({
                        type: 'ADD_MESSAGE',
                        message: {
                            type: 'assistant',
                            agent_name: payload.agent_id || 'System',
                            message: payload.content,
                            timestamp: new Date().toISOString(),
                            agent_id: payload.agent_id
                        }
                    });
                    break;

                case 'group.status':
                    dispatch({
                        type: 'UPDATE_AGENT_STATE',
                        agentId: payload.agent_id,
                        patch: { status: payload.status }
                    });
                    if (payload.status === 'running') {
                        dispatch({ type: 'SET_AGENT_ID', agentId: payload.agent_id });
                    }
                    break;

                case 'workspace.progress':
                    if (payload.plan) {
                        dispatch({ type: 'SET_PLAN', plan: payload.plan });
                    }
                    break;

                case 'workspace.artifacts':
                    dispatch({ type: 'SET_ARTIFACTS', artifacts: payload.artifacts });
                    break;

                case 'viewer.frame':
                    dispatch({
                        type: 'UPDATE_AGENT_STATE',
                        agentId: payload.agent_id,
                        patch: { lastFrame: payload.frame }
                    });
                    break;

                case 'viewer.lock_state':
                    dispatch({
                        type: 'UPDATE_AGENT_STATE',
                        agentId: payload.agent_id,
                        patch: { isLocked: payload.is_locked }
                    });
                    break;

                default:
                    console.log('Unhandled event:', event);
            }
        };

        connect();

        return () => {
            if (socketRef.current) {
                socketRef.current.close();
            }
        };
    }, [dispatch]);

    const sendCommand = (type: string, agentId: string | null, payload?: any) => {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({
                type,
                agent_id: agentId,
                payload
            }));
        }
    };

    return { sendCommand };
}
