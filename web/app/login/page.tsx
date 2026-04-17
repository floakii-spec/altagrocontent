'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    })
    if (res.ok) {
      router.push('/')
    } else {
      setError('Senha incorreta')
      setLoading(false)
    }
  }

  return (
    <div
      className="flex h-screen w-screen items-center justify-center"
      style={{ background: '#000' }}
    >
      <div
        className="w-80 rounded-xl p-8 space-y-6"
        style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}
      >
        <div className="text-center space-y-1">
          <p className="text-2xl">🌾</p>
          <h1 className="text-lg font-semibold text-white">Agro Intel</h1>
          <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.35)' }}>
            Acesso restrito
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Senha"
            className="w-full rounded-lg px-3 py-2.5 text-sm outline-none"
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#fff',
            }}
          />
          {error && (
            <p className="text-[11px] text-center" style={{ color: '#ef4444' }}>
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading || !password}
            className="w-full py-2.5 rounded-lg text-sm font-semibold transition-all"
            style={{
              background: loading || !password ? '#16a34a44' : '#16a34a',
              color: loading || !password ? 'rgba(255,255,255,0.4)' : '#fff',
              cursor: loading || !password ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
