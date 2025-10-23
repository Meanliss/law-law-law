/**
 * API Service - Connect to FastAPI Backend
 */

// Use relative path to leverage Vite proxy in development
// In production, this should be the actual API URL
const API_BASE = import.meta.env.PROD 
  ? (import.meta.env.VITE_API_URL || 'http://localhost:7860')
  : ''; // In dev, use proxy (no base URL needed)

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface QuestionRequest {
  question: string;
  use_advanced: boolean;
  model_mode: 'fast' | 'quality';
  chat_history: ChatMessage[];
}

export interface PDFSource {
  pdf_file: string;
  page_num?: number;
  content: string;
  highlight_text: string;
  json_file?: string;
  article_num?: string;
}

export interface TimingInfo {
  total_ms: number;
  search_ms: number;
  generation_ms: number;
  status: string;
}

export interface AnswerResponse {
  answer: string;
  sources: Array<{
    source: string;
    content: string;
  }>;
  pdf_sources: PDFSource[];
  search_mode: string;
  timing?: TimingInfo;
}

export interface FeedbackRequest {
  query: string;
  answer: string;
  context: Array<{ source: string; content: string }>;
  status: 'like' | 'dislike';
  comment?: string;
}

export interface StatsResponse {
  total_chunks: number;
  laws: Record<string, number>;
  models: {
    embedder: string;
    llm_full: string;
    llm_lite: string;
  };
  intent_cache_size: number;
}

/**
 * Send question to backend
 */
export async function askQuestion(
  question: string,
  mode: 'fast' | 'quality' = 'quality',
  chatHistory: ChatMessage[] = []
): Promise<AnswerResponse> {
  const response = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      use_advanced: true,
      model_mode: mode,
      chat_history: chatHistory,
    } as QuestionRequest),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Submit feedback
 */
export async function submitFeedback(
  query: string,
  answer: string,
  context: Array<{ source: string; content: string }>,
  status: 'like' | 'dislike',
  comment?: string
): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      answer,
      context,
      status,
      comment,
    } as FeedbackRequest),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Get system statistics
 */
export async function getStats(): Promise<StatsResponse> {
  const response = await fetch(`${API_BASE}/stats`);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Get PDF document (base64)
 */
export async function getDocument(filename: string): Promise<{
  filename: string;
  data: string;
  size: number;
  type: string;
}> {
  const response = await fetch(`${API_BASE}/api/get-document`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ filename }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{
  status: string;
  models_loaded: boolean;
  total_chunks: number;
}> {
  const response = await fetch(`${API_BASE}/health`);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}
