'use client'

import { useState } from 'react'
import { TREE, type Module, type Group } from '@/lib/tree-data'

interface SidebarProps {
  activeModuleId: string | null
  onSelectModule: (module: Module, group: Group) => void
}

export function Sidebar({ activeModuleId, onSelectModule }: SidebarProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <aside
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
      className="fixed left-0 top-0 h-screen z-20 flex flex-col border-r overflow-hidden"
      style={{
        width: expanded ? 220 : 48,
        transition: 'width 0.2s ease',
        borderColor: 'rgba(255,255,255,0.06)',
        background: '#050505',
      }}
    >
      {/* Logo */}
      <div
        className="flex items-center gap-2 border-b shrink-0 overflow-hidden"
        style={{ borderColor: 'rgba(255,255,255,0.06)', height: 60, padding: '0 12px' }}
      >
        <span className="text-lg shrink-0">🌾</span>
        {expanded && (
          <span className="text-xs font-bold tracking-widest whitespace-nowrap" style={{ color: 'rgba(255,255,255,0.7)' }}>
            AGRO INTEL
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-3" style={{ padding: '12px 6px' }}>
        {TREE.groups.map((group) => (
          <div key={group.id} className="mb-4">
            {expanded && (
              <div
                className="flex items-center gap-2 py-1 mb-1 text-[10px] font-semibold tracking-widest uppercase"
                style={{ color: group.color + 'aa', padding: '4px 12px' }}
              >
                <span>{group.emoji}</span>
                <span className="whitespace-nowrap">{group.label}</span>
              </div>
            )}

            {group.children.map((mod) => {
              const isActive = activeModuleId === mod.id
              return (
                <button
                  key={mod.id}
                  onClick={() => onSelectModule(mod, group)}
                  title={!expanded ? mod.label : undefined}
                  className="w-full flex items-center rounded-md text-left transition-all duration-150"
                  style={{
                    gap: 10,
                    padding: expanded ? '8px 12px' : '8px 0',
                    justifyContent: expanded ? 'flex-start' : 'center',
                    background: isActive ? group.color + '18' : 'transparent',
                    color: isActive ? '#fff' : 'rgba(255,255,255,0.45)',
                  }}
                >
                  <span className="text-sm shrink-0">{mod.emoji}</span>
                  {expanded && (
                    <>
                      <span className="text-[12px] font-medium whitespace-nowrap flex-1 min-w-0">{mod.label}</span>
                      {mod.status === 'coming' && (
                        <span
                          className="text-[8px] font-bold tracking-wider px-1.5 py-0.5 rounded-full shrink-0"
                          style={{ background: '#ffffff0a', color: 'rgba(255,255,255,0.25)', border: '1px solid rgba(255,255,255,0.08)' }}
                        >
                          EM BREVE
                        </span>
                      )}
                      {isActive && mod.status === 'active' && (
                        <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: group.color }} />
                      )}
                    </>
                  )}
                </button>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div
        className="border-t shrink-0 flex items-center gap-2 overflow-hidden"
        style={{
          borderColor: 'rgba(255,255,255,0.06)',
          padding: '12px',
          justifyContent: expanded ? 'flex-start' : 'center',
        }}
      >
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
          style={{ background: '#16a34a22', border: '1px solid #16a34a44', color: '#16a34a' }}
        >
          N
        </div>
        {expanded && (
          <span className="text-[11px] whitespace-nowrap" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Nathan
          </span>
        )}
      </div>
    </aside>
  )
}
