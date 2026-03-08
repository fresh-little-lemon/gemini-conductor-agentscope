import React from 'react';
import { useStore } from '../store/useStore';
import { Lock, Unlock } from 'lucide-react';

interface LiveViewerProps {
  tabId: string;
}

const LiveViewer: React.FC<LiveViewerProps> = ({ tabId }) => {
  const { frames, lockState } = useStore();
  const frame = frames[tabId];
  const isLocked = lockState[tabId] !== false; // Default to locked

  return (
    <div className="relative w-full h-full bg-black flex items-center justify-center overflow-hidden">
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
      <div className="absolute top-4 right-4 flex gap-2">
        <div className={`p-2 rounded-full ${isLocked ? 'bg-red-500' : 'bg-green-500'} text-white shadow-lg`}>
          {isLocked ? <Lock className="w-5 h-5" /> : <Unlock className="w-5 h-5" />}
        </div>
      </div>
      
      {isLocked && (
        <div className="absolute inset-0 bg-black bg-opacity-10 cursor-not-allowed" />
      )}
    </div>
  );
};

export default LiveViewer;
