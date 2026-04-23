'use client'

import { type CSSProperties, useCallback, useMemo, useRef, useState } from 'react'
import { Sidebar } from '@/components/sidebar/Sidebar'
import { OrbitalTree, type OrbitalTreeHandle } from '@/components/orbital/OrbitalTree'
import { ModuleDrawer } from '@/components/drawers/ModuleDrawer'
import { TREE, type Module, type Group } from '@/lib/tree-data'

const QUICK_START_IDS = ['identidade', 'concorrentes', 'inteligencia-posts', 'studio', 'carrossel']

function resolveModule(id: string) {
  for (const group of TREE.groups) {
    const module = group.children.find((entry) => entry.id === id)
    if (module) {
      return { module, group }
    }
  }
  return null
}

export default function HomePage() {
  const [openModule, setOpenModule] = useState<{ module: Module; group: Group } | null>(null)
  const [orbitalInGroup, setOrbitalInGroup] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [sidebarMobileOpen, setSidebarMobileOpen] = useState(false)
  const orbitalRef = useRef<OrbitalTreeHandle>(null)

  const handleOpenModule = useCallback((module: Module, group: Group) => {
    setOpenModule({ module, group })
    setSidebarMobileOpen(false)
  }, [])

  const handleClose = useCallback(() => {
    setOpenModule(null)
  }, [])

  const moduleEntries = useMemo(
    () => TREE.groups.flatMap((group) => group.children.map((module) => ({ group, module }))),
    []
  )
  const activeModules = moduleEntries.filter(({ module }) => module.status === 'active')
  const quickStart = QUICK_START_IDS
    .map((id) => resolveModule(id))
    .filter((entry): entry is { module: Module; group: Group } => entry !== null)
  const layoutStyle = {
    '--sidebar-width': `${sidebarCollapsed ? 92 : 284}px`,
  } as CSSProperties

  return (
    <div className="h-screen overflow-hidden text-white" style={{ background: '#000' }}>
      <Sidebar
        activeModuleId={openModule?.module.id ?? null}
        collapsed={sidebarCollapsed}
        mobileOpen={sidebarMobileOpen}
        onCloseMobile={() => setSidebarMobileOpen(false)}
        onSelectModule={handleOpenModule}
        onToggleCollapsed={() => setSidebarCollapsed((current) => !current)}
      />

      <div className="h-screen md:pl-[var(--sidebar-width)]" style={layoutStyle}>
        <header
          className="absolute inset-x-0 top-0 z-30 flex items-center justify-between border-b px-4 py-3 md:hidden"
          style={{
            background: 'rgba(0,0,0,0.82)',
            borderColor: 'rgba(255,255,255,0.06)',
            backdropFilter: 'blur(14px)',
          }}
        >
          <button
            onClick={() => setSidebarMobileOpen(true)}
            className="h-10 rounded-2xl px-3 text-[12px] font-semibold"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
          >
            ☰ Módulos
          </button>

          <div className="text-center">
            <p className="text-[10px] font-bold tracking-[0.28em]" style={{ color: 'rgba(255,255,255,0.58)' }}>
              AGRO INTEL
            </p>
            <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.34)' }}>
              Mapa interno
            </p>
          </div>

          <div
            className="max-w-[128px] truncate rounded-full px-3 py-1 text-[10px] text-right"
            style={{ background: 'rgba(22,163,74,0.12)', border: '1px solid rgba(22,163,74,0.18)', color: '#4ade80' }}
          >
            {openModule?.module.label ?? 'Mapa'}
          </div>
        </header>

        <main className="relative h-full overflow-hidden">
          <div
            className="absolute inset-0"
            style={{
              background:
                'radial-gradient(circle at 50% 44%, rgba(22,163,74,0.18), transparent 28%), radial-gradient(circle at 78% 18%, rgba(59,130,246,0.12), transparent 26%), radial-gradient(circle at 20% 76%, rgba(245,158,11,0.10), transparent 24%), #000',
            }}
          />
          <div
            className="absolute inset-0 opacity-60"
            style={{
              backgroundImage:
                'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
              backgroundSize: '34px 34px',
              maskImage: 'radial-gradient(circle at center, rgba(0,0,0,0.95), rgba(0,0,0,0.38), transparent 82%)',
            }}
          />

          <section className="absolute inset-0 pt-16 md:pt-0">
            <div className="absolute inset-0">
              <OrbitalTree
                ref={orbitalRef}
                onOpenModule={handleOpenModule}
                onStateChange={setOrbitalInGroup}
              />
            </div>
          </section>

          <section
            className="absolute left-4 right-4 top-20 z-10 hidden rounded-[24px] border p-3 md:left-8 md:right-auto md:top-8 md:block md:w-[360px] md:rounded-[26px] md:p-5"
            style={{
              background: 'rgba(5,5,5,0.72)',
              borderColor: 'rgba(255,255,255,0.08)',
              backdropFilter: 'blur(18px)',
            }}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.24em]" style={{ color: '#4ade80' }}>
                  Operação Nathan
                </p>
                <h1 className="mt-1.5 text-[18px] font-semibold leading-tight text-white md:mt-2 md:text-[26px]">
                  Mapa privado da esteira de conteúdo.
                </h1>
              </div>
              <div
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl text-base md:h-11 md:w-11 md:text-lg"
                style={{ background: 'rgba(22,163,74,0.16)', border: '1px solid rgba(22,163,74,0.24)' }}
              >
                🌾
              </div>
            </div>
            <p className="mt-3 hidden text-[12px] leading-relaxed md:block" style={{ color: 'rgba(255,255,255,0.48)' }}>
              Use os nós para entrar nos blocos de criação, coleta, gestão e análise. A barra lateral fica como atalho, mas o mapa é a visão principal.
            </p>

            <div className="mt-4 hidden grid-cols-3 gap-2 md:grid">
              {[
                { label: 'Ativos', value: String(activeModules.length), color: '#22c55e' },
                { label: 'Blocos', value: String(TREE.groups.length), color: '#3b82f6' },
                { label: 'Fluxo', value: String(quickStart.length), color: '#f59e0b' },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-2xl border px-3 py-2.5"
                  style={{ background: `${stat.color}10`, borderColor: `${stat.color}22` }}
                >
                  <p className="text-[9px] uppercase tracking-[0.16em]" style={{ color: `${stat.color}cc` }}>
                    {stat.label}
                  </p>
                  <p className="mt-1 text-[18px] font-semibold text-white">{stat.value}</p>
                </div>
              ))}
            </div>
          </section>

          <section
            className="absolute right-8 top-8 z-10 hidden w-[320px] rounded-[26px] border p-5 xl:block"
            style={{
              background: 'rgba(5,5,5,0.68)',
              borderColor: 'rgba(255,255,255,0.08)',
              backdropFilter: 'blur(18px)',
            }}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: '#60a5fa' }}>
                  Navegação
                </p>
                <p className="mt-2 text-[14px] font-semibold text-white">
                  {orbitalInGroup ? 'Dentro de um bloco' : 'Mapa geral'}
                </p>
              </div>
              {orbitalInGroup && (
                <button
                  onClick={() => orbitalRef.current?.goBack()}
                  className="rounded-full px-3 py-1.5 text-[11px] font-semibold"
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.62)' }}
                >
                  ← Voltar
                </button>
              )}
            </div>

            <p className="mt-3 text-[12px] leading-relaxed" style={{ color: 'rgba(255,255,255,0.44)' }}>
              Clique em um grupo para abrir seus módulos. Clique em um módulo para abrir o drawer operacional.
            </p>

            {openModule && (
              <div
                className="mt-4 rounded-2xl border p-4"
                style={{ background: `${openModule.group.color}12`, borderColor: `${openModule.group.color}28` }}
              >
                <p className="text-[10px] font-bold uppercase tracking-[0.18em]" style={{ color: openModule.group.color }}>
                  Aberto agora
                </p>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-lg">{openModule.module.emoji}</span>
                  <p className="text-[14px] font-semibold text-white">{openModule.module.label}</p>
                </div>
                <button
                  onClick={handleClose}
                  className="mt-3 rounded-full px-3 py-1.5 text-[11px] font-semibold"
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.62)' }}
                >
                  Fechar drawer
                </button>
              </div>
            )}
          </section>

          <section
            className="absolute bottom-4 left-4 right-4 z-10 rounded-[22px] border p-1.5 md:bottom-6 md:left-8 md:right-8 md:rounded-[26px] md:p-4 xl:left-8 xl:right-auto xl:w-[760px]"
            style={{
              background: 'rgba(5,5,5,0.72)',
              borderColor: 'rgba(255,255,255,0.08)',
              backdropFilter: 'blur(18px)',
            }}
          >
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="hidden md:block">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: '#f59e0b' }}>
                  Rotina curta
                </p>
                <p className="mt-1 text-[12px]" style={{ color: 'rgba(255,255,255,0.42)' }}>
                  Atalhos internos para quando não quiser navegar pela órbita.
                </p>
              </div>

              <div className="flex gap-2 overflow-x-auto pb-1 md:max-w-[520px] md:pb-0">
                {quickStart.map(({ module, group }, index) => (
                  <button
                    key={module.id}
                    onClick={() => handleOpenModule(module, group)}
                    className="flex shrink-0 items-center gap-2 rounded-2xl border px-2.5 py-2 text-left transition-all hover:-translate-y-0.5 md:px-3"
                    style={{
                      background: openModule?.module.id === module.id ? `${group.color}18` : 'rgba(255,255,255,0.04)',
                      borderColor: openModule?.module.id === module.id ? `${group.color}32` : 'rgba(255,255,255,0.08)',
                    }}
                  >
                    <span
                      className="flex h-7 w-7 items-center justify-center rounded-xl text-[11px] font-bold"
                      style={{ background: `${group.color}16`, color: group.color }}
                    >
                      {index + 1}
                    </span>
                    <span className="text-[12px] font-semibold text-white">{module.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </section>

          <p
            className="pointer-events-none absolute bottom-[118px] left-1/2 z-10 hidden -translate-x-1/2 select-none text-[10px] uppercase tracking-[0.24em] md:block"
            style={{ color: 'rgba(255,255,255,0.24)' }}
          >
            {orbitalInGroup ? 'Clique em um módulo para abrir' : 'Clique em um grupo para explorar'}
          </p>
        </main>
      </div>

      <ModuleDrawer
        module={openModule?.module ?? null}
        group={openModule?.group ?? null}
        open={openModule !== null}
        onClose={handleClose}
      />
    </div>
  )
}
