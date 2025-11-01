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
  search_mode?: string;  // Legacy field
  search_method?: string;  // New field (domain_based_quality, etc.)
  timing?: TimingInfo;
  timing_ms?: number;  // Simple timing in milliseconds
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
export async function getDocument(filename: string): Promise<{ filename: string; data: string }> {
  console.log('[API] getDocument called with:', filename);
  
  // ✅ Map filename to domain_id
  const domainMap: Record<string, string> = {
    'luat_hon_nhan.pdf': 'hon_nhan',
    'luat_hinh_su.pdf': 'hinh_su',
    'luat_lao_dong.pdf': 'lao_dong',
    'luat_dat_dai.pdf': 'dat_dai',
    'luat_dau_thau.pdf': 'dau_thau',
    'luat_chuyen_giao_cong_nghe.pdf': 'chuyen_giao_cong_nghe',
    'nghi_dinh_214_2025.pdf': 'nghi_dinh_214',
  };
  
  let domain_id = 'hon_nhan'; // default
  for (const [pdf, domain] of Object.entries(domainMap)) {
    if (filename.includes(pdf)) {
      domain_id = domain;
      break;
    }
  }
  
  console.log('[API] Parsed:', { domain_id, filename });
  
  const url = `${API_BASE}/api/pdf-file/${domain_id}/${filename}`;
  console.log('[API] Fetching from:', url);
  
  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Accept': 'application/pdf' },
  });

  if (!response.ok) {
    console.error('[API] HTTP error:', response.status, response.statusText);
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const blob = await response.blob();
  const reader = new FileReader();
  
  return new Promise((resolve, reject) => {
    reader.onloadend = () => {
      const base64 = (reader.result as string).split(',')[1];
      console.log('[API] PDF loaded, size:', blob.size, 'bytes');
      resolve({ filename, data: base64 });
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
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
