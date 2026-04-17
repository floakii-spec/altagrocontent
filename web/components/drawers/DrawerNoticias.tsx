'use client'

const MOCK_NEWS = [
  { source: 'Canal Rural', title: 'Soja bate recorde de exportação no trimestre', time: '2h', tag: 'soja' },
  { source: 'Globo Rural', title: 'Milho safrinha com déficit hídrico no Centro-Oeste', time: '4h', tag: 'milho' },
  { source: 'Agrolink', title: 'USDA revisa projeções de oferta global de grãos', time: '6h', tag: 'mercado' },
  { source: 'N. Agrícolas', title: 'Insumos biológicos crescem 34% no mercado nacional', time: '8h', tag: 'insumos' },
  { source: 'Canal Rural', title: 'Câmbio favorece exportadores de commodities', time: '10h', tag: 'mercado' },
  { source: 'Agrolink', title: 'Novas tecnologias de irrigação ganham espaço', time: '12h', tag: 'tecnologia' },
]

const TAG_COLORS: Record<string, string> = {
  soja: '#16a34a',
  milho: '#d97706',
  mercado: '#3b82f6',
  insumos: '#8b5cf6',
  tecnologia: '#06b6d4',
}

export function DrawerNoticias() {
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
          4 fontes · atualizado agora
        </p>
        <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: '#16a34a18', color: '#16a34a', border: '1px solid #16a34a33' }}>
          ● AO VIVO
        </span>
      </div>

      <div className="space-y-2">
        {MOCK_NEWS.map((item, i) => (
          <div
            key={i}
            className="px-3 py-3 rounded-lg cursor-pointer transition-all"
            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-semibold" style={{ color: 'rgba(255,255,255,0.35)' }}>
                {item.source}
              </span>
              <div className="flex items-center gap-2">
                <span
                  className="text-[9px] font-bold px-1.5 py-0.5 rounded-full"
                  style={{
                    background: (TAG_COLORS[item.tag] ?? '#fff') + '18',
                    color: TAG_COLORS[item.tag] ?? '#fff',
                    border: `1px solid ${(TAG_COLORS[item.tag] ?? '#fff')}33`,
                  }}
                >
                  {item.tag}
                </span>
                <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.25)' }}>{item.time}</span>
              </div>
            </div>
            <p className="text-[12px] leading-snug" style={{ color: 'rgba(255,255,255,0.75)' }}>
              {item.title}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
