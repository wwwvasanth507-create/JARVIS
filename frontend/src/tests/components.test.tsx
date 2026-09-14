import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MessageBubble } from '../components/MessageBubble';
import { Composer } from '../components/Composer';
import { Header } from '../components/Header';
import { SettingsModal } from '../components/SettingsModal';
import { ModelModal } from '../components/ModelModal';
import type { Message, GenerationSettings, ModelInfo } from '../types/api';

describe('Frontend Component Tests', () => {
  describe('MessageBubble', () => {
    it('renders user message correctly', () => {
      const msg: Message = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello, MyLLM!',
        timestamp: '2026-09-14T10:00:00Z',
      };
      render(<MessageBubble message={msg} />);
      expect(screen.getByText('Hello, MyLLM!')).toBeDefined();
      expect(screen.getByText('You')).toBeDefined();
    });

    it('renders assistant message with code block and copy action', () => {
      const msg: Message = {
        id: 'msg-2',
        role: 'assistant',
        content: 'Here is code:\n```python\nprint("hello")\n```',
        timestamp: '2026-09-14T10:00:01Z',
      };
      render(<MessageBubble message={msg} />);
      expect(screen.getByText(/MyLLM Assistant/)).toBeDefined();
      expect(screen.getByText('Here is code:')).toBeDefined();
      expect(screen.getByText('print("hello")')).toBeDefined();
      expect(screen.getByText(/Copy/)).toBeDefined();
    });

    it('renders streaming indicator when isStreaming is true', () => {
      const msg: Message = {
        id: 'msg-3',
        role: 'assistant',
        content: 'Thinking...',
        timestamp: '2026-09-14T10:00:02Z',
        isStreaming: true,
      };
      const { container } = render(<MessageBubble message={msg} />);
      expect(container.querySelector('.streaming-cursor')).toBeDefined();
    });

    it('renders telemetry metrics when completed', () => {
      const msg: Message = {
        id: 'msg-4',
        role: 'assistant',
        content: 'Done response',
        timestamp: '2026-09-14T10:00:03Z',
        telemetry: {
          prompt_tokens: 12,
          generated_tokens: 24,
          total_tokens: 36,
          tokens_per_second: 42.5,
          generation_latency: 0.56,
          stop_reason: 'eos',
          context_truncated: false,
          removed_messages: 0,
        },
      };
      render(<MessageBubble message={msg} />);
      expect(screen.getByText(/42\.5 tok\/s/)).toBeDefined();
      expect(screen.getByText(/24 tok/)).toBeDefined();
      expect(screen.getByText(/560 ms/)).toBeDefined();
    });
  });

  describe('Composer', () => {
    it('allows typing and triggers onSend on Enter', async () => {
      const user = userEvent.setup();
      const onSend = vi.fn();
      const onStop = vi.fn();

      render(<Composer onSend={onSend} onStop={onStop} isGenerating={false} />);
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      await user.type(textarea, 'Hello world{enter}');

      expect(onSend).toHaveBeenCalledWith('Hello world');
      expect(textarea.value).toBe('');
    });

    it('does not send on Shift+Enter (inserts newline instead)', async () => {
      const user = userEvent.setup();
      const onSend = vi.fn();
      const onStop = vi.fn();

      render(<Composer onSend={onSend} onStop={onStop} isGenerating={false} />);
      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Hello{Shift>}{enter}{/Shift}world');

      expect(onSend).not.toHaveBeenCalled();
    });

    it('renders Stop button and triggers onStop when generating', () => {
      const onSend = vi.fn();
      const onStop = vi.fn();

      render(<Composer onSend={onSend} onStop={onStop} isGenerating={true} />);
      const stopBtn = screen.getByRole('button', { name: /stop generation/i });
      expect(stopBtn).toBeDefined();

      fireEvent.click(stopBtn);
      expect(onStop).toHaveBeenCalled();
    });

    it('disables input when disabled prop is true', () => {
      render(<Composer onSend={vi.fn()} onStop={vi.fn()} isGenerating={false} disabled={true} />);
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea.disabled).toBe(true);
    });
  });

  describe('Header', () => {
    it('displays connected status badge', () => {
      render(
        <Header
          connectionStatus="connected"
          onRetryConnection={vi.fn()}
          onToggleSidebar={vi.fn()}
          onOpenModelInfo={vi.fn()}
          onOpenSettings={vi.fn()}
        />
      );
      expect(screen.getByText('Connected (CPU)')).toBeDefined();
    });

    it('displays retry button when disconnected and triggers retry', () => {
      const onRetry = vi.fn();
      render(
        <Header
          connectionStatus="disconnected"
          onRetryConnection={onRetry}
          onToggleSidebar={vi.fn()}
          onOpenModelInfo={vi.fn()}
          onOpenSettings={vi.fn()}
        />
      );
      expect(screen.getByText('Disconnected')).toBeDefined();
      const retryBtn = screen.getByRole('button', { name: /retry/i });
      fireEvent.click(retryBtn);
      expect(onRetry).toHaveBeenCalled();
    });
  });

  describe('SettingsModal', () => {
    const initialSettings: GenerationSettings = {
      max_new_tokens: 32,
      temperature: 0.7,
      top_k: 0,
      top_p: 0.9,
      repetition_penalty: 1.0,
      do_sample: false,
      seed: null,
    };

    it('renders controls and applies changes', () => {
      const onSaveSettings = vi.fn();
      const onSavePrompt = vi.fn();
      const onClose = vi.fn();

      render(
        <SettingsModal
          isOpen={true}
          onClose={onClose}
          settings={initialSettings}
          onSaveSettings={onSaveSettings}
          systemPrompt="You are a helpful assistant."
          onSaveSystemPrompt={onSavePrompt}
        />
      );

      expect(screen.getByText('⚙️ Generation Settings')).toBeDefined();
      expect(screen.getByDisplayValue('You are a helpful assistant.')).toBeDefined();

      // Switch to sampling
      const sampleBtn = screen.getByText('Sampling');
      fireEvent.click(sampleBtn);

      const applyBtn = screen.getByRole('button', { name: /apply settings/i });
      fireEvent.click(applyBtn);

      expect(onSaveSettings).toHaveBeenCalledWith(
        expect.objectContaining({ do_sample: true })
      );
      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('ModelModal', () => {
    const mockModel: ModelInfo = {
      model_name: 'MyLLM-Phase7-SFT',
      parameter_count: 84384,
      context_length: 64,
      vocab_size: 305,
      device: 'cpu',
      checkpoint: 'experiments/phase7/phase7_sft_run/checkpoints/best.pt',
      tokenizer_fingerprint: 'a89c78921e8b',
      kv_cache_supported: true,
    };

    it('renders model architecture specifications correctly', () => {
      render(
        <ModelModal
          isOpen={true}
          onClose={vi.fn()}
          modelInfo={mockModel}
          loading={false}
        />
      );

      expect(screen.getByText('MyLLM-Phase7-SFT')).toBeDefined();
      expect(screen.getByText('84,384')).toBeDefined();
      expect(screen.getByText('64 tokens')).toBeDefined();
      expect(screen.getByText('305 tokens')).toBeDefined();
      expect(screen.getByText('CPU (Strict CPU)')).toBeDefined();
      expect(screen.getByText('✓ Enabled')).toBeDefined();
    });
  });
});
