'use client'

import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { type Module, type Group } from '@/lib/tree-data'
import { DrawerCarrossel } from './DrawerCarrossel'
import { DrawerConcorrentes } from './DrawerConcorrentes'
import { DrawerNoticias } from './DrawerNoticias'
import { DrawerRelatorios } from './DrawerRelatorios'
import { DrawerIdentidade } from './DrawerIdentidade'
import { DrawerStudio } from './DrawerStudio'
import { DrawerComingSoon } from './DrawerComingSoon'
import { DrawerInteligenciaPosts } from './DrawerInteligenciaPosts'
import { DrawerInteligenciaArgumentos } from './DrawerInteligenciaArgumentos'

interface ModuleDrawerProps {
  module: Module | null
  group: Group | null
  open: boolean
  onClose: () => void
}

const DRAWER_MAP: Record<string, React.ComponentType> = {
  carrossel: DrawerCarrossel,
  concorrentes: DrawerConcorrentes,
  noticias: DrawerNoticias,
  relatorios: DrawerRelatorios,
  identidade: DrawerIdentidade,
  studio: DrawerStudio,
  'inteligencia-posts': DrawerInteligenciaPosts,
  'inteligencia-argumentos': DrawerInteligenciaArgumentos,
}

export function ModuleDrawer({ module, group, open, onClose }: ModuleDrawerProps) {
  if (!module || !group) return null

  const Content =
    module.status === 'coming'
      ? DrawerComingSoon
      : DRAWER_MAP[module.id] ?? DrawerComingSoon
  const isWideDrawer = ['concorrentes', 'studio'].includes(module.id)
  const drawerClassName = isWideDrawer
    ? 'w-screen max-w-none sm:w-[min(94vw,1040px)] sm:max-w-[1040px] p-0 border-l flex flex-col overflow-hidden'
    : 'w-screen max-w-none sm:w-[480px] sm:max-w-[480px] p-0 border-l flex flex-col overflow-hidden'

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        side="right"
        showCloseButton={false}
        className={drawerClassName}
        style={{
          background: '#080808',
          borderColor: 'rgba(255,255,255,0.08)',
        }}
      >
        {/* Header */}
        <SheetHeader className="px-6 pt-6 pb-4 border-b shrink-0" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-all"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.5)' }}
              aria-label="Voltar"
            >
              ←
            </button>
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center text-xl shrink-0"
              style={{ background: group.color + '18', border: `1px solid ${group.color}33` }}
            >
              {module.emoji}
            </div>
            <div className="flex-1 min-w-0">
              <SheetTitle className="text-[15px] font-semibold text-white leading-tight">
                {module.label}
              </SheetTitle>
              <p className="text-[11px] mt-0.5" style={{ color: 'rgba(255,255,255,0.4)' }}>
                {module.desc}
              </p>
            </div>
            <span
              className="text-[9px] font-bold tracking-wider px-2 py-1 rounded-full shrink-0"
              style={
                module.status === 'active'
                  ? { background: '#16a34a18', color: '#16a34a', border: '1px solid #16a34a33' }
                  : { background: '#ffffff08', color: 'rgba(255,255,255,0.3)', border: '1px solid rgba(255,255,255,0.08)' }
              }
            >
              {module.status === 'active' ? '● ATIVO' : '○ EM BREVE'}
            </span>
          </div>
        </SheetHeader>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto">
          <Content />
        </div>
      </SheetContent>
    </Sheet>
  )
}
