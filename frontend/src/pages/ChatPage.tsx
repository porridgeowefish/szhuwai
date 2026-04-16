import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Plus, MessageCircle, Loader2, X } from 'lucide-react';
import { chatAPI, ChatSession, ChatMessage } from '../lib/api/chat';
import { streamChatMessage } from '../lib/api/sse';
import { cn } from '../utils/cn';
import MessageBubble from '../components/chat/MessageBubble';
import ToolCallCard from '../components/chat/ToolCallCard';
import ChatInput from '../components/chat/ChatInput';

interface ToolCall {
  tool: string;
  status: 'running' | 'completed' | 'error';
  output?: string;
}

const ChatPage: React.FC = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);

  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent, toolCalls, scrollToBottom]);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Create new session if none active
  useEffect(() => {
    if (!loadingSessions && sessions.length === 0) {
      createNewSession();
    } else if (!loadingSessions && !activeSessionId && sessions.length > 0) {
      setActiveSessionId(sessions[0].session_id);
      loadMessages(sessions[0].session_id);
    }
  }, [loadingSessions, sessions, activeSessionId]);

  const loadSessions = async () => {
    setLoadingSessions(true);
    try {
      const data = await chatAPI.getSessions();
      setSessions(data);
    } catch (error) {
      console.error('加载会话列表失败:', error);
    } finally {
      setLoadingSessions(false);
    }
  };

  const createNewSession = async () => {
    try {
      const newSession = await chatAPI.createSession();
      setSessions(prev => [newSession, ...prev]);
      setActiveSessionId(newSession.session_id);
      setMessages([]);
      setToolCalls([]);
      setStreamingContent('');
    } catch (error) {
      console.error('创建会话失败:', error);
    }
  };

  const loadMessages = async (sessionId: string) => {
    // For now, we'll start fresh. Message history loading can be added later
    setMessages([]);
    setToolCalls([]);
    setStreamingContent('');
  };

  const handleSendMessage = async (text: string) => {
    if (!activeSessionId || isStreaming) return;

    // Add user message
    const userMessage: ChatMessage = {
      role: 'user',
      content: text,
    };
    setMessages(prev => [...prev, userMessage]);

    // Prepare for assistant response
    setIsStreaming(true);
    setStreamingContent('');
    setToolCalls([]);

    // Start streaming
    abortControllerRef.current = streamChatMessage(
      activeSessionId,
      text,
      {
        onToken: (content) => {
          setStreamingContent(prev => prev + content);
        },
        onToolStart: (tool, input) => {
          setToolCalls(prev => [
            ...prev,
            { tool, status: 'running', output: undefined },
          ]);
        },
        onToolEnd: (tool, output) => {
          setToolCalls(prev =>
            prev.map(tc =>
              tc.tool === tool && tc.status === 'running'
                ? { tool, status: 'completed', output }
                : tc
            )
          );
        },
        onDone: () => {
          // Finalize assistant message
          setMessages(prev => [
            ...prev,
            { role: 'assistant', content: streamingContent },
          ]);
          setStreamingContent('');
          setIsStreaming(false);
          setToolCalls([]);
        },
        onError: (error) => {
          console.error('流式传输错误:', error);
          setMessages(prev => [
            ...prev,
            {
              role: 'assistant',
              content: `抱歉，发生了错误：${error.message}`,
            },
          ]);
          setStreamingContent('');
          setIsStreaming(false);
          setToolCalls([]);
        },
      }
    );
  };

  const handleUploadTrack = async (file: File) => {
    if (!activeSessionId || isStreaming) return;

    try {
      await chatAPI.uploadTrack(activeSessionId, file);

      // Add system message about upload
      const uploadMessage: ChatMessage = {
        role: 'assistant',
        content: `已成功上传轨迹文件：${file.name}。您可以要求我分析这条轨迹的详细信息。`,
      };
      setMessages(prev => [...prev, uploadMessage]);
    } catch (error) {
      console.error('上传轨迹失败:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `上传失败：${error instanceof Error ? error.message : '未知错误'}`,
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleSessionChange = (sessionId: string) => {
    if (isStreaming && abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
      setStreamingContent('');
      setToolCalls([]);
    }
    setActiveSessionId(sessionId);
    loadMessages(sessionId);
  };

  return (
    <div className="flex h-screen bg-[var(--sand)]">
      {/* Sidebar */}
      <div
        className={cn(
          'bg-white border-r border-[var(--stone)] transition-all duration-300',
          sidebarCollapsed ? 'w-16' : 'w-72'
        )}
      >
        <div className="p-4 border-b border-[var(--stone)]">
          {!sidebarCollapsed && (
            <button
              onClick={createNewSession}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 btn-forest rounded-xl text-white font-medium"
            >
              <Plus size={20} />
              新对话
            </button>
          )}
          {sidebarCollapsed && (
            <button
              onClick={createNewSession}
              className="w-full flex items-center justify-center p-2 hover:bg-[var(--sand)] rounded-xl"
            >
              <Plus size={24} className="text-[var(--forest)]" />
            </button>
          )}
        </div>

        <div className="p-2">
          {loadingSessions ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-2 border-[var(--stone)] border-t-[var(--forest)] rounded-full animate-spin" />
            </div>
          ) : (
            <div className="space-y-1">
              {sessions.map(session => (
                <button
                  key={session.session_id}
                  onClick={() => handleSessionChange(session.session_id)}
                  className={cn(
                    'w-full text-left px-3 py-2 rounded-xl transition-colors',
                    activeSessionId === session.session_id
                      ? 'bg-[var(--forest)] text-white'
                      : 'hover:bg-[var(--sand)] text-zinc-700',
                    sidebarCollapsed && 'justify-center'
                  )}
                >
                  {sidebarCollapsed ? (
                    <MessageCircle size={20} className="mx-auto" />
                  ) : (
                    <div className="truncate text-sm">
                      {session.title || '新对话'}
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-[var(--stone)] px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-zinc-900">智能助手</h1>
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-2 hover:bg-[var(--sand)] rounded-lg transition-colors"
          >
            {sidebarCollapsed ? <MessageCircle size={20} /> : <X size={20} />}
          </button>
        </div>

        {/* Messages Area */}
        <div
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto p-6"
        >
          {messages.length === 0 && !isStreaming && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-full bg-[var(--forest)] bg-opacity-10 flex items-center justify-center mb-4">
                <MessageCircle size={32} className="text-[var(--forest)]" />
              </div>
              <h2 className="text-2xl font-bold text-zinc-900 mb-2">
                您好！我是您的户外规划助手
              </h2>
              <p className="text-zinc-500 max-w-md">
                我可以帮助您分析徒步轨迹、查询天气、搜索交通信息和生成详细报告。
              </p>
              <div className="mt-6 space-y-2 text-left">
                <div className="text-sm text-zinc-600 bg-white border border-[var(--stone)] rounded-xl p-3">
                  📊 上传 KML/GPX 轨迹文件，我会为您分析详细数据
                </div>
                <div className="text-sm text-zinc-600 bg-white border border-[var(--stone)] rounded-xl p-3">
                  🌤️ 询问目的地的天气情况和最佳出行时间
                </div>
                <div className="text-sm text-zinc-600 bg-white border border-[var(--stone)] rounded-xl p-3">
                  🚌 查询交通路线和出行方案
                </div>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <MessageBubble
              key={`${message.role}-${index}`}
              role={message.role}
              content={message.content}
            />
          ))}

          {isStreaming && (
            <>
              {toolCalls.map((toolCall, index) => (
                <ToolCallCard
                  key={`${toolCall.tool}-${index}`}
                  tool={toolCall.tool}
                  status={toolCall.status}
                  output={toolCall.output}
                />
              ))}

              {streamingContent && (
                <MessageBubble role="assistant" content={streamingContent} />
              )}

              {!streamingContent && toolCalls.length === 0 && (
                <div className="flex items-center gap-2 text-zinc-500 mb-4">
                  <Loader2 size={20} className="animate-spin" />
                  <span className="text-sm">思考中...</span>
                </div>
              )}
            </>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <ChatInput
          onSend={handleSendMessage}
          onUpload={handleUploadTrack}
          disabled={isStreaming}
        />
      </div>
    </div>
  );
};

export default ChatPage;
