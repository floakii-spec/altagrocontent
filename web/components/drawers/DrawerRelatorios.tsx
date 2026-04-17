'use client'

import { useState } from 'react'

export function DrawerRelatorios() {
  const [generating, setGenerating] = useState(false)

  async function generate() {
    setGenerating(true)
    await new Promise((r) => setTimeout(r, 1500))
    setGenerating(false)
  }

  return (
    <div className="p-6 space-y-5">
      {/* Last report summary */}
      <div className="rounded-lg p-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex items-center justify-between mb-3">
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Último relatório
          </p>
          <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.25)' }}>há 3 dias</span>
        </div>
        {[
          { label: 'Posts analisados', value: '247' },
          { label: 'Perfis monitorados', value: '8' },
          { label: 'Score médio viral', value: '84%', highlight: true },
          { label: 'Gaps identificados', value: '12' },
        ].map((row) => (
          <div key={row.label} className="flex items-center justify-between py-1.5 border-b" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
            <span className="text-[12px]" style={{ color: 'rgba(255,255,255,0.45)' }}>{row.label}</span>
            <span className="text-[13px] font-semibold" style={{ color: row.highlight ? '#16a34a' : '#fff' }}>
              {row.value}
            </span>
          </div>
        ))}
      </div>

      {/* Top topics */}
      <div>
        <p className="text-[11px] font-semibold tracking-wider uppercase mb-2" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Tópicos em alta
        </p>
        {['Soja — exportação', 'Milho safrinha', 'Insumos biológicos', 'Tecnologia de precisão'].map((t, i) => (
          <div key={t} className="flex items-center gap-3 py-2 border-b" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
            <span className="text-[11px] font-bold w-4 text-center" style={{ color: 'rgba(255,255,255,0.25)' }}>{i + 1}</span>
            <span className="text-[12px] flex-1" style={{ color: 'rgba(255,255,255,0.65)' }}>{t}</span>
            <div className="h-1 rounded-full" style={{ width: `${80 - i * 12}px`, background: '#8b5cf6' }} />
          </div>
        ))}
      </div>

      <button
        onClick={generate}
        disabled={generating}
        className="w-full py-2.5 rounded-lg text-sm font-semibold transition-all"
        style={{
          background: generating ? '#8b5cf644' : '#8b5cf6',
          color: generating ? 'rgba(255,255,255,0.4)' : '#fff',
          cursor: generating ? 'not-allowed' : 'pointer',
        }}
      >
        {generating ? '⟳ Gerando com GPT-4o...' : '✦ Gerar novo relatório'}
      </button>
    </div>
  )
}
