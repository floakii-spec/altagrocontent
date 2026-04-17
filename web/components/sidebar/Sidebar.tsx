'use client'

import { TREE, type Module, type Group } from '@/lib/tree-data'

interface SidebarProps {
  activeModuleId: string | null
  onSelectModule: (module: Module, group: Group) => void
}

export function Sidebar({ activeModuleId, onSelectModule }: SidebarProps) {
  return (
    <aside
      className="flex flex-col h-full w-[220px] shrink-0 border-r"
      style={{ borderColor: 'rgba(255,255,255,0.06)', background: '#050505' }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-5 border-b" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <span className="text-lg">🌾</span>
        <span className="text-xs font-bold tracking-widest" style={{ color: 'rgba(255,255,255,0.7)' }}>
          AGRO INTEL
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {TREE.groups.map((group) => (
          <div key={group.id} className="mb-4">
            {/* Group header */}
            <div
              className="flex items-center gap-2 px-3 py-1 mb-1 text-[10px] font-semibold tracking-widest uppercase"
              style={{ color: group.color + 'aa' }}
            >
              <span>{group.emoji}</span>
              <span>{group.label}</span>
            </div>

            {/* Children */}
            {group.children.map((mod) => {
              const isActive = activeModuleId === mod.id
              return (
                <button
                  key={mod.id}
                  onClick={() => onSelectModule(mod, group)}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-left transition-all duration-150 group"
                  style={{
                    background: isActive ? group.color + '18' : 'transparent',
                    color: isActive ? '#fff' : 'rgba(255,255,255,0.45)',
                  }}
                >
                  <span className="text-sm">{mod.emoji}</span>
                  <span className="text-[12px] font-medium">{mod.label}</span>
                  {mod.status === 'coming' && (
                    <span
                      className="ml-auto text-[8px] font-bold tracking-wider px-1.5 py-0.5 rounded-full"
                      style={{ background: '#ffffff0a', color: 'rgba(255,255,255,0.25)', border: '1px solid rgba(255,255,255,0.08)' }}
                    >
                      EM BREVE
                    </span>
                  )}
                  {isActive && mod.status === 'active' && (
                    <span
                      className="ml-auto w-1.5 h-1.5 rounded-full"
                      style={{ background: group.color }}
                    />
                  )}
                </button>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div
        className="px-4 py-3 border-t flex items-center gap-2"
        style={{ borderColor: 'rgba(255,255,255,0.06)' }}
      >
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
          style={{ background: '#16a34a22', border: '1px solid #16a34a44', color: '#16a34a' }}
        >
          N
        </div>
        <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Nathan
        </span>
      </div>
    </aside>
  )
}
