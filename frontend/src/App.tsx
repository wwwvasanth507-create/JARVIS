import { useState } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatWindow } from './components/ChatWindow';
import { Composer } from './components/Composer';
import { SettingsModal } from './components/SettingsModal';
import { ModelModal } from './components/ModelModal';
import { useHealth } from './hooks/useHealth';
import { useModelInfo } from './hooks/useModelInfo';
import { useChat } from './hooks/useChat';

export function App() {
  const { status: connectionStatus, retry: retryConnection } = useHealth();
  const { modelInfo, loading: modelLoading } = useModelInfo(connectionStatus);

  const {
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
    clearError,
  } = useChat();

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isModelInfoOpen, setIsModelInfoOpen] = useState(false);

  return (
    <div className="app-container">
      <Header
        connectionStatus={connectionStatus}
        onRetryConnection={retryConnection}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        onOpenModelInfo={() => setIsModelInfoOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <div className="main-body">
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onNewChat={() => createNewSession()}
          onSelectSession={selectSession}
          onDeleteSession={deleteSession}
          onSaveSession={async (path) => {
            await saveCurrentSession(path);
          }}
          onOpenSettings={() => setIsSettingsOpen(true)}
          onOpenModelInfo={() => setIsModelInfoOpen(true)}
          isOpen={isSidebarOpen}
          onToggleOpen={() => setIsSidebarOpen((prev) => !prev)}
        />

        <main className="chat-container">
          <ChatWindow
            messages={messages}
            isGenerating={isGenerating}
            onSelectPrompt={(p) => sendMessage(p)}
            error={error}
            onDismissError={clearError}
          />
          <Composer
            onSend={sendMessage}
            onStop={stopGeneration}
            isGenerating={isGenerating}
            disabled={connectionStatus === 'disconnected'}
          />
        </main>
      </div>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={settings}
        onSaveSettings={updateSettings}
        systemPrompt={systemPrompt}
        onSaveSystemPrompt={setSystemPrompt}
      />

      <ModelModal
        isOpen={isModelInfoOpen}
        onClose={() => setIsModelInfoOpen(false)}
        modelInfo={modelInfo}
        loading={modelLoading}
      />
    </div>
  );
}

export default App;
