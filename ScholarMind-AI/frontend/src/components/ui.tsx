import { ButtonHTMLAttributes, ReactNode } from 'react'
import { AlertCircle, Loader2, X } from 'lucide-react'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'
const VARIANTS: Record<Variant, string> = {
  primary: 'bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-indigo-300',
  secondary: 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 disabled:text-slate-400',
  danger: 'bg-white text-red-600 border border-red-200 hover:bg-red-50 disabled:text-red-300',
  ghost: 'text-slate-600 hover:bg-slate-100 disabled:text-slate-300',
}
export function Button({ variant = 'secondary', loading, className = '', children, disabled, ...rest }:
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; loading?: boolean }) {
  return (
    <button {...rest} disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 disabled:cursor-not-allowed ${VARIANTS[variant]} ${className}`}>
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}{children}
    </button>
  )
}
export const Card = ({ children, className = '' }: { children: ReactNode; className?: string }) =>
  <div className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>{children}</div>

const TONES = { green: 'bg-emerald-50 text-emerald-700 ring-emerald-200', amber: 'bg-amber-50 text-amber-700 ring-amber-200',
  red: 'bg-red-50 text-red-700 ring-red-200', indigo: 'bg-indigo-50 text-indigo-700 ring-indigo-200', slate: 'bg-slate-100 text-slate-600 ring-slate-200' }
export const Badge = ({ tone = 'slate', children }: { tone?: keyof typeof TONES; children: ReactNode }) =>
  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES[tone]}`}>{children}</span>

export const Spinner = ({ label = 'Loading…' }: { label?: string }) =>
  <div className="flex items-center gap-2 py-6 text-sm text-slate-500" role="status"><Loader2 className="h-4 w-4 animate-spin" />{label}</div>

export function Alert({ children, tone = 'red', onRetry }: { children: ReactNode; tone?: 'red' | 'amber' | 'indigo'; onRetry?: () => void }) {
  const c = { red: 'border-red-200 bg-red-50 text-red-800', amber: 'border-amber-200 bg-amber-50 text-amber-800', indigo: 'border-indigo-200 bg-indigo-50 text-indigo-800' }[tone]
  return (
    <div role="alert" className={`flex items-start gap-2 rounded-lg border px-3 py-2.5 text-sm ${c}`}>
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden /><div className="flex-1">{children}</div>
      {onRetry && <button onClick={onRetry} className="font-medium underline">Retry</button>}
    </div>
  )
}
export function EmptyState({ icon, title, text, action }: { icon: ReactNode; title: string; text: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
      <div className="mb-3 rounded-full bg-indigo-50 p-3 text-indigo-600">{icon}</div>
      <h3 className="font-semibold text-slate-800">{title}</h3><p className="mt-1 max-w-sm text-sm text-slate-500">{text}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
export const PageHeader = ({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) =>
  <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
    <div><h2 className="text-xl font-semibold text-slate-900">{title}</h2>{subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}</div>{actions}
  </div>

export function Drawer({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: ReactNode }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-900/30" onClick={onClose}>
      <aside role="dialog" aria-label={title} className="h-full w-full max-w-lg overflow-y-auto bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between"><h3 className="font-semibold">{title}</h3>
          <button onClick={onClose} aria-label="Close" className="rounded p-1 hover:bg-slate-100"><X className="h-5 w-5" /></button></div>
        {children}
      </aside>
    </div>
  )
}
export const statusTone = (s: string) => (s === 'indexed' ? 'green' : s === 'failed' ? 'red' : 'amber') as 'green' | 'red' | 'amber'
