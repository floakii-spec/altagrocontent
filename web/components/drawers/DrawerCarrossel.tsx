'use client'

import { useState } from 'react'

export function DrawerCarrossel() {
  const [topic, setTopic] = useState('')
  const [generating, setGenerating] = useState(false)
  const [slides, setSlides] = useState<string[]>([])

  async function generate() {
    if (!topic.trim()) return
    setGenerating(true)
    // TODO: call FastAPI /api/carousel/generate
    await new Promise((r) => setTimeout(r, 1200))
    setSlides([
      `📌 ${topic}`,
      '⚡ O agro movimenta R$ 2,4 tri por ano',
      '🌱 Safra 24/25 com projeção recorde',
      '📊 +18% de valorização em commodities',
      '🚜 Tecnologia muda o campo',
      '💡 Dica: antecipe-se ao mercado',
    ])
    setGenerating(false)
  }

  return (
    <div className="p-6 space-y-5">
      {/* Input */}
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
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            color: '#fff',
          }}
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

      {/* Slides preview */}
      {slides.length > 0 && (
        <div className="space-y-2">
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            {slides.length} slides gerados
          </p>
          {slides.map((slide, i) => (
            <div
              key={i}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <span
                className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
                style={{ background: '#16a34a22', color: '#16a34a' }}
              >
                {i + 1}
              </span>
              <span className="text-[12px]" style={{ color: 'rgba(255,255,255,0.7)' }}>
                {slide}
              </span>
            </div>
          ))}
          <button
            className="w-full py-2 rounded-lg text-[12px] font-medium mt-2"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.5)' }}
          >
            📋 Copiar todos
          </button>
        </div>
      )}
    </div>
  )
}
