# Next.js Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the Next.js orbital UI to the real FastAPI backend — replacing all mock data with live API calls — and add password-based auth so only the team can access the app.

**Architecture:** A catch-all Next.js Route Handler at `app/api/[...proxy]/route.ts` proxies all `/api/*` calls to `BACKEND_URL` (the Railway internal URL of the `altagrocontent` FastAPI service). Auth is enforced by `middleware.ts` using an httpOnly cookie. `/api/auth/*` routes are handled locally and never forwarded to FastAPI.

**Tech Stack:** Next.js 16 App Router, TypeScript, `crypto` (Node built-in for cookie signing), existing Tailwind/inline-style components.

**Prerequisite:** Plan 1 (FastAPI backend) must be deployed and healthy at `BACKEND_URL` before starting this plan.

---

## File Structure

```
web/
  middleware.ts                          NEW — auth guard for all routes
  app/
    login/
      page.tsx                           NEW — login form
    api/
      auth/
        login/
          route.ts                       NEW — POST: validate password, set cookie
        logout/
          route.ts                       NEW — POST: clear cookie
      [...proxy]/
        route.ts                         NEW — catch-all proxy to BACKEND_URL
  components/
    drawers/
      DrawerConcorrentes.tsx             MODIFY — real data
      DrawerCarrossel.tsx                MODIFY — real data
      DrawerNoticias.tsx                 MODIFY — real data
      DrawerRelatorios.tsx               MODIFY — real data
      DrawerIdentidade.tsx               MODIFY — real data
      DrawerStudio.tsx                   MODIFY — real picker + real generation
```

---

### Task 1: Auth — middleware, login page, and API routes

**Files:**
- Create: `web/middleware.ts`
- Create: `web/app/login/page.tsx`
- Create: `web/app/api/auth/login/route.ts`
- Create: `web/app/api/auth/logout/route.ts`

- [ ] **Step 1: Create the middleware**

Create `web/middleware.ts`:

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { createHash } from 'crypto'

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl

  // Auth routes and static assets are always public
  if (
    pathname.startsWith('/api/auth') ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/favicon')
  ) {
    return NextResponse.next()
  }

  const token = req.cookies.get('auth_token')?.value
  const expected = createHash('sha256')
    .update(process.env.APP_PASSWORD! + process.env.AUTH_SECRET!)
    .digest('hex')

  if (token !== expected) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
```

- [ ] **Step 2: Create the login page**

Create `web/app/login/page.tsx`:

```tsx
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
```

- [ ] **Step 3: Create the login API route**

Create `web/app/api/auth/login/route.ts`:

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { createHash } from 'crypto'

export async function POST(req: NextRequest) {
  const { password } = await req.json()

  if (password !== process.env.APP_PASSWORD) {
    return NextResponse.json({ error: 'Invalid password' }, { status: 401 })
  }

  const token = createHash('sha256')
    .update(process.env.APP_PASSWORD! + process.env.AUTH_SECRET!)
    .digest('hex')

  const res = NextResponse.json({ ok: true })
  res.cookies.set('auth_token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 30, // 30 days
  })
  return res
}
```

- [ ] **Step 4: Create the logout API route**

Create `web/app/api/auth/logout/route.ts`:

```typescript
import { NextResponse } from 'next/server'

export async function POST() {
  const res = NextResponse.json({ ok: true })
  res.cookies.set('auth_token', '', { maxAge: 0, path: '/' })
  return res
}
```

- [ ] **Step 5: Manually test auth**

Set env vars locally:

```bash
cd web
APP_PASSWORD=testpass AUTH_SECRET=somesecret npm run dev
```

- Open `http://localhost:3000` — should redirect to `/login`
- Enter wrong password — should show "Senha incorreta"
- Enter `testpass` — should redirect to `/`
- Refresh — should stay on `/`

- [ ] **Step 6: Commit**

```bash
git add web/middleware.ts web/app/login/ web/app/api/auth/
git commit -m "feat: password auth with httpOnly cookie"
```

---

### Task 2: Proxy catch-all route

**Files:**
- Create: `web/app/api/[...proxy]/route.ts`

- [ ] **Step 1: Create the proxy route**

Create `web/app/api/[...proxy]/route.ts`:

