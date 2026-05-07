type TokenHandler = (token: string) => void;
type ErrorHandler = (error: string) => void;
type SessionIdHandler = (sessionId: string) => void;

export interface ChatModes {
  rag: boolean;
  reasoning: boolean;
  webSearch: boolean;
}

const WS_BASE = (() => {
  const apiUrl = import.meta.env.VITE_API_URL ?? '';
  if (apiUrl) {
    return apiUrl.replace(/^http/, 'ws');
  }
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${proto}://${window.location.host}`;
})();

const WS_URL = `${WS_BASE}/chat/stream`;
const CONNECTION_TIMEOUT = 10000; // 10 seconds

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private readonly onToken: TokenHandler;
  private readonly onError: ErrorHandler;
  private readonly onSessionId: SessionIdHandler;
  private connectionTimeoutId: ReturnType<typeof setTimeout> | null = null;
  private currentRequestId: string | null = null;
  private sessionId: string | null = null;

  constructor(onToken: TokenHandler, onError: ErrorHandler, onSessionId: SessionIdHandler) {
    this.onToken = onToken;
    this.onError = onError;
    this.onSessionId = onSessionId;
  }

  private clearConnectionTimeout(): void {
    if (this.connectionTimeoutId) {
      clearTimeout(this.connectionTimeoutId);
      this.connectionTimeoutId = null;
    }
  }

  private connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.clearConnectionTimeout();
        resolve();
        return;
      }
      if (this.ws?.readyState === WebSocket.CONNECTING) {
        // Wait for existing connection attempt
        const checkConnection = setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            clearInterval(checkConnection);
            this.clearConnectionTimeout();
            resolve();
          } else if (this.ws?.readyState === WebSocket.CLOSED) {
            clearInterval(checkConnection);
            reject(new Error('Connection failed'));
          }
        }, 50);
        return;
      }

      this.ws = new WebSocket(WS_URL);

      // Set connection timeout
      this.connectionTimeoutId = setTimeout(() => {
        if (this.ws?.readyState !== WebSocket.OPEN) {
          this.ws?.close();
          this.ws = null;
          reject(new Error('Connection timeout - backend may not be running'));
        }
      }, CONNECTION_TIMEOUT);

      this.ws.onopen = () => {
        this.clearConnectionTimeout();
        resolve();
      };

      this.ws.onmessage = (event) => {
        // Try to parse as JSON first (for sessionId and other metadata)
        try {
          const data = JSON.parse(event.data);
          if (data.sessionId) {
            this.sessionId = data.sessionId;
            this.onSessionId(data.sessionId);
            console.log('✓ Received sessionId:', data.sessionId);
          } else if (data.error) {
            // Handle JSON error objects
            this.onError(data.error);
          } else {
            // Other JSON messages are treated as tokens
            this.onToken(JSON.stringify(data));
          }
        } catch {
          // Not JSON, treat as text token
          // Filter out error text messages that might have been sent after streaming completed
          const text = event.data as string;
          if (text && !text.toLowerCase().includes('error during')) {
            this.onToken(text);
          } else if (text.toLowerCase().includes('error during')) {
            // Only treat as error if it appears to be a genuine error message
            console.debug('Filtering out potential post-stream error message:', text);
          }
        }
      };

      this.ws.onerror = (event) => {
        this.clearConnectionTimeout();
        console.error('WebSocket error:', event);
        const errorMsg = 'Unable to connect to backend. Please ensure the server is running on http://localhost:8000';
        this.onError(errorMsg);
        reject(new Error(errorMsg));
      };

      this.ws.onclose = () => {
        this.clearConnectionTimeout();
        this.ws = null;
      };
    });
  }

  async sendMessage(text: string, modes: ChatModes, sessionId?: string): Promise<string> {
    try {
      await this.connect();
      
      // Use provided sessionId or stored one
      if (sessionId) {
        this.sessionId = sessionId;
      }
      
      // Generate unique request ID to track this specific request
      const requestId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      this.currentRequestId = requestId;

      if (this.ws?.readyState === WebSocket.OPEN) {
        // Build message with appropriate flags
        const message: any = { 
          text,
          requestId, // Include request ID in message
        };

        // Include session ID if available
        if (this.sessionId) {
          message.sessionId = this.sessionId;
        }

        if (modes.rag) {
          message.rag = true;
        }
        if (modes.webSearch) {
          message.googleSearch = true;
        }
        if (modes.reasoning) {
          message.reasoning = true;
        }

        this.ws.send(JSON.stringify(message));
        return requestId;
      } else {
        this.onError('WebSocket is not connected');
        throw new Error('WebSocket is not connected');
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to connect to backend';
      this.onError(errorMsg);
      throw error;
    }
  }

  getCurrentRequestId(): string | null {
    return this.currentRequestId;
  }

  isRequestCurrent(requestId: string): boolean {
    return requestId === this.currentRequestId;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  setSessionId(sessionId: string): void {
    this.sessionId = sessionId;
    console.log('✓ Set sessionId:', sessionId);
  }

  disconnect(): void {
    this.clearConnectionTimeout();
    this.ws?.close();
    this.ws = null;
  }

  reconnect(): void {
    this.disconnect();
    this.ws = null;
    this.currentRequestId = null;
  }
}
