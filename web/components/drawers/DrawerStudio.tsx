'use client'

import { useEffect, useState } from 'react'

interface CompetitorPost {
  id: number
  handle: string
  caption: string | null
  post_type: string
  virality_score: number | null
  published_at: string
}

interface GeneratedPost {
  id: number
  hook: string | null
  caption: string | null
  cta: string | null
  created_at: string
}

export function DrawerStudio() {
  const [posts, setPosts] = useState<CompetitorPost[]>([])
  const [selected, setSelected] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<GeneratedPost | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetch('/api/studio/posts')
      .then((r) => r.json())
      .then((data) => { setPosts(data); setLoading(false) })
  }, [])

  async function generate() {
    if (!selected) return
    setGenerating(true)
    setResult(null)
    const res = await fetch('/api/studio/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ post_id: selected }),
    })
    if (res.ok) setResult(await res.json())
    setGenerating(false)
  }

  function copyToClipboard() {
    if (!result) return
    const text = [result.hook, result.caption, result.cta].filter(Boolean).join('\n\n')
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="p-6 space-y-5">
      <div className="space-y-2">
        <label className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Post do concorrente para adaptar
        </label>

        {loading ? (
          <p className="text-[12px]" style={{ color: 'rgba(255,255,255,0.25)' }}>Carregando posts...</p>
        ) : posts.length === 0 ? (
          <p className="text-[12px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
            Nenhum post coletado. Use Concorrentes → Coletar agora primeiro.
          </p>
        ) : (
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {posts.map((p) => (
              <button
                key={p.id}
                onClick={() => { setSelected(p.id); setResult(null) }}
                className="w-full text-left px-3 py-2.5 rounded-lg transition-all"
                style={{
                  background: selected === p.id ? 'rgba(22,163,74,0.1)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${selected === p.id ? '#16a34a44' : 'rgba(255,255,255,0.06)'}`,
                }}
              >
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-[11px] font-semibold" style={{ color: selected === p.id ? '#16a34a' : 'rgba(255,255,255,0.5)' }}>
                    @{p.handle}
                  </span>
                  {p.virality_score != null && (
                    <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
                      {(p.virality_score * 100).toFixed(0)}% viral
                    </span>
                  )}
                </div>
                {p.caption && (
                  <p className="text-[11px] truncate" style={{ color: 'rgba(255,255,255,0.4)' }}>
                    {p.caption}
                  </p>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      <button
        onClick={generate}
        disabled={generating || !selected}
        className="w-full py-2.5 rounded-lg text-sm font-semibold transition-all"
        style={{
          background: generating || !selected ? '#16a34a44' : '#16a34a',
          color: generating || !selected ? 'rgba(255,255,255,0.4)' : '#fff',
          cursor: generating || !selected ? 'not-allowed' : 'pointer',
        }}
      >
        {generating ? '⟳ Adaptando com sua voz...' : '🎬 Adaptar com minha voz'}
      </button>

      {result && (
        <div className="space-y-2">
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Post adaptado
          </p>
          <div className="rounded-lg px-4 py-3 space-y-3" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
            {result.hook && (
              <p className="text-[13px] font-semibold text-white">{result.hook}</p>
            )}
            {result.caption && (
              <p className="text-[12px] leading-relaxed whitespace-pre-line" style={{ color: 'rgba(255,255,255,0.7)' }}>
                {result.caption}
              </p>
            )}
            {result.cta && (
              <p className="text-[12px] font-medium" style={{ color: '#16a34a' }}>→ {result.cta}</p>
            )}
          </div>
          <button
            onClick={copyToClipboard}
            className="w-full py-2 rounded-lg text-[12px] font-medium"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.5)' }}
          >
            {copied ? '✓ Copiado!' : '📋 Copiar'}
          </button>
        </div>
      )}
    </div>
  )
}
