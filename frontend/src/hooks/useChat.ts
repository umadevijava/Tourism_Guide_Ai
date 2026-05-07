import { useCallback, useEffect, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import { ChatWebSocket } from '../services/websocket';
import { resetChatHistory } from '../services/api';
import { getCachedResponse, cacheResponse, clearResponseCache } from '../services/cache';
import type { ChatModes } from '@/components/chat';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isStreaming?: boolean;
  requestId?: string; // Track which request this message belongs to
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const wsRef = useRef<ChatWebSocket | null>(null);
  const idRef = useRef(0);
  const streamingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const currentRequestIdRef = useRef<string | null>(null);
  const userQueryRef = useRef<string>('');

  useEffect(() => {
    const ws = new ChatWebSocket(
      (token) => {
        flushSync(() => {
          // Only process token if this is still the current request
          if (!currentRequestIdRef.current) return;

          // Clear any existing timeout
          if (streamingTimeoutRef.current) {
            clearTimeout(streamingTimeoutRef.current);
          }

          setMessages((prev) => {
            const last = prev[prev.length - 1];
            
            // Safety checks:
            // 1. Last message must be from bot
            // 2. Last message must belong to current request
            // 3. Last message must be streaming
            if (
              !last ||
              last.sender !== 'bot' ||
              last.requestId !== currentRequestIdRef.current ||
              !last.isStreaming
            ) {
              return prev;
            }

            const updated = {
              ...last,
              text: last.text + token,
              isStreaming: true,
            };
            return [...prev.slice(0, -1), updated];
          });

          // Set timeout to mark streaming as done after no tokens for 500ms
          streamingTimeoutRef.current = setTimeout(() => {
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (
                last?.sender === 'bot' &&
                last?.isStreaming &&
                last?.requestId === currentRequestIdRef.current
              ) {
                const completed = { ...last, isStreaming: false };
                // Cache the response
                if (userQueryRef.current) {
                  cacheResponse(userQueryRef.current, completed.text);
                }
                return [...prev.slice(0, -1), completed];
              }
              return prev;
            });
            setIsStreaming(false);
          }, 500);
        });
      },
      (error) => {
        if (streamingTimeoutRef.current) {
          clearTimeout(streamingTimeoutRef.current);
        }
        
        // Only show error if it's for the current request
        if (!currentRequestIdRef.current) return;

        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.sender === 'bot' && last?.requestId === currentRequestIdRef.current) {
            const updated = {
              ...last,
              text: `Error: ${error}`,
              isStreaming: false,
            };
            return [...prev.slice(0, -1), updated];
          }
          return [
            ...prev,
            {
              id: ++idRef.current,
              text: `Error: ${error}`,
              sender: 'bot',
              timestamp: new Date(),
              requestId: currentRequestIdRef.current || undefined,
            },
          ];
        });
        setIsStreaming(false);
      },
      (newSessionId) => {
        console.log('useChat: Received sessionId:', newSessionId);
        setSessionId(newSessionId);
      },
    );
    wsRef.current = ws;
    return () => {
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
      }
      ws.disconnect();
    };
  }, []);

  const sendMessage = useCallback(
    (text: string, modes: ChatModes) => {
      if (!text.trim() || isStreaming) return;

      // Check cache first
      const cached = getCachedResponse(text);
      if (cached) {
        const userMsg: Message = {
          id: ++idRef.current,
          text,
          sender: 'user',
          timestamp: new Date(),
        };
        const cachedMsg: Message = {
          id: ++idRef.current,
          text: cached,
          sender: 'bot',
          timestamp: new Date(),
          isStreaming: false,
        };
        setMessages((prev) => [...prev, userMsg, cachedMsg]);
        return;
      }

      // Clear previous streaming if any
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
        streamingTimeoutRef.current = null;
      }

      userQueryRef.current = text;
      const userMsg: Message = {
        id: ++idRef.current,
        text,
        sender: 'user',
        timestamp: new Date(),
      };

      // Request ID will be returned from sendMessage
      const requestId = `msg-${++idRef.current}-${Date.now()}`;
      currentRequestIdRef.current = requestId;

      const botPlaceholder: Message = {
        id: ++idRef.current,
        text: '',
        sender: 'bot',
        timestamp: new Date(),
        isStreaming: true,
        requestId,
      };

      setMessages((prev) => [...prev, userMsg, botPlaceholder]);
      setIsStreaming(true);

      // Send message with sessionId and track the request
      wsRef.current?.sendMessage(text, modes, sessionId || undefined).catch((error) => {
        console.error('Failed to send message:', error);
        setIsStreaming(false);
      });
    },
    [isStreaming, sessionId],
  );

  const clearMessages = useCallback(() => {
    // Clear streaming timeout
    if (streamingTimeoutRef.current) {
      clearTimeout(streamingTimeoutRef.current);
      streamingTimeoutRef.current = null;
    }

    // Clear current request
    currentRequestIdRef.current = null;
    userQueryRef.current = '';

    // Reset state
    setMessages([]);
    setIsStreaming(false);
    setSessionId(null); // Reset sessionId for new chat
    idRef.current = 0;

    // Clear cache when starting new chat
    clearResponseCache();

    // Reconnect WebSocket for clean slate
    wsRef.current?.reconnect();
    resetChatHistory();
  }, []);

  const loadHistoryMessages = useCallback((messages: Array<{ question: string; answer: string }>) => {
    // Load messages from history into the UI
    const loadedMessages: Message[] = [];
    let msgId = 0;
    
    messages.forEach((msg) => {
      // Add user message
      loadedMessages.push({
        id: msgId++,
        text: msg.question,
        sender: 'user',
        timestamp: new Date(),
      });
      
      // Add bot message
      loadedMessages.push({
        id: msgId++,
        text: msg.answer,
        sender: 'bot',
        timestamp: new Date(),
        isStreaming: false,
      });
    });
    
    setMessages(loadedMessages);
    idRef.current = msgId;
  }, []);

  return { messages, isStreaming, sessionId, sendMessage, clearMessages, loadHistoryMessages };
}
