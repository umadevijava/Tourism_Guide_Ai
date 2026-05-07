import { useCallback, useEffect, useState } from 'react';
import {
  getChatSessions,
  getChatHistory,
  deleteSession,
  updateSessionTitle,
  createNewSession,
  clearAllHistory,
  type ChatHistoryResponse,
  type ChatSessionSummary,
} from '../services/api';

export interface UseChatHistoryReturn {
  sessions: ChatSessionSummary[];
  currentSession: ChatHistoryResponse | null;
  sessionId: string | null;
  loading: boolean;
  error: string | null;
  fetchSessions: () => Promise<void>;
  loadSession: (id: string) => Promise<void>;
  createSession: () => Promise<string | null>;
  removeSession: (id: string) => Promise<void>;
  updateTitle: (id: string, title: string) => Promise<void>;
  clearHistory: () => Promise<void>;
  setSessionId: (id: string | null) => void;
}

export function useChatHistory(): UseChatHistoryReturn {
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatHistoryResponse | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all sessions
  const fetchSessions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getChatSessions(50);
      setSessions(response.sessions);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load sessions';
      setError(message);
      console.error('Failed to fetch sessions:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch specific session history
  const loadSession = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const history = await getChatHistory(id);
      setCurrentSession(history);
      setSessionId(id);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load session';
      setError(message);
      console.error('Failed to load session:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Create new session
  const createSession = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await createNewSession();
      setSessionId(response.session_id);
      setCurrentSession(null);
      await fetchSessions(); // Refresh sessions list
      return response.session_id;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create session';
      setError(message);
      console.error('Failed to create session:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [fetchSessions]);

  // Delete session
  const removeSession = useCallback(
    async (id: string) => {
      try {
        await deleteSession(id);
        if (sessionId === id) {
          setCurrentSession(null);
          setSessionId(null);
        }
        await fetchSessions();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to delete session';
        setError(message);
        console.error('Failed to delete session:', err);
      }
    },
    [sessionId, fetchSessions],
  );

  // Update session title
  const updateTitle = useCallback(
    async (id: string, title: string) => {
      try {
        await updateSessionTitle(id, title);
        await fetchSessions();
        if (currentSession?.session_id === id) {
          setCurrentSession({ ...currentSession, title });
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update title';
        setError(message);
        console.error('Failed to update title:', err);
      }
    },
    [currentSession, fetchSessions],
  );

  // Clear all history
  const clearHistory = useCallback(async () => {
    try {
      await clearAllHistory();
      setSessions([]);
      setCurrentSession(null);
      setSessionId(null);
      await createSession(); // Create a new session after clearing
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to clear history';
      setError(message);
      console.error('Failed to clear history:', err);
    }
  }, [createSession]);

  // Initial load
  useEffect(() => {
    const init = async () => {
      await fetchSessions();
      if (!sessionId) {
        await createSession();
      }
    };
    init();
  }, []);

  return {
    sessions,
    currentSession,
    sessionId,
    loading,
    error,
    fetchSessions,
    loadSession,
    createSession,
    removeSession,
    updateTitle,
    clearHistory,
    setSessionId,
  };
}
