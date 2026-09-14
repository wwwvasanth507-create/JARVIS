import React from 'react';
import type { Message } from '../types/api';
import { parseMarkdown, formatInlineMarkdown } from '../utils/markdown';
import { CodeBlock } from './CodeBlock';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const segments = parseMarkdown(message.content);

  return (
    <div className={`message-row ${isUser ? 'user-row' : 'assistant-row'}`}>
      <div className={`avatar ${isUser ? 'user-avatar' : 'assistant-avatar'}`}>
        {isUser ? '👤' : '⚡'}
      </div>

      <div className={`message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
        <div className="message-header">
          <span className="sender-name">{isUser ? 'You' : 'MyLLM Assistant'}</span>
          <span className="timestamp">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        <div className="message-content">
          {message.content ? (
            segments.map((seg, idx) => {
              if (seg.type === 'codeblock') {
                return (
                  <CodeBlock
                    key={idx}
                    code={seg.content}
                    language={seg.language}
                  />
                );
              }
              if (seg.type === 'list' && seg.items) {
                return (
                  <ul key={idx} className="message-list">
                    {seg.items.map((item, itemIdx) => (
                      <li
                        key={itemIdx}
                        dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(item) }}
                      />
                    ))}
                  </ul>
                );
              }
              return (
                <p
                  key={idx}
                  className="message-paragraph"
                  dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(seg.content) }}
                />
              );
            })
          ) : (
            message.isStreaming && <span className="streaming-cursor">▊</span>
          )}

          {message.isStreaming && message.content && (
            <span className="streaming-cursor">▊</span>
          )}
        </div>

        {/* Telemetry pill */}
        {!isUser && message.telemetry && !message.isStreaming && (
          <div className="telemetry-bar">
            <span>{message.telemetry.generated_tokens} tok</span>
            <span>•</span>
            <span>{message.telemetry.tokens_per_second.toFixed(1)} tok/s</span>
            <span>•</span>
            <span>{(message.telemetry.generation_latency * 1000).toFixed(0)} ms</span>
            <span>•</span>
            <span className="stop-reason-tag">stop: {message.telemetry.stop_reason}</span>
          </div>
        )}
      </div>
    </div>
  );
};
