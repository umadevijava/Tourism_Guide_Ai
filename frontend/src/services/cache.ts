/**
 * Response cache service using localStorage
 * Caches responses to avoid redundant API calls for identical queries
 */

const CACHE_KEY = 'chat_response_cache';
const CACHE_EXPIRY_MS = 1000 * 60 * 60; // 1 hour
const MAX_CACHE_ITEMS = 50;

export interface CachedResponse {
  query: string;
  response: string;
  timestamp: number;
}

export function getCachedResponse(query: string): string | null {
  try {
    const cache = JSON.parse(localStorage.getItem(CACHE_KEY) || '{}') as Record<
      string,
      CachedResponse
    >;
    const cached = cache[query];

    if (!cached) return null;

    // Check if expired
    if (Date.now() - cached.timestamp > CACHE_EXPIRY_MS) {
      delete cache[query];
      localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
      return null;
    }

    return cached.response;
  } catch {
    return null;
  }
}

export function cacheResponse(query: string, response: string): void {
  try {
    const cache = JSON.parse(localStorage.getItem(CACHE_KEY) || '{}') as Record<
      string,
      CachedResponse
    >;

    cache[query] = {
      query,
      response,
      timestamp: Date.now(),
    };

    // Keep only the latest items
    const entries = Object.entries(cache).sort((a, b) => b[1].timestamp - a[1].timestamp);
    const trimmedCache = Object.fromEntries(entries.slice(0, MAX_CACHE_ITEMS));

    localStorage.setItem(CACHE_KEY, JSON.stringify(trimmedCache));
  } catch {
    // Silently fail if cache is full or unavailable
  }
}

export function clearResponseCache(): void {
  try {
    localStorage.removeItem(CACHE_KEY);
  } catch {
    // Silently fail
  }
}
