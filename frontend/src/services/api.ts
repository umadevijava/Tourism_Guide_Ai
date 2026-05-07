import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

export interface DocumentInfo {
  document_id: string;
  filename: string;
  size: number;
  content_type: string;
}

interface DocumentUploadResponse {
  document_id: string;
  filename: string;
}

interface DocumentListResponse {
  documents: DocumentInfo[];
}

// Chat History Types
export interface ChatMessageItem {
  question: string;
  answer: string;
  timestamp: string;
  rag_mode: boolean;
  reasoning_mode: boolean;
  web_search_mode: boolean;
}

export interface ChatSessionSummary {
  session_id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  title: string | null;
  last_message: string | null;
  last_question: string | null;
}

export interface ChatSessionListResponse {
  sessions: ChatSessionSummary[];
  total: number;
}

export interface ChatHistoryResponse {
  session_id: string;
  created_at: string;
  updated_at: string;
  title: string | null;
  messages: ChatMessageItem[];
}

// Document APIs
export async function uploadDocument(
  file: File,
  onProgress?: (pct: number) => void,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post<DocumentUploadResponse>(
    `${API_BASE}/documents`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // 5 minutes - document processing can take time
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          onProgress(Math.round((event.loaded * 100) / event.total));
        }
      },
    },
  );
  return response.data;
}

export async function listDocuments(): Promise<DocumentListResponse> {
  const response = await axios.get<DocumentListResponse>(`${API_BASE}/documents`);
  return response.data;
}

export async function deleteDocument(documentId: string): Promise<void> {
  await axios.delete(`${API_BASE}/documents/${documentId}`);
}

// Chat History APIs
export async function getChatSessions(limit: number = 50): Promise<ChatSessionListResponse> {
  const response = await axios.get<ChatSessionListResponse>(`${API_BASE}/history?limit=${limit}`);
  return response.data;
}

export async function getChatHistory(sessionId: string): Promise<ChatHistoryResponse> {
  const response = await axios.get<ChatHistoryResponse>(`${API_BASE}/history/${sessionId}`);
  return response.data;
}

export async function updateSessionTitle(sessionId: string, title: string): Promise<void> {
  await axios.put(`${API_BASE}/history/${sessionId}/title`, { title });
}

export async function deleteSession(sessionId: string): Promise<void> {
  await axios.delete(`${API_BASE}/history/${sessionId}`);
}

export async function createNewSession(): Promise<{ session_id: string }> {
  const response = await axios.post(`${API_BASE}/history/session/create`, {});
  return response.data;
}

export async function clearAllHistory(): Promise<void> {
  await axios.delete(`${API_BASE}/history`);
}

export async function resetChatHistory(): Promise<void> {
  await axios.delete(`${API_BASE}/chat/history`);
}
