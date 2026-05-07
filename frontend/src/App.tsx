import { useState, useCallback, useMemo, useEffect } from 'react';
import { ChatHeader, ChatViewport, ChatInput, type Message, type ChatModes } from '@/components/chat';
import { HistoryPanel } from '@/components/chat/history-panel';
import { useChat } from '@/hooks/useChat';
import { useChatHistory } from '@/hooks/useChatHistory';
import { useDocuments } from '@/hooks/useDocuments';

function App() {
  const { messages: rawMessages, isStreaming, sessionId, sendMessage, clearMessages, loadHistoryMessages } = useChat();
  const { sessions, currentSession, loading: historyLoading, error: historyError, fetchSessions, loadSession, createSession, removeSession, updateTitle, clearHistory } = useChatHistory();
  const { documents, uploading, error: docError, setDocuments, setUploading, setError } = useDocuments();

  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [displayedError, setDisplayedError] = useState<string | null>(null);

  const [modes, setModes] = useState<ChatModes>({
    rag: false,
    reasoning: false,
    webSearch: false,
  });

  // Show document errors
  useEffect(() => {
    if (docError) {
      setDisplayedError(docError);
      const timer = setTimeout(() => setDisplayedError(null), 7000); // Auto-hide after 7s
      return () => clearTimeout(timer);
    }
  }, [docError]);

  // Use the messages directly from useChat hook
  const messages: Message[] = useMemo(
    () => rawMessages,
    [rawMessages],
  );

  const handleSend = useCallback(
    (content: string) => {
      sendMessage(content, modes);
    },
    [sendMessage, modes],
  );

  const handleNewChat = useCallback(async () => {
    clearMessages();
    // Create a new session for fresh chat
    await createSession();
  }, [clearMessages, createSession]);

  const handleSelectHistoryItem = useCallback(
    async (sessionId: string) => {
      console.log('📂 Loading history session:', sessionId);
      // Load the full session history
      await loadSession(sessionId);
      setIsHistoryOpen(false);
    },
    [loadSession],
  );

  const handleUploadStart = useCallback(
    (filename: string) => {
      setError(null);
      setUploading({ filename, progress: 0 });
    },
    [setError, setUploading],
  );

  const handleUploadProgress = useCallback(
    (filename: string, progress: number) => {
      setUploading({ filename, progress });
    },
    [setUploading],
  );

  const handleUploadEnd = useCallback(() => {
    setUploading(null);
  }, [setUploading]);

  const handleError = useCallback(
    (message: string) => {
      setError(message);
    },
    [setError],
  );

  // When currentSession changes, load those messages into the chat UI
  useEffect(() => {
    if (currentSession && currentSession.messages.length > 0) {
      console.log('✓ Restoring chat messages from history:', currentSession.messages.length);
      const historyMessages = currentSession.messages.map((msg) => ({
        question: msg.question,
        answer: msg.answer,
      }));
      loadHistoryMessages(historyMessages);
    }
  }, [currentSession, loadHistoryMessages]);

  return (
    <div className="flex flex-col h-screen bg-background">
      <ChatHeader 
        onNewChat={handleNewChat} 
        onHistoryClick={() => setIsHistoryOpen(true)}
        disabled={isStreaming} 
      />

      <HistoryPanel
        sessions={sessions}
        currentSessionId={sessionId}
        isOpen={isHistoryOpen}
        loading={historyLoading}
        error={historyError}
        onClose={() => setIsHistoryOpen(false)}
        onSelectSession={handleSelectHistoryItem}
        onCreateNew={handleNewChat}
        onDeleteSession={removeSession}
        onClearHistory={clearHistory}
      />

      {displayedError && (
        <div className="mx-4 mt-2 mb-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-start justify-between animate-fade-in-down">
          <div className="flex-1">
            <p className="font-medium">Upload Error</p>
            <p className="text-xs opacity-90 mt-1">{displayedError}</p>
          </div>
          <button
            onClick={() => setDisplayedError(null)}
            className="ml-3 text-destructive/60 hover:text-destructive"
          >
            ✕
          </button>
        </div>
      )}

      <main className="flex-1 flex flex-col min-h-0">
        <ChatViewport messages={messages} />

        <div className="shrink-0 border-t border-border/30 bg-background/50 backdrop-blur-sm">
          <ChatInput
            onSend={handleSend}
            isLoading={isStreaming}
            modes={modes}
            onModesChange={setModes}
            documents={documents}
            uploading={uploading}
            onDocumentsChange={setDocuments}
            onUploadStart={handleUploadStart}
            onUploadProgress={handleUploadProgress}
            onUploadEnd={handleUploadEnd}
            onError={handleError}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
