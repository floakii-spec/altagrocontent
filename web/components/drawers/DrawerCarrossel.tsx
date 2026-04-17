'use client'

import { useEffect, useState } from 'react'

interface Slide {
  slide_number: number
  title: string
  copy: string
  cta: string
}

interface Carousel {
  id: number
  theme: string
  slides: Slide[]
  generated_at: string
}

interface Suggestion {
  title: string
  rationale: string
}

interface SuggestionBlock {
  id: number
  themes: Suggestion[]
  generated_at: string
}

export function DrawerCarrossel() {
  const [topic, setTopic] = useState('')
  const [generating, setGenerating] = useState(false)
  const [current, setCurrent] = useState<Carousel | null>(null)
  const [history, setHistory] = useState<Carousel[]>([])
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [refreshingSuggestions, setRefreshingSuggestions] = useState(false)

  async function loadHistory() {
    const res = await fetch('/api/carousel')
    if (res.ok) setHistory(await res.json())
    setLoadingHistory(false)
  }

  async function loadSuggestions() {
    const res = await fetch('/api/carousel/suggestions')
    if (res.ok) {
      const data: SuggestionBlock = await res.json()
      setSuggestions(data.themes)
    }
  }

  useEffect(() => {
    loadHistory()
    loadSuggestions()
  }, [])

  async function generate() {
    if (!topic.trim()) return
    setGenerating(true)
    const res = await fetch('/api/carousel/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theme: topic.trim() }),
    })
    if (res.ok) {
      const data = await res.json()
      setCurrent(data)
      loadHistory()
    }
    setGenerating(false)
  }

  async function refreshSuggestions() {
    setRefreshingSuggestions(true)
    const res = await fetch('/api/carousel/suggestions/refresh', { method: 'POST' })
    if (res.ok) {
      const data: SuggestionBlock = await res.json()
      setSuggestions(data.themes)
    }
    setRefreshingSuggestions(false)
  }

  return (
    <div className="p-6 space-y-5">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Sugestões IA
          </p>
          <button
            onClick={refreshSuggestions}
            disabled={refreshingSuggestions}
            className="text-[11px] px-2 py-0.5 rounded"
            style={{ color: refreshingSuggestions ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.04)' }}
          >
            {refreshingSuggestions ? '⟳' : '↻'}
          </button>
        </div>

        {suggestions.length === 0 ? (
          <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.25)' }}>
            A IA vai gerar sugestões às 06:00 ou clique em ↻
          </p>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => setTopic(s.title)}
                title={s.rationale}
                className="px-2.5 py-1 rounded-full text-[11px] text-left transition-all"
                style={{
                  background: topic === s.title ? 'rgba(22,163,74,0.15)' : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${topic === s.title ? '#16a34a44' : 'rgba(255,255,255,0.08)'}`,
                  color: topic === s.title ? '#16a34a' : 'rgba(255,255,255,0.55)',
                }}
              >
                {s.title}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <label className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Tema do carrossel
        </label>
        <textarea
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Ex: Alta da soja, irrigação inteligente, gestão de safra..."
          rows={3}
          className="w-full rounded-lg px-3 py-2.5 text-sm resize-none outline-none"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#fff' }}
        />
      </div>

      <button
        onClick={generate}
        disabled={generating || !topic.trim()}
        className="w-full py-2.5 rounded-lg text-sm font-semibold transition-all"
        style={{
          background: generating || !topic.trim() ? '#16a34a44' : '#16a34a',
          color: generating || !topic.trim() ? 'rgba(255,255,255,0.4)' : '#fff',
          cursor: generating || !topic.trim() ? 'not-allowed' : 'pointer',
        }}
      >
        {generating ? '⟳ Gerando com GPT-4o...' : '✦ Gerar Carrossel'}
      </button>

      {current && (
        <div className="space-y-2">
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            {current.slides.length} slides gerados
          </p>
          {current.slides.map((slide) => (
            <div
              key={slide.slide_number}
              className="px-3 py-2.5 rounded-lg space-y-1"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
                  style={{ background: '#16a34a22', color: '#16a34a' }}>
                  {slide.slide_number}
                </span>
                <span className="text-[12px] font-semibold text-white">{slide.title}</span>
              </div>
              <p className="text-[11px] pl-7" style={{ color: 'rgba(255,255,255,0.55)' }}>{slide.copy}</p>
              {slide.cta && (
                <p className="text-[11px] pl-7" style={{ color: '#16a34a' }}>→ {slide.cta}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {!loadingHistory && history.length > 0 && (
        <div className="space-y-2 pt-2 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.3)' }}>
            Histórico
          </p>
          {history.map((c) => (
            <button
              key={c.id}
              onClick={() => setCurrent(c)}
              className="w-full text-left px-3 py-2 rounded-lg text-[11px] truncate"
              style={{
                background: current?.id === c.id ? 'rgba(22,163,74,0.1)' : 'rgba(255,255,255,0.02)',
                border: `1px solid ${current?.id === c.id ? '#16a34a33' : 'rgba(255,255,255,0.05)'}`,
                color: 'rgba(255,255,255,0.5)',
              }}
            >
              {c.theme}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
