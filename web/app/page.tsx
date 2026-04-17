'use client'

import { useState, useCallback, useRef } from 'react'
import { Sidebar } from '@/components/sidebar/Sidebar'
import { OrbitalTree, type OrbitalTreeHandle } from '@/components/orbital/OrbitalTree'
import { ModuleDrawer } from '@/components/drawers/ModuleDrawer'
import { type Module, type Group } from '@/lib/tree-data'

export default function HomePage() {
  const [openModule, setOpenModule] = useState<{ module: Module; group: Group } | null>(null)
  const [inGroup, setInGroup] = useState(false)
  const orbitalRef = useRef<OrbitalTreeHandle>(null)

  const handleOpenModule = useCallback((module: Module, group: Group) => {
    setOpenModule({ module, group })
  }, [])

  const handleSidebarSelect = useCallback((module: Module, group: Group) => {
    setOpenModule({ module, group })
  }, [])

  const handleClose = useCallback(() => {
    setOpenModule(null)
  }, [])

  return (
    <div className="h-screen w-screen overflow-hidden" style={{ background: '#000' }}>
      {/* Sidebar — fixed overlay, expands on hover */}
      <Sidebar
        activeModuleId={openModule?.module.id ?? null}
        onSelectModule={handleSidebarSelect}
      />

      {/* Main — offset by collapsed sidebar width (48px) */}
      <main className="absolute inset-0 overflow-hidden" style={{ left: 48 }}>
        {/* Back button — visible when inside a group */}
        {inGroup && (
          <button
            onClick={() => orbitalRef.current?.goBack()}
            className="absolute top-5 left-5 z-10 flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all"
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: 'rgba(255,255,255,0.5)',
            }}
          >
            ← Voltar
          </button>
        )}

        {/* Hint */}
        <p
          className="absolute bottom-6 left-1/2 -translate-x-1/2 z-10 text-[10px] tracking-[0.5px] whitespace-nowrap select-none pointer-events-none"
          style={{ color: 'rgba(255,255,255,0.18)' }}
        >
          {inGroup ? 'Clique em um módulo para abrir' : 'Clique em um grupo para explorar'}
        </p>

        {/* Orbital tree */}
        <div className="absolute inset-0 flex items-center justify-center">
          <OrbitalTree
            ref={orbitalRef}
            onOpenModule={handleOpenModule}
            onStateChange={setInGroup}
          />
        </div>
      </main>

      {/* Module drawer */}
      <ModuleDrawer
        module={openModule?.module ?? null}
        group={openModule?.group ?? null}
        open={openModule !== null}
        onClose={handleClose}
      />
    </div>
  )
}
