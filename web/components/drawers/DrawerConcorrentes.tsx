'use client'

import { useEffect, useState } from 'react'

interface Profile {
  id: number
  handle: string
  type: string
  post_count: number
  last_sync: string | null
}

export function DrawerConcorrentes() {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [handle, setHandle] = useState('')
  const [type, setType] = useState('competitor')

  async function load() {
    const res = await fetch('/api/competitors')
    if (res.ok) setProfiles(await res.json())
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function addProfile() {
    if (!handle.trim()) return
    await fetch('/api/competitors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ handle: handle.trim(), type }),
    })
    setHandle('')
    load()
  }

  async function removeProfile(id: number) {
    await fetch(`/api/competitors/${id}`, { method: 'DELETE' })
    load()
  }

  async function sync() {
    setSyncing(true)
    await fetch('/api/competitors/sync', { method: 'POST' })
    setSyncing(false)
    load()
  }

  const competitors = profiles.filter((p) => p.type === 'competitor')
  const totalPosts = profiles.reduce((sum, p) => sum + p.post_count, 0)

  return (
    <div className="p-6 space-y-4">
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: 'Perfis monitorados', value: String(competitors.length), color: '#3b82f6' },
          { label: 'Posts coletados', value: String(totalPosts), color: '#3b82f6' },
        ].map((s) => (
          <div key={s.label} className="rounded-lg p-3" style={{ background: s.color + '10', border: `1px solid ${s.color}22` }}>
            <p className="text-[10px]" style={{ color: s.color + 'aa' }}>{s.label}</p>
            <p className="text-xl font-bold text-white mt-0.5">{loading ? '—' : s.value}</p>
          </div>
        ))}
      </div>

      <div>
        <p className="text-[11px] font-semibold tracking-wider uppercase mb-2" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Perfis
        </p>
        <div className="space-y-1.5">
          {loading ? (
            <p className="text-[12px] text-center py-4" style={{ color: 'rgba(255,255,255,0.25)' }}>Carregando...</p>
          ) : profiles.length === 0 ? (
            <p className="text-[12px] text-center py-4" style={{ color: 'rgba(255,255,255,0.25)' }}>Nenhum perfil cadastrado.</p>
          ) : profiles.map((p) => (
            <div
              key={p.id}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0"
                style={{ background: '#3b82f618', color: '#3b82f6' }}>
                {(p.handle?.[0] ?? '?').toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[12px] font-medium text-white truncate">@{p.handle}</p>
                <p className="text-[10px]" style={{ color: 'rgba(255,255,255,0.35)' }}>
                  {p.post_count} posts · {p.type === 'own' ? 'Meu perfil' : 'Concorrente'}
                </p>
              </div>
              <button
                onClick={() => removeProfile(p.id)}
                className="text-[10px] px-2 py-0.5 rounded"
                style={{ color: 'rgba(255,255,255,0.3)', background: 'rgba(255,255,255,0.04)' }}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Adicionar perfil
        </p>
        <div className="flex gap-2">
          <input
            value={handle}
            onChange={(e) => setHandle(e.target.value)}
            placeholder="username"
            className="flex-1 rounded-lg px-3 py-2 text-sm outline-none"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#fff' }}
          />
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="rounded-lg px-2 py-2 text-[11px] outline-none"
            style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)', color: '#fff' }}
          >
            <option value="competitor">Concorrente</option>
            <option value="own">Meu perfil</option>
          </select>
          <button
            onClick={addProfile}
            disabled={!handle.trim()}
            className="px-3 rounded-lg text-[12px] font-semibold"
            style={{ background: '#3b82f6', color: '#fff' }}
          >
            +
          </button>
        </div>
      </div>

      <button
        onClick={sync}
        disabled={syncing}
        className="w-full py-2.5 rounded-lg text-sm font-semibold"
        style={{
          background: syncing ? '#3b82f644' : '#3b82f618',
          border: '1px solid #3b82f633',
          color: syncing ? 'rgba(255,255,255,0.35)' : '#3b82f6',
          cursor: syncing ? 'not-allowed' : 'pointer',
        }}
      >
        {syncing ? '⟳ Coletando e analisando...' : '⟳ Coletar agora'}
      </button>
    </div>
  )
}
