export function DrawerComingSoon() {
  return (
    <div className="flex flex-col items-center justify-center h-full py-24 px-6 text-center">
      <div className="text-4xl mb-4 opacity-40">🚧</div>
      <p className="text-sm font-medium" style={{ color: 'rgba(255,255,255,0.35)' }}>
        Em desenvolvimento
      </p>
      <p className="text-xs mt-2" style={{ color: 'rgba(255,255,255,0.2)' }}>
        Este módulo estará disponível em breve.
      </p>
    </div>
  )
}
