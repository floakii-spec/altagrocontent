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
          className="sticky top-0 z-20 flex items-center justify-between border-b px-4 py-3 md:hidden"
          style={{
            background: 'rgba(0,0,0,0.92)',
            borderColor: 'rgba(255,255,255,0.06)',
            backdropFilter: 'blur(12px)',
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
              Painel operacional
            </p>
          </div>

          <div
            className="max-w-[140px] truncate rounded-full px-3 py-1 text-[10px] text-right"
            style={{ background: 'rgba(22,163,74,0.12)', border: '1px solid rgba(22,163,74,0.18)', color: '#4ade80' }}
          >
            {openModule?.module.label ?? 'Sem módulo aberto'}
          </div>
        </header>

        <main className="h-full overflow-y-auto">
          <div className="mx-auto max-w-[1480px] space-y-6 px-4 pb-10 pt-4 sm:px-6 lg:px-8 lg:pt-8">
            <section
              className="relative overflow-hidden rounded-[30px] border p-5 sm:p-7 lg:p-8"
              style={{
                borderColor: 'rgba(255,255,255,0.08)',
                background:
                  'radial-gradient(circle at top left, rgba(22,163,74,0.20), transparent 34%), radial-gradient(circle at right center, rgba(59,130,246,0.16), transparent 28%), radial-gradient(circle at bottom left, rgba(245,158,11,0.10), transparent 24%), #050505',
              }}
            >
              <div
                className="absolute inset-0 opacity-70"
                style={{
                  backgroundImage:
                    'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
                  backgroundSize: '28px 28px',
                  maskImage: 'linear-gradient(to bottom, rgba(0,0,0,0.9), transparent)',
                }}
              />

              <div className="relative grid gap-8 xl:grid-cols-[minmax(0,1.2fr)_380px]">
                <div className="space-y-6">
                  <div className="space-y-3">
                    <span
                      className="inline-flex rounded-full px-3 py-1 text-[10px] font-bold tracking-[0.22em]"
                      style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.09)', color: 'rgba(255,255,255,0.62)' }}
                    >
                      OPERAÇÃO DE CONTEÚDO AGRO
                    </span>
                    <div className="max-w-3xl space-y-3">
                      <h1 className="text-[30px] leading-none font-semibold sm:text-[40px] lg:text-[52px]">
                        O app agora começa pelo fluxo real de uso, não por tentativa e erro.
                      </h1>
                      <p className="max-w-2xl text-[14px] leading-relaxed sm:text-[15px]" style={{ color: 'rgba(255,255,255,0.66)' }}>
                        Organizei a navegação para ficar claro o que vem primeiro, o que alimenta cada ferramenta e onde cada ativo mora:
                        perfil próprio em <strong>Identidade</strong>, biblioteca em <strong>Concorrentes</strong>, análise em <strong>Deep Dive</strong> e geração em <strong>Studio</strong> ou <strong>Carrossel</strong>.
                      </p>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-3">
                    {[
                      { label: 'Módulos ativos', value: String(activeModules.length), color: '#22c55e' },
                      { label: 'Frentes operacionais', value: String(TREE.groups.length), color: '#3b82f6' },
                      { label: 'Fluxos essenciais', value: String(quickStart.length), color: '#f59e0b' },
                    ].map((stat) => (
                      <div
                        key={stat.label}
                        className="rounded-2xl border p-4"
                        style={{ background: `${stat.color}12`, borderColor: `${stat.color}22` }}
                      >
                        <p className="text-[11px] uppercase tracking-[0.18em]" style={{ color: `${stat.color}cc` }}>
                          {stat.label}
                        </p>
                        <p className="mt-2 text-3xl font-semibold text-white">{stat.value}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div
                  className="rounded-[26px] border p-5"
                  style={{ background: 'rgba(7,7,7,0.82)', borderColor: 'rgba(255,255,255,0.08)' }}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em]" style={{ color: '#22c55e' }}>
                        Fluxo recomendado
                      </p>
                      <p className="mt-1 text-[12px]" style={{ color: 'rgba(255,255,255,0.42)' }}>
                        O caminho mais curto para sair da coleta para geração.
                      </p>
                    </div>
                    <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.28)' }}>
                      5 etapas
                    </span>
                  </div>

                  <div className="mt-5 space-y-3">
                    {quickStart.map(({ module, group }, index) => (
                      <button
                        key={module.id}
                        onClick={() => handleOpenModule(module, group)}
                        className="group flex w-full items-start gap-4 rounded-2xl border px-4 py-4 text-left transition-all duration-200 hover:-translate-y-0.5"
                        style={{
                          background: 'rgba(255,255,255,0.03)',
                          borderColor: 'rgba(255,255,255,0.06)',
                        }}
                      >
                        <div
                          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl text-[13px] font-bold"
                          style={{ background: `${group.color}18`, border: `1px solid ${group.color}28`, color: group.color }}
                        >
                          {index + 1}
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-lg">{module.emoji}</span>
                            <p className="text-[14px] font-semibold text-white">{module.label}</p>
                          </div>
                          <p className="mt-1 text-[12px] leading-relaxed" style={{ color: 'rgba(255,255,255,0.42)' }}>
                            {module.desc}
                          </p>
                        </div>

                        <span className="text-[12px] shrink-0 transition-transform group-hover:translate-x-0.5" style={{ color: 'rgba(255,255,255,0.3)' }}>
                          →
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            {openModule && (
              <section
                className="rounded-[24px] border px-5 py-4"
                style={{ background: `${openModule.group.color}10`, borderColor: `${openModule.group.color}24` }}
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em]" style={{ color: openModule.group.color }}>
                      Módulo ativo
                    </p>
                    <p className="mt-1 text-[14px] text-white">
                      {openModule.module.emoji} {openModule.module.label}
                    </p>
                  </div>

                  <button
                    onClick={handleClose}
                    className="rounded-full px-3 py-1.5 text-[11px] font-semibold"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.56)' }}
                  >
                    Fechar drawer
                  </button>
                </div>
              </section>
            )}

            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_420px]">
              <div className="space-y-6">
                {TREE.groups.map((group) => (
                  <section
                    key={group.id}
                    className="rounded-[28px] border p-5 sm:p-6"
                    style={{ background: 'rgba(255,255,255,0.025)', borderColor: 'rgba(255,255,255,0.08)' }}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center gap-3">
                          <div
                            className="flex h-11 w-11 items-center justify-center rounded-2xl text-lg"
                            style={{ background: `${group.color}18`, border: `1px solid ${group.color}28` }}
                          >
                            {group.emoji}
                          </div>
                          <div>
                            <p className="text-[11px] font-semibold uppercase tracking-[0.18em]" style={{ color: group.color }}>
                              {group.label}
                            </p>
                            <p className="text-[12px]" style={{ color: 'rgba(255,255,255,0.42)' }}>
                              {group.children.filter((module) => module.status === 'active').length} módulos ativos neste bloco
                            </p>
                          </div>
                        </div>
                      </div>

                      <div
                        className="rounded-full px-3 py-1 text-[10px] font-semibold tracking-[0.18em]"
                        style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.38)' }}
                      >
                        {group.children.length} entradas
                      </div>
                    </div>

                    <div className="mt-5 grid gap-3 md:grid-cols-2 2xl:grid-cols-3">
                      {group.children.map((module) => {
                        const isActive = openModule?.module.id === module.id
                        const isRecommended = quickStart.some((entry) => entry.module.id === module.id)

                        return (
                          <button
                            key={module.id}
                            onClick={() => handleOpenModule(module, group)}
                            className="group relative overflow-hidden rounded-[24px] border p-4 text-left transition-all duration-200 hover:-translate-y-0.5"
                            style={{
                              background: isActive ? `${group.color}14` : 'rgba(255,255,255,0.03)',
                              borderColor: isActive ? `${group.color}2f` : 'rgba(255,255,255,0.08)',
                              boxShadow: isActive ? `0 18px 60px ${group.color}16` : 'none',
                            }}
                          >
                            <div
                              className="absolute inset-0 opacity-0 transition-opacity duration-200 group-hover:opacity-100"
                              style={{ background: `radial-gradient(circle at top right, ${group.color}18, transparent 42%)` }}
                            />

                            <div className="relative space-y-4">
                              <div className="flex items-start justify-between gap-3">
                                <div
                                  className="flex h-12 w-12 items-center justify-center rounded-2xl text-xl shrink-0"
                                  style={{ background: `${group.color}18`, border: `1px solid ${group.color}28` }}
                                >
                                  {module.emoji}
                                </div>
                                <div className="flex flex-wrap justify-end gap-2">
                                  {isRecommended && (
                                    <span
                                      className="rounded-full px-2.5 py-1 text-[9px] font-bold tracking-[0.16em]"
                                      style={{ background: 'rgba(22,163,74,0.12)', border: '1px solid rgba(34,197,94,0.16)', color: '#4ade80' }}
                                    >
                                      ESSENCIAL
                                    </span>
                                  )}
                                  <span
                                    className="rounded-full px-2.5 py-1 text-[9px] font-bold tracking-[0.16em]"
                                    style={
                                      module.status === 'active'
                                        ? { background: `${group.color}18`, border: `1px solid ${group.color}28`, color: group.color }
                                        : { background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.36)' }
                                    }
                                  >
                                    {module.status === 'active' ? 'ATIVO' : 'EM BREVE'}
                                  </span>
                                </div>
                              </div>

                              <div className="space-y-2">
                                <p className="text-[16px] font-semibold text-white">{module.label}</p>
                                <p className="text-[13px] leading-relaxed" style={{ color: 'rgba(255,255,255,0.46)' }}>
                                  {module.desc}
                                </p>
                              </div>

                              <div className="flex items-center justify-between pt-2">
                                <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
                                  {group.label}
                                </span>
                                <span className="text-[12px] transition-transform group-hover:translate-x-0.5" style={{ color: 'rgba(255,255,255,0.4)' }}>
                                  Abrir →
                                </span>
                              </div>
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </section>
                ))}
              </div>

              <aside className="hidden xl:block">
                <section
                  className="rounded-[28px] border p-5"
                  style={{ background: 'rgba(255,255,255,0.025)', borderColor: 'rgba(255,255,255,0.08)' }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em]" style={{ color: '#3b82f6' }}>
                        Mapa visual
                      </p>
                      <p className="mt-1 text-[12px] leading-relaxed" style={{ color: 'rgba(255,255,255,0.42)' }}>
                        Mantive o explorador orbital como forma rápida de navegar pelo sistema, mas agora ele é complementar ao painel principal.
                      </p>
                    </div>

                    {orbitalInGroup && (
                      <button
                        onClick={() => orbitalRef.current?.goBack()}
                        className="rounded-full px-3 py-1.5 text-[11px] font-semibold shrink-0"
                        style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.56)' }}
                      >
                        ← Voltar
                      </button>
                    )}
                  </div>

                  <div
                    className="relative mt-5 overflow-hidden rounded-[26px] border"
                    style={{
                      height: 560,
                      borderColor: 'rgba(255,255,255,0.08)',
                      background:
                        'radial-gradient(circle at center, rgba(22,163,74,0.12), transparent 40%), radial-gradient(circle at top, rgba(59,130,246,0.12), transparent 30%), #030303',
                    }}
                  >
                    <div
                      className="absolute inset-0 opacity-60"
                      style={{
                        backgroundImage:
                          'linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)',
                        backgroundSize: '30px 30px',
                      }}
                    />

                    <div className="absolute inset-0">
                      <OrbitalTree
                        ref={orbitalRef}
                        onOpenModule={handleOpenModule}
                        onStateChange={setOrbitalInGroup}
                      />
                    </div>
                  </div>

                  <p className="mt-4 text-[12px]" style={{ color: 'rgba(255,255,255,0.34)' }}>
                    Clique em um grupo para ver os módulos da órbita e abrir o drawer correspondente.
                  </p>
                </section>
              </aside>
            </div>
          </div>
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
