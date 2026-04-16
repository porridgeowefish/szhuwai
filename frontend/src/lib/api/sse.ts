/**
 * SSE 流式客户端 — 解析 Chat API 的 Server-Sent Events
 */

export interface SSECallbacks {
  onToken: (content: string) => void;
  onToolStart: (tool: string, input: string) => void;
  onToolEnd: (tool: string, output: string) => void;
  onDone: () => void;
  onError: (error: Error) => void;
}

export function streamChatMessage(
  sessionId: string,
  message: string,
  callbacks: SSECallbacks
): AbortController {
  const controller = new AbortController();

  const token = localStorage.getItem('access_token');

  fetch(`/api/v1/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7);
          } else if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const parsed = JSON.parse(data);
              switch (currentEvent) {
                case 'token':
                  callbacks.onToken(parsed.content);
                  break;
                case 'tool_start':
                  callbacks.onToolStart(parsed.tool, parsed.input);
                  break;
                case 'tool_end':
                  callbacks.onToolEnd(parsed.tool, parsed.output);
                  break;
                case 'done':
                  callbacks.onDone();
                  break;
                case 'error':
                  callbacks.onError(new Error(parsed.message || 'Unknown error'));
                  break;
              }
            } catch {
              // Ignore malformed JSON
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        callbacks.onError(err);
      }
    });

  return controller;
}
