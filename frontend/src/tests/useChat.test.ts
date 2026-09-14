import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChat } from '../hooks/useChat';
import { apiClient } from '../services/apiClient';

describe('useChat Hook State Management', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('initializes with default state', () => {
    const { result } = renderHook(() => useChat());
    expect(result.current.sessions).toEqual([]);
    expect(result.current.activeSessionId).toBeNull();
    expect(result.current.messages).toEqual([]);
    expect(result.current.isGenerating).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.settings.max_new_tokens).toBe(32);
  });

  it('creates new session and updates active session', async () => {
    vi.spyOn(apiClient, 'createSession').mockResolvedValue({
      session_id: 'sess-new-1',
      created_at: '2026-09-14T10:00:00Z',
      model: 'gpt_custom',
      context_length: 64,
    });

    const { result } = renderHook(() => useChat());

    let newId = '';
    await act(async () => {
      newId = await result.current.createNewSession('Custom system directive');
    });

    expect(newId).toBe('sess-new-1');
    expect(result.current.activeSessionId).toBe('sess-new-1');
    expect(result.current.sessions.length).toBe(1);
    expect(result.current.sessions[0].session_id).toBe('sess-new-1');
  });

  it('selects session and loads messages', async () => {
    vi.spyOn(apiClient, 'getSession').mockResolvedValue({
      session_id: 'sess-existing',
      model_checkpoint: 'checkpoints/best.pt',
      created_at: '2026-09-14T09:00:00Z',
      updated_at: '2026-09-14T09:10:00Z',
      system_prompt: 'Assistant prompt',
      messages: [
        { role: 'user', content: 'What is 1+1?' },
        { role: 'assistant', content: '2' },
      ],
      generation_config: { max_new_tokens: 32 },
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.selectSession('sess-existing');
    });

    expect(result.current.activeSessionId).toBe('sess-existing');
    expect(result.current.messages.length).toBe(2);
    expect(result.current.messages[0].content).toBe('What is 1+1?');
    expect(result.current.messages[1].content).toBe('2');
    expect(result.current.systemPrompt).toBe('Assistant prompt');
  });

  it('deletes session and resets active session if deleted', async () => {
    vi.spyOn(apiClient, 'createSession').mockResolvedValue({
      session_id: 'sess-to-del',
      created_at: '2026-09-14T10:00:00Z',
      model: 'gpt_custom',
      context_length: 64,
    });
    vi.spyOn(apiClient, 'deleteSession').mockResolvedValue({
      status: 'deleted',
      session_id: 'sess-to-del',
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.createNewSession();
    });
    expect(result.current.activeSessionId).toBe('sess-to-del');

    await act(async () => {
      await result.current.deleteSession('sess-to-del');
    });

    expect(result.current.activeSessionId).toBeNull();
    expect(result.current.sessions.length).toBe(0);
    expect(result.current.messages.length).toBe(0);
  });

  it('updates generation settings partially', () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.updateSettings({ temperature: 0.9, do_sample: true });
    });

    expect(result.current.settings.temperature).toBe(0.9);
    expect(result.current.settings.do_sample).toBe(true);
    expect(result.current.settings.max_new_tokens).toBe(32); // untouched
  });

  it('handles streaming communication error gracefully', async () => {
    vi.spyOn(apiClient, 'createSession').mockResolvedValue({
      session_id: 'sess-err',
      created_at: '2026-09-14T10:00:00Z',
      model: 'gpt_custom',
      context_length: 64,
    });
    vi.spyOn(apiClient, 'streamMessage').mockImplementation(async (_sid, _msg, _cfg, callbacks) => {
      callbacks?.onError?.(new Error('Context overflow: prompt exceeds context limit'));
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.createNewSession();
    });

    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    expect(result.current.error).toContain('Context overflow');
    expect(result.current.isGenerating).toBe(false);
  });
});
