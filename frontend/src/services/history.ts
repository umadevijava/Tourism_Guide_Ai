export interface HistoryItem {
  id: string;
  query: string;
  response: string;
  timestamp: string;
  date?: string; // For grouping
}

const STORAGE_KEY = 'chat_history';
const MAX_HISTORY_ITEMS = 50;

/**
 * Get all chat history from localStorage
 */
export function getChatHistory(): HistoryItem[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    return JSON.parse(stored) as HistoryItem[];
  } catch {
    console.error('Failed to retrieve chat history');
    return [];
  }
}

/**
 * Add a new item to chat history
 */
export function addToHistory(query: string, response: string): HistoryItem {
  const history = getChatHistory();
  const now = new Date().toISOString();
  
  const newItem: HistoryItem = {
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    query: query.substring(0, 100), // Store preview
    response: response.substring(0, 500), // Store preview
    timestamp: now,
  };

  // Add to beginning to show newest first
  const updated = [newItem, ...history].slice(0, MAX_HISTORY_ITEMS);
  
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {
    console.error('Failed to save chat history');
  }

  return newItem;
}

/**
 * Remove a single item from history
 */
export function removeFromHistory(id: string): void {
  try {
    const history = getChatHistory();
    const updated = history.filter((item) => item.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {
    console.error('Failed to remove item from history');
  }
}

/**
 * Clear all chat history
 */
export function clearChatHistory(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    console.error('Failed to clear chat history');
  }
}

/**
 * Format timestamp to display
 */
export function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days === 1) return 'yesterday';
  if (days < 7) return `${days}d ago`;

  return date.toLocaleDateString();
}

/**
 * Group history by date
 */
export function groupHistoryByDate(items: HistoryItem[]): Record<string, HistoryItem[]> {
  const groups: Record<string, HistoryItem[]> = {
    'Today': [],
    'Yesterday': [],
    'Earlier': [],
  };

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  items.forEach(item => {
    const itemDate = new Date(item.timestamp);
    const itemDay = new Date(itemDate.getFullYear(), itemDate.getMonth(), itemDate.getDate());

    if (itemDay.getTime() === today.getTime()) {
      groups['Today'].push(item);
    } else if (itemDay.getTime() === yesterday.getTime()) {
      groups['Yesterday'].push(item);
    } else {
      groups['Earlier'].push(item);
    }
  });

  return groups;
}
