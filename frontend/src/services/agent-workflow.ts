/**
 * WebSocket service for agent workflows
 */

type AgentUpdateHandler = (update: AgentWorkflowUpdate) => void;
type AgentErrorHandler = (error: string) => void;

export interface AgentWorkflowUpdate {
  type:
    | 'workflow_start'
    | 'phase_complete'
    | 'workflow_complete'
    | 'error'
    | 'agent_thought'
    | 'agent_action';
  iteration?: number;
  goal?: string;
  phase_name?: string;
  phase_results?: Record<string, unknown>;
  final_results?: Record<string, unknown>;
  thought?: string;
  action?: string;
  message?: string;
  data?: Record<string, unknown>;
}

const WS_BASE = (() => {
  const apiUrl = import.meta.env.VITE_API_URL ?? '';
  if (apiUrl) {
    return apiUrl.replace(/^http/, 'ws');
  }
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${proto}://${window.location.host}`;
})();

const WS_AGENT_URL = `${WS_BASE}/agents/workflow`;

export class AgentWorkflowWebSocket {
  private ws: WebSocket | null = null;
  private readonly onUpdate: AgentUpdateHandler;
  private readonly onError: AgentErrorHandler;

  constructor(onUpdate: AgentUpdateHandler, onError: AgentErrorHandler) {
    this.onUpdate = onUpdate;
    this.onError = onError;
  }

  private connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }
      if (this.ws?.readyState === WebSocket.CONNECTING) {
        const checkConnection = setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            clearInterval(checkConnection);
            resolve();
          } else if (this.ws?.readyState === WebSocket.CLOSED) {
            clearInterval(checkConnection);
            reject(new Error('Connection failed'));
          }
        }, 50);
        return;
      }

      this.ws = new WebSocket(WS_AGENT_URL);

      this.ws.onopen = () => {
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data as string);
          this.onUpdate(data);
        } catch (e) {
          this.onError('Failed to parse workflow update');
        }
      };

      this.ws.onerror = () => {
        this.onError('WebSocket connection error');
        reject(new Error('WebSocket connection error'));
      };

      this.ws.onclose = () => {
        this.ws = null;
      };
    });
  }

  async executeWorkflow(goal: string, query: string): Promise<void> {
    try {
      await this.connect();
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ goal, query }));
      } else {
        this.onError('WebSocket is not connected');
      }
    } catch (error) {
      this.onError(
        error instanceof Error ? error.message : 'Failed to connect'
      );
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
