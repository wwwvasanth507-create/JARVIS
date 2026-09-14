import React, { useState } from 'react';
import type { SessionSummary } from '../types/api';

interface SidebarProps {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  onSaveSession: (path: string) => Promise<void>;
  onOpenSettings: () => void;
  onOpenModelInfo: () => void;
  isOpen: boolean;
  onToggleOpen: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  onSaveSession,
  onOpenSettings,
  onOpenModelInfo,
  isOpen,
  onToggleOpen,
}) => {
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const handleSavePrompt = async () => {
    if (!activeSessionId) {
      alert('Please start or select a chat first.');
      return;
    }
    const defaultPath = `scratch/session_${activeSessionId.slice(0, 8)}.json`;
    const targetPath = prompt('Enter path to save session JSON:', defaultPath);
    if (targetPath) {
      try {
        await onSaveSession(targetPath);
        setSaveStatus(`Saved to ${targetPath}`);
        setTimeout(() => setSaveStatus(null), 3000);
      } catch (err: any) {
        alert(`Error saving session: ${err.message}`);
      }
    }
  };

  return (
    <>
      <div className={`sidebar ${isOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        <div className="sidebar-top">
          <button
            type="button"
            className="new-chat-btn"
            onClick={onNewChat}
            aria-label="Create new conversation"
          >
            <span className="btn-icon">+</span>
            <span>New Chat</span>
          </button>
        </div>

        <div className="sidebar-sessions-list">
          <div className="sessions-header">Conversations</div>
          {sessions.length === 0 ? (
            <div className="no-sessions-hint">No active sessions</div>
          ) : (
            sessions.map((s) => (
              <div
                key={s.session_id}
                className={`session-item ${s.session_id === activeSessionId ? 'active-session' : ''}`}
                onClick={() => onSelectSession(s.session_id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') onSelectSession(s.session_id);
                }}
              >
                <div className="session-item-content">
                  <span className="session-icon">💬</span>
                  <span className="session-title" title={s.title}>
                    {s.title}
                  </span>
                </div>
                <button
                  type="button"
                  className="delete-session-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('Delete this conversation?')) {
                      onDeleteSession(s.session_id);
                    }
                  }}
                  aria-label="Delete session"
                  title="Delete session"
                >
                  ✕
                </button>
              </div>
            ))
          )}
        </div>

        {saveStatus && <div className="save-status-toast">{saveStatus}</div>}

        <div className="sidebar-footer">
          <button
            type="button"
            className="footer-action-btn"
            onClick={handleSavePrompt}
            disabled={!activeSessionId}
            title="Save current conversation to JSON"
          >
            <span>💾</span>
            <span>Save Session</span>
          </button>

          <button
            type="button"
            className="footer-action-btn"
            onClick={onOpenSettings}
            title="Configure model parameters and system prompt"
          >
            <span>⚙️</span>
            <span>Settings</span>
          </button>

          <button
            type="button"
            className="footer-action-btn"
            onClick={onOpenModelInfo}
            title="Inspect model architecture and checkpoint"
          >
            <span>ℹ️</span>
            <span>Model Details</span>
          </button>
        </div>
      </div>

      {/* Mobile overlay */}
      {isOpen && <div className="sidebar-overlay" onClick={onToggleOpen} />}
    </>
  );
};
