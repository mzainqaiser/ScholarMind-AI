import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import type { AgentReply } from '../types'
import { TOOL_TITLES } from '../utils/format'
import { AgentTrace, CitationList } from './Citations'
import Markdown from './Markdown'
import { FlashcardView, QuizView } from './StudyViews'
import { Alert, Badge, Button, Card } from './ui'

/** Shared renderer for study / research results returned by the agent. */
export default function ResultPanel({ reply }: { reply: AgentReply }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => { await navigator.clipboard.writeText(reply.answer); setCopied(true); setTimeout(() => setCopied(false), 1500) }
  if (reply.status !== 'answered') {
    return <Alert tone="amber">{reply.answer}<span className="mt-1 block text-xs opacity-75">Status: {reply.status.replace('_', ' ')}</span></Alert>
  }
  const s = reply.structured
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Badge tone="indigo">{TOOL_TITLES[reply.tool ?? ''] ?? reply.tool}</Badge>
        <Button variant="ghost" onClick={copy} aria-label="Copy result">{copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}{copied ? 'Copied' : 'Copy'}</Button>
      </div>
      {reply.warnings.map((w) => <Alert key={w} tone="amber">{w}</Alert>)}
      {s?.items ? <QuizView items={s.items} /> : s?.cards ? <FlashcardView cards={s.cards} /> : <Card><Markdown>{reply.answer}</Markdown></Card>}
      <details className="rounded-lg border border-slate-200 bg-white p-3"><summary className="cursor-pointer text-sm font-medium">Sources ({reply.citations.length})</summary>
        <div className="mt-3"><CitationList citations={reply.citations} /></div></details>
      <details className="rounded-lg border border-slate-200 bg-white p-3"><summary className="cursor-pointer text-sm font-medium">Agent activity</summary>
        <div className="mt-3"><AgentTrace trace={reply.trace} /></div></details>
    </div>
  )
}
