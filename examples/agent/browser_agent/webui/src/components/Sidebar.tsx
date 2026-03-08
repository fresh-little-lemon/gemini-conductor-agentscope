import React, { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { Clock, FolderOpen } from 'lucide-react';

interface Session {
  id: string;
  timestamp: string;
  title: string;
  status: string;
  task_count: number;
}

const Sidebar: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const { setRunId } = useStore();

  useEffect(() => {
    fetch('http://localhost:8000/sessions')
      .then(res => res.json())
      .then(data => setSessions(data))
      .catch(err => console.error('Failed to fetch sessions:', err));
  }, []);

  return (
    <div className="w-64 bg-white border-r border-borderSubtle flex flex-col h-screen overflow-hidden">
      <div className="p-4 border-b border-borderSubtle">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Sessions
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        {sessions.map(session => (
          <div 
            key={session.id}
            onClick={() => setRunId(session.id)}
            className="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-50 transition-colors"
          >
            <div className="text-sm font-medium truncate">{session.id}</div>
            <div className="text-xs text-textMuted flex items-center gap-1 mt-1">
              <FolderOpen className="w-3 h-3" />
              {session.task_count} tasks
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;
