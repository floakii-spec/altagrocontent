'use client'

import { useEffect, useState } from 'react'

interface DataPoint {
  value: string
  context: string
  source: string | null
}

interface PostIntelligence {
  post_id: number
  handle: string
  likes: number
  virality_score: number | null
  agro_topic_cluster: string | null
  agro_segment: string | null
  technical_depth: string | null
  core_argument: string | null
  argument_structure: string | null
  technical_claims: string[]
  data_points: DataPoint[]
  sources_referenced: string[]
  knowledge_assumptions: string | null
  content_gaps: string | null
  replication_template: string | null
  analyzed_at: string
}

const DEPTH_COLORS: Record<string, string> = {
  especialista: '#16a34a',
  intermediário: '#f59e0b',
  superficial: '#6b7280',
}

export function DrawerInteligenciaPosts() {
  const [posts, setPosts] = useState<PostIntelligence[]>([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [expanded, setExpanded] = useState<number | null>(null)

  async function load() {
    const res = await fetch('/api/intelligence/posts')
    if (res.ok) setPosts(await res.json())
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function analyzeNew() {
    setAnalyzing(true)
    const res = await fetch('/api/intelligence/analyze', { method: 'POST' })
    if (res.ok) {
      await load()
    }
    setAnalyzing(false)
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
          {posts.length} posts analisados
        </p>
        <button
          onClick={analyzeNew}
          disabled={analyzing}
          className="text-[11px] px-3 py-1 rounded-lg transition-all"
          style={{
            background: 'rgba(245,158,11,0.1)',
            border: '1px solid rgba(245,158,11,0.2)',
            color: analyzing ? 'rgba(255,255,255,0.25)' : '#f59e0b',
          }}
        >
          {analyzing ? '⟳ Analisando...' : '⚡ Analisar novos'}
        </button>
      </div>

      {loading ? (
        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.25)' }}>Carregando...</p>
      ) : posts.length === 0 ? (
        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.25)' }}>
          Nenhum post analisado ainda. Clique em &quot;Analisar novos&quot;.
        </p>
      ) : (
        <div className="space-y-2">
          {posts.map((p) => {
            const depthColor = DEPTH_COLORS[p.technical_depth ?? ''] ?? '#6b7280'
            const isOpen = expanded === p.post_id
            return (
              <div
                key={p.post_id}
                className="rounded-lg overflow-hidden"
                style={{ border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.02)' }}
              >
                <button
                  onClick={() => setExpanded(isOpen ? null : p.post_id)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] font-semibold text-white truncate">@{p.handle}</span>
                      <span
                        className="text-[9px] font-bold px-1.5 py-0.5 rounded-full shrink-0"
                        style={{ background: depthColor + '22', color: depthColor, border: `1px solid ${depthColor}44` }}
                      >
                        {p.technical_depth ?? '—'}
                      </span>
                    </div>
                    <p className="text-[11px] mt-0.5 truncate" style={{ color: 'rgba(255,255,255,0.4)' }}>
                      {p.agro_topic_cluster ?? '—'} · {p.likes.toLocaleString()} likes
                    </p>
                  </div>
                  <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 12 }}>{isOpen ? '▲' : '▼'}</span>
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 space-y-3 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                    {p.core_argument && (
                      <div className="pt-3">
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: '#f59e0b' }}>Tese central</p>
                        <p className="text-[12px] text-white">{p.core_argument}</p>
                      </div>
                    )}
                    {p.argument_structure && (
                      <div>
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Estrutura</p>
                        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.6)' }}>{p.argument_structure}</p>
                      </div>
                    )}
                    {p.technical_claims.length > 0 && (
                      <div>
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Afirmações técnicas</p>
                        <ul className="space-y-1">
                          {p.technical_claims.map((c, i) => (
                            <li key={i} className="text-[11px] flex gap-2" style={{ color: 'rgba(255,255,255,0.6)' }}>
                              <span style={{ color: '#f59e0b' }}>•</span>{c}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {p.data_points.length > 0 && (
                      <div>
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Dados citados</p>
                        {p.data_points.map((d, i) => (
                          <p key={i} className="text-[11px]" style={{ color: 'rgba(255,255,255,0.55)' }}>
                            <span className="font-semibold text-white">{d.value}</span> — {d.context}
                            {d.source && <span style={{ color: '#f59e0b' }}> · {d.source}</span>}
                          </p>
                        ))}
                      </div>
                    )}
                    {p.content_gaps && (
                      <div>
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Lacunas</p>
                        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.5)' }}>{p.content_gaps}</p>
                      </div>
                    )}
                    {p.replication_template && (
                      <div className="rounded-lg px-3 py-2" style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.15)' }}>
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: '#f59e0b' }}>Template replicável</p>
                        <p className="text-[11px] font-mono" style={{ color: 'rgba(255,255,255,0.7)' }}>{p.replication_template}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
