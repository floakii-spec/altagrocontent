'use client'

import { useEffect, useMemo, useState } from 'react'

interface Profile {
  id: number
  handle: string
  type: string
  post_count: number
  last_sync: string | null
}

interface CompetitorPost {
  id: number
  instagram_id: string
  title: string
  image_url: string
  post_type: string
  published_at: string
  collected_at: string
  status: 'analisado' | 'parcial' | 'nao_analisado'
  has_analysis: boolean
  has_intelligence: boolean
}

interface CompetitorLibrary {
  id: number
  handle: string
  follower_count: number | null
  post_count: number
  analyzed_posts: number
  pending_posts: number
  last_sync: string | null
  posts: CompetitorPost[]
}

const STATUS_META: Record<CompetitorPost['status'], { label: string; color: string; bg: string; border: string }> = {
  analisado: {
    label: 'Analisado',
    color: '#22c55e',
    bg: 'rgba(34,197,94,0.1)',
    border: 'rgba(34,197,94,0.22)',
  },
  parcial: {
    label: 'Análise parcial',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.1)',
    border: 'rgba(245,158,11,0.22)',
  },
  nao_analisado: {
    label: 'Não analisado',
    color: 'rgba(255,255,255,0.62)',
    bg: 'rgba(255,255,255,0.06)',
    border: 'rgba(255,255,255,0.12)',
  },
}

function formatDate(date: string | null) {
  if (!date) return 'Nunca'
  return new Date(date).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function CompetitorThumb({
  src,
  alt,
}: {
  src: string | null | undefined
  alt: string
}) {
  const [failed, setFailed] = useState(false)

  if (!src || failed) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-white/5 px-3 text-center">
        <div>
          <p className="text-[20px]">🖼️</p>
          <p className="mt-2 text-[11px] leading-snug" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Miniatura indisponível
          </p>
        </div>
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={alt}
      className="w-full h-full object-cover"
      loading="lazy"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
    />
  )
}

