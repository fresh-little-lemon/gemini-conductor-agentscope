import React from 'react';
import { useStore } from '../store/useStore';

interface ChatInterfaceProps {
  filterType?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ filterType }) => {
  const { messages } = useStore();
  
  const filteredMessages = filterType 
    ? messages.filter(m => m.type === filterType || m.type === 'system')
    : messages;

  return (
    <div className="flex flex-col gap-4">
      {filteredMessages.map((msg) => (
        <div 
          key={msg.id} 
          className={`flex flex-col ${msg.type === 'system' ? 'items-center' : 'items-start'}`}
        >
          {msg.type === 'system' ? (
            <div className="text-xs text-textMuted bg-gray-100 px-2 py-1 rounded-full">
              {msg.content}
            </div>
          ) : (
            <div className="max-w-[90%] bg-white border border-borderSubtle p-3 rounded-lg shadow-sm">
              <div className="text-xs font-bold text-accentPrimary mb-1 uppercase">
                {msg.type.replace('_', ' ')}
              </div>
              <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
              <div className="text-[10px] text-textMuted mt-2 text-right">
                {new Date(msg.ts).toLocaleTimeString()}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default ChatInterface;
