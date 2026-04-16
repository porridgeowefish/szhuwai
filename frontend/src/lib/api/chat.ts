/**
 * Chat API — 聊天会话管理
 * 使用原生 fetch（不经过 Axios 拦截器，因为 SSE 需要手动处理流）
 */

const API_BASE = '/api/v1/chat';

export interface ChatSession {
  session_id: string;
  created_at: string;
  title?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at?: string;
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export const chatAPI = {
  createSession: async (): Promise<ChatSession> => {
    const res = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    const json = await res.json();
    return json.data;
  },

  getSessions: async (): Promise<ChatSession[]> => {
    const res = await fetch(`${API_BASE}/sessions`, {
      headers: getAuthHeaders(),
    });
    const json = await res.json();
    return json.data ?? [];
  },

  uploadTrack: async (
    sessionId: string,
    file: File
  ): Promise<{ file_path: string; filename: string }> => {
    const token = localStorage.getItem('access_token');
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    const json = await res.json();
    return json.data;
  },
};
