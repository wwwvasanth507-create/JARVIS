/**
 * Core conversational state management hook for MyLLM.
 *
 * Coordinates multi-turn dialogue, Server-Sent Events (SSE) streaming,
 * AbortController cancellation, session switching, and generation settings.
 */

import { useState, useCallback, useRef } from 'react';
import { apiClient } from '../services/apiClient';
import type {
  Message,
  SessionSummary,
  GenerationSettings,
} from '../types/api';

const DEFAULT_SETTINGS: GenerationSettings = {
  max_new_tokens: 32,
  temperature: 0.7,
  top_k: 0,
  top_p: 0.9,
  repetition_penalty: 1.0,
  do_sample: false,
  seed: null,
};

export function useChat() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<GenerationSettings>(DEFAULT_SETTINGS);
  const [systemPrompt, setSystemPrompt] = useState<string>('');

  const abortControllerRef = useRef<AbortController | null>(null);

  const createNewSession = useCallback(
    async (customSystemPrompt?: string): Promise<string> => {
      setError(null);
      const promptToUse = customSystemPrompt !== undefined ? customSystemPrompt : systemPrompt;
      try {
        const data = await apiClient.createSession(promptToUse, settings);
        const newSessionId = data.session_id;

        const newSummary: SessionSummary = {
          session_id: newSessionId,
          title: 'New Chat',
          created_at: data.created_at,
          updated_at: data.created_at,
          system_prompt: promptToUse || null,
          message_count: 0,
        };

        setSessions((prev) => [newSummary, ...prev]);
        setActiveSessionId(newSessionId);
        setMessages([]);
        return newSessionId;
      } catch (err: any) {
        const msg = err.message || 'Failed to create session';
        setError(msg);
        throw err;
      }
    },
    [systemPrompt, settings]
  );

  const selectSession = useCallback(async (sessionId: string) => {
    setError(null);
    try {
      const detail = await apiClient.getSession(sessionId);
      setActiveSessionId(sessionId);

      const mapped: Message[] = detail.messages.map((m, idx) => ({
        id: `msg-${sessionId}-${idx}`,
        role: m.role,
        content: m.content,
        timestamp: detail.updated_at,
        isStreaming: false,
      }));

      setMessages(mapped);
      setSystemPrompt(detail.system_prompt || '');
    } catch (err: any) {
      setError(`Failed to load session: ${err.message}`);
    }
  }, []);

  const deleteSession = useCallback(
    async (sessionId: string) => {
      setError(null);
      try {
        await apiClient.deleteSession(sessionId);
        setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));

        if (activeSessionId === sessionId) {
          setActiveSessionId(null);
          setMessages([]);
        }
      } catch (err: any) {
        setError(`Failed to delete session: ${err.message}`);
      }
    },
    [activeSessionId]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isGenerating) return;

      setError(null);
      let targetSessionId = activeSessionId;

      // Create session on-demand if none active
      if (!targetSessionId) {
        try {
          targetSessionId = await createNewSession();
        } catch {
          return;
        }
      }

      const nowIso = new Date().toISOString();
      const userMsgId = `user-${Date.now()}`;
      const assistantMsgId = `assistant-${Date.now()}`;

      const userMsg: Message = {
        id: userMsgId,
        role: 'user',
        content: trimmed,
        timestamp: nowIso,
      };

      const assistantPlaceholder: Message = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: nowIso,
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantPlaceholder]);
      setIsGenerating(true);

      // Update session title locally if still 'New Chat'
      setSessions((prev) =>
        prev.map((s) => {
          if (s.session_id === targetSessionId && s.title === 'New Chat') {
            const shortTitle = trimmed.length > 28 ? `${trimmed.slice(0, 25)}...` : trimmed;
            return { ...s, title: shortTitle, updated_at: nowIso };
          }
          return s;
        })
      );

      const controller = new AbortController();
      abortControllerRef.current = controller;

      let accumulatedText = '';
      const startTime = performance.now();
      let tokenCount = 0;

      try {
        await apiClient.streamMessage(
          targetSessionId,
          trimmed,
          settings,
          {
            onToken: (tok) => {
              accumulatedText += tok;
              tokenCount++;
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantMsgId ? { ...m, content: accumulatedText } : m))
              );
            },
            onComplete: (stopReason) => {
              const elapsedSec = (performance.now() - startTime) / 1000;
              const tps = elapsedSec > 0 ? tokenCount / elapsedSec : 0;

              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? {
                        ...m,
                        content: accumulatedText.trim() || '...',
                        isStreaming: false,
                        telemetry: {
                          prompt_tokens: 0,
                          generated_tokens: tokenCount,
                          total_tokens: tokenCount,
                          tokens_per_second: tps,
                          generation_latency: elapsedSec,
                          stop_reason: stopReason,
                          context_truncated: false,
                          removed_messages: 0,
                        },
                      }
                    : m
                )
              );
            },
            onError: (err) => {
              setError(`Generation error: ${err.message}`);
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, content: accumulatedText || '(Generation interrupted)', isStreaming: false }
                    : m
                )
              );
            },
          },
          controller.signal
        );
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Streaming communication failed');
        }
      } finally {
        setIsGenerating(false);
        abortControllerRef.current = null;
      }
    },
    [activeSessionId, isGenerating, createNewSession, settings]
  );

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsGenerating(false);
    }
  }, []);

  const saveCurrentSession = useCallback(
    async (path: string): Promise<string> => {
      if (!activeSessionId) {
        throw new Error('No active session to save');
      }
      const res = await apiClient.saveSession(activeSessionId, path);
      return res.path;
    },
    [activeSessionId]
  );

  const updateSettings = useCallback((newSettings: Partial<GenerationSettings>) => {
    setSettings((prev) => ({ ...prev, ...newSettings }));
  }, []);

  return {
    sessions,
    activeSessionId,
    messages,
    isGenerating,
    error,
    settings,
    systemPrompt,
    createNewSession,
    selectSession,
    deleteSession,
    sendMessage,
    stopGeneration,
    saveCurrentSession,
    updateSettings,
    setSystemPrompt,
    clearError: () => setError(null),
  };
}
