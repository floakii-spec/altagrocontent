export type ModuleStatus = 'active' | 'coming'

export interface Module {
  id: string
  emoji: string
  label: string
  color: string
  status: ModuleStatus
  desc: string
}

export interface Group {
  id: string
  emoji: string
  label: string
  color: string
  children: Module[]
}

export interface TreeData {
  root: { id: string; emoji: string; label: string; color: string }
  groups: Group[]
}

export const TREE: TreeData = {
  root: { id: 'root', emoji: '🌾', label: 'Agro Intel', color: '#16a34a' },
  groups: [
    {
      id: 'criacao',
      emoji: '✍️',
      label: 'Criação',
      color: '#16a34a',
      children: [
        {
          id: 'carrossel',
          emoji: '🎠',
          label: 'Carrossel',
          color: '#16a34a',
          status: 'active',
          desc: 'Gera carrosséis completos com base nos relatórios, na voz do Nathan e na inteligência já coletada.',
        },
        {
          id: 'motivacional',
          emoji: '💬',
          label: 'Motivacional',
          color: '#16a34a',
          status: 'coming',
          desc: 'Posts motivacionais e de autoridade adaptados à linguagem do agro.',
        },
        {
          id: 'studio',
          emoji: '🎬',
          label: 'Studio',
          color: '#16a34a',
          status: 'active',
          desc: 'Adapta posts coletados dos concorrentes para a voz do Nathan em formato de carrossel.',
        },
      ],
    },
    {
      id: 'coleta',
      emoji: '📡',
      label: 'Coleta',
      color: '#3b82f6',
      children: [
        {
          id: 'concorrentes',
          emoji: '📊',
          label: 'Concorrentes',
          color: '#3b82f6',
          status: 'active',
          desc: 'Biblioteca dos concorrentes monitorados, com posts coletados, miniaturas e estado de análise.',
        },
        {
          id: 'noticias',
          emoji: '📰',
          label: 'Notícias',
          color: '#3b82f6',
          status: 'active',
          desc: 'Radar de notícias do agro para alimentar contexto, repertório e novos conteúdos.',
        },
      ],
    },
    {
      id: 'gestao',
      emoji: '⚙️',
      label: 'Gestão',
      color: '#8b5cf6',
      children: [
        {
          id: 'relatorios',
          emoji: '📋',
          label: 'Relatórios',
          color: '#8b5cf6',
          status: 'active',
          desc: 'Consolida sinais da semana em relatórios acionáveis para orientar criação e análise.',
        },
        {
          id: 'calendario',
          emoji: '📅',
          label: 'Calendário',
          color: '#8b5cf6',
          status: 'coming',
          desc: 'Plano editorial semanal gerado por IA com base em gaps e sazonalidade.',
        },
        {
          id: 'identidade',
          emoji: '🪪',
          label: 'Identidade',
          color: '#8b5cf6',
          status: 'active',
          desc: 'Central do perfil próprio: coleta dos seus posts e construção da voz do Nathan.',
        },
      ],
    },
    {
      id: 'analise',
      emoji: '🧠',
      label: 'Análise',
      color: '#f59e0b',
      children: [
        {
          id: 'inteligencia-posts',
          emoji: '🔍',
          label: 'Deep Dive',
          color: '#f59e0b',
          status: 'active',
          desc: 'Análise técnica profunda por post: argumentos, dados, profundidade e lógica do conteúdo agro.',
        },
        {
          id: 'inteligencia-argumentos',
          emoji: '📚',
          label: 'Argumentos',
          color: '#f59e0b',
          status: 'active',
          desc: 'Banco de argumentos extraídos dos posts virais, pontuados por qualidade e viralidade.',
        },
      ],
    },
  ],
}

export const ALL_MODULES: Module[] = TREE.groups.flatMap((g) => g.children)

export function findModule(id: string): Module | undefined {
  return ALL_MODULES.find((m) => m.id === id)
}

export function findGroup(id: string): Group | undefined {
  return TREE.groups.find((g) => g.id === id)
}
