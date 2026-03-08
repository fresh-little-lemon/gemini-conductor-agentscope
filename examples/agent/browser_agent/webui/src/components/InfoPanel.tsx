import { useState } from 'react';
import {
    CheckCircle2,
    ChevronDown,
    BarChart3,
    FileText,
    Folder,
    Clock
} from 'lucide-react';
import { cn } from '../lib/utils';

export default function InfoPanel() {
    return (
        <div className="flex flex-col h-full overflow-y-auto px-4 pb-8 no-scrollbar space-y-6">

            {/* Progress Section */}
            <Section title="Progress" icon={<Clock size={16} />}>
                <div className="space-y-4">
                    <ProgressItem
                        step="1"
                        label="Analyze receipt images to extract transaction data"
                        status="done"
                    />
                    <ProgressItem
                        step="2"
                        label="Creating spreadsheet"
                        status="active"
                    />
                    <ProgressItem
                        step="3"
                        label="Add budget recommendations section"
                        status="pending"
                    />
                    <ProgressItem
                        step="4"
                        label="Recalculate formulas and verify"
                        status="pending"
                    />
                </div>
            </Section>

            {/* Artifacts Section */}
            <Section title="Artifacts" icon={<BarChart3 size={16} />}>
                <div className="grid grid-cols-2 gap-3">
                    <div className="aspect-square bg-white border border-borderSubtle rounded-xl flex items-center justify-center p-4 hover:shadow-md transition-shadow cursor-pointer">
                        <BarChart3 size={32} className="text-gray-300" />
                    </div>
                    <div className="aspect-square bg-gray-50 border border-borderSubtle border-dashed rounded-xl flex items-center justify-center p-4 text-center">
                        <p className="text-[10px] text-gray-400">Outputs created during task land here.</p>
                    </div>
                </div>
            </Section>

            {/* Context Section */}
            <Section title="Context" icon={<FileText size={16} />}>
                <div className="space-y-4">
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                        <ChevronDown size={14} />
                        <span>Selected folders</span>
                        <span className="ml-auto">1</span>
                    </div>
                    <div className="flex items-center gap-2 pl-4 text-sm text-gray-600">
                        <Folder size={14} className="text-gray-400" />
                        <span>All Claude</span>
                    </div>

                    <div className="pt-2">
                        <p className="text-xs font-medium text-gray-400 mb-2">Working files</p>
                        <div className="space-y-2">
                            <FileItem name="SKILL.md" />
                            <FileItem name="receipt_amazon_dec15.png" />
                            <FileItem name="receipt_apple_dec22.png" />
                            <FileItem name="receipt_pret_dec20.png" isGray />
                        </div>
                        <button className="text-xs text-gray-400 hover:text-gray-600 mt-2">Show 2 more</button>
                    </div>
                </div>
            </Section>

        </div>
    );
}

function Section({ title, icon, children }: { title: string, icon: React.ReactNode, children: React.ReactNode }) {
    const [isOpen, setIsOpen] = useState(true);

    return (
        <div className="flex flex-col gap-3">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 w-full text-sm font-semibold text-textMain group"
            >
                <div className="text-gray-400 group-hover:text-gray-600 truncate flex items-center gap-2">
                    {icon}
                    {title}
                </div>
                <ChevronDown size={14} className={cn("ml-auto text-gray-400 transition-transform", !isOpen && "-rotate-90")} />
            </button>
            {isOpen && (
                <div className="animate-in slide-in-from-top-2 fade-in duration-200">
                    {children}
                </div>
            )}
        </div>
    );
}

function ProgressItem({ step, label, status }: { step: string, label: string, status: 'done' | 'active' | 'pending' }) {
    return (
        <div className="flex gap-3 group">
            <div className="relative flex flex-col items-center">
                <div className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center shrink-0 border transition-all",
                    status === 'done' ? "bg-accentPrimary border-accentPrimary text-white" :
                        status === 'active' ? "border-accentPrimary text-accentPrimary font-bold" : "border-gray-200 bg-white text-gray-400"
                )}>
                    {status === 'done' ? <CheckCircle2 size={14} /> : <span className="text-[10px]">{step}</span>}
                </div>
                <div className="w-[1px] h-full bg-gray-100 absolute top-6" />
            </div>
            <div className="pb-4">
                <p className={cn(
                    "text-sm leading-tight transition-colors",
                    status === 'done' ? "text-gray-400 line-through" :
                        status === 'active' ? "text-textMain font-medium" : "text-gray-500"
                )}>
                    {label}
                </p>
            </div>
        </div>
    );
}

function FileItem({ name, isGray = false }: { name: string, isGray?: boolean }) {
    return (
        <div className="flex items-center gap-2 group cursor-pointer">
            <FileText size={14} className={cn("text-gray-400 group-hover:text-gray-600", isGray && "opacity-50")} />
            <span className={cn("text-xs transition-colors", isGray ? "text-gray-300" : "text-gray-600 group-hover:text-textMain")}>
                {name}
            </span>
        </div>
    );
}
