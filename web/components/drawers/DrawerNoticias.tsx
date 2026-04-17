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
