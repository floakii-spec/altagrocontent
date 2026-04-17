'use client'

const MOCK_PROFILES = [
  { handle: '@canalagro', posts: 247, followers: '142k', score: 92 },
  { handle: '@agronoticias', posts: 183, followers: '89k', score: 87 },
  { handle: '@campotec', posts: 312, followers: '201k', score: 78 },
  { handle: '@safrabrasil', posts: 95, followers: '54k', score: 71 },
  { handle: '@agrodigital', posts: 178, followers: '67k', score: 65 },
  { handle: '@ruraltech', posts: 143, followers: '43k', score: 58 },
  { handle: '@milhoesoja', posts: 89, followers: '31k', score: 52 },
  { handle: '@boigordo_br', posts: 201, followers: '118k', score: 84 },
]

export function DrawerConcorrentes() {
  return (
    <div className="p-6 space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: 'Perfis monitorados', value: '8', color: '#3b82f6' },
          { label: 'Posts coletados', value: '1.448', color: '#3b82f6' },
        ].map((s) => (
          <div key={s.label} className="rounded-lg p-3" style={{ background: s.color + '10', border: `1px solid ${s.color}22` }}>
            <p className="text-[10px]" style={{ color: s.color + 'aa' }}>{s.label}</p>
            <p className="text-xl font-bold text-white mt-0.5">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Profiles list */}
      <div>
        <p className="text-[11px] font-semibold tracking-wider uppercase mb-2" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Perfis
        </p>
        <div className="space-y-1.5">
          {MOCK_PROFILES.map((p) => (
            <div
              key={p.handle}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0"
                style={{ background: '#3b82f618', color: '#3b82f6' }}>
                {p.handle[1].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[12px] font-medium text-white truncate">{p.handle}</p>
                <p className="text-[10px]" style={{ color: 'rgba(255,255,255,0.35)' }}>
                  {p.posts} posts · {p.followers}
                </p>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <div className="w-16 h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.08)' }}>
                  <div className="h-full rounded-full" style={{ width: `${p.score}%`, background: '#3b82f6' }} />
                </div>
                <span className="text-[10px] font-semibold" style={{ color: '#3b82f6' }}>{p.score}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <button
        className="w-full py-2.5 rounded-lg text-sm font-semibold"
        style={{ background: '#3b82f618', border: '1px solid #3b82f633', color: '#3b82f6' }}
      >
        ⟳ Coletar agora
      </button>
    </div>
  )
}
