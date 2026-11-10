import { useCallback, useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Check, Copy, FileText, History, Library, Loader2, MessageSquare, Plus, Send, Trash2 } from 'lucide-react'
import { AgentTrace, CitationList } from '../components/Citations'
import DocPicker from '../components/DocPicker'
import Markdown from '../components/Markdown'
import { Alert, Badge, Button, Drawer } from '../components/ui'
import { useApp } from '../context/AppContext'
import { api } from '../services/api'
import type { Conversation, Message } from '../types'
import { TOOL_TITLES } from '../utils/format'

const SUGGESTIONS = ['Summarize my uploaded documents', 'Create 5 MCQs from my notes', 'Find where the key terms are defined', 'Create a 7-day study plan']

export default function Chat() {
  const { docs, toast } = useApp()
  const { state } = useLocation() as { state: { newChat?: number } | null }
  const [convs, setConvs] = useState<Conversation[]>([])
  const [active, setActive] = useState<string | null>(null)
  const [msgs, setMsgs] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selDocs, setSelDocs] = useState<string[]>([])
  const [showPicker, setShowPicker] = useState(false)
  const [sourcesFor, setSourcesFor] = useState<Message | null>(null)
  const [showHistory, setShowHistory] = useState(false)
  const [mobileSources, setMobileSources] = useState(false)   // drawer is only rendered below the lg breakpoint
  const [copied, setCopied] = useState<string | number | null>(null)
  const bottom = useRef<HTMLDivElement>(null)

  const loadConvs = useCallback(() => api.conversations().then(setConvs).catch((e) => setError(e.message)), [])
  useEffect(() => { loadConvs() }, [loadConvs])
  useEffect(() => { setActive(null); setMsgs([]); setSelDocs([]); setSourcesFor(null); setError(null) }, [state?.newChat])
  useEffect(() => { bottom.current?.scrollIntoView?.({ behavior: 'smooth' }) }, [msgs, sending])

  async function open(id: string) {
    setShowHistory(false); setError(null)
    try {
      const c = await api.conversation(id)
      setActive(id); setMsgs(c.messages); setSelDocs(c.doc_ids.filter((d) => docs.some((x) => x.id === d))); setSourcesFor(null)
    } catch (e) { setError((e as Error).message) }
  }
  async function send(text: string) {
    const message = text.trim()
    if (!message || sending) return
    setError(null); setSending(true); setInput('')
    setMsgs((m) => [...m, { id: `u${Date.now()}`, role: 'user', content: message, meta: {} }])
    try {
      const r = await api.chat(message, active, selDocs)
      const reply: Message = { id: `a${Date.now()}`, role: 'assistant', content: r.answer,
        meta: { tool: r.tool, intent: r.intent, status: r.status, citations: r.citations, trace: r.trace, warnings: r.warnings, structured: r.structured } }
      setMsgs((m) => [...m, reply]); setActive(r.conversation_id ?? active)
      if (r.citations.length) setSourcesFor(reply)
      loadConvs()
    } catch (e) { setError((e as Error).message); setInput(message) }
    finally { setSending(false) }
  }
  async function remove(id: string) {
    try { await api.deleteConversation(id); if (id === active) { setActive(null); setMsgs([]) } toast('success', 'Conversation deleted.'); loadConvs() }
    catch (e) { toast('error', (e as Error).message) }
  }
  async function clear() {
    if (!active) return
    try { await api.clearConversation(active); setMsgs([]); setSourcesFor(null); loadConvs() } catch (e) { toast('error', (e as Error).message) }
  }
  async function copy(m: Message) { await navigator.clipboard.writeText(m.content); setCopied(m.id); setTimeout(() => setCopied(null), 1500) }

  const history = (
    <div className="flex h-full flex-col">
      <Button variant="primary" className="m-3" onClick={() => { setActive(null); setMsgs([]); setShowHistory(false) }}><Plus className="h-4 w-4" />New conversation</Button>
      <ul className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
        {convs.length === 0 && <li className="px-2 py-3 text-sm text-slate-500">No conversations yet.</li>}
        {convs.map((c) => (
          <li key={c.id} className={`group flex items-center rounded-lg ${c.id === active ? 'bg-indigo-50' : 'hover:bg-slate-50'}`}>
            <button onClick={() => open(c.id)} className="min-w-0 flex-1 truncate px-3 py-2 text-left text-sm">{c.title}</button>
            <button onClick={() => remove(c.id)} aria-label={`Delete conversation ${c.title}`} className="mr-1 rounded p-1.5 text-slate-400 hover:bg-white hover:text-red-600"><Trash2 className="h-3.5 w-3.5" /></button>
          </li>))}
      </ul>
    </div>)
  const sources = sourcesFor ? <div className="space-y-4"><CitationList citations={sourcesFor.meta.citations ?? []} />
    {sourcesFor.meta.trace && <div><h4 className="mb-2 text-sm font-semibold">Agent activity</h4><AgentTrace trace={sourcesFor.meta.trace} /></div>}</div>
    : <p className="text-sm text-slate-500">Select “Sources” on an answer to inspect its evidence and the agent’s steps.</p>

  return (
    <div className="flex h-full">
      <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white md:block">{history}</aside>
      <section className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-2 border-b border-slate-200 bg-white px-4 py-2">
          <Button variant="ghost" className="md:hidden" onClick={() => setShowHistory(true)} aria-label="Conversation history"><History className="h-4 w-4" /></Button>
          <Button variant="secondary" onClick={() => setShowPicker(true)}><Library className="h-4 w-4" />{selDocs.length ? `${selDocs.length} document${selDocs.length > 1 ? 's' : ''}` : 'All documents'}</Button>
          <div className="ml-auto flex gap-1">
            <Button variant="ghost" disabled={!active || msgs.length === 0} onClick={clear}>Clear chat</Button>
          </div>
        </div>
        <div className="flex-1 space-y-4 overflow-y-auto px-4 py-5" aria-live="polite">
          {msgs.length === 0 && !sending && (
            <div className="mx-auto mt-10 max-w-xl text-center">
              <div className="mx-auto mb-3 w-fit rounded-full bg-indigo-50 p-3 text-indigo-600"><MessageSquare className="h-6 w-6" /></div>
              <h3 className="text-lg font-semibold">Ask about your documents</h3>
              <p className="mt-1 text-sm text-slate-500">{docs.some((d) => d.status === 'indexed') ? 'Answers are grounded in your files and cite their sources.' : 'Upload a document first so the assistant has material to work from.'}</p>
              <div className="mt-5 grid gap-2 sm:grid-cols-2">{SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-sm hover:bg-slate-50">{s}</button>))}</div>
            </div>)}
          {msgs.map((m) => m.role === 'user' ? (
            <div key={m.id} className="flex justify-end"><div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-indigo-600 px-4 py-2.5 text-sm text-white">{m.content}</div></div>
          ) : (
            <div key={m.id} className="flex"><div className="max-w-[92%] rounded-2xl rounded-bl-sm border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <div className="mb-1 flex flex-wrap items-center gap-2">
                {m.meta.tool && <Badge tone="indigo">{TOOL_TITLES[m.meta.tool] ?? m.meta.tool}</Badge>}
                {m.meta.status && m.meta.status !== 'answered' && m.meta.status !== 'chitchat' && <Badge tone="amber">{m.meta.status.replace('_', ' ')}</Badge>}
              </div>
              <Markdown>{m.content}</Markdown>
              {m.meta.warnings?.map((w) => <div key={w} className="mt-2"><Alert tone="amber">{w}</Alert></div>)}
              <div className="mt-2 flex gap-1 border-t border-slate-100 pt-2">
                <Button variant="ghost" className="!px-2 !py-1 text-xs" onClick={() => copy(m)}>{copied === m.id ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}Copy</Button>
                {(m.meta.citations?.length || m.meta.trace?.length) ? <Button variant="ghost" className="!px-2 !py-1 text-xs" onClick={() => { setSourcesFor(m); setMobileSources(true) }}><FileText className="h-3.5 w-3.5" />Sources ({m.meta.citations?.length ?? 0})</Button> : null}
              </div></div></div>))}
          {sending && <div className="flex items-center gap-2 text-sm text-slate-500" role="status"><Loader2 className="h-4 w-4 animate-spin" />Agent is working — retrieving evidence and generating a response…</div>}
          <div ref={bottom} />
        </div>
        <div className="border-t border-slate-200 bg-white p-3">
          {error && <div className="mb-2"><Alert>{error}</Alert></div>}
          <form className="flex items-end gap-2" onSubmit={(e) => { e.preventDefault(); send(input) }}>
            <textarea value={input} onChange={(e) => setInput(e.target.value)} rows={1} maxLength={4000} aria-label="Message"
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) } }}
              placeholder="Ask a question, or request a summary, quiz, comparison…" className="max-h-40 min-h-[42px] flex-1 resize-y rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none" />
            <Button type="submit" variant="primary" loading={sending} disabled={!input.trim()} aria-label="Send message"><Send className="h-4 w-4" /></Button>
          </form>
        </div>
      </section>
      <aside className="hidden w-80 shrink-0 overflow-y-auto border-l border-slate-200 bg-slate-50 p-4 lg:block"><h3 className="mb-3 font-semibold">Sources</h3>{sources}</aside>
      <Drawer open={showHistory} onClose={() => setShowHistory(false)} title="Conversations">{history}</Drawer>
      <Drawer open={showPicker} onClose={() => setShowPicker(false)} title="Search scope">
        <p className="mb-3 text-sm text-slate-500">Choose which documents the assistant may use. Leave empty to search everything.</p>
        <DocPicker value={selDocs} onChange={setSelDocs} /><Button variant="primary" className="mt-4" onClick={() => setShowPicker(false)}>Done</Button></Drawer>
      <div className="lg:hidden"><Drawer open={mobileSources} onClose={() => setMobileSources(false)} title="Sources">{sources}</Drawer></div>
    </div>
  )
}
