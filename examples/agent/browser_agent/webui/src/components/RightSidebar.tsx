import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import { Briefcase, MessageSquare, ListTodo, FileBox } from 'lucide-react';
import ChatInterface from './ChatInterface';

const RightSidebar: React.FC = () => {
  const [activePanel, setActivePanel] = useState<'workspace' | 'chat'>('workspace');
  const { artifacts } = useStore();

  return (
    <div className="flex flex-col h-full border-l border-borderSubtle">
      {/* Switch Bar */}
      <div className="flex border-b border-borderSubtle bg-gray-50">
        <button 
          onClick={() => setActivePanel('workspace')}
          className={`flex-1 py-3 flex items-center justify-center gap-2 text-sm font-medium transition-colors ${activePanel === 'workspace' ? 'bg-white text-accentPrimary border-b-2 border-b-accentPrimary' : 'text-textMuted hover:bg-gray-100'}`}
        >
          <Briefcase className="w-4 h-4" />
          Workspace
        </button>
        <button 
          onClick={() => setActivePanel('chat')}
          className={`flex-1 py-3 flex items-center justify-center gap-2 text-sm font-medium transition-colors ${activePanel === 'chat' ? 'bg-white text-accentPrimary border-b-2 border-b-accentPrimary' : 'text-textMuted hover:bg-gray-100'}`}
        >
          <MessageSquare className="w-4 h-4" />
          Chat
        </button>
      </div>

      {/* Panel Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activePanel === 'workspace' ? (
          <div className="space-y-6">
            {/* Progress Section */}
            <section>
              <h3 className="text-xs font-bold text-textMuted uppercase mb-3 flex items-center gap-2">
                <ListTodo className="w-3 h-3" />
                Current Progress
              </h3>
              <div className="space-y-2">
                 <div className="p-3 bg-blue-50 border border-blue-100 rounded-md text-sm text-blue-800">
                    Agent is currently exploring the page...
                 </div>
              </div>
            </section>

            {/* Artifacts Section */}
            <section>
              <h3 className="text-xs font-bold text-textMuted uppercase mb-3 flex items-center gap-2">
                <FileBox className="w-3 h-3" />
                Artifacts
              </h3>
              <div className="space-y-2">
                {artifacts.length > 0 ? artifacts.map(art => (
                  <div key={art.id} className="p-2 border border-borderSubtle rounded-md hover:bg-gray-50 cursor-pointer text-sm">
                    {art.name}
                  </div>
                )) : (
                  <div className="text-xs text-textMuted italic">No artifacts generated yet.</div>
                )}
              </div>
            </section>
          </div>
        ) : (
          <ChatInterface />
        )}
      </div>
    </div>
  );
};

export default RightSidebar;
