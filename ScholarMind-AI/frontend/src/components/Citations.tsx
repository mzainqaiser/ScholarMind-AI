import { FileText } from 'lucide-react'
import type { Citation, TraceStep } from '../types'
import { Badge } from './ui'

export function CitationList({ citations }: { citations: Citation[] }) {
  if (!citations.length) return <p className="text-sm text-slate-500">No sources for this message.</p>
  return (
    <ul className="space-y-3">
      {citations.map((c) => (
        <li key={c.chunk_id} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="indigo">{c.id}</Badge>
            <span className="flex items-center gap-1 font-medium text-slate-800"><FileText className="h-3.5 w-3.5" />{c.filename}</span>
            {c.page != null && <span className="text-slate-500">p. {c.page}</span>}
            {c.section && <span className="text-slate-500">· {c.section}</span>}
          </div>
          <p className="mt-2 border-l-2 border-indigo-200 pl-2 text-slate-600">{c.excerpt}{c.excerpt.length >= 300 ? '…' : ''}</p>
          <div className="mt-2 flex gap-2 text-xs">
            <Badge tone={c.cited_in_answer ? 'green' : 'slate'}>{c.cited_in_answer ? 'cited in answer' : 'retrieved'}</Badge>
            <Badge>relevance {c.score.toFixed(2)}</Badge>
            {c.injection_suspected && <Badge tone="amber">instruction-like text removed</Badge>}
          </div>
        </li>
      ))}
    </ul>
  )
}

/** Shows only concise execution steps (tool, scope, counts) - never model reasoning. */
export function AgentTrace({ trace }: { trace: TraceStep[] }) {
  return (
    <ol className="space-y-1 text-xs text-slate-600">
      {trace.map((t, i) => (
        <li key={i} className="flex gap-2"><span className="mt-0.5 h-1.5 w-1.5 shrink-0 translate-y-1 rounded-full bg-indigo-400" />
          <span><span className="font-medium text-slate-700">{t.step}</span>{t.detail && <span> — {t.detail}</span>}</span></li>
      ))}
    </ol>
  )
}
