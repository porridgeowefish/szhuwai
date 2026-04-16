import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, X } from 'lucide-react';
import { cn } from '../../utils/cn';

interface ChatInputProps {
  onSend: (text: string) => void;
  onUpload: (file: File) => void;
  disabled: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend, onUpload, disabled }) => {
  const [text, setText] = useState('');
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current && !disabled) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  const handleSend = () => {
    if (disabled || (!text.trim() && !attachedFile)) return;

    if (attachedFile) {
      onUpload(attachedFile);
      setAttachedFile(null);
    }

    if (text.trim()) {
      onSend(text);
      setText('');
    }

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAttachedFile(file);
    }
  };

  const removeAttachedFile = () => {
    setAttachedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  return (
    <div className="bg-white border-t border-[var(--stone)] p-4">
      {attachedFile && (
        <div className="mb-3 flex items-center gap-2 p-2 bg-[var(--sand)] rounded-lg">
          <div className="flex-1 flex items-center gap-2">
            <Paperclip size={16} className="text-zinc-500" />
            <span className="text-sm text-zinc-700 truncate">{attachedFile.name}</span>
            <span className="text-xs text-zinc-500">
              {(attachedFile.size / 1024).toFixed(1)} KB
            </span>
          </div>
          <button
            onClick={removeAttachedFile}
            className="p-1 hover:bg-red-50 rounded-lg transition-colors"
          >
            <X size={16} className="text-red-500" />
          </button>
        </div>
      )}

      <div className="flex items-end gap-3">
        <input
          ref={fileInputRef}
          type="file"
          accept=".kml,.gpx,.json"
          onChange={handleFileChange}
          className="hidden"
        />

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className={cn(
            'p-2 rounded-xl transition-colors',
            disabled
              ? 'text-zinc-300 cursor-not-allowed'
              : 'text-zinc-500 hover:bg-[var(--sand)] hover:text-[var(--forest)]'
          )}
        >
          <Paperclip size={20} />
        </button>

        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
            className={cn(
              'w-full px-4 py-3 rounded-xl resize-none input-nature',
              'min-h-[48px] max-h-[120px]',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            rows={1}
          />
        </div>

        <button
          onClick={handleSend}
          disabled={disabled || (!text.trim() && !attachedFile)}
          className={cn(
            'p-3 rounded-xl transition-all',
            disabled || (!text.trim() && !attachedFile)
              ? 'bg-zinc-100 text-zinc-400 cursor-not-allowed'
              : 'btn-forest text-white'
          )}
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

export default ChatInput;
