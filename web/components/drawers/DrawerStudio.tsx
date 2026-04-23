'use client'

import { useEffect, useMemo, useState } from 'react'

interface CompetitorPost {
  id: number
  handle: string
  title: string
  caption: string | null
  image_url: string
  post_type: string
  virality_score: number | null
  published_at: string
  status: string
  has_analysis: boolean
  has_intelligence: boolean
  core_argument: string | null
  technical_depth: string | null
  agro_topic_cluster: string | null
}

interface GeneratedPost {
  id: number
  hook: string | null
  caption: string | null
  cta: string | null
  slides: Slide[]
  funnel_stage: string | null
  format: string | null
  created_at: string
}

interface Slide {
  slide_number: number
  slide_type: string
  title: string
  copy: string
  cta: string
}

const DEPTH_META: Record<string, { label: string; color: string; bg: string; border: string }> = {
  especialista: {
    label: 'Especialista',
    color: '#22c55e',
    bg: 'rgba(34,197,94,0.1)',
    border: 'rgba(34,197,94,0.18)',
  },
  intermediario: {
    label: 'Intermediário',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.1)',
    border: 'rgba(245,158,11,0.18)',
  },
  intermediário: {
    label: 'Intermediário',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.1)',
    border: 'rgba(245,158,11,0.18)',
  },
  superficial: {
    label: 'Superficial',
    color: 'rgba(255,255,255,0.65)',
    bg: 'rgba(255,255,255,0.06)',
    border: 'rgba(255,255,255,0.12)',
  },
}

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function formatVirality(score: number | null) {
  if (score == null) return 'Sem score'
  return `${Math.round(score * 100)}% viral`
}

function getDepthMeta(depth: string | null) {
  if (!depth) return null
  return DEPTH_META[depth.toLowerCase()] ?? null
}

