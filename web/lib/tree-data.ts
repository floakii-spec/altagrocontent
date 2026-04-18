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
          desc: 'Gera slides virais com GPT-4o baseado no relatório semanal e voz do Nathan.',
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
          desc: 'Cria posts adaptados de concorrentes com voz própria do Nathan.',
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
          desc: '8 perfis monitorados. Posts coletados via Apify + Instaloader automaticamente.',
        },
        {
          id: 'noticias',
          emoji: '📰',
          label: 'Notícias',
          color: '#3b82f6',
          status: 'active',
          desc: 'RSS de 4 fontes agro: Canal Rural, Globo Rural, Agrolink, Notícias Agrícolas.',
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
          desc: 'Consolida análises semanais em insights acionáveis via GPT-4o.',
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
          desc: 'Perfil de voz do Nathan: vocabulário, tom, temas dominantes, estilo único.',
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