export function DrawerConcorrentes() {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [library, setLibrary] = useState<CompetitorLibrary[]>([])
  const [expandedIds, setExpandedIds] = useState<number[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [handle, setHandle] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    const [profilesRes, libraryRes] = await Promise.all([
      fetch('/api/competitors'),
      fetch('/api/competitors/library'),
    ])

    if (profilesRes.ok) {
      setProfiles(await profilesRes.json())
    }
    if (libraryRes.ok) {
      const nextLibrary: CompetitorLibrary[] = await libraryRes.json()
      setLibrary(nextLibrary)
      setExpandedIds((current) => {
        const kept = current.filter((id) => nextLibrary.some((profile) => profile.id === id))
        if (kept.length === 0 && nextLibrary.length === 1) {
          return [nextLibrary[0].id]
        }
        return kept
      })
    } else {
      const body = await libraryRes.json().catch(() => ({}))
      setError(body.detail ?? 'Erro ao carregar a biblioteca de concorrentes.')
    }

    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [])

  async function addProfile() {
    if (!handle.trim()) return
    setError(null)
    const res = await fetch('/api/competitors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ handle: handle.trim(), type: 'competitor' }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      setError(body.detail ?? 'Erro ao adicionar concorrente.')
      return
    }
    setHandle('')
    await load()
  }

  async function removeProfile(id: number) {
    setError(null)
    const res = await fetch(`/api/competitors/${id}`, { method: 'DELETE' })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      setError(body.detail ?? 'Erro ao remover concorrente.')
      return
    }
    await load()
  }

  async function sync() {
    setSyncing(true)
    setError(null)
    const res = await fetch('/api/competitors/sync', { method: 'POST' })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      setError(body.detail ?? 'Erro ao coletar os concorrentes.')
    } else {
      await load()
    }
    setSyncing(false)
  }

  function toggleProfile(id: number) {
    setExpandedIds((current) =>
      current.includes(id)
        ? current.filter((profileId) => profileId !== id)
        : [...current, id]
    )
  }

  const ownProfiles = useMemo(
    () => profiles.filter((profile) => profile.type === 'own'),
    [profiles]
  )
  const totalPosts = library.reduce((sum, profile) => sum + profile.post_count, 0)
  const analyzedPosts = library.reduce((sum, profile) => sum + profile.analyzed_posts, 0)
  const pendingPosts = library.reduce((sum, profile) => sum + profile.pending_posts, 0)

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[15px] font-semibold text-white">Biblioteca de concorrentes</p>
          <p className="text-[12px] mt-1 max-w-2xl" style={{ color: 'rgba(255,255,255,0.45)' }}>
            Cada concorrente tem uma pasta própria com os posts coletados, organizados por data, com miniatura, título e estado de análise.
          </p>
        </div>
        <button
          onClick={sync}
          disabled={syncing}
          className="px-4 py-2.5 rounded-lg text-sm font-semibold shrink-0"
          style={{
            background: syncing ? '#3b82f644' : '#3b82f618',
            border: '1px solid #3b82f633',
            color: syncing ? 'rgba(255,255,255,0.35)' : '#3b82f6',
            cursor: syncing ? 'not-allowed' : 'pointer',
          }}
        >
          {syncing ? '⟳ Coletando...' : '⟳ Coletar agora'}
        </button>
      </div>

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
        {[
          { label: 'Concorrentes', value: String(library.length), color: '#3b82f6' },
          { label: 'Posts coletados', value: String(totalPosts), color: '#3b82f6' },
          { label: 'Posts analisados', value: String(analyzedPosts), color: '#22c55e' },
          { label: 'Pendentes', value: String(pendingPosts), color: '#f59e0b' },
        ].map((stat) => (
          <div key={stat.label} className="rounded-xl p-4" style={{ background: `${stat.color}10`, border: `1px solid ${stat.color}22` }}>
            <p className="text-[10px] uppercase tracking-wider" style={{ color: `${stat.color}bb` }}>{stat.label}</p>
            <p className="text-2xl font-bold text-white mt-1">{loading ? '—' : stat.value}</p>
          </div>
        ))}
      </div>

      {ownProfiles.length > 0 && (
        <div className="rounded-xl px-4 py-3" style={{ background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.18)' }}>
          <p className="text-[12px] text-white font-medium">
            Seu perfil agora fica na aba <span style={{ color: '#8b5cf6' }}>Identidade</span>.
          </p>
          <p className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.45)' }}>
            {ownProfiles.length} perfil próprio configurado e separado da biblioteca dos concorrentes.
          </p>
        </div>
      )}

      <div className="rounded-xl p-4 space-y-3" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
        <div>
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Adicionar concorrente
          </p>
          <p className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.35)' }}>
            Cadastre apenas perfis concorrentes aqui.
          </p>
        </div>
        <div className="flex gap-2">
          <input
            value={handle}
            onChange={(event) => setHandle(event.target.value)}
            placeholder="username do concorrente"
            className="flex-1 rounded-lg px-3 py-2 text-sm outline-none"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#fff' }}
          />
          <button
            onClick={addProfile}
            disabled={!handle.trim()}
            className="px-4 rounded-lg text-[12px] font-semibold"
            style={{
              background: !handle.trim() ? '#3b82f644' : '#3b82f6',
              color: '#fff',
              cursor: !handle.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            Adicionar
          </button>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Pastas dos concorrentes
          </p>
          <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
            Mais recentes primeiro
          </p>
        </div>

        {error && (
          <p className="text-[11px] px-3 py-2 rounded-lg" style={{ color: '#f87171', background: '#f8717110', border: '1px solid #f8717122' }}>
            {error}
          </p>
        )}

        {loading ? (
          <p className="text-[12px] text-center py-8" style={{ color: 'rgba(255,255,255,0.25)' }}>Carregando biblioteca...</p>
        ) : library.length === 0 ? (
          <div className="rounded-xl p-6 text-center" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <p className="text-[12px] text-white">Nenhum concorrente monitorado ainda.</p>
            <p className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Adicione um perfil acima para começar a construir a biblioteca.
            </p>
          </div>
        ) : (
          library.map((profile) => {
            const isExpanded = expandedIds.includes(profile.id)
            return (
              <div
                key={profile.id}
                className="rounded-2xl overflow-hidden"
                style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
              >
                <div className="px-4 py-4">
                  <div className="flex items-start gap-3">
                    <button
                      onClick={() => toggleProfile(profile.id)}
                      className="w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0 transition-all"
                      style={{ background: '#3b82f618', border: '1px solid #3b82f633', color: '#3b82f6' }}
                      aria-label={isExpanded ? `Fechar pasta de @${profile.handle}` : `Abrir pasta de @${profile.handle}`}
                    >
                      {isExpanded ? '📂' : '📁'}
                    </button>

                    <button onClick={() => toggleProfile(profile.id)} className="flex-1 min-w-0 text-left">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-[14px] font-semibold text-white truncate">@{profile.handle}</p>
                        <span className="text-[10px] px-2 py-1 rounded-full" style={{ background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.55)' }}>
                          {profile.post_count} posts
                        </span>
                        <span className="text-[10px] px-2 py-1 rounded-full" style={{ background: 'rgba(34,197,94,0.1)', color: '#22c55e' }}>
                          {profile.analyzed_posts} analisados
                        </span>
                        {profile.pending_posts > 0 && (
                          <span className="text-[10px] px-2 py-1 rounded-full" style={{ background: 'rgba(245,158,11,0.1)', color: '#f59e0b' }}>
                            {profile.pending_posts} pendentes
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.38)' }}>
                        Última coleta em {formatDate(profile.last_sync)}
                        {profile.follower_count ? ` · ${profile.follower_count.toLocaleString('pt-BR')} seguidores` : ''}
                      </p>
                    </button>

                    <button
                      onClick={() => removeProfile(profile.id)}
                      className="text-[10px] px-3 py-1.5 rounded-lg shrink-0"
                      style={{ color: 'rgba(255,255,255,0.42)', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
                    >
                      Remover
                    </button>
                  </div>
                </div>

                {isExpanded && (
                  <div className="px-4 pb-4 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                    {profile.posts.length === 0 ? (
                      <p className="text-[12px] text-center py-6" style={{ color: 'rgba(255,255,255,0.3)' }}>
                        Nenhum post coletado ainda para @{profile.handle}.
                      </p>
                    ) : (
                      <div className="grid grid-cols-1 xl:grid-cols-2 gap-3 pt-4">
                        {profile.posts.map((post) => {
                          const status = STATUS_META[post.status]
                          return (
                            <article
                              key={post.id}
                              className="rounded-xl overflow-hidden"
                              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
                            >
                              <div className="grid grid-cols-[112px,1fr] min-h-[112px]">
                                <div className="h-full" style={{ background: 'rgba(255,255,255,0.04)' }}>
                                  <CompetitorThumb
                                    src={post.image_url}
                                    alt={post.title}
                                  />
                                </div>
                                <div className="p-3 flex flex-col gap-2 min-w-0">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <span
                                      className="text-[10px] px-2 py-1 rounded-full"
                                      style={{ background: status.bg, color: status.color, border: `1px solid ${status.border}` }}
                                    >
                                      {status.label}
                                    </span>
                                    <span className="text-[10px] px-2 py-1 rounded-full" style={{ background: 'rgba(59,130,246,0.1)', color: '#60a5fa' }}>
                                      {post.post_type}
                                    </span>
                                  </div>

                                  <p className="text-[13px] font-semibold text-white leading-snug line-clamp-2">
                                    {post.title}
                                  </p>

                                  <div className="mt-auto flex items-center justify-between gap-3">
                                    <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.38)' }}>
                                      Publicado em {formatDate(post.published_at)}
                                    </p>
                                    <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.26)' }}>
                                      #{post.instagram_id.slice(-6)}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </article>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
