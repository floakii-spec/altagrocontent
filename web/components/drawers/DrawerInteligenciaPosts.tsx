'use client'

import { useEffect, useState } from 'react'

interface DataPoint {
  value: string
  context: string
  source: string | null
}

interface SlideBeat {
  slide_number: number
  role: string
  summary: string
  key_data: string[]
}

interface CarouselComplexity {
  slide_count?: number
  structure_style?: string
  information_density?: string
  proof_strength?: string
  narrative_cohesion?: string
  context_dependency?: string
  complexity_score?: number
  why_it_works?: string
  replication_risk?: string
}

interface PostIntelligence {
  post_id: number
  handle: string
  post_type: string
  likes: number
  virality_score: number | null
  slides_count: number
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
  slide_breakdown: SlideBeat[]
  carousel_complexity: CarouselComplexity
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
  const [handleInput, setHandleInput] = useState('')
  const [activeHandle, setActiveHandle] = useState('')
  const [forceReanalysis, setForceReanalysis] = useState(true)

  async function load(handle = activeHandle) {
    setLoading(true)
    const params = new URLSearchParams()
    if (handle) params.set('handle', handle)
    const res = await fetch(`/api/intelligence/posts?${params}`)
    if (res.ok) setPosts(await res.json())
    setLoading(false)
  }

  useEffect(() => { load(activeHandle) }, [activeHandle]) // eslint-disable-line react-hooks/exhaustive-deps

  async function analyzeNew() {
    setAnalyzing(true)
    const res = await fetch('/api/intelligence/analyze', { method: 'POST' })
    if (res.ok) {
      await load(activeHandle)
    }
    setAnalyzing(false)
  }

  async function analyzeProfile() {
    const handle = handleInput.trim()
    if (!handle) return
    setAnalyzing(true)
    const syncRes = await fetch(`/api/competitors/sync?handle=${encodeURIComponent(handle)}`, { method: 'POST' })
    const params = new URLSearchParams({ handle })
    if (forceReanalysis) params.set('force', 'true')
    const analyzeRes = await fetch(`/api/intelligence/analyze?${params}`, { method: 'POST' })
    if (syncRes.ok && analyzeRes.ok) {
      setActiveHandle(handle)
      await load(handle)
    }
    setAnalyzing(false)
  }

  return (
    <div className="p-6 space-y-4">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            {posts.length} posts analisados{activeHandle ? ` · @${activeHandle}` : ''}
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

        <div className="rounded-lg p-3 space-y-3" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="space-y-1">
            <p className="text-[10px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
              Analisar perfil específico
            </p>
            <input
              value={handleInput}
              onChange={(e) => setHandleInput(e.target.value)}
              placeholder="ex: leandro.varos"
              className="w-full rounded-lg px-3 py-2 text-[12px] outline-none"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'white' }}
            />
          </div>
          <label className="flex items-center gap-2 text-[11px]" style={{ color: 'rgba(255,255,255,0.55)' }}>
            <input
              type="checkbox"
              checked={forceReanalysis}
              onChange={(e) => setForceReanalysis(e.target.checked)}
            />
            Reanalisar mesmo posts já estudados
          </label>
          <div className="flex gap-2">
            <button
              onClick={analyzeProfile}
              disabled={analyzing || !handleInput.trim()}
              className="flex-1 text-[11px] px-3 py-2 rounded-lg transition-all"
              style={{
                background: 'rgba(22,163,74,0.14)',
                border: '1px solid rgba(22,163,74,0.26)',
                color: analyzing || !handleInput.trim() ? 'rgba(255,255,255,0.25)' : '#16a34a',
              }}
            >
              {analyzing ? '⟳ Processando...' : 'Analisar perfil'}
            </button>
            <button
              onClick={() => { setActiveHandle(''); setHandleInput('') }}
              className="text-[11px] px-3 py-2 rounded-lg transition-all"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.5)' }}
            >
              Limpar
            </button>
          </div>
        </div>
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
                      {p.agro_topic_cluster ?? '—'} · {p.post_type} · {p.slides_count || 1} slides · {p.likes.toLocaleString()} likes
                    </p>
                  </div>
                  {typeof p.carousel_complexity?.complexity_score === 'number' && (
                    <span className="text-[10px] px-2 py-1 rounded-full shrink-0" style={{ background: 'rgba(245,158,11,0.1)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.2)' }}>
                      complexidade {p.carousel_complexity.complexity_score}/5
                    </span>
                  )}
                  <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 12 }}>{isOpen ? '▲' : '▼'}</span>
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 space-y-3 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                    {p.carousel_complexity && Object.keys(p.carousel_complexity).length > 0 && (
                      <div className="pt-3 space-y-1">
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: '#16a34a' }}>Complexidade do carrossel</p>
                        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.65)' }}>
                          Estilo: {p.carousel_complexity.structure_style ?? '—'} · Densidade: {p.carousel_complexity.information_density ?? '—'} · Prova: {p.carousel_complexity.proof_strength ?? '—'} · Coesão: {p.carousel_complexity.narrative_cohesion ?? '—'}
                        </p>
                        {p.carousel_complexity.why_it_works && (
                          <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.55)' }}>{p.carousel_complexity.why_it_works}</p>
                        )}
                        {p.carousel_complexity.replication_risk && (
                          <p className="text-[11px]" style={{ color: '#f59e0b' }}>Risco de replicação: {p.carousel_complexity.replication_risk}</p>
                        )}
                      </div>
                    )}
                    {p.core_argument && (
                      <div>
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
                    {p.slide_breakdown.length > 0 && (
                      <div>
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Roteiro slide a slide</p>
                        <div className="space-y-2">
                          {p.slide_breakdown.map((slide, i) => (
                            <div key={i} className="rounded-lg px-3 py-2" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                              <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: '#f59e0b' }}>
                                Slide {slide.slide_number} · {slide.role}
                              </p>
                              <p className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.68)' }}>{slide.summary}</p>
                              {slide.key_data?.length > 0 && (
                                <p className="text-[10px] mt-1" style={{ color: 'rgba(255,255,255,0.45)' }}>
                                  Dados-chave: {slide.key_data.join(' · ')}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
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
