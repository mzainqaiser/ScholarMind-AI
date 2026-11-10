export interface Doc {
  id: string; filename: string; file_type: string; category: string; status: 'processing' | 'indexed' | 'failed'
  error: string | null; chunk_count: number; pages: number | null; size_bytes: number; uploaded_at: string
}
export interface Citation {
  id: string; chunk_id: string; doc_id: string; filename: string; page: number | null; section: string | null
  score: number; excerpt: string; cited_in_answer?: boolean; injection_suspected?: boolean
}
export interface TraceStep { step: string; detail: string }
export interface QuizItem { question: string; options?: string[]; answer: string; explanation: string; source: string }
export interface Flashcard { front: string; back: string; source: string }
export interface Structured { type?: string; items?: QuizItem[]; cards?: Flashcard[] }
export interface AgentReply {
  conversation_id?: string; answer: string; status: string; tool: string | null; intent: string | null
  citations: Citation[]; trace: TraceStep[]; structured: Structured | null; warnings: string[]
}
export interface Conversation { id: string; title: string; doc_ids: string[]; created_at: string; updated_at: string; message_count?: number }
export interface Message {
  id: number | string; role: 'user' | 'assistant'; content: string; created_at?: string
  meta: Partial<Omit<AgentReply, 'answer' | 'conversation_id'>>
}
export interface SystemStatus {
  vector_store: { status: string; chunks: number; embedder: string; semantic: boolean }
  database: { status: string; documents: number }
  llm: { available: boolean; provider?: string; model?: string; detail: string }
  config: Record<string, string | number>
}
export interface Overview {
  documents: { total: number; indexed: number; failed: number; processing: number }
  chunks: number; conversations: number; messages: number
  by_type: Record<string, number>; by_category: Record<string, number>
  recent_documents: Doc[]; recent_conversations: { id: string; title: string; updated_at: string; message_count: number }[]
}
export interface Usage { messages_per_day: { date: string; user: number; assistant: number }[]; tools: Record<string, number>; statuses: Record<string, number> }
export interface UploadResult { filename: string; ok: boolean; error?: string; document?: Doc }
