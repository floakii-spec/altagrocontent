# Design: Instagram Competitor Intelligence Tool

**Date:** 2026-04-14
**Status:** Approved

---

## Overview

Ferramenta de inteligência competitiva para monitorar 20+ perfis concorrentes no Instagram no nicho de agronegócio. Coleta posts diariamente, analisa imagens e legendas com GPT-4o Vision, gera relatórios semanais consolidados e produz carrosséis virais adaptados à linguagem do próprio perfil do usuário.

**Usuários:** Time de marketing pequeno (2-5 pessoas)
**Stack:** Python + PostgreSQL + Streamlit + OpenAI API (GPT-4o + GPT-4o Vision) + Apify

---

## Arquitetura Geral

```
[Scheduler diário - APScheduler/cron]
      ↓
[Coletor - Apify + Instaloader fallback]
  ← concorrentes (20+ perfis) + perfil próprio
      ↓
[PostgreSQL] ← posts, métricas, análises
      ↓
[Analisador - GPT-4o Vision]
  ← processa cada imagem nova
      ↓ insights por post
[PostgreSQL]
      ↓                          ↓
[Gerador de relatório]    [Gerador de carrossel]
  semanal - GPT-4o          sob demanda - GPT-4o
      ↓                          ↓
[Dashboard - Streamlit]
  ← tabs em acordeão (uma aberta por vez)
```

---

## Banco de Dados (PostgreSQL)

### Grupo 1 — Perfis e Posts

**`profiles`**
- `id`, `handle` (username Instagram), `type` (competitor | own), `niche`, `follower_count`, `created_at`, `active` (bool)

**`posts`**
- `id`, `profile_id` (FK), `instagram_id`, `image_url`, `caption`, `hashtags` (array), `likes`, `comments`, `post_type` (feed | reel | carousel), `published_at`, `collected_at`

### Grupo 2 — Análises

**`post_analyses`**
- `id`, `post_id` (FK), `visual_theme` (maquinário/insumo/campo/pessoa/dado), `visual_format` (infográfico/foto real/montagem), `emotional_tone`, `trigger` (autoridade/escassez/pertencimento/resultado), `virality_score` (float, normalizado por seguidores), `raw_analysis` (JSON com resposta completa do GPT-4o), `analyzed_at`

**`profile_voice`**
- `id`, `profile_id` (FK — sempre o perfil próprio), `vocabulary` (JSON), `tone`, `dominant_themes` (array), `competitor_comparison` (JSON), `generated_at`

### Grupo 3 — Relatórios e Carrosséis

**`weekly_reports`**
- `id`, `period_start`, `period_end`, `top_formats` (JSON), `top_themes` (JSON), `language_patterns` (JSON), `top_hashtags` (array), `viral_posts` (array de post_ids), `report_text` (markdown), `generated_at`

**`carousels`**
- `id`, `theme` (pauta digitada pelo usuário), `slides` (JSON: `[{slide_number, title, copy, cta}]`), `based_on_reports` (array de report_ids), `generated_at`

---

## Dashboard (Streamlit)

Interface com navegação em tabs estilo acordeão — apenas uma tab aberta por vez, botões para alternar.

### Tab 1 — Concorrentes
- Lista de perfis monitorados com status de coleta (último sync, total de posts)
- Formulário para adicionar perfil (handle) e definir tipo
- Botão para remover perfil

### Tab 2 — Posts
- Feed de posts coletados
- Filtros: perfil, período, tipo de post (feed/reel/carrossel), faixa de virality score
- Card por post: imagem, legenda, métricas, análise do GPT-4o Vision expandível

### Tab 3 — Relatório Semanal
- Relatório consolidado da semana atual em markdown renderizado
- Seções: formatos que mais engajaram, padrões de linguagem, temas em alta, hashtags recorrentes
- Selector de semana para ver relatórios históricos

### Tab 4 — Meu Perfil de Voz
- Perfil de linguagem consolidado do perfil próprio
- Exibe: tom predominante, vocabulário característico, temas dominantes
- Comparativo visual (texto) com padrões dos concorrentes
- Data da última atualização

### Tab 5 — Gerador de Carrossel
- Campo de texto: "Digite o tema ou pauta"
- Botão "Gerar Carrossel"
- Output: estrutura completa por slide (título + copy + CTA final)
- Histórico de carrosséis gerados com opção de rever

---

## Coleta e Processamento

### Coleta Diária (06h00)
- **Primeira execução:** busca posts dos últimos 6 meses de todos os perfis cadastrados
- **Execuções subsequentes:** apenas posts novos desde o último `collected_at`
- **Ferramenta principal:** Apify (Actor: Instagram Scraper) — suporta 20+ perfis com rotação de IP embutida
- **Fallback:** Instaloader para perfis que falharem no Apify
- Dados salvos no PostgreSQL; imagens referenciadas por URL (não armazenadas localmente)

### Análise de Imagens (GPT-4o Vision)
- Cada post novo entra em fila de análise após coleta
- Prompt especializado em agronegócio: identifica tema visual, formato, tom emocional, gatilho psicológico
- `virality_score` = (likes + comentários × 2) / follower_count — normalizado entre 0 e 1
- Resultado salvo em `post_analyses`

### Atualização Semanal (domingo 08h00)
- GPT-4o consolida todas as `post_analyses` da semana → gera `weekly_reports`
- Reanálise do perfil próprio → atualiza `profile_voice`

### Geração de Carrossel (sob demanda)
- GPT-4o recebe: tema digitado + último `weekly_report` + último `profile_voice`
- Retorna JSON estruturado com slides: `{slide_number, title, copy, cta}`
- Salvo em `carousels`

---

## Stack Técnica

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Banco de dados | PostgreSQL 15 |
| ORM | SQLAlchemy |
| Scraping principal | Apify (Instagram Scraper Actor) |
| Scraping fallback | Instaloader |
| Scheduler | APScheduler |
| Análise de imagem | OpenAI GPT-4o Vision |
| Geração de texto | OpenAI GPT-4o |
| Dashboard | Streamlit |
| Config | python-dotenv (.env) |

---

## Fora do Escopo (v1)

- Geração de imagens para carrosséis (DALL-E ou similar) — futuro
- Exportação para Canva / Google Slides — futuro
- Monitoramento de stories — futuro
- Multi-tenant / autenticação de usuários — futuro
- Deploy em cloud — a definir após validação local
