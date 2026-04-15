# Content Studio — Design Spec

## Objetivo

Adicionar uma aba "Criar Conteúdo" ao dashboard que usa os posts analisados dos concorrentes, a voz própria do usuário e posts aprovados anteriormente para gerar legendas prontas para o Instagram do `@nathanlimagro`, com foco na captação de clientes para a **Confraria de Vendas no Agro**.

---

## Contexto do Usuário

- **Perfil:** Engenheiro Agrônomo, 15+ anos em vendas, varejo e cooperativismo no agro
- **Empresas:** Phos Consultoria Agro, Projeto Agroroot, Confraria de Vendas no Agro
- **Oferta principal:** Confraria — comunidade de vendas no agro com curso Agroroot + encontros ao vivo quinzenais
- **Instagram:** `@nathanlimagro` (ativo, posts frequentes)
- **Dores:** falta de ideias e demora para produzir conteúdo

---

## Arquitetura

Três fontes de contexto alimentam a geração:

1. **Posts dos concorrentes analisados** — estrutura, hook, gatilho, narrativa de quem performa bem no mercado
2. **Voz do usuário** — análise dos posts do próprio `@nathanlimagro` para extrair tom, vocabulário e estilo
3. **Posts aprovados** — histórico do que o usuário salvou, usado como exemplos de referência (auto-refinamento)

A geração usa GPT-4o com um prompt que combina os três contextos acima mais o contexto fixo da Confraria.

---

## Banco de Dados

### Nova tabela: `generated_posts`

| Coluna | Tipo | Descrição |
|---|---|---|
| id | int PK | |
| source_post_id | int FK → posts.id | Post do concorrente usado como inspiração |
| hook | text | Primeira linha gerada |
| caption | text | Legenda completa |
| cta | text | Call-to-action sugerido |
| status | varchar | `generated`, `approved`, `discarded` |
| created_at | timestamp | |

### Nova tabela: `user_voice_profile`

| Coluna | Tipo | Descrição |
|---|---|---|
| id | int PK | |
| handle | varchar | `nathanlimagro` |
| voice_summary | text | Resumo da voz extraído pelo GPT-4o |
| sample_posts | json | Trechos representativos dos posts |
| updated_at | timestamp | |

---

## Módulos Novos

### `src/collector/own_profile_collector.py`
Coleta os posts do `@nathanlimagro` via Instaloader/Apify (mesma lógica dos concorrentes).

### `src/analyzer/voice_analyzer.py`
Envia os últimos 10-15 posts do usuário ao GPT-4o e extrai um "perfil de voz":
- Tom predominante (técnico, inspirador, direto)
- Vocabulário característico
- Como abre posts (hook style)
- Como fecha posts (CTA style)
- Estrutura narrativa preferida

### `src/generator/content_generator.py`
Função `generate_post(source_post, voice_profile, approved_examples)`:
- Monta prompt com: análise do post do concorrente + perfil de voz + até 3 exemplos aprovados + contexto da Confraria
- Chama GPT-4o
- Retorna dict com `hook`, `caption`, `cta`

### `dashboard/tabs/content_studio.py`
Nova aba do Streamlit com:
- Lista de posts dos concorrentes (ranqueados por virality_score), filtráveis por perfil
- Clique num post → gera conteúdo à direita
- Botões: Regenerar / Salvar / Descartar
- Seção "Meus Conteúdos" com posts aprovados prontos para copiar

---

## Prompt de Geração

```
Você é um ghostwriter especializado em conteúdo para Instagram no agronegócio brasileiro.

SOBRE O AUTOR:
- Engenheiro Agrônomo com 15+ anos em vendas, varejo e cooperativismo no agro
- Fundador da Confraria de Vendas no Agro: comunidade para quem quer dominar o comercial no campo
- A Confraria inclui curso Agroroot + encontros ao vivo quinzenais com especialistas
- Tom: direto, experiente, provocador, próximo do produtor rural

ESTILO DE VOZ DO AUTOR:
{voice_summary}

EXEMPLOS DE POSTS QUE ELE APROVOU:
{approved_examples}

POST DO CONCORRENTE PARA INSPIRAÇÃO:
- Hook: {hook}
- Mensagem central: {main_message}
- Dor abordada: {problem_addressed}
- Estrutura narrativa: {narrative_structure}
- Gatilho: {trigger}
- CTA original: {call_to_action}

Crie um post para o Instagram do autor adaptando a estrutura e abordagem acima para a sua voz e realidade. O post deve falar para agrônomos, consultores e profissionais de vendas no agro que querem crescer na carreira comercial.

Retorne JSON:
{
  "hook": "<primeira linha que prende — máximo 1 frase>",
  "caption": "<legenda completa com quebras de linha, emojis moderados, máximo 300 palavras>",
  "cta": "<call-to-action para a Confraria>"
}
```

---

## Fluxo de Auto-Refinamento

1. Usuário salva um post gerado → status = `approved`
2. Nas próximas gerações, o sistema busca os últimos 3 posts aprovados
3. Eles são incluídos no prompt como exemplos de referência
4. Com o tempo, o sistema converge para o estilo e formatos que o usuário prefere — sem configuração manual

---

## UI — Aba "Criar Conteúdo"

```
[ Filtrar por perfil ▾ ]  [ Ordenar: Viralidade ▾ ]

┌─────────────────────┐  ┌──────────────────────────────────┐
│ @leandro.varos  9.2 │  │  CONTEÚDO GERADO                 │
│ [imagem] [caption]  │  │                                  │
├─────────────────────┤  │  Hook:                           │
│ @cumbre.agro    8.7 │  │  "Você sabe vender, mas não sabe │
│ [imagem] [caption]  │◄─┤   cobrar o que vale."            │
├─────────────────────┤  │                                  │
│ @nathanlimaagro 8.1 │  │  Legenda:                        │
│ ...                 │  │  [legenda completa]              │
└─────────────────────┘  │                                  │
                         │  CTA:                            │
                         │  "Entra na Confraria →"          │
                         │                                  │
                         │  [Regenerar] [Salvar] [Descartar]│
                         └──────────────────────────────────┘

── Meus Conteúdos Salvos ──────────────────────────────────
  [post 1 — copiar]  [post 2 — copiar]  [post 3 — copiar]
```

---

## Arquivos a Criar/Modificar

| Ação | Arquivo |
|---|---|
| Criar | `src/collector/own_profile_collector.py` |
| Criar | `src/analyzer/voice_analyzer.py` |
| Criar | `src/generator/content_generator.py` |
| Criar | `dashboard/tabs/content_studio.py` |
| Modificar | `dashboard/app.py` — adicionar aba |
| Modificar | `src/models.py` — tabelas `generated_posts`, `user_voice_profile` |
| Criar | `alembic/versions/xxx_content_studio.py` |

---

## O que NÃO está no escopo

- Agendamento automático de posts
- Publicação direta no Instagram
- Geração de imagens
- Múltiplos usuários / perfis de voz
