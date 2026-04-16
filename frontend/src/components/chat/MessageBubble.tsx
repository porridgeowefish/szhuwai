import React from 'react';
import { Bot, User } from 'lucide-react';
import { cn } from '../../utils/cn';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ role, content }) => {
  return (
    <div
      className={cn(
        'flex gap-3 mb-4 animate-fade-in-up',
        role === 'user' ? 'justify-end' : 'justify-start'
      )}
    >
      {role === 'assistant' && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[var(--forest)] flex items-center justify-center">
          <Bot size={18} className="text-white" />
        </div>
      )}

      <div
        className={cn(
          'max-w-[70%] rounded-2xl px-4 py-3',
          role === 'user'
            ? 'bg-[var(--forest)] text-white rounded-br-sm'
            : 'bg-white border border-[var(--stone)] text-zinc-900 rounded-bl-sm'
        )}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
          {content}
        </p>
      </div>

      {role === 'user' && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[var(--earth)] flex items-center justify-center">
          <User size={18} className="text-white" />
        </div>
      )}
    </div>
  );
};

export default MessageBubble;
