import React, { useEffect } from 'react';
import Sidebar from './components/Sidebar';
import AgentTabs from './components/AgentTabs';
import LiveViewer from './components/LiveViewer';
import ChatInterface from './components/ChatInterface';
import RightSidebar from './components/RightSidebar';
import { useStore } from './store/useStore';

const App: React.FC = () => {
  const { currentStage, activeTab, handleEvent } = useStore();

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/events');
    ws.onmessage = (event) => {
      const runEvent = JSON.parse(event.data);
      handleEvent(runEvent);
    };
    return () => ws.close();
  }, [handleEvent]);

  const isExploreStage = currentStage === 'dispatching' || currentStage === 'done';

  return (
    <div className="flex h-screen w-full overflow-hidden bg-bgMain">
      {/* Left Sidebar - Session History */}
      <div className={`layout-transition ${isExploreStage ? 'w-0 opacity-0 invisible' : 'w-64'}`}>
        <Sidebar />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <AgentTabs />
        
        <div className="flex-1 flex overflow-hidden">
          {/* Center Area: Viewer or Plan Chat */}
          <div className="flex-1 relative border-r border-borderSubtle">
            {activeTab === 'plan' ? (
              <ChatInterface filterType="system" />
            ) : (
              <LiveViewer tabId={activeTab} />
            )}
          </div>

          {/* Right Panel: Workspace or Sub-agent Chat */}
          <div className="w-96 flex flex-col bg-white">
             <RightSidebar />
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
