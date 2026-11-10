export const formatBytes = (n: number) => (n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(1)} KB` : `${(n / 1048576).toFixed(1)} MB`)
export const formatDate = (iso: string) => new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
export const TOOL_TITLES: Record<string, string> = {
  document_search: 'Document Search', summarize: 'Summarization', compare: 'Comparison', notes: 'Study Notes', quiz: 'Quiz Generator',
  flashcards: 'Flashcards', research: 'Research Assistant', document_qa: 'Document Q&A', study_plan: 'Learning Plan',
}
