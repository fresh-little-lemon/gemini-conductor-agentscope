import { Plus, MessageSquare, Code, Layout, Settings } from 'lucide-react';
import { cn } from '../lib/utils';

interface SidebarProps {
    className?: string;
}

const sessions = [
    "Organize folder by file type",
    "Prepare Vercel analytics daily report",
    "Review best performing analytics...",
    "Auto-reply emails with Superhuman",
    "Draft Slack message for channel"
];

export default function Sidebar({ className }: SidebarProps) {
    return (
        <div className={cn("flex flex-col h-full", className)}>
            <div className="p-4 flex flex-col gap-4">
                {/* Top Switcher (Claude style) */}
                <div className="flex bg-gray-100 p-1 rounded-lg">
                    <button className="flex-1 flex items-center justify-center gap-1 py-1.5 px-3 rounded-md bg-white shadow-sm text-sm font-medium">
                        <MessageSquare size={14} />
                        Chat
                    </button>
                    <button className="flex-1 flex items-center justify-center gap-1 py-1.5 px-3 rounded-md text-gray-500 hover:text-gray-700 text-sm font-medium">
                        <Code size={14} />
                        Code
                    </button>
                    <button className="flex-1 flex items-center justify-center gap-1 py-1.5 px-3 rounded-md text-gray-500 hover:text-gray-700 text-sm font-medium">
                        <Layout size={14} />
                        Cowork
                    </button>
                </div>

                <button className="flex items-center gap-2 w-full p-2.5 rounded-lg border border-borderSubtle hover:bg-gray-50 transition-colors text-sm font-medium">
                    <Plus size={18} className="text-gray-500" />
                    New task
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-2">
                <ul className="space-y-1">
                    {sessions.map((session, i) => (
                        <li key={i}>
                            <button className={cn(
                                "w-full text-left p-2.5 rounded-lg text-sm transition-colors truncate",
                                i === 0 ? "bg-gray-100 font-medium" : "text-gray-600 hover:bg-gray-50"
                            )}>
                                {session}
                            </button>
                        </li>
                    ))}
                </ul>
            </div>

            <div className="p-4 border-t border-borderSubtle">
                <div className="text-xs text-gray-400 mb-4 px-2">
                    These tasks run locally and aren't synced across devices
                </div>
                <button className="flex items-center gap-2 p-2 w-full rounded-lg hover:bg-gray-50 text-gray-500 transition-colors">
                    <Settings size={18} />
                    <span className="text-sm">Settings</span>
                </button>
            </div>
        </div>
    );
}
