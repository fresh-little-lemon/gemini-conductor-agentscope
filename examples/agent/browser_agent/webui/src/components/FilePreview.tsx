import React from 'react';
import { FileText, Image as ImageIcon, Video, FileCode } from 'lucide-react';

interface FilePreviewProps {
  path: string;
  type: string;
  name: string;
}

const FilePreview: React.FC<FilePreviewProps> = ({ path, type, name }) => {
  const isImage = ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(type.toLowerCase());
  const isVideo = ['mp4', 'webm'].includes(type.toLowerCase());
  const isMarkdown = type.toLowerCase() === 'md';

  return (
    <div className="w-full h-full bg-white flex flex-col">
      <div className="p-2 border-b border-borderSubtle bg-gray-50 flex items-center gap-2 text-sm text-textMuted">
        {isImage && <ImageIcon className="w-4 h-4" />}
        {isVideo && <Video className="w-4 h-4" />}
        {isMarkdown && <FileText className="w-4 h-4" />}
        {!isImage && !isVideo && !isMarkdown && <FileCode className="w-4 h-4" />}
        <span>{name}</span>
      </div>
      <div className="flex-1 overflow-auto p-4">
        {isImage && (
          <div className="flex items-center justify-center h-full">
            <img src={`http://localhost:8000/files?path=${encodeURIComponent(path)}`} alt={name} className="max-w-full max-h-full shadow-md" />
          </div>
        )}
        {isVideo && (
          <div className="flex items-center justify-center h-full">
            <video controls className="max-w-full max-h-full shadow-md">
              <source src={`http://localhost:8000/files?path=${encodeURIComponent(path)}`} type={`video/${type}`} />
            </video>
          </div>
        )}
        {(isMarkdown || !isImage && !isVideo) && (
          <div className="prose max-w-none">
             {/* In a real implementation, we would fetch and render markdown/text here */}
             <div className="p-4 bg-gray-100 rounded border border-dashed border-gray-300 text-center text-textMuted">
                File content preview for <code>{path}</code>
             </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FilePreview;
