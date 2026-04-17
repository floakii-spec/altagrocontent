'use client'

import { useState } from 'react'

export function DrawerStudio() {
  const [url, setUrl] = useState('')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState('')

  async function adapt() {
    if (!url.trim()) return
    setGenerating(true)
    await new Promise((r) => setTimeout(r, 1400))
    setResult(
      'Você sabia que a soja brasileira está quebrando recordes de exportação? 🌱\n\nEnquanto o mundo debate segurança alimentar, o produtor brasileiro já está dando a resposta — com tecnologia, gestão e muita dedicação.\n\nNo campo, a inovação não para. E você, está pronto para essa safra? 🚜\n\n#agro #soja #tecnologia #safra2025'
    )
    setGenerating(false)
  }

  return (
    <div className="p-6 space-y-5">
      <div className="space-y-2">
        <label className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Post do concorrente (URL ou texto)
        </label>
        <textarea
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Cole a URL do Instagram ou o texto do post..."
          rows={3}
          className="w-full rounded-lg px-3 py-2.5 text-sm resize-none outline-none"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#fff' }}
        />
      </div>

      <button
        onClick={adapt}
        disabled={generating || !url.trim()}
        className="w-full py-2.5 rounded-lg text-sm font-semibold transition-all"
        style={{
          background: generating || !url.trim() ? '#16a34a44' : '#16a34a',
          color: generating || !url.trim() ? 'rgba(255,255,255,0.4)' : '#fff',
          cursor: generating || !url.trim() ? 'not-allowed' : 'pointer',
        }}
      >
        {generating ? '⟳ Adaptando com voz do Nathan...' : '🎬 Adaptar com minha voz'}
      </button>

      {result && (
        <div className="space-y-2">
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Post adaptado
          </p>
          <div className="rounded-lg px-4 py-3" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <p className="text-[12px] leading-relaxed whitespace-pre-line" style={{ color: 'rgba(255,255,255,0.75)' }}>
              {result}
            </p>
          </div>
          <button
            className="w-full py-2 rounded-lg text-[12px] font-medium"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.5)' }}
          >
            📋 Copiar
          </button>
        </div>
      )}
    </div>
  )
}
