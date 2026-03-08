import { useState } from 'react';
import { Lock, Unlock, RotateCcw, ChevronLeft, ChevronRight, Home } from 'lucide-react';
import { cn } from '../lib/utils';

export default function BrowserView() {
    const [isLocked, setIsLocked] = useState(true);

    return (
        <div className="h-full flex flex-col bg-gray-100">
            {/* Browser Navbar */}
            <div className="flex items-center gap-2 px-4 py-2 bg-white border-b border-borderSubtle shadow-sm">
                <div className="flex items-center gap-1 mr-2">
                    <button className="p-1 hover:bg-gray-100 rounded text-gray-500"><ChevronLeft size={18} /></button>
                    <button className="p-1 hover:bg-gray-100 rounded text-gray-500"><ChevronRight size={18} /></button>
                    <button className="p-1 hover:bg-gray-100 rounded text-gray-500"><RotateCcw size={18} /></button>
                </div>

                <div className="flex-1 flex items-center bg-gray-100 rounded-lg px-3 py-1.5 text-sm text-gray-600 gap-2 border border-transparent focus-within:border-accentPrimary focus-within:bg-white transition-all">
                    <Globe size={14} className="text-gray-400" />
                    <span className="truncate">https://instacart.com</span>
                </div>

                <button className="p-1.5 hover:bg-gray-100 rounded text-gray-500 ml-2"><Home size={18} /></button>
            </div>

            {/* Main Browser Viewport */}
            <div className="flex-1 relative overflow-hidden bg-white m-4 rounded-xl border border-borderSubtle shadow-xl overflow-y-auto">
                {/* Mock Browser Content (from ChatGPT Atlas example) */}
                <div className="w-full min-h-full p-8 text-center text-gray-300 flex flex-col items-center justify-center pointer-events-none select-none">
                    <div className="w-full max-w-4xl p-8 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200">
                        <h2 className="text-2xl font-bold text-gray-400 mb-4">Browser Viewport Stream</h2>
                        <p className="text-gray-400">Agent is currently exploring the page...</p>
                        {/* Image Placeholder */}
                        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4 opacity-50">
                            {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                                <div key={i} className="aspect-square bg-gray-200 rounded-lg animate-pulse" />
                            ))}
                        </div>
                    </div>
                </div>

                {/* Lock Overlay */}
                {isLocked && (
                    <div className="absolute inset-0 bg-white/20 backdrop-blur-[1px] flex items-center justify-center z-10">
                        <div className="p-6 bg-white/90 shadow-2xl rounded-2xl border border-white/50 flex flex-col items-center gap-4 animate-in fade-in zoom-in duration-300">
                            <div className="p-4 bg-gray-100 rounded-full text-textMain">
                                <Lock size={32} />
                            </div>
                            <div className="text-center">
                                <p className="text-lg font-semibold text-textMain">Screen is locked</p>
                                <p className="text-sm text-textMuted">Interaction is disabled while agent is working</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Floating Controls (Corner) */}
                <div className="absolute bottom-6 right-6 z-20">
                    <button
                        onClick={() => setIsLocked(!isLocked)}
                        className={cn(
                            "flex items-center gap-2 px-5 py-2.5 rounded-full shadow-2xl transition-all font-medium text-sm border-2",
                            isLocked
                                ? "bg-textMain text-white border-white/20 hover:scale-105 active:scale-95"
                                : "bg-red-500 text-white border-red-400 hover:bg-red-600"
                        )}
                    >
                        {isLocked ? (
                            <>
                                <Unlock size={16} />
                                <span>Take control</span>
                            </>
                        ) : (
                            <>
                                <Lock size={16} />
                                <span>Stop controlling</span>
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}

function Globe({ size, className }: { size: number, className?: string }) {
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
            <circle cx="12" cy="12" r="10" />
            <line x1="2" y1="12" x2="22" y2="12" />
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
    );
}
