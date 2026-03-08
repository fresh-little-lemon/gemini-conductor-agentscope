import { useState } from 'react';
import type { AppMode } from '../App';
import ChatInterface from './ChatInterface';
import BrowserView from './BrowserView';
import { cn } from '../lib/utils';
import { X, Globe, MessageSquare } from 'lucide-react';

interface CenterAreaProps {
    appMode: AppMode;
    onSwitchMode: (mode: AppMode) => void;
}

export default function CenterArea({ onSwitchMode }: CenterAreaProps) {
    const [activeTab, setActiveTab] = useState<'plan' | 'browser'>('plan');

    const tabs = [
        { id: 'plan', title: 'Plan', icon: MessageSquare },
        { id: 'browser', title: 'Browser', icon: Globe },
    ];

    const handleTabClick = (tabId: 'plan' | 'browser') => {
        setActiveTab(tabId);
        if (tabId === 'plan') {
            onSwitchMode('plan');
        } else {
            onSwitchMode('explore');
        }
    };

    return (
        <div className="flex flex-col h-full bg-white">
            {/* VSCode style Tab Bar */}
            <div className="flex bg-gray-50 border-b border-borderSubtle h-10 items-center overflow-x-auto no-scrollbar">
                {tabs.map((tab) => (
                    <div
                        key={tab.id}
                        onClick={() => handleTabClick(tab.id as any)}
                        className={cn(
                            "flex items-center gap-2 px-4 h-full border-r border-borderSubtle cursor-pointer min-w-[120px] transition-colors relative",
                            activeTab === tab.id
                                ? "bg-white text-textMain"
                                : "text-gray-500 hover:bg-gray-100"
                        )}
                    >
                        {activeTab === tab.id && (
                            <div className="absolute top-0 left-0 right-0 h-0.5 bg-accentPrimary" />
                        )}
                        <tab.icon size={14} className={activeTab === tab.id ? "text-accentPrimary" : "text-gray-400"} />
                        <span className="text-sm truncate">{tab.title}</span>
                        <X size={12} className="ml-auto text-gray-400 hover:text-gray-600 rounded-sm hover:bg-gray-200" />
                    </div>
                ))}
            </div>

            {/* Content Area */}
            <div className="flex-1 relative overflow-hidden">
                {activeTab === 'plan' ? (
                    <div className="h-full flex flex-col items-center justify-center p-4">
                        <div className="w-full max-w-4xl h-full">
                            <ChatInterface isSidebar={false} />
                        </div>
                    </div>
                ) : (
                    <BrowserView />
                )}
            </div>
        </div>
    );
}
