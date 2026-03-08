import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../store/useStore';
import { Send, Terminal } from 'lucide-react';

interface ChatInterfaceProps {
  filterType?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ filterType }) => {
  const { messages, currentStage } = useStore();
  const [inputValue, setInputValue] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    
    // In a real app, we might send this to the backend
    // For now, let's trigger the /run endpoint if we're idle
    if (currentStage === 'idle' || currentStage === 'done') {
       try {
         await fetch(`http://localhost:8000/run?html_path=${encodeURIComponent(inputValue)}`, {
           method: 'POST'
         });
         setInputValue('');
       } catch (err) {
         console.error('Failed to start run:', err);
       }
    } else {
       // Handle sending messages to active agents if needed
       console.log('Sending message to agent:', inputValue);
       setInputValue('');
    }
  };

  const filteredMessages = filterType 
    ? messages.filter(m => m.type === filterType || m.type === 'system')
    : messages;

  return (
    <div className="flex flex-col h-full">
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
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

      {/* Input Area */}
      <div className="p-4 border-t border-borderSubtle bg-white">
        <div className="relative flex items-center">
          <Terminal className="absolute left-3 w-4 h-4 text-textMuted" />
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={currentStage === 'idle' || currentStage === 'done' ? "Enter HTML path to start..." : "Message agent..."}
            className="w-full pl-10 pr-12 py-3 bg-gray-50 border border-borderSubtle rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accentPrimary focus:bg-white transition-all"
          />
          <button 
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="absolute right-2 p-2 text-accentPrimary hover:bg-blue-50 rounded-lg disabled:opacity-30 transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <div className="mt-2 text-[10px] text-textMuted text-center">
          {currentStage === 'idle' || currentStage === 'done' ? "Ready to launch new exploration" : "Agent is running..."}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
