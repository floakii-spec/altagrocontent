'use client'

import { TREE, type Module, type Group } from '@/lib/tree-data'
import { cn } from '@/lib/utils'

interface SidebarProps {
  activeModuleId: string | null
  collapsed: boolean
  mobileOpen: boolean
  onCloseMobile: () => void
  onSelectModule: (module: Module, group: Group) => void
  onToggleCollapsed: () => void
}

interface SidebarContentProps {
  activeModuleId: string | null
  compact: boolean
  mobile?: boolean
  onCloseMobile?: () => void
  onSelectModule: (module: Module, group: Group) => void
  onToggleCollapsed?: () => void
}

function SidebarContent({
  activeModuleId,
  compact,
  mobile = false,
  onCloseMobile,
  onSelectModule,
  onToggleCollapsed,
}: SidebarContentProps) {
  return (
    <>
      <div
        className="flex items-center gap-3 border-b shrink-0"
        style={{ borderColor: 'rgba(255,255,255,0.06)', padding: compact ? '18px 16px' : '18px 18px' }}
      >
        <div
          className="flex h-11 w-11 items-center justify-center rounded-2xl text-lg shrink-0"
          style={{ background: 'rgba(22,163,74,0.16)', border: '1px solid rgba(22,163,74,0.22)' }}
        >
          🌾
        </div>

        {!compact && (
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-bold tracking-[0.28em]" style={{ color: 'rgba(255,255,255,0.58)' }}>
              AGRO INTEL
            </p>
            <p className="text-[12px] mt-1" style={{ color: 'rgba(255,255,255,0.38)' }}>
              Coleta, analisa e cria com contexto.
            </p>
          </div>
        )}

        {mobile ? (
          <button
            onClick={onCloseMobile}
            className="h-9 w-9 rounded-xl text-[15px] shrink-0"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.56)' }}
            aria-label="Fechar menu"
          >
            ✕
          </button>
        ) : (
          <button
            onClick={onToggleCollapsed}
            className="h-9 w-9 rounded-xl text-[15px] shrink-0"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.56)' }}
            aria-label={compact ? 'Expandir sidebar' : 'Recolher sidebar'}
          >
            {compact ? '→' : '←'}
          </button>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {TREE.groups.map((group) => (
          <section key={group.id} className="space-y-2">
            <div
              className={cn(
                'flex items-center',
                compact ? 'justify-center' : 'justify-between gap-3 px-2'
              )}
            >
              <div className={cn('flex items-center gap-2 min-w-0', compact && 'justify-center')}>
                <span className="text-base shrink-0">{group.emoji}</span>
                {!compact && (
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em]" style={{ color: group.color }}>
                      {group.label}
                    </p>
                    <p className="text-[10px] truncate" style={{ color: 'rgba(255,255,255,0.26)' }}>
                      {group.children.filter((mod) => mod.status === 'active').length} módulos ativos
                    </p>
                  </div>
                )}
              </div>
              {!compact && (
                <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.2)' }}>
                  {group.children.length}
                </span>
              )}
            </div>

            <div className="space-y-1">
              {group.children.map((mod) => {
                const isActive = activeModuleId === mod.id

                return (
                  <button
                    key={mod.id}
                    onClick={() => {
                      onSelectModule(mod, group)
                      onCloseMobile?.()
                    }}
                    title={compact ? mod.label : undefined}
                    className={cn(
                      'w-full rounded-2xl text-left transition-all duration-200',
                      compact ? 'px-0 py-3 flex justify-center' : 'px-3 py-3'
                    )}
                    style={{
                      background: isActive ? `${group.color}16` : 'rgba(255,255,255,0.02)',
                      border: `1px solid ${isActive ? `${group.color}33` : 'rgba(255,255,255,0.06)'}`,
                      color: isActive ? '#fff' : 'rgba(255,255,255,0.7)',
                    }}
                  >
                    <div className={cn('flex items-center', compact ? 'justify-center' : 'gap-3')}>
                      <div
                        className="h-10 w-10 rounded-2xl flex items-center justify-center text-[18px] shrink-0"
                        style={{
                          background: isActive ? `${group.color}18` : 'rgba(255,255,255,0.04)',
                          border: `1px solid ${isActive ? `${group.color}30` : 'rgba(255,255,255,0.06)'}`,
                        }}
                      >
                        {mod.emoji}
                      </div>

                      {!compact && (
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-[13px] font-semibold truncate">{mod.label}</p>
                            <span
                              className="text-[9px] px-2 py-0.5 rounded-full font-bold tracking-[0.18em] shrink-0"
                              style={
                                mod.status === 'active'
                                  ? { background: 'rgba(22,163,74,0.12)', color: '#22c55e', border: '1px solid rgba(34,197,94,0.18)' }
                                  : { background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.34)', border: '1px solid rgba(255,255,255,0.08)' }
                              }
                            >
                              {mod.status === 'active' ? 'ATIVO' : 'EM BREVE'}
                            </span>
                          </div>
                          <p className="text-[11px] mt-1 leading-relaxed" style={{ color: 'rgba(255,255,255,0.38)' }}>
                            {mod.desc}
                          </p>
                        </div>
                      )}
                    </div>
                  </button>
                )
              })}
            </div>
          </section>
        ))}
      </nav>

      <div
        className={cn('border-t shrink-0', compact ? 'px-3 py-4' : 'px-4 py-4')}
        style={{ borderColor: 'rgba(255,255,255,0.06)' }}
      >
        <div
          className={cn(
            'rounded-2xl border',
            compact ? 'p-2.5 flex justify-center' : 'p-3.5'
          )}
          style={{ background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.06)' }}
        >
          {compact ? (
            <div
              className="h-9 w-9 rounded-full flex items-center justify-center text-xs font-bold"
              style={{ background: '#16a34a22', border: '1px solid #16a34a44', color: '#16a34a' }}
            >
              N
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <div
                className="h-10 w-10 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                style={{ background: '#16a34a22', border: '1px solid #16a34a44', color: '#16a34a' }}
              >
                N
              </div>
              <div className="min-w-0">
                <p className="text-[12px] font-semibold text-white">Nathan</p>
                <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.35)' }}>
                  Perfil operacional ativo
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export function Sidebar({
  activeModuleId,
  collapsed,
  mobileOpen,
  onCloseMobile,
  onSelectModule,
  onToggleCollapsed,
}: SidebarProps) {
  return (
    <>
      <div
        className={cn(
          'fixed inset-0 z-40 bg-black/70 backdrop-blur-sm transition-opacity md:hidden',
          mobileOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        )}
        onClick={onCloseMobile}
      />

      <aside
        className={cn(
          'fixed left-0 top-0 z-50 h-screen w-[min(88vw,320px)] border-r transition-transform duration-200 md:hidden',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        style={{
          borderColor: 'rgba(255,255,255,0.06)',
          background: '#050505',
        }}
      >
        <SidebarContent
          activeModuleId={activeModuleId}
          compact={false}
          mobile
          onCloseMobile={onCloseMobile}
          onSelectModule={onSelectModule}
        />
      </aside>

      <aside
        className="fixed left-0 top-0 z-30 hidden h-screen border-r transition-[width] duration-200 md:flex md:flex-col"
        style={{
          width: collapsed ? 92 : 284,
          borderColor: 'rgba(255,255,255,0.06)',
          background: '#050505',
        }}
      >
        <SidebarContent
          activeModuleId={activeModuleId}
          compact={collapsed}
          onSelectModule={onSelectModule}
          onToggleCollapsed={onToggleCollapsed}
        />
      </aside>
    </>
  )
}
