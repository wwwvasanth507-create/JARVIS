import React from 'react';
import type { ConnectionStatus } from '../types/api';

interface HeaderProps {
  connectionStatus: ConnectionStatus;
  onRetryConnection: () => void;
  onToggleSidebar: () => void;
  onOpenModelInfo: () => void;
  onOpenSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  connectionStatus,
  onRetryConnection,
  onToggleSidebar,
  onOpenModelInfo,
  onOpenSettings,
}) => {
  return (
    <header className="app-header">
      <div className="header-left">
        <button
          type="button"
          className="sidebar-toggle-btn"
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar"
        >
          ☰
        </button>
        <div className="brand-lockup">
          <span className="brand-logo">🧠</span>
          <div className="brand-text">
            <h1 className="brand-name">MyLLM</h1>
            <span className="brand-tag">Pure CPU Transformer</span>
          </div>
        </div>
      </div>

      <div className="header-right">
        <div className={`status-badge status-${connectionStatus}`}>
          <span className="status-dot" />
          <span className="status-label">
            {connectionStatus === 'connected'
              ? 'Connected (CPU)'
              : connectionStatus === 'connecting'
              ? 'Connecting...'
              : 'Disconnected'}
          </span>
          {connectionStatus === 'disconnected' && (
            <button
              type="button"
              className="retry-btn"
              onClick={onRetryConnection}
              title="Retry connection to API server"
            >
              🔄 Retry
            </button>
          )}
        </div>

        <button
          type="button"
          className="icon-header-btn"
          onClick={onOpenModelInfo}
          title="View model specifications"
          aria-label="Model info"
        >
          ℹ️
        </button>

        <button
          type="button"
          className="icon-header-btn"
          onClick={onOpenSettings}
          title="Generation settings"
          aria-label="Settings"
        >
          ⚙️
        </button>
      </div>
    </header>
  );
};