```typescript
import { NextRequest, NextResponse } from 'next/server'

const BACKEND = process.env.BACKEND_URL!

async function proxy(req: NextRequest, { params }: { params: Promise<{ proxy: string[] }> }) {
  const { proxy } = await params
  const path = proxy.join('/')
  const url = new URL(req.url)
  const target = `${BACKEND}/${path}${url.search}`

  const headers = new Headers()
  req.headers.forEach((value, key) => {
    if (!['host', 'connection'].includes(key.toLowerCase())) {
      headers.set(key, value)
    }
  })

  const body = req.method !== 'GET' && req.method !== 'HEAD'
    ? await req.arrayBuffer()
    : undefined

  const res = await fetch(target, {
    method: req.method,
    headers,
    body,
  })

  const responseHeaders = new Headers()
  res.headers.forEach((value, key) => {
    responseHeaders.set(key, value)
  })

  return new NextResponse(res.body, {
    status: res.status,
    headers: responseHeaders,
  })
}

export { proxy as GET, proxy as POST, proxy as PUT, proxy as DELETE, proxy as PATCH }
```

- [ ] **Step 2: Test proxy locally**

With both `npm run dev` (Next.js) and `uvicorn api.main:app` (FastAPI) running locally:

```bash
BACKEND_URL=http://localhost:8080 npm run dev
```

Then in a second terminal:

```bash
curl http://localhost:3000/api/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 3: Commit**

```bash
git add web/app/api/
git commit -m "feat: catch-all proxy to FastAPI backend"
```

---

### Task 3: Wire DrawerConcorrentes

**Files:**
- Modify: `web/components/drawers/DrawerConcorrentes.tsx`

The drawer lists active profiles with post count, lets the user add/remove profiles, and triggers a sync.

- [ ] **Step 1: Replace the component**

Overwrite `web/components/drawers/DrawerConcorrentes.tsx` with:

```tsx
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
                {p.handle[0].toUpperCase()}
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
```

- [ ] **Step 2: Start dev server and verify**

```bash
cd web && BACKEND_URL=http://localhost:8080 APP_PASSWORD=test AUTH_SECRET=secret npm run dev
```

Open `http://localhost:3000`, login, navigate to Concorrentes drawer. Verify:
- Profiles load (or empty state shows)
- Add a profile → appears in list
- Remove a profile → disappears
- "Coletar agora" shows spinner while running

- [ ] **Step 3: Commit**

```bash
git add web/components/drawers/DrawerConcorrentes.tsx
git commit -m "feat: DrawerConcorrentes wired to real API"
```

---

### Task 4: Wire DrawerCarrossel

**Files:**
- Modify: `web/components/drawers/DrawerCarrossel.tsx`

- [ ] **Step 1: Replace the component**

Overwrite `web/components/drawers/DrawerCarrossel.tsx` with:

```tsx
'use client'

import { useEffect, useState } from 'react'

interface Slide {
  slide_number: number
  title: string
  copy: string
  cta: string
}

interface Carousel {
  id: number
  theme: string
  slides: Slide[]
  generated_at: string
}

export function DrawerCarrossel() {
  const [topic, setTopic] = useState('')
  const [generating, setGenerating] = useState(false)
  const [current, setCurrent] = useState<Carousel | null>(null)
  const [history, setHistory] = useState<Carousel[]>([])
  const [loadingHistory, setLoadingHistory] = useState(true)

  async function loadHistory() {
    const res = await fetch('/api/carousel')
    if (res.ok) setHistory(await res.json())
    setLoadingHistory(false)
  }

  useEffect(() => { loadHistory() }, [])

  async function generate() {
    if (!topic.trim()) return
    setGenerating(true)
    const res = await fetch('/api/carousel/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theme: topic.trim() }),
    })
    if (res.ok) {
      const data = await res.json()
      setCurrent(data)
      loadHistory()
    }
    setGenerating(false)
  }

  const displayCarousel = current

  return (
    <div className="p-6 space-y-5">
      <div className="space-y-2">
        <label className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Tema do carrossel
        </label>
        <textarea
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Ex: Alta da soja, irrigação inteligente, gestão de safra..."
          rows={3}
          className="w-full rounded-lg px-3 py-2.5 text-sm resize-none outline-none"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#fff' }}
        />
      </div>

      <button
        onClick={generate}
        disabled={generating || !topic.trim()}
        className="w-full py-2.5 rounded-lg text-sm font-semibold transition-all"
        style={{
          background: generating || !topic.trim() ? '#16a34a44' : '#16a34a',
          color: generating || !topic.trim() ? 'rgba(255,255,255,0.4)' : '#fff',
          cursor: generating || !topic.trim() ? 'not-allowed' : 'pointer',
        }}
      >
        {generating ? '⟳ Gerando com GPT-4o...' : '✦ Gerar Carrossel'}
      </button>

      {displayCarousel && (
        <div className="space-y-2">
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            {displayCarousel.slides.length} slides gerados
          </p>
          {displayCarousel.slides.map((slide) => (
            <div
              key={slide.slide_number}
              className="px-3 py-2.5 rounded-lg space-y-1"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
                  style={{ background: '#16a34a22', color: '#16a34a' }}>
                  {slide.slide_number}
                </span>
                <span className="text-[12px] font-semibold text-white">{slide.title}</span>
              </div>
              <p className="text-[11px] pl-7" style={{ color: 'rgba(255,255,255,0.55)' }}>{slide.copy}</p>
              {slide.cta && (
                <p className="text-[11px] pl-7" style={{ color: '#16a34a' }}>→ {slide.cta}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {!loadingHistory && history.length > 0 && (
        <div className="space-y-2 pt-2 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.3)' }}>
            Histórico
          </p>
          {history.map((c) => (
            <button
              key={c.id}
              onClick={() => setCurrent(c)}
              className="w-full text-left px-3 py-2 rounded-lg text-[11px] truncate"
              style={{
                background: current?.id === c.id ? 'rgba(22,163,74,0.1)' : 'rgba(255,255,255,0.02)',
                border: `1px solid ${current?.id === c.id ? '#16a34a33' : 'rgba(255,255,255,0.05)'}`,
                color: 'rgba(255,255,255,0.5)',
              }}
            >
              {c.theme}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Test in browser**

With dev server running, open Carrossel drawer:
- Type a theme, click "Gerar Carrossel" — spinner shows, slides appear with real GPT-4o content
- History section shows past carousels
- Click a past carousel — slides update

- [ ] **Step 3: Commit**

```bash
git add web/components/drawers/DrawerCarrossel.tsx
git commit -m "feat: DrawerCarrossel wired to real API"
```

---

### Task 5: Wire DrawerNoticias

**Files:**
- Modify: `web/components/drawers/DrawerNoticias.tsx`

- [ ] **Step 1: Replace the component**

Overwrite `web/components/drawers/DrawerNoticias.tsx` with:

```tsx
'use client'

