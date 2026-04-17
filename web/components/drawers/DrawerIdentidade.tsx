export function DrawerIdentidade() {
  return (
    <div className="p-6 space-y-5">
      {/* Voice profile */}
      <div className="rounded-lg p-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold"
            style={{ background: '#8b5cf618', border: '1px solid #8b5cf633', color: '#8b5cf6' }}>
            N
          </div>
          <div>
            <p className="text-[13px] font-semibold text-white">Nathan</p>
            <p className="text-[10px]" style={{ color: 'rgba(255,255,255,0.35)' }}>Perfil de voz · atualizado semanalmente</p>
          </div>
        </div>

        {[
          { label: 'Tom', value: 'Direto, técnico, confiante' },
          { label: 'Linguagem', value: 'Agro + tecnologia' },
          { label: 'Estilo', value: 'Dados + experiência prática' },
          { label: 'CTA recorrente', value: 'Educacional → ação' },
        ].map((row) => (
          <div key={row.label} className="flex items-start justify-between py-1.5 border-b gap-4" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
            <span className="text-[11px] shrink-0" style={{ color: 'rgba(255,255,255,0.35)' }}>{row.label}</span>
            <span className="text-[12px] text-right" style={{ color: 'rgba(255,255,255,0.7)' }}>{row.value}</span>
          </div>
        ))}
      </div>

      {/* Top words */}
      <div>
        <p className="text-[11px] font-semibold tracking-wider uppercase mb-2" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Vocabulário dominante
        </p>
        <div className="flex flex-wrap gap-2">
          {['safra', 'mercado', 'gestão', 'tecnologia', 'resultado', 'produtor', 'dado', 'estratégia', 'campo', 'inovação'].map((word) => (
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
    </div>
  )
}
