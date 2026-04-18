'use client'

import { useEffect, useState } from 'react'

interface ArgumentEntry {
  id: number
  text: string
  topic_cluster: string | null
  agro_segment: string | null
  quality_score: number
  virality_weight: number
  times_seen: number
  source_post_count: number
  origin: string
}

const CLUSTERS = ['soja', 'milho', 'pecuária', 'insumos', 'gestão', 'tecnologia', 'crédito', 'outro']
const SEGMENTS = ['grãos', 'fibras', 'pecuária', 'horticultura', 'cafeicultura', 'geral']

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className="flex-1 h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.08)' }}>
        <div className="h-full rounded-full" style={{ width: `${Math.round(value * 100)}%`, background: color }} />
      </div>
      <span className="text-[10px] shrink-0" style={{ color: 'rgba(255,255,255,0.35)' }}>
        {Math.round(value * 100)}
      </span>
    </div>
  )
}

export function DrawerInteligenciaArgumentos() {
  const [args, setArgs] = useState<ArgumentEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [cluster, setCluster] = useState<string | null>(null)
  const [segment, setSegment] = useState<string | null>(null)
  const [copied, setCopied] = useState<number | null>(null)

  async function load(c: string | null, s: string | null) {
    setLoading(true)
    const params = new URLSearchParams()
    if (c) params.set('topic_cluster', c)
    if (s) params.set('agro_segment', s)
    const res = await fetch(`/api/intelligence/arguments?${params}`)
    if (res.ok) setArgs(await res.json())
    setLoading(false)
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(cluster, segment) }, [cluster, segment])

  async function copyArg(arg: ArgumentEntry) {
    await navigator.clipboard.writeText(arg.text)
    setCopied(arg.id)
    setTimeout(() => setCopied(null), 1500)
  }

  return (
    <div className="p-6 space-y-4">
      <div className="space-y-2">
        <p className="text-[10px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>Tema</p>
        <div className="flex flex-wrap gap-1">
          {CLUSTERS.map((c) => (
            <button
              key={c}
              onClick={() => setCluster(cluster === c ? null : c)}
              className="text-[10px] px-2 py-0.5 rounded-full transition-all"
              style={{
                background: cluster === c ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.04)',
                border: `1px solid ${cluster === c ? '#f59e0b44' : 'rgba(255,255,255,0.08)'}`,
                color: cluster === c ? '#f59e0b' : 'rgba(255,255,255,0.45)',
              }}
            >
              {c}
            </button>
          ))}
        </div>
        <p className="text-[10px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>Segmento</p>
        <div className="flex flex-wrap gap-1">
          {SEGMENTS.map((s) => (
            <button
              key={s}
              onClick={() => setSegment(segment === s ? null : s)}
              className="text-[10px] px-2 py-0.5 rounded-full transition-all"
              style={{
                background: segment === s ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.04)',
                border: `1px solid ${segment === s ? '#f59e0b44' : 'rgba(255,255,255,0.08)'}`,
                color: segment === s ? '#f59e0b' : 'rgba(255,255,255,0.45)',
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.25)' }}>Carregando...</p>
      ) : args.length === 0 ? (
        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.25)' }}>
          Nenhum argumento ainda. Analise posts no Deep Dive primeiro.
        </p>
      ) : (
        <div className="space-y-2">
          {args.map((a) => (
            <div
              key={a.id}
              className="px-3 py-2.5 rounded-lg space-y-2"
              style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <p className="text-[12px] text-white leading-snug">{a.text}</p>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] w-14 shrink-0" style={{ color: 'rgba(255,255,255,0.35)' }}>qualidade</span>
                  <ScoreBar value={a.quality_score} color="#f59e0b" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] w-14 shrink-0" style={{ color: 'rgba(255,255,255,0.35)' }}>viralidade</span>
                  <ScoreBar value={a.virality_weight} color="#16a34a" />
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {a.topic_cluster && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded-full" style={{ background: 'rgba(245,158,11,0.1)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.2)' }}>
                      {a.topic_cluster}
                    </span>
                  )}
                  <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
                    {a.times_seen}× · {a.source_post_count} posts
                  </span>
                </div>
                <button
                  onClick={() => copyArg(a)}
                  className="text-[10px] px-2 py-0.5 rounded transition-all"
                  style={{
                    background: copied === a.id ? 'rgba(22,163,74,0.15)' : 'rgba(255,255,255,0.04)',
                    color: copied === a.id ? '#16a34a' : 'rgba(255,255,255,0.4)',
                    border: `1px solid ${copied === a.id ? '#16a34a33' : 'rgba(255,255,255,0.08)'}`,
                  }}
                >
                  {copied === a.id ? '✓ Copiado' : 'Copiar'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