import { useEffect, useState } from 'react'

interface NewsItem {
  id: number
  source: string
  title: string
  url: string
  published_at: string
  tags: string[]
}

const TAG_COLORS: Record<string, string> = {
  soja: '#16a34a',
  milho: '#d97706',
  mercado: '#3b82f6',
  insumos: '#8b5cf6',
  tecnologia: '#06b6d4',
  café: '#92400e',
  cana: '#16a34a',
  algodão: '#6b7280',
  clima: '#0ea5e9',
  exportação: '#f59e0b',
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const hours = Math.floor(diff / 3600000)
  if (hours < 1) return 'agora'
  if (hours < 24) return `${hours}h`
  return `${Math.floor(hours / 24)}d`
}

export function DrawerNoticias() {
  const [items, setItems] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  async function load() {
    const res = await fetch('/api/news')
    if (res.ok) setItems(await res.json())
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function refresh() {
    setRefreshing(true)
    await fetch('/api/news/refresh', { method: 'POST' })
    await load()
    setRefreshing(false)
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
          4 fontes · {items.length} notícias
        </p>
        <button
          onClick={refresh}
          disabled={refreshing}
          className="text-[10px] px-2.5 py-1 rounded-full"
          style={{
            background: '#16a34a18',
            color: refreshing ? 'rgba(22,163,74,0.4)' : '#16a34a',
            border: '1px solid #16a34a33',
          }}
        >
          {refreshing ? '⟳' : '● Atualizar'}
        </button>
      </div>

      <div className="space-y-2">
        {loading ? (
          <p className="text-[12px] text-center py-6" style={{ color: 'rgba(255,255,255,0.25)' }}>Carregando...</p>
        ) : items.length === 0 ? (
          <p className="text-[12px] text-center py-6" style={{ color: 'rgba(255,255,255,0.25)' }}>
            Nenhuma notícia. Clique em Atualizar.
          </p>
        ) : items.map((item) => (
          <a
            key={item.id}
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block px-3 py-3 rounded-lg transition-all"
            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-semibold" style={{ color: 'rgba(255,255,255,0.35)' }}>
                {item.source.replace('_', ' ')}
              </span>
              <div className="flex items-center gap-2">
                {item.tags.slice(0, 1).map((tag) => (
                  <span
                    key={tag}
                    className="text-[9px] font-bold px-1.5 py-0.5 rounded-full"
                    style={{
                      background: (TAG_COLORS[tag] ?? '#fff') + '18',
                      color: TAG_COLORS[tag] ?? 'rgba(255,255,255,0.5)',
                      border: `1px solid ${(TAG_COLORS[tag] ?? '#fff')}33`,
                    }}
                  >
                    {tag}
                  </span>
                ))}
                <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.25)' }}>
                  {timeAgo(item.published_at)}
                </span>
              </div>
            </div>
            <p className="text-[12px] leading-snug" style={{ color: 'rgba(255,255,255,0.75)' }}>
              {item.title}
            </p>
          </a>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Test in browser**

Open Notícias drawer — items load from DB (or empty state with Atualizar button). Click Atualizar — RSS feeds are polled, new items appear.

- [ ] **Step 3: Commit**

```bash
git add web/components/drawers/DrawerNoticias.tsx
git commit -m "feat: DrawerNoticias wired to real API"
```

---

### Task 6: Wire DrawerRelatorios

**Files:**
- Modify: `web/components/drawers/DrawerRelatorios.tsx`

- [ ] **Step 1: Replace the component**

Overwrite `web/components/drawers/DrawerRelatorios.tsx` with:

```tsx
'use client'

import { useEffect, useState } from 'react'

interface Report {
  id: number
  period_start: string
  period_end: string
  top_formats: Record<string, number> | null
  top_themes: Record<string, number> | null
  top_hashtags: string[] | null
  report_text: string | null
  generated_at: string
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function DrawerRelatorios() {
  const [reports, setReports] = useState<Report[]>([])
  const [selected, setSelected] = useState<Report | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  async function load() {
    const res = await fetch('/api/reports')
    if (res.ok) {
      const data: Report[] = await res.json()
      setReports(data)
      if (data.length > 0 && !selected) setSelected(data[0])
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function generate() {
    setGenerating(true)
    const res = await fetch('/api/reports/generate', { method: 'POST' })
    if (res.ok) {
      const report: Report = await res.json()
      setReports((prev) => [report, ...prev])
      setSelected(report)
    }
    setGenerating(false)
  }

  const topThemes = selected?.top_themes
    ? Object.entries(selected.top_themes).sort((a, b) => b[1] - a[1]).slice(0, 4)
    : []

  return (
    <div className="p-6 space-y-5">
      {reports.length > 0 && (
        <select
          value={selected?.id ?? ''}
          onChange={(e) => setSelected(reports.find((r) => r.id === Number(e.target.value)) ?? null)}
          className="w-full rounded-lg px-3 py-2 text-[12px] outline-none"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#fff' }}
        >
          {reports.map((r) => (
            <option key={r.id} value={r.id}>
              {formatDate(r.period_start)} – {formatDate(r.period_end)}
            </option>
          ))}
        </select>
      )}

      {loading ? (
        <p className="text-[12px] text-center py-6" style={{ color: 'rgba(255,255,255,0.25)' }}>Carregando...</p>
      ) : selected ? (
        <>
          <div className="rounded-lg p-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <p className="text-[11px] font-semibold tracking-wider uppercase mb-3" style={{ color: 'rgba(255,255,255,0.4)' }}>
              Formatos
            </p>
            {Object.entries(selected.top_formats ?? {}).map(([fmt, count]) => (
              <div key={fmt} className="flex justify-between py-1.5 border-b" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                <span className="text-[12px]" style={{ color: 'rgba(255,255,255,0.45)' }}>{fmt}</span>
                <span className="text-[13px] font-semibold text-white">{count}</span>
              </div>
            ))}
          </div>

          {topThemes.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold tracking-wider uppercase mb-2" style={{ color: 'rgba(255,255,255,0.4)' }}>
                Tópicos em alta
              </p>
              {topThemes.map(([theme, count], i) => (
                <div key={theme} className="flex items-center gap-3 py-2 border-b" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                  <span className="text-[11px] font-bold w-4 text-center" style={{ color: 'rgba(255,255,255,0.25)' }}>{i + 1}</span>
                  <span className="text-[12px] flex-1" style={{ color: 'rgba(255,255,255,0.65)' }}>{theme}</span>
                  <div className="h-1 rounded-full" style={{ width: `${Math.min(count * 8, 80)}px`, background: '#8b5cf6' }} />
                </div>
              ))}
            </div>
          )}

          {selected.report_text && (
            <div className="rounded-lg p-4 text-[11px] leading-relaxed" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.55)', whiteSpace: 'pre-wrap' }}>
              {selected.report_text}
            </div>
          )}
        </>
      ) : (
        <p className="text-[12px] text-center py-6" style={{ color: 'rgba(255,255,255,0.25)' }}>
          Nenhum relatório. Gere o primeiro abaixo.
        </p>
      )}

      <button
        onClick={generate}
        disabled={generating}
        className="w-full py-2.5 rounded-lg text-sm font-semibold transition-all"
        style={{
          background: generating ? '#8b5cf644' : '#8b5cf6',
          color: generating ? 'rgba(255,255,255,0.4)' : '#fff',
          cursor: generating ? 'not-allowed' : 'pointer',
        }}
      >
        {generating ? '⟳ Gerando com GPT-4o...' : '✦ Gerar novo relatório'}
      </button>
    </div>
  )
}
```

- [ ] **Step 2: Test in browser**

Open Relatórios drawer — existing reports load (or empty state). Click "Gerar novo relatório" — spinner → real GPT-4o report appears.

- [ ] **Step 3: Commit**

```bash
git add web/components/drawers/DrawerRelatorios.tsx
git commit -m "feat: DrawerRelatorios wired to real API"
```

---

### Task 7: Wire DrawerIdentidade

**Files:**
- Modify: `web/components/drawers/DrawerIdentidade.tsx`

- [ ] **Step 1: Replace the component**

Overwrite `web/components/drawers/DrawerIdentidade.tsx` with:

```tsx
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

  async function load() {
    const res = await fetch('/api/voice')
    if (res.status === 404) {
      setNoProfile(true)
    } else if (res.ok) {
      setVoice(await res.json())
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function analyze() {
    setAnalyzing(true)
    const res = await fetch('/api/voice/analyze', { method: 'POST' })
    if (res.ok) {
      setVoice(await res.json())
      setNoProfile(false)
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
```

- [ ] **Step 2: Test in browser**

Open Identidade drawer — shows real voice profile from DB, or "no profile" state. "Gerar perfil de voz" triggers real GPT-4o analysis.

- [ ] **Step 3: Commit**

```bash
git add web/components/drawers/DrawerIdentidade.tsx
git commit -m "feat: DrawerIdentidade wired to real API"
```

---

### Task 8: Wire DrawerStudio

**Files:**
- Modify: `web/components/drawers/DrawerStudio.tsx`

The Studio drawer changes UX: instead of a URL input, it shows collected competitor posts sorted by virality score. User picks one, clicks generate.

- [ ] **Step 1: Replace the component**

Overwrite `web/components/drawers/DrawerStudio.tsx` with:

```tsx
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

  const selectedPost = posts.find((p) => p.id === selected)

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
```

- [ ] **Step 2: Test in browser**

Open Studio drawer — list of competitor posts appears sorted by virality. Select one, click "Adaptar" — spinner → real GPT-4o adapted post appears. Copy button works.

- [ ] **Step 3: Commit**

```bash
git add web/components/drawers/DrawerStudio.tsx
git commit -m "feat: DrawerStudio wired to real API with post picker"
```

---

### Task 9: Configure Railway env vars and deploy

**Files:** No code changes — Railway configuration only.

- [ ] **Step 1: Set env vars on agro-frontend service**

In Railway dashboard → `agro-frontend` service → Variables, add:

| Variable | Value |
|----------|-------|
| `BACKEND_URL` | Internal URL of `altagrocontent` service (Railway shows this as "Private Domain" in the service settings, e.g. `altagrocontent.railway.internal`) |
| `APP_PASSWORD` | Choose a strong team password |
| `AUTH_SECRET` | Generate with: `openssl rand -hex 16` |

- [ ] **Step 2: Push to GitHub to trigger deploy**

```bash
git push origin main
```

Both services (`altagrocontent` and `agro-frontend`) will redeploy.

- [ ] **Step 3: Smoke-test the live app**

```bash
curl https://agro-frontend-production.up.railway.app/api/health
```

Expected: `{"status":"ok"}` (proxied from FastAPI)

Open `https://agro-frontend-production.up.railway.app` in browser → redirected to `/login` → enter password → orbital UI loads.

- [ ] **Step 4: Configure custom domain altagro.site**

In Railway dashboard → `agro-frontend` service → Settings → Custom Domain → add `altagro.site`.

Railway will show a CNAME target (e.g. `<hash>.up.railway.app`).

In your DNS provider (wherever `altagro.site` is registered), add:
```
CNAME  @  <railway-provided-target>
```

Wait for DNS propagation (usually 1-5 minutes with most providers). Verify:

```bash
curl https://altagro.site/api/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 5: Final end-to-end test**

Open `https://altagro.site` → login → verify each drawer loads real data:
- Concorrentes: real profiles from DB
- Notícias: real RSS items (click Atualizar if empty)
- Carrossel: generate a real carousel
- Relatórios: generate a real report
- Identidade: shows voice profile (or generates one)
- Studio: lists competitor posts, adapts one
