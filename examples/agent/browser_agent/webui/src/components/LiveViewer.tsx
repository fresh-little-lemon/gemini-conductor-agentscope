import React, { useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import { Lock, Unlock } from 'lucide-react';

interface LiveViewerProps {
  tabId: string;
}

const LiveViewer: React.FC<LiveViewerProps> = ({ tabId }) => {
  const { frames, lockState } = useStore();
  const frame = frames[tabId];
  const isLocked = lockState[tabId] !== false;
  
  const controlWs = useRef<WebSocket | null>(null);
  const autoLockTimer = useRef<number | null>(null);

  useEffect(() => {
    controlWs.current = new WebSocket('ws://localhost:8000/control');
    return () => controlWs.current?.close();
  }, []);

  const toggleLock = () => {
    if (isLocked) {
      // Unlock: pause agent and unlock viewer
      controlWs.current?.send(JSON.stringify({
        type: 'agent.pause',
        payload: { agentId: tabId }
      }));
      controlWs.current?.send(JSON.stringify({
        type: 'viewer.unlock',
        payload: { tabId }
      }));
      
      // Start auto-lock timer (30s)
      resetAutoLockTimer();
    } else {
      lockManually();
    }
  };

  const lockManually = () => {
    controlWs.current?.send(JSON.stringify({
      type: 'viewer.lock',
      payload: { tabId }
    }));
    controlWs.current?.send(JSON.stringify({
      type: 'agent.resume',
      payload: { agentId: tabId }
    }));
    if (autoLockTimer.current) window.clearTimeout(autoLockTimer.current);
  };

  const resetAutoLockTimer = () => {
    if (autoLockTimer.current) window.clearTimeout(autoLockTimer.current);
    autoLockTimer.current = window.setTimeout(() => {
      console.log('Auto-relocking due to inactivity');
      lockManually();
    }, 30000);
  };

  const handleInteraction = () => {
    if (!isLocked) {
      resetAutoLockTimer();
    }
  };

  return (
    <div 
      className="relative w-full h-full bg-black flex items-center justify-center overflow-hidden"
      onMouseMove={handleInteraction}
      onClick={handleInteraction}
      onKeyDown={handleInteraction}
    >
      {frame ? (
        <img 
          src={`data:image/jpeg;base64,${frame}`} 
          alt={`Agent Browser ${tabId}`}
          className="max-w-full max-h-full object-contain"
        />
      ) : (
        <div className="text-white flex flex-col items-center gap-2">
          <div className="animate-pulse w-12 h-12 bg-gray-700 rounded-full" />
          <span>Waiting for stream...</span>
        </div>
      )}

      {/* Lock Overlay */}
      <div className="absolute top-4 right-4 flex gap-2 z-10">
        <button 
          onClick={toggleLock}
          className={`p-2 rounded-full ${isLocked ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'} text-white shadow-lg transition-colors`}
        >
          {isLocked ? <Lock className="w-5 h-5" /> : <Unlock className="w-5 h-5" />}
        </button>
      </div>
      
      {isLocked && (
        <div className="absolute inset-0 bg-black bg-opacity-10 cursor-not-allowed" />
      )}
    </div>
  );
};

export default LiveViewer;
