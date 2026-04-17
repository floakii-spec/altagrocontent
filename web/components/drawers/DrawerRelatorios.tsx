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
