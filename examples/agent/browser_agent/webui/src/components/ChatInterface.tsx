import { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Paperclip, ChevronDown, Plus } from 'lucide-react';
import { cn } from '../lib/utils';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    type?: 'text' | 'step' | 'plan';
    steps?: { title: string; status: 'done' | 'running' | 'pending' }[];
}

interface ChatInterfaceProps {
    isSidebar?: boolean;
}

export default function ChatInterface({ isSidebar = false }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: 'assistant',
            content: "I'll analyze the receipts and create a neat spreadsheet for you. Let me first read the skill file and then examine the receipts.",
            type: 'plan',
            steps: [
                { title: "Reading file", status: 'done' },
                { title: "Running command", status: 'running' },
                { title: "Updating todo list", status: 'pending' },
            ]
        },
        {
            role: 'user',
            content: "Can you help me organize these receipts into a spreadsheet?",
        },
    ]);
    const [input, setInput] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = () => {
        if (!input.trim()) return;
        setMessages([...messages, { role: 'user', content: input }]);
        setInput('');
    };

    return (
        <div className={cn("flex flex-col h-full bg-white", isSidebar ? "w-full" : "max-w-4xl mx-auto")}>
            {/* Search / Context Bar for Chat (optional) */}
            {!isSidebar && (
                <div className="flex items-center gap-2 px-4 py-3 border-b border-borderSubtle">
                    <h1 className="text-lg font-semibold truncate text-textMain">Organize folder by file type</h1>
                </div>
            )}

            {/* Messages */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto px-4 py-6 space-y-8 no-scrollbar"
            >
                {messages.map((msg, idx) => (
                    <div key={idx} className={cn(
                        "flex gap-4",
                        msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                    )}>
                        <div className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                            msg.role === 'user' ? "bg-accentPrimary text-white" : "bg-gray-100 text-gray-500"
                        )}>
                            {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                        </div>

                        <div className={cn(
                            "flex flex-col gap-2 max-w-[85%]",
                            msg.role === 'user' ? "items-end text-right" : "items-start text-left"
                        )}>
                            <div className={cn(
                                "p-3 rounded-2xl text-sm leading-relaxed",
                                msg.role === 'user' ? "bg-accentPrimary text-white" : "bg-white border border-gray-100 shadow-sm text-gray-800"
                            )}>
                                {msg.content}
                            </div>

                            {/* Agent Steps / Thinking (Claude style) */}
                            {msg.steps && (
                                <div className="w-full mt-2 space-y-2">
                                    <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-100">
                                        <div className="animate-spin h-3 w-3 border-2 border-accentPrimary/30 border-t-accentPrimary rounded-full" />
                                        <span className="text-xs text-gray-500 font-medium">Running 3 steps...</span>
                                        <ChevronDown size={14} className="ml-auto text-gray-400" />
                                    </div>
                                    <div className="pl-4 border-l-2 border-gray-100 space-y-2">
                                        {msg.steps.map((step, sIdx) => (
                                            <div key={sIdx} className="flex items-center gap-2 text-xs">
                                                <div className={cn(
                                                    "w-1.5 h-1.5 rounded-full",
                                                    step.status === 'done' ? "bg-green-500" : (step.status === 'running' ? "bg-blue-500" : "bg-gray-200")
                                                )} />
                                                <span className={step.status === 'pending' ? "text-gray-400" : "text-gray-600"}>{step.title}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-borderSubtle">
                <div className="relative bg-gray-50 rounded-2xl border border-borderSubtle focus-within:border-accentPrimary transition-all p-2">
                    <textarea
                        rows={1}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
                        placeholder="Message agent..."
                        className="w-full bg-transparent border-none focus:ring-0 text-sm py-2 px-3 min-h-[44px] max-h-48 resize-none scroll-smooth"
                    />
                    <div className="flex items-center justify-between mt-1 px-1">
                        <div className="flex gap-2">
                            <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-200"><Paperclip size={18} /></button>
                            <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-200"><Plus size={18} /></button>
                        </div>
                        <button
                            onClick={handleSend}
                            disabled={!input.trim()}
                            className={cn(
                                "p-2 rounded-xl transition-all",
                                input.trim() ? "bg-accentPrimary text-white shadow-lg shadow-accentPrimary/20" : "bg-gray-200 text-gray-400"
                            )}
                        >
                            <Send size={18} />
                        </button>
                    </div>
                </div>
                <p className="text-[10px] text-center text-muted-foreground mt-2 text-gray-400">
                    Agent can make mistakes. Verify important information.
                </p>
            </div>
        </div>
    );
}
