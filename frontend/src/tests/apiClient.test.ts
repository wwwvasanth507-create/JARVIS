import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from '../services/apiClient';

describe('ApiClient', () => {
  let client: ApiClient;

  beforeEach(() => {
    vi.restoreAllMocks();
    client = new ApiClient('http://127.0.0.1:8000');
  });

  it('normalizes base url correctly', () => {
    const c1 = new ApiClient('http://localhost:8000/');
    expect(c1.getBaseUrl()).toBe('http://localhost:8000');
    c1.setBaseUrl('http://127.0.0.1:8000/');
    expect(c1.getBaseUrl()).toBe('http://127.0.0.1:8000');
  });

  it('checkHealth() sends GET /health and returns response', async () => {
    const mockHealth = { status: 'ok', model: 'gpt_custom', device: 'cpu' };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
    });

    const res = await client.checkHealth();
    expect(res).toEqual(mockHealth);
    expect(globalThis.fetch).toHaveBeenCalledWith('http://127.0.0.1:8000/health', expect.any(Object));
  });

  it('checkHealth() throws formatted error on failure', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: async () => ({ error: { message: 'Inference engine not ready' } }),
    });

    await expect(client.checkHealth()).rejects.toThrow('Inference engine not ready');
  });

  it('getModelInfo() sends GET /v1/model and returns specs', async () => {
    const mockModel = {
      model_name: 'MyLLM-Phase7-SFT',
      parameter_count: 84384,
      context_length: 64,
      vocab_size: 305,
      device: 'cpu',
      checkpoint: 'experiments/phase7/phase7_sft_run/checkpoints/best.pt',
      tokenizer_fingerprint: 'a89c78921e8b',
      kv_cache_supported: true,
    };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockModel,
    });

    const res = await client.getModelInfo();
    expect(res).toEqual(mockModel);
    expect(globalThis.fetch).toHaveBeenCalledWith('http://127.0.0.1:8000/v1/model', expect.any(Object));
  });

  it('createSession() posts system prompt and generation config', async () => {
    const mockCreated = {
      session_id: 'test-uuid-123',
      created_at: '2026-09-14T10:00:00Z',
      model: 'gpt_custom',
      context_length: 64,
      system_prompt: 'You are helpful.',
    };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockCreated,
    });

    const res = await client.createSession('You are helpful.', { temperature: 0.5, do_sample: true });
    expect(res.session_id).toBe('test-uuid-123');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/v1/sessions',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          system_prompt: 'You are helpful.',
          generation_config: { temperature: 0.5, do_sample: true },
        }),
      })
    );
  });

  it('getSession() retrieves messages and conversation state', async () => {
    const mockSession = {
      session_id: 's-123',
      created_at: '2026-09-14T10:00:00Z',
      updated_at: '2026-09-14T10:05:00Z',
      system_prompt: 'Test',
      messages: [{ role: 'user', content: 'Hi' }],
      generation_config: { max_new_tokens: 32 },
    };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockSession,
    });

    const res = await client.getSession('s-123');
    expect(res.session_id).toBe('s-123');
    expect(res.messages.length).toBe(1);
    expect(globalThis.fetch).toHaveBeenCalledWith('http://127.0.0.1:8000/v1/sessions/s-123', expect.any(Object));
  });

  it('deleteSession() sends DELETE request', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'deleted', session_id: 's-del' }),
    });

    const res = await client.deleteSession('s-del');
    expect(res.status).toBe('deleted');
    expect(globalThis.fetch).toHaveBeenCalledWith('http://127.0.0.1:8000/v1/sessions/s-del', expect.objectContaining({ method: 'DELETE' }));
  });

  it('saveSession() sends POST to save endpoint with path', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'saved', session_id: 's-save', path: 'scratch/sess.json' }),
    });

    const res = await client.saveSession('s-save', 'scratch/sess.json');
    expect(res.path).toBe('scratch/sess.json');
  });

  it('streamMessage() correctly processes tokens, completed event, and malformed chunks', async () => {
    const chunks = [
      'data: {"token": "Hello", "finished": false}\n\n',
      'data: invalid json chunk that should not crash the stream\n\n',
      'data: {"token": " world", "finished": false}\n\n',
      'data: {"token": "!", "finished": false}\n\n',
      'data: {"token": "", "finished": true, "stop_reason": "eos"}\n\n',
    ];

    const encoder = new TextEncoder();
    let chunkIndex = 0;
    const stream = new ReadableStream({
      pull(controller) {
        if (chunkIndex < chunks.length) {
          controller.enqueue(encoder.encode(chunks[chunkIndex++]));
        } else {
          controller.close();
        }
      },
    });

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: stream,
    });

    const tokens: string[] = [];
    let completedReason = '';

    await client.streamMessage(
      's-stream',
      'Tell me something',
      { max_new_tokens: 16 },
      {
        onToken: (tok) => tokens.push(tok),
        onComplete: (reason) => {
          completedReason = reason;
        },
      }
    );

    expect(tokens.join('')).toBe('Hello world!');
    expect(completedReason).toBe('eos');
  });

  it('streamMessage() handles abort/cancellation signal gracefully', async () => {
    const controller = new AbortController();
    const abortError = new Error('The user aborted a request.');
    abortError.name = 'AbortError';

    const stream = new ReadableStream({
      pull() {
        throw abortError;
      },
    });

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: stream,
    });

    let completedReason = '';
    await client.streamMessage(
      's-cancel',
      'Cancel this',
      {},
      {
        onComplete: (reason) => {
          completedReason = reason;
        },
      },
      controller.signal
    );

    expect(completedReason).toBe('cancelled');
  });
});
