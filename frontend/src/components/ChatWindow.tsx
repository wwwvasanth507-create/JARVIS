import { useEffect, useRef } from 'react';
import type { Message } from '../types/api';
import { MessageBubble } from './MessageBubble';

interface ChatWindowProps {
  messages: Message[];
  isGenerating: boolean;
  onSelectPrompt: (prompt: string) => void;
  error: string | null;
  onDismissError: () => void;
}

const STARTER_PROMPTS = [
  'What is 2 + 2?',
  'Explain why the sky is blue in simple terms.',
  'Write a Python function to reverse a string.',
  'வணக்கம், நீங்கள் யார்? (Hello, who are you?)',
];

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isGenerating,
  onSelectPrompt,
  error,
  onDismissError,
}) => {
  const scrollEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isGenerating]);

  return (
    <div className="chat-window">
      {error && (
        <div className="error-banner" role="alert">
          <div className="error-text">
            <strong>Notice:</strong> {error}
          </div>
          <button
            type="button"
            className="error-dismiss"
            onClick={onDismissError}
            aria-label="Dismiss error"
          >
            ✕
          </button>
        </div>
      )}

      {messages.length === 0 ? (
        <div className="empty-state">
          <div className="empty-hero">
            <div className="empty-logo">🧠</div>
            <h2 className="empty-title">Welcome to MyLLM</h2>
            <p className="empty-subtitle">
              A self-contained GPT Transformer built from scratch, running entirely on your local CPU.
            </p>
          </div>

          <div className="starters-grid">
            {STARTER_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                type="button"
                className="starter-card"
                onClick={() => onSelectPrompt(prompt)}
              >
                <span className="starter-icon">💡</span>
                <span className="starter-text">{prompt}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="messages-list">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          <div ref={scrollEndRef} />
        </div>
      )}
    </div>
  );
};
