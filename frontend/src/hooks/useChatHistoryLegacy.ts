import { useCallback, useState } from 'react';
import {
  getChatHistory as getStoredHistory,
  addToHistory as addStoredHistory,
  removeFromHistory as removeStoredHistory,
  clearChatHistory as clearStoredHistory,
  type HistoryItem,
} from '../services/history';

export interface UseChatHistoryLegacyReturn {
  history: HistoryItem[];
  isLoading: boolean;
  addToHistory: (query: string, response: string) => void;
  clearHistory: () => void;
  removeFromHistory: (id: string) => void;
}

/**
 * Legacy hook for backward compatibility with existing App.tsx
 * Uses localStorage-based history storage
 */
export function useChatHistoryLegacy(): UseChatHistoryLegacyReturn {
  const [history, setHistory] = useState<HistoryItem[]>(getStoredHistory());
  const [isLoading] = useState(false);

  const addToHistory = useCallback((query: string, response: string) => {
    const item = addStoredHistory(query, response);
    setHistory((prev) => [item, ...prev]);
  }, []);

  const removeFromHistory = useCallback((id: string) => {
    removeStoredHistory(id);
    setHistory((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const clearHistory = useCallback(() => {
    clearStoredHistory();
    setHistory([]);
  }, []);

  return {
    history,
    isLoading,
    addToHistory,
    clearHistory,
    removeFromHistory,
  };
}
