import React, { useState, useRef, useEffect } from 'react';

interface ComposerProps {
  onSend: (text: string) => void;
  onStop: () => void;
  isGenerating: boolean;
  disabled?: boolean;
}

export const Composer: React.FC<ComposerProps> = ({
  onSend,
  onStop,
  isGenerating,
  disabled = false,
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!isGenerating && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isGenerating]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (isGenerating) {
      onStop();
      return;
    }
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form className="composer-container" onSubmit={handleSubmit}>
      <div className="composer-box">
        <textarea
          ref={textareaRef}
          className="composer-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isGenerating
              ? 'Generating response...'
              : disabled
              ? 'Connecting to server...'
              : 'Message MyLLM... (Enter to send, Shift+Enter for newline)'
          }
          disabled={disabled || isGenerating}
          rows={1}
          aria-label="Message input"
        />

        <div className="composer-actions">
          {isGenerating ? (
            <button
              type="button"
              className="action-btn stop-btn"
              onClick={onStop}
              aria-label="Stop generation"
            >
              ⏹ Stop
            </button>
          ) : (
            <button
              type="submit"
              className="action-btn send-btn"
              disabled={disabled || !input.trim()}
              aria-label="Send message"
            >
              ➔ Send
            </button>
          )}
        </div>
      </div>
      <div className="composer-footer-note">
        MyLLM CPU-first Transformer • Responses generated locally in real-time
      </div>
    </form>
  );
};
