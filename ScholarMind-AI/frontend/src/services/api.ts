import type { AgentReply, Citation, Conversation, Doc, Message, Overview, SystemStatus, UploadResult, Usage } from '../types'

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? ''

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) { super(message); this.status = status }
}

/** Turns every FastAPI error shape (string, {message}, validation list, upload result list) into one readable message. */
export function errorMessage(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === 'string' ? d : d?.error ?? d?.msg ?? JSON.stringify(d))).join('; ')
  }
  if (detail && typeof detail === 'object' && 'message' in detail) return String((detail as { message: unknown }).message)
  return 'Unexpected error'
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try { res = await fetch(BASE + path, init) }
  catch { throw new ApiError('Cannot reach the backend. Is it running on port 8000?', 0) }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`
    try { msg = errorMessage((await res.json()).detail) } catch { /* non-JSON error body */ }
    throw new ApiError(msg, res.status)
  }
  return res.json() as Promise<T>
}
const json = (method: string, body?: unknown): RequestInit => ({
  method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body),
})

export interface StudyBody { document_ids: string[]; topic?: string; count?: number; days?: number; quiz_type?: 'mcq' | 'short' }

export const api = {
  status: () => request<SystemStatus>('/api/system/status'),
  overview: () => request<Overview>('/api/analytics/overview'),
  usage: () => request<Usage>('/api/analytics/usage'),
  analyticsDocs: () => request<{ documents: Doc[] }>('/api/analytics/documents'),
  listDocs: () => request<{ documents: Doc[] }>('/api/documents').then((r) => r.documents),
  preview: (id: string) => request<{ text: string; truncated: boolean }>(`/api/documents/${id}/preview?max_chars=8000`),
  deleteDoc: (id: string) => request<{ deleted: string }>(`/api/documents/${id}`, { method: 'DELETE' }),
  reindex: (id: string) => request<Doc>(`/api/documents/${id}/reindex`, { method: 'POST' }),
  /** XHR (not fetch) so the browser can report real upload progress. */
  upload(files: File[], category: string, onProgress: (pct: number) => void): Promise<UploadResult[]> {
    return new Promise((resolve, reject) => {
      const form = new FormData()
      files.forEach((f) => form.append('files', f))
      form.append('category', category)
      const xhr = new XMLHttpRequest()
      xhr.open('POST', BASE + '/api/documents/upload')
      xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(Math.round((e.loaded / e.total) * 100))
      xhr.onerror = () => reject(new ApiError('Cannot reach the backend. Is it running on port 8000?', 0))
      xhr.onload = () => {
        let body: { results?: UploadResult[]; detail?: unknown } = {}
        try { body = JSON.parse(xhr.responseText) } catch { /* ignore */ }
        if (xhr.status === 400 && Array.isArray(body.detail)) return resolve(body.detail as UploadResult[])   // every file rejected
        if (xhr.status >= 400) return reject(new ApiError(errorMessage(body.detail), xhr.status))
        resolve(body.results ?? [])
      }
      xhr.send(form)
    })
  },
  chat: (message: string, conversation_id: string | null, document_ids: string[]) =>
    request<AgentReply>('/api/agent/chat', json('POST', { message, conversation_id, document_ids })),
  conversations: () => request<{ conversations: Conversation[] }>('/api/conversations').then((r) => r.conversations),
  conversation: (id: string) => request<Conversation & { messages: Message[] }>(`/api/conversations/${id}`),
  deleteConversation: (id: string) => request(`/api/conversations/${id}`, { method: 'DELETE' }),
  clearConversation: (id: string) => request(`/api/conversations/${id}/messages`, { method: 'DELETE' }),
  study: (kind: 'notes' | 'quiz' | 'flashcards' | 'plan' | 'research' | 'compare', body: StudyBody) =>
    request<AgentReply>(`/api/study/${kind}`, json('POST', body)),
  search: (query: string, top_k: number, document_ids: string[]) =>
    request<{ results: Citation[]; embedder: string }>('/api/rag/search', json('POST', { query, top_k, document_ids: document_ids.length ? document_ids : null })),
}
