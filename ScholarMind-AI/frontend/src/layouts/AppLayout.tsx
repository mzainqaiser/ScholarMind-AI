import { useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { BarChart3, BookOpen, FileText, FlaskConical, GraduationCap, LayoutDashboard, Menu, MessageSquare, Plus, Settings } from 'lucide-react'
import { useApp } from '../context/AppContext'
import { Badge, Button } from '../components/ui'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, title: 'Dashboard' },
  { to: '/assistant', label: 'AI Assistant', icon: MessageSquare, title: 'AI Assistant' },
  { to: '/documents', label: 'My Documents', icon: FileText, title: 'My Documents' },
  { to: '/research', label: 'Research Workspace', icon: FlaskConical, title: 'Research Workspace' },
  { to: '/study', label: 'Study Tools', icon: BookOpen, title: 'Study Tools' },
  { to: '/analytics', label: 'Analytics', icon: BarChart3, title: 'Analytics' },
  { to: '/settings', label: 'Settings', icon: Settings, title: 'Settings' },
]

export default function AppLayout() {
  const [open, setOpen] = useState(false)
  const nav = useNavigate()
  const { pathname } = useLocation()
  const { status, statusError } = useApp()
  const title = NAV.find((n) => n.to === pathname)?.title ?? 'ScholarMind AI'
  const sidebar = (
    <div className="flex h-full flex-col bg-white">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="rounded-lg bg-indigo-600 p-1.5 text-white"><GraduationCap className="h-5 w-5" /></div>
        <div><div className="font-semibold leading-tight">ScholarMind AI</div><div className="text-[11px] text-slate-500">Agentic research assistant</div></div>
      </div>
      <div className="px-4"><Button variant="primary" className="w-full" onClick={() => { setOpen(false); nav('/assistant', { state: { newChat: Date.now() } }) }}>
        <Plus className="h-4 w-4" />New Chat</Button></div>
      <nav className="mt-4 flex-1 space-y-1 px-3" aria-label="Main">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === '/'} onClick={() => setOpen(false)}
            className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'}`}>
            <Icon className="h-4 w-4" />{label}</NavLink>
        ))}
      </nav>
      <p className="px-5 py-4 text-[11px] text-slate-400">Answers are grounded in your uploaded documents.</p>
    </div>
  )
  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="hidden w-64 shrink-0 border-r border-slate-200 md:block">{sidebar}</aside>
      {open && <div className="fixed inset-0 z-40 md:hidden" onClick={() => setOpen(false)}><div className="h-full w-64 border-r border-slate-200 shadow-xl" onClick={(e) => e.stopPropagation()}>{sidebar}</div></div>}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3">
          <button className="rounded p-1.5 hover:bg-slate-100 md:hidden" aria-label="Open menu" onClick={() => setOpen(true)}><Menu className="h-5 w-5" /></button>
          <h1 className="text-base font-semibold">{title}</h1>
          <div className="ml-auto flex items-center gap-2">
            {statusError ? <Badge tone="red">Backend offline</Badge> : status && (
              <>
                {!status.vector_store.semantic && <span title="Semantic model not loaded; using lexical fallback"><Badge tone="amber">Fallback embeddings</Badge></span>}
                {status.llm.available ? <Badge tone="green">LLM: {status.llm.model}</Badge> : <span title={status.llm.detail}><Badge tone="amber">LLM offline</Badge></span>}
              </>)}
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700" title="Profile (placeholder)">MZ</div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto"><Outlet /></main>
      </div>
    </div>
  )
}
