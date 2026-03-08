import type { AppMode, RightTab } from '../App';
import ChatInterface from './ChatInterface';
import InfoPanel from './InfoPanel';
import { cn } from '../lib/utils';
import { MessageSquare } from 'lucide-react';

interface RightSidebarProps {
    appMode: AppMode;
    activeRightTab: RightTab;
    setActiveRightTab: (tab: RightTab) => void;
}

export default function RightSidebar({
    activeRightTab,
    setActiveRightTab
}: RightSidebarProps) {

    return (
        <div className="flex flex-col h-full">
            {/* Tab Switcher (Claude style) */}
            <div className="px-4 mb-4">
                <div className="flex bg-gray-100 p-1 rounded-lg">
                    <button
                        onClick={() => setActiveRightTab('chat')}
                        className={cn(
                            "flex-1 flex items-center justify-center gap-1 py-1.5 px-3 rounded-md text-sm font-medium transition-all",
                            activeRightTab === 'chat' ? "bg-white shadow-sm text-textMain" : "text-gray-500 hover:text-gray-700"
                        )}
                    >
                        <MessageSquare size={14} />
                        Chat
                    </button>
                    <button
                        onClick={() => setActiveRightTab('workspace')}
                        className={cn(
                            "flex-1 flex items-center justify-center gap-1 py-1.5 px-3 rounded-md text-sm font-medium transition-all",
                            activeRightTab === 'workspace' ? "bg-white shadow-sm text-textMain" : "text-gray-500 hover:text-gray-700"
                        )}
                    >
                        <LayoutWorkspace size={14} />
                        Workspace
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-hidden">
                {activeRightTab === 'chat' ? (
                    <ChatInterface isSidebar={true} />
                ) : (
                    <InfoPanel />
                )}
            </div>
        </div>
    );
}

// Simple Layout icon fallback
function LayoutWorkspace({ size, className }: { size: number, className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            <rect width="18" height="18" x="3" y="3" rx="2" />
            <path d="M3 9h18" />
            <path d="M9 21V9" />
        </svg>
    );
}
