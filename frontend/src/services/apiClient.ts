/**
 * Typed HTTP and Server-Sent Events (SSE) client for MyLLM API Server.
 */

import type {
  HealthResponse,
  ModelInfo,
  SessionDetail,
  StreamTokenEvent,
  Telemetry,
  Role,
  GenerationSettings,
} from '../types/api';

const DEFAULT_API_URL = 'http://127.0.0.1:8000';

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = (baseUrl || (import.meta as any).env?.VITE_API_URL || DEFAULT_API_URL).replace(/\/$/, '');
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/$/, '');
  }

  private async handleResponse<T>(res: Response): Promise<T> {
    if (!res.ok) {
      let errorMsg = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const body = await res.json();
        if (body?.error?.message) {
          errorMsg = body.error.message;
        }
      } catch {
        // Fallback to HTTP status text
      }
      throw new Error(errorMsg);
    }
    return res.json() as Promise<T>;
  }

  async checkHealth(): Promise<HealthResponse> {
    const res = await fetch(`${this.baseUrl}/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    return this.handleResponse<HealthResponse>(res);
  }

  async getModelInfo(): Promise<ModelInfo> {
    const res = await fetch(`${this.baseUrl}/v1/model`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    return this.handleResponse<ModelInfo>(res);
  }

  async createSession(
    systemPrompt?: string,
    config?: Partial<GenerationSettings>
  ): Promise<{ session_id: string; created_at: string; model: string; context_length: number; system_prompt?: string | null }> {
    const payload: Record<string, unknown> = {};
    if (systemPrompt && systemPrompt.trim()) {
      payload.system_prompt = systemPrompt.trim();
    }
    if (config) {
      payload.generation_config = config;
    }

    const res = await fetch(`${this.baseUrl}/v1/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    return this.handleResponse(res);
  }

  async getSession(sessionId: string): Promise<SessionDetail> {
    const res = await fetch(`${this.baseUrl}/v1/sessions/${encodeURIComponent(sessionId)}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    return this.handleResponse<SessionDetail>(res);
  }

  async deleteSession(sessionId: string): Promise<{ status: string; session_id: string }> {
    const res = await fetch(`${this.baseUrl}/v1/sessions/${encodeURIComponent(sessionId)}`, {
      method: 'DELETE',
      headers: { 'Accept': 'application/json' },
    });
    return this.handleResponse(res);
  }

  async sendMessage(
    sessionId: string,
    content: string,
    config?: Partial<GenerationSettings>
  ): Promise<{ message: { role: Role; content: string }; telemetry: Telemetry }> {
    const payload: Record<string, unknown> = { content };
    if (config) {
      payload.generation_config = config;
    }

    const res = await fetch(`${this.baseUrl}/v1/sessions/${encodeURIComponent(sessionId)}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    return this.handleResponse(res);
  }

  async streamMessage(
    sessionId: string,
    content: string,
    config?: Partial<GenerationSettings>,
    callbacks?: {
      onToken?: (token: string) => void;
      onComplete?: (stopReason: string) => void;
      onError?: (err: Error) => void;
    },
    signal?: AbortSignal
  ): Promise<void> {
    const payload: Record<string, unknown> = { content };
    if (config) {
      payload.generation_config = config;
    }

    const res = await fetch(`${this.baseUrl}/v1/sessions/${encodeURIComponent(sessionId)}/messages/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(payload),
      signal,
    });

    if (!res.ok) {
      let errorMsg = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const body = await res.json();
        if (body?.error?.message) {
          errorMsg = body.error.message;
        }
      } catch {
        // Fallback
      }
      const err = new Error(errorMsg);
      callbacks?.onError?.(err);
      throw err;
    }

    const reader = res.body?.getReader();
    if (!reader) {
      throw new Error('ReadableStream not supported on response body.');
    }

    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const block of lines) {
          const trimmed = block.trim();
          if (trimmed.startsWith('data: ')) {
            const jsonStr = trimmed.slice(6);
            try {
              const event: StreamTokenEvent = JSON.parse(jsonStr);
              if (event.finished) {
                callbacks?.onComplete?.(event.stop_reason || 'eos');
              } else if (event.token) {
                callbacks?.onToken?.(event.token);
              }
            } catch {
              // Ignore malformed JSON chunks gracefully
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        callbacks?.onComplete?.('cancelled');
        return;
      }
      callbacks?.onError?.(err);
      throw err;
    }
  }

  async saveSession(sessionId: string, path: string): Promise<{ status: string; session_id: string; path: string }> {
    const res = await fetch(`${this.baseUrl}/v1/sessions/${encodeURIComponent(sessionId)}/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ path }),
    });
    return this.handleResponse(res);
  }
}

export const apiClient = new ApiClient();