function StudioThumb({
  src,
  alt,
  fallbackLabel,
  className,
}: {
  src: string | null | undefined
  alt: string
  fallbackLabel: string
  className: string
}) {
  const [failed, setFailed] = useState(false)

  if (!src || failed) {
    return (
      <div
        className={`flex items-center justify-center bg-white/5 ${className}`}
        style={{ color: 'rgba(255,255,255,0.42)' }}
      >
        <div className="px-3 text-center">
          <p className="text-[20px]">🖼️</p>
          <p className="mt-2 text-[11px] leading-snug">{fallbackLabel}</p>
        </div>
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={alt}
      className={className}
      loading="lazy"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
    />
  )
}

export function DrawerStudio() {
  const [posts, setPosts] = useState<CompetitorPost[]>([])
  const [selected, setSelected] = useState<number | null>(null)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<GeneratedPost | null>(null)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    const res = await fetch('/api/studio/posts')
    if (res.ok) {
      const data: CompetitorPost[] = await res.json()
      setPosts(data)
      setSelected((current) => current ?? data[0]?.id ?? null)
      setError(null)
    } else {
      const body = await res.json().catch(() => ({}))
      setPosts([])
      setError(body.detail ?? 'Erro ao carregar a biblioteca do Studio.')
    }
    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [])

  const filteredPosts = useMemo(() => {
    const term = query.trim().toLowerCase()
    if (!term) return posts
    return posts.filter((post) =>
      [
        post.handle,
        post.title,
        post.caption ?? '',
        post.core_argument ?? '',
        post.agro_topic_cluster ?? '',
        post.technical_depth ?? '',
      ]
        .join(' ')
        .toLowerCase()
        .includes(term)
    )
  }, [posts, query])

  const selectedPost =
    filteredPosts.find((post) => post.id === selected) ??
    posts.find((post) => post.id === selected) ??
    null

  useEffect(() => {
    if (!selected && filteredPosts.length > 0) {
      setSelected(filteredPosts[0].id)
      return
    }
    if (selected && filteredPosts.length > 0 && !filteredPosts.some((post) => post.id === selected)) {
      setSelected(filteredPosts[0].id)
    }
  }, [filteredPosts, selected])

  async function generate() {
    if (!selectedPost) return
    setGenerating(true)
    setResult(null)
    setError(null)
    const res = await fetch('/api/studio/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ post_id: selectedPost.id }),
    })
    if (res.ok) {
      setResult(await res.json())
    } else {
      const body = await res.json().catch(() => ({}))
      setError(body.detail ?? 'Erro ao gerar post.')
    }
    setGenerating(false)
  }

  function copyToClipboard() {
    if (!result) return
    const slidesText = result.slides.map((slide) => (
      [`[${slide.slide_type}] ${slide.title}`, slide.copy, slide.cta ? `CTA: ${slide.cta}` : null]
        .filter(Boolean)
        .join('\n')
    )).join('\n\n')
    const text = [slidesText, result.caption ? `Legenda:\n${result.caption}` : null].filter(Boolean).join('\n\n')
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const readyCount = posts.filter((post) => post.has_intelligence).length

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <p className="text-[15px] font-semibold text-white">Studio de adaptação</p>
          <p className="max-w-3xl text-[12px] leading-relaxed" style={{ color: 'rgba(255,255,255,0.45)' }}>
            Selecione um post já analisado do concorrente, revise o argumento central e gere um carrossel na sua voz.
            Agora a biblioteca mostra miniatura, título, score e contexto antes da adaptação.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Prontos', value: String(readyCount), color: '#22c55e' },
            { label: 'Na vitrine', value: String(posts.length), color: '#3b82f6' },
            { label: 'Filtrados', value: String(filteredPosts.length), color: '#f59e0b' },
          ].map((stat) => (
            <div
              key={stat.label}
              className="min-w-[92px] rounded-2xl border p-3"
              style={{ background: `${stat.color}10`, borderColor: `${stat.color}22` }}
            >
              <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: `${stat.color}cc` }}>
                {stat.label}
              </p>
              <p className="mt-1 text-[22px] font-semibold text-white">{loading ? '—' : stat.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
        <section className="space-y-4">
          <div className="rounded-[24px] border p-4" style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.06)' }}>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em]" style={{ color: '#16a34a' }}>
                  Biblioteca de origem
                </p>
                <p className="mt-1 text-[12px]" style={{ color: 'rgba(255,255,255,0.38)' }}>
                  Posts de concorrentes com inteligência pronta para adaptação.
                </p>
              </div>

              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Buscar por handle, tema, argumento..."
                className="w-full rounded-2xl px-4 py-3 text-sm outline-none lg:max-w-[320px]"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#fff' }}
              />
            </div>
          </div>

          {loading ? (
            <div className="rounded-[24px] border p-8 text-center" style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.06)' }}>
              <p className="text-[12px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
                Carregando posts analisados...
              </p>
            </div>
          ) : filteredPosts.length === 0 ? (
            <div className="rounded-[24px] border p-8 text-center" style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.06)' }}>
              <p className="text-[13px] text-white">Nenhum post pronto para adaptação.</p>
              <p className="mt-1 text-[12px]" style={{ color: 'rgba(255,255,255,0.34)' }}>
                Reanalise os concorrentes no Deep Dive ou ajuste o filtro da busca.
              </p>
            </div>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {filteredPosts.map((post) => {
                const isSelected = selected === post.id
                const depth = getDepthMeta(post.technical_depth)

                return (
                  <button
                    key={post.id}
                    onClick={() => {
                      setSelected(post.id)
                      setResult(null)
                    }}
                    className="group overflow-hidden rounded-[24px] border text-left transition-all duration-200 hover:-translate-y-0.5"
                    style={{
                      background: isSelected ? 'rgba(22,163,74,0.1)' : 'rgba(255,255,255,0.03)',
                      borderColor: isSelected ? 'rgba(22,163,74,0.3)' : 'rgba(255,255,255,0.06)',
                      boxShadow: isSelected ? '0 20px 60px rgba(22,163,74,0.12)' : 'none',
                    }}
                  >
                    <div className="aspect-[1.2/1] w-full overflow-hidden bg-white/5">
                      <StudioThumb
                        src={post.image_url}
                        alt={post.title}
                        fallbackLabel="Miniatura indisponível"
                        className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
                      />
                    </div>

                    <div className="space-y-3 p-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full px-2.5 py-1 text-[10px] font-semibold" style={{ background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.62)' }}>
                          @{post.handle}
                        </span>
                        <span className="rounded-full px-2.5 py-1 text-[10px] font-semibold" style={{ background: 'rgba(59,130,246,0.1)', color: '#60a5fa' }}>
                          {post.post_type}
                        </span>
                        <span className="rounded-full px-2.5 py-1 text-[10px] font-semibold" style={{ background: 'rgba(34,197,94,0.1)', color: '#4ade80' }}>
                          {formatVirality(post.virality_score)}
                        </span>
                        {depth && (
                          <span
                            className="rounded-full px-2.5 py-1 text-[10px] font-semibold"
                            style={{ background: depth.bg, border: `1px solid ${depth.border}`, color: depth.color }}
                          >
                            {depth.label}
                          </span>
                        )}
                      </div>

                      <div className="space-y-2">
                        <p className="line-clamp-2 text-[15px] font-semibold text-white leading-snug">
                          {post.title}
                        </p>
                        {post.caption && (
                          <p className="line-clamp-3 text-[12px] leading-relaxed" style={{ color: 'rgba(255,255,255,0.42)' }}>
                            {post.caption}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center justify-between gap-3">
                        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.34)' }}>
                          {post.agro_topic_cluster ? `${post.agro_topic_cluster} · ` : ''}
                          {formatDate(post.published_at)}
                        </p>
                        <span className="text-[12px] transition-transform group-hover:translate-x-0.5" style={{ color: isSelected ? '#4ade80' : 'rgba(255,255,255,0.34)' }}>
                          Ver contexto →
                        </span>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </section>

        <section className="space-y-4">
          <div className="rounded-[24px] border p-4" style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.06)' }}>
            {selectedPost ? (
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="h-24 w-24 shrink-0 overflow-hidden rounded-2xl border" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
                    <StudioThumb
                      src={selectedPost.image_url}
                      alt={selectedPost.title}
                      fallbackLabel="Sem imagem"
                      className="h-full w-full object-cover"
                    />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em]" style={{ color: '#16a34a' }}>
                      Post selecionado
                    </p>
                    <p className="mt-1 text-[15px] font-semibold text-white leading-snug">
                      {selectedPost.title}
                    </p>
                    <p className="mt-2 text-[12px]" style={{ color: 'rgba(255,255,255,0.42)' }}>
                      @{selectedPost.handle} · {formatDate(selectedPost.published_at)} · {formatVirality(selectedPost.virality_score)}
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {selectedPost.agro_topic_cluster && (
                    <span className="rounded-full px-2.5 py-1 text-[10px] font-semibold" style={{ background: 'rgba(59,130,246,0.1)', color: '#60a5fa' }}>
                      {selectedPost.agro_topic_cluster}
                    </span>
                  )}
                  {selectedPost.technical_depth && (
                    <span className="rounded-full px-2.5 py-1 text-[10px] font-semibold" style={{ background: 'rgba(245,158,11,0.1)', color: '#f59e0b' }}>
                      {selectedPost.technical_depth}
                    </span>
                  )}
                  <span className="rounded-full px-2.5 py-1 text-[10px] font-semibold" style={{ background: 'rgba(34,197,94,0.1)', color: '#4ade80' }}>
                    Inteligência pronta
                  </span>
                </div>

                {selectedPost.core_argument && (
                  <div className="rounded-2xl border p-4" style={{ background: 'rgba(22,163,74,0.08)', borderColor: 'rgba(22,163,74,0.18)' }}>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em]" style={{ color: '#4ade80' }}>
                      Argumento central
                    </p>
                    <p className="mt-2 text-[13px] leading-relaxed text-white">
                      {selectedPost.core_argument}
                    </p>
                  </div>
                )}

                {selectedPost.caption && (
                  <div className="rounded-2xl border p-4" style={{ background: 'rgba(255,255,255,0.025)', borderColor: 'rgba(255,255,255,0.06)' }}>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em]" style={{ color: 'rgba(255,255,255,0.38)' }}>
                      Legenda original
                    </p>
                    <p className="mt-2 text-[12px] leading-relaxed whitespace-pre-line" style={{ color: 'rgba(255,255,255,0.58)' }}>
                      {selectedPost.caption}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-[14px] font-semibold text-white">Selecione um post para continuar.</p>
                <p className="text-[12px]" style={{ color: 'rgba(255,255,255,0.38)' }}>
                  O painel lateral mostra o contexto do post escolhido e recebe o carrossel adaptado.
                </p>
              </div>
            )}
          </div>

          <button
            onClick={generate}
            disabled={generating || !selectedPost}
            className="w-full rounded-2xl py-3 text-sm font-semibold transition-all"
            style={{
              background: generating || !selectedPost ? '#16a34a44' : '#16a34a',
              color: generating || !selectedPost ? 'rgba(255,255,255,0.4)' : '#fff',
              cursor: generating || !selectedPost ? 'not-allowed' : 'pointer',
            }}
          >
            {generating ? '⟳ Adaptando carrossel com sua voz...' : '🎬 Adaptar para carrossel'}
          </button>

          {error && (
            <p className="rounded-2xl px-3 py-3 text-[12px]" style={{ color: '#f87171', background: '#f8717110', border: '1px solid #f8717122' }}>
              {error}
            </p>
          )}

          {result && (
            <div className="space-y-4 rounded-[24px] border p-4" style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.06)' }}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em]" style={{ color: '#16a34a' }}>
                    Carrossel adaptado
                  </p>
                  <p className="mt-1 text-[12px]" style={{ color: 'rgba(255,255,255,0.4)' }}>
                    {result.slides.length} slides · {result.funnel_stage ?? 'funil não informado'}
                  </p>
                </div>
                <button
                  onClick={copyToClipboard}
                  className="rounded-full px-3 py-1.5 text-[11px] font-semibold"
                  style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: copied ? '#4ade80' : 'rgba(255,255,255,0.58)' }}
                >
                  {copied ? '✓ Copiado' : '📋 Copiar'}
                </button>
              </div>

              <div className="space-y-3">
                {result.slides.map((slide) => (
                  <div
                    key={`${slide.slide_number}-${slide.slide_type}`}
                    className="rounded-2xl border p-4"
                    style={{ background: 'rgba(255,255,255,0.025)', borderColor: 'rgba(255,255,255,0.06)' }}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="rounded-full px-2.5 py-1 text-[10px] font-semibold"
                        style={{ background: '#16a34a22', color: '#4ade80' }}
                      >
                        {slide.slide_type}
                      </span>
                      <span className="text-[13px] font-semibold text-white">
                        {slide.slide_number}. {slide.title}
                      </span>
                    </div>
                    {slide.copy && (
                      <p className="mt-2 text-[12px] leading-relaxed" style={{ color: 'rgba(255,255,255,0.64)' }}>
                        {slide.copy}
                      </p>
                    )}
                    {slide.cta && (
                      <p className="mt-2 text-[12px] font-medium" style={{ color: '#4ade80' }}>
                        → {slide.cta}
                      </p>
                    )}
                  </div>
                ))}
              </div>

              {result.caption && (
                <div className="rounded-2xl border p-4" style={{ background: 'rgba(255,255,255,0.025)', borderColor: 'rgba(255,255,255,0.06)' }}>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em]" style={{ color: 'rgba(255,255,255,0.4)' }}>
                    Legenda final
                  </p>
                  <p className="mt-2 whitespace-pre-line text-[12px] leading-relaxed" style={{ color: 'rgba(255,255,255,0.68)' }}>
                    {result.caption}
                  </p>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
