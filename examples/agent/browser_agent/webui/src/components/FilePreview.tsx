import { X, FileText, Download } from 'lucide-react';
import { useEffect, useState } from 'react';

interface FilePreviewProps {
    path: string;
    name: string;
    onClose: () => void;
}

export default function FilePreview({ path, name, onClose }: FilePreviewProps) {
    const [content, setContent] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        fetch(`/api/file/preview?path=${encodeURIComponent(path)}`)
            .then(res => res.json())
            .then(data => {
                setContent(data.content);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    }, [path]);

    return (
        <div className="h-full flex flex-col bg-white">
            <div className="flex items-center gap-2 px-4 py-2 border-b border-borderSubtle bg-gray-50">
                <FileText size={16} className="text-gray-400" />
                <span className="text-sm font-medium text-gray-700 truncate">{name}</span>
                <button onClick={onClose} className="ml-auto p-1 hover:bg-gray-200 rounded text-gray-400">
                    <X size={16} />
                </button>
            </div>
            <div className="flex-1 overflow-auto p-4 font-mono text-xs whitespace-pre-wrap bg-white">
                {loading ? (
                    <div className="flex items-center justify-center h-full text-gray-400">Loading...</div>
                ) : (
                    content || "No content or failed to load."
                )}
            </div>
        </div>
    );
}
