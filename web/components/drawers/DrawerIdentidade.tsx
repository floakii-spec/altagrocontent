'use client'

import { useEffect, useState } from 'react'

interface VoiceProfile {
  id: number
  tone: string | null
  dominant_themes: string[]
  vocabulary: { palavras_frequentes?: string[] }
  voice_summary: string | null
  generated_at: string
}

interface OwnProfile {
  id: number
  handle: string
  type: string
  follower_count: number | null
  post_count: number
  last_sync: string | null
}

function formatDate(date: string | null) {
  if (!date) return 'Nunca sincronizado'
  return new Date(date).toLocaleDateString('pt-BR')
}

export function DrawerIdentidade() {
  const [voice, setVoice] = useState<VoiceProfile | null>(null)
  const [ownProfile, setOwnProfile] = useState<OwnProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [savingProfile, setSavingProfile] = useState(false)
  const [syncingProfile, setSyncingProfile] = useState(false)
  const [removingProfile, setRemovingProfile] = useState(false)
  const [handle, setHandle] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    const [voiceRes, profilesRes] = await Promise.all([
      fetch('/api/voice'),
      fetch('/api/competitors'),
    ])

    if (profilesRes.ok) {
      const profiles: OwnProfile[] = await profilesRes.json()
      const own = profiles.find((profile) => profile.type === 'own') ?? null
      setOwnProfile(own)
    } else {
      setOwnProfile(null)
    }

    if (voiceRes.ok) {
      setVoice(await voiceRes.json())
    } else {
      setVoice(null)
    }

    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [])

  async function saveOwnProfile() {
    if (!handle.trim()) return
    setSavingProfile(true)
    setError(null)
    const res = await fetch('/api/competitors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ handle: handle.trim(), type: 'own' }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      setError(body.detail ?? 'Erro ao salvar o perfil próprio.')
    } else {
      setHandle('')
      await load()
    }
    setSavingProfile(false)
  }

  async function syncOwnProfile() {
    if (!ownProfile) return
    setSyncingProfile(true)
    setError(null)
    const res = await fetch(`/api/competitors/sync?handle=${encodeURIComponent(ownProfile.handle)}`, { method: 'POST' })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      setError(body.detail ?? 'Erro ao coletar os posts do perfil próprio.')
    } else {
      await load()
    }
    setSyncingProfile(false)
  }

  async function removeOwnProfile() {
    if (!ownProfile) return
    setRemovingProfile(true)
    setError(null)
    const res = await fetch(`/api/competitors/${ownProfile.id}`, { method: 'DELETE' })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      setError(body.detail ?? 'Erro ao remover o perfil próprio.')
    } else {
      setVoice(null)
      await load()
    }
    setRemovingProfile(false)
  }

  async function analyze() {
    setAnalyzing(true)
    setError(null)
    const res = await fetch('/api/voice/analyze', { method: 'POST' })
    if (res.ok) {
      setVoice(await res.json())
      await load()
    } else {
      const body = await res.json().catch(() => ({}))
      setError(body.detail ?? 'Erro ao gerar perfil de voz.')
    }
    setAnalyzing(false)
  }

  const words = voice?.vocabulary?.palavras_frequentes ?? []

  return (
    <div className="p-6 space-y-5">
      {loading ? (
        <p className="text-[12px] text-center py-6" style={{ color: 'rgba(255,255,255,0.25)' }}>Carregando...</p>
      ) : (
        <>
          <div className="rounded-lg p-4 space-y-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[13px] font-semibold text-white">Perfil próprio</p>
                <p className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
                  Seu perfil fica separado dos concorrentes e é usado para coleta dos seus posts e geração da identidade de voz.
                </p>
              </div>
              <span
                className="text-[9px] font-bold tracking-wider px-2 py-1 rounded-full shrink-0"
                style={
                  ownProfile
                    ? { background: '#8b5cf618', color: '#8b5cf6', border: '1px solid #8b5cf633' }
                    : { background: '#ffffff08', color: 'rgba(255,255,255,0.3)', border: '1px solid rgba(255,255,255,0.08)' }
                }
              >
                {ownProfile ? '● CONFIGURADO' : '○ NÃO CONFIGURADO'}
              </span>
            </div>

            {ownProfile ? (
              <div className="space-y-3">
                <div className="rounded-xl p-4" style={{ background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.18)' }}>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shrink-0"
                      style={{ background: '#8b5cf622', color: '#8b5cf6' }}>
                      {(ownProfile.handle?.[0] ?? '?').toUpperCase()}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-[14px] font-semibold text-white truncate">@{ownProfile.handle}</p>
                      <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.45)' }}>
                        {ownProfile.post_count} posts coletados · última coleta em {formatDate(ownProfile.last_sync)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={syncOwnProfile}
                    disabled={syncingProfile}
                    className="py-2.5 rounded-lg text-sm font-semibold transition-all"
                    style={{
                      background: syncingProfile ? '#8b5cf644' : '#8b5cf618',
                      border: '1px solid #8b5cf633',
                      color: syncingProfile ? 'rgba(255,255,255,0.4)' : '#8b5cf6',
                      cursor: syncingProfile ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {syncingProfile ? '⟳ Coletando posts...' : '⟳ Coletar meus posts'}
                  </button>
                  <button
                    onClick={removeOwnProfile}
                    disabled={removingProfile}
                    className="py-2.5 rounded-lg text-sm font-semibold transition-all"
                    style={{
                      background: 'rgba(248,113,113,0.08)',
                      border: '1px solid rgba(248,113,113,0.18)',
                      color: removingProfile ? 'rgba(255,255,255,0.35)' : '#f87171',
                      cursor: removingProfile ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {removingProfile ? '⟳ Removendo...' : 'Remover perfil'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-[12px]" style={{ color: 'rgba(255,255,255,0.45)' }}>
                  Cadastre aqui o seu perfil para coletar seus posts e gerar a identidade de voz.
                </p>
                <div className="flex gap-2">
                  <input
                    value={handle}
                    onChange={(event) => setHandle(event.target.value)}
                    placeholder="seu username"
                    className="flex-1 rounded-lg px-3 py-2 text-sm outline-none"
                    style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#fff' }}
                  />
                  <button
                    onClick={saveOwnProfile}
                    disabled={!handle.trim() || savingProfile}
                    className="px-4 rounded-lg text-[12px] font-semibold transition-all"
                    style={{
                      background: !handle.trim() || savingProfile ? '#8b5cf644' : '#8b5cf6',
                      color: '#fff',
                      cursor: !handle.trim() || savingProfile ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {savingProfile ? '⟳' : 'Salvar'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {ownProfile ? (
            voice ? (
              <>
                <div className="rounded-lg p-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold"
                      style={{ background: '#8b5cf618', border: '1px solid #8b5cf633', color: '#8b5cf6' }}>
                      {voice.tone?.[0]?.toUpperCase() ?? '?'}
                    </div>
                    <div>
                      <p className="text-[13px] font-semibold text-white">Perfil de voz</p>
                      <p className="text-[10px]" style={{ color: 'rgba(255,255,255,0.35)' }}>
                        Atualizado em {new Date(voice.generated_at).toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                  </div>

                  {[
                    { label: 'Tom', value: voice.tone ?? '—' },
                    { label: 'Temas dominantes', value: voice.dominant_themes.join(', ') || '—' },
                  ].map((row) => (
                    <div key={row.label} className="flex items-start justify-between py-1.5 border-b gap-4" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                      <span className="text-[11px] shrink-0" style={{ color: 'rgba(255,255,255,0.35)' }}>{row.label}</span>
                      <span className="text-[12px] text-right" style={{ color: 'rgba(255,255,255,0.7)' }}>{row.value}</span>
                    </div>
                  ))}

                  {voice.voice_summary && (
                    <p className="text-[11px] mt-3 leading-relaxed" style={{ color: 'rgba(255,255,255,0.45)' }}>
                      {voice.voice_summary}
                    </p>
                  )}
                </div>

                {words.length > 0 && (
                  <div>
                    <p className="text-[11px] font-semibold tracking-wider uppercase mb-2" style={{ color: 'rgba(255,255,255,0.4)' }}>
                      Vocabulário dominante
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {words.slice(0, 12).map((word) => (
                        <span
                          key={word}
                          className="px-2.5 py-1 rounded-full text-[11px]"
                          style={{ background: '#8b5cf610', border: '1px solid #8b5cf622', color: '#8b5cf6' }}
                        >
                          {word}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p className="text-[12px] text-center py-6" style={{ color: 'rgba(255,255,255,0.25)' }}>
                Nenhum perfil de voz gerado ainda. Colete seus posts e gere a identidade abaixo.
              </p>
            )
          ) : (
            <p className="text-[12px] text-center py-1" style={{ color: 'rgba(255,255,255,0.25)' }}>
              Configure seu perfil para habilitar a análise de voz.
            </p>
          )}
        </>
      )}

      {error && (
        <p className="text-[11px] text-center px-2 py-2 rounded-lg" style={{ color: '#f87171', background: '#f8717110', border: '1px solid #f8717122' }}>
          {error}
        </p>
      )}

      <button
        onClick={analyze}
        disabled={analyzing || !ownProfile}
        className="w-full py-2.5 rounded-lg text-sm font-semibold transition-all"
        style={{
          background: analyzing || !ownProfile ? '#8b5cf644' : '#8b5cf6',
          color: analyzing || !ownProfile ? 'rgba(255,255,255,0.4)' : '#fff',
          cursor: analyzing || !ownProfile ? 'not-allowed' : 'pointer',
        }}
      >
        {analyzing ? '⟳ Analisando posts...' : '✦ Gerar perfil de voz'}
      </button>
    </div>
  )
}
