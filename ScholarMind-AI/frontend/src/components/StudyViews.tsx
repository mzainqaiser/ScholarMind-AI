import { useState } from 'react'
import { Check, ChevronLeft, ChevronRight, RotateCw, X } from 'lucide-react'
import type { Flashcard, QuizItem } from '../types'
import { Badge, Button, Card } from './ui'

export function QuizView({ items }: { items: QuizItem[] }) {
  const [picked, setPicked] = useState<Record<number, string>>({})
  const [shown, setShown] = useState<Record<number, boolean>>({})
  const answered = Object.keys(picked).length
  const correct = items.filter((q, i) => picked[i] === q.answer).length
  return (
    <div className="space-y-4">
      {items.some((q) => q.options) && <p className="text-sm text-slate-500">Answered {answered}/{items.length} · Score {correct}</p>}
      {items.map((q, i) => (
        <Card key={i}>
          <p className="font-medium">{i + 1}. {q.question}</p>
          {q.options ? (
            <div className="mt-3 space-y-2">
              {q.options.map((o) => {
                const chosen = picked[i] === o, done = picked[i] !== undefined
                const style = !done ? 'border-slate-200 hover:bg-slate-50' : o === q.answer ? 'border-emerald-300 bg-emerald-50' : chosen ? 'border-red-300 bg-red-50' : 'border-slate-200 opacity-70'
                return (
                  <button key={o} disabled={done} onClick={() => setPicked({ ...picked, [i]: o })}
                    className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-sm ${style}`}>
                    <span>{o}</span>{done && o === q.answer && <Check className="h-4 w-4 text-emerald-600" />}{done && chosen && o !== q.answer && <X className="h-4 w-4 text-red-600" />}
                  </button>)
              })}
            </div>
          ) : (
            <Button variant="secondary" className="mt-3" onClick={() => setShown({ ...shown, [i]: !shown[i] })}>{shown[i] ? 'Hide answer' : 'Show answer'}</Button>
          )}
          {(picked[i] !== undefined || shown[i]) && (
            <div className="mt-3 rounded-lg bg-slate-50 p-3 text-sm"><p><b>Answer:</b> {q.answer}</p>
              {q.explanation && <p className="mt-1 text-slate-600">{q.explanation}</p>}<div className="mt-2"><Badge tone="indigo">source {q.source}</Badge></div></div>
          )}
        </Card>
      ))}
    </div>
  )
}

export function FlashcardView({ cards }: { cards: Flashcard[] }) {
  const [i, setI] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const go = (n: number) => { setI((i + n + cards.length) % cards.length); setFlipped(false) }
  const c = cards[i]
  return (
    <div className="mx-auto max-w-xl">
      <button onClick={() => setFlipped(!flipped)} aria-label="Flip card"
        className="flex min-h-[200px] w-full flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm hover:shadow">
        <span className="mb-3 text-xs uppercase tracking-wide text-slate-400">{flipped ? 'Answer' : 'Question'}</span>
        <span className="text-lg font-medium">{flipped ? c.back : c.front}</span>
        {flipped && <span className="mt-3"><Badge tone="indigo">source {c.source}</Badge></span>}
      </button>
      <div className="mt-4 flex items-center justify-between">
        <Button onClick={() => go(-1)} aria-label="Previous card"><ChevronLeft className="h-4 w-4" />Prev</Button>
        <span className="flex items-center gap-2 text-sm text-slate-500">{i + 1} / {cards.length}
          <button onClick={() => setFlipped(!flipped)} aria-label="Flip" className="rounded p-1 hover:bg-slate-100"><RotateCw className="h-4 w-4" /></button></span>
        <Button onClick={() => go(1)} aria-label="Next card">Next<ChevronRight className="h-4 w-4" /></Button>
      </div>
    </div>
  )
}
