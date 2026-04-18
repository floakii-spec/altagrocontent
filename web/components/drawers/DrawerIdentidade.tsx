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

export function DrawerIdentidade() {
  const [voice, setVoice] = useState<VoiceProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [noProfile, setNoProfile] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    const res = await fetch('/api/voice')
    if (res.status === 404) {
      const body = await res.json().catch(() => ({}))
      if (body.detail === 'No own profile configured') setNoProfile(true)
      // "Voice profile not generated yet" → profile exists, just no voice yet → keep noProfile=false
    } else if (res.ok) {
      setVoice(await res.json())
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function analyze() {
    setAnalyzing(true)
    setError(null)
    const res = await fetch('/api/voice/analyze', { method: 'POST' })
    if (res.ok) {
      setVoice(await res.json())
      setNoProfile(false)
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
      ) : noProfile ? (
        <div className="text-center py-6 space-y-3">
          <p className="text-[12px]" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Nenhum perfil próprio configurado.<br />
            Adicione seu perfil na aba Concorrentes com tipo "Meu perfil".
          </p>
        </div>
      ) : voice ? (
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
          Nenhum perfil de voz gerado. Clique abaixo.
        </p>
      )}

      {error && (
        <p className="text-[11px] text-center px-2 py-2 rounded-lg" style={{ color: '#f87171', background: '#f8717110', border: '1px solid #f8717122' }}>
          {error}
        </p>
      )}

      <button
        onClick={analyze}
        disabled={analyzing || noProfile}
        className="w-full py-2.5 rounded-lg text-sm font-semibold transition-all"
        style={{
          background: analyzing || noProfile ? '#8b5cf644' : '#8b5cf6',
          color: analyzing || noProfile ? 'rgba(255,255,255,0.4)' : '#fff',
          cursor: analyzing || noProfile ? 'not-allowed' : 'pointer',
        }}
      >
        {analyzing ? '⟳ Analisando posts...' : '✦ Gerar perfil de voz'}
      </button>
    </div>
  )
}
