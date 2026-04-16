# Content Strategy Engine — Plan C: Dashboard

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Prerequisite:** Plans A and B must be complete (all models, news_monitor, carousel_analyzer, strategy_engine, calendar_generator implemented and tested).

**Goal:** Add two new dashboard tabs (📰 Notícias, 📅 Calendário) and update the existing ✍️ Criar Conteúdo tab to support Strategy Mode (market-expert idea generation), hook variations, and funnel stage tagging. Register all tabs in app.py.

**Architecture:** Each tab is a standalone `render()` function in its own file under `dashboard/tabs/`. No shared state beyond `st.session_state` and the DB session. The content_studio.py tab gains a toggle between "Inspiração em post" (existing flow) and "Ideia de mercado" (strategy engine flow).

**Tech Stack:** Streamlit 1.35, SQLAlchemy 2.0, Python 3.9. No new dependencies.

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `dashboard/tabs/news.py` | News monitor tab — display + manual refresh + "Usar como base" |
| Create | `dashboard/tabs/calendar_tab.py` | Weekly editorial calendar tab |
| Modify | `dashboard/tabs/content_studio.py` | Add Strategy Mode toggle, hook variations picker, funnel stage display |
| Modify | `dashboard/app.py` | Register news and calendar tabs |

---

## Task 1: News Tab

**Files:**
- Create: `dashboard/tabs/news.py`

- [ ] **Step 1: Implement news.py**

Create `dashboard/tabs/news.py`:

```python
import streamlit as st
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List

from src.database import get_session
from src.models import NewsItem
from src.collector.news_monitor import fetch_all_feeds, get_recent_news

_TAG_COLORS = {
    "soja": "🟡",
    "milho": "🟠",
    "café": "🟤",
    "cana": "🟢",
    "mercado": "📈",
    "clima": "🌧️",
    "tecnologia": "💡",
    "exportação": "🚢",
    "insumos": "🧪",
    "crédito": "💰",
    "venda": "🤝",
    "algodão": "🌿",
}

_ALL_TAGS = sorted(_TAG_COLORS.keys())


def _tag_badge(tag: str) -> str:
    icon = _TAG_COLORS.get(tag, "🔹")
    return f"{icon} {tag}"


def render():
    st.subheader("📰 Notícias do Agro")
    session: Session = get_session()

    try:
        col_refresh, col_count = st.columns([1, 3])

        with col_refresh:
            if st.button("🔄 Atualizar feeds", use_container_width=True):
                with st.spinner("Buscando notícias..."):
                    saved = fetch_all_feeds(session)
                    if saved > 0:
                        st.success(f"{saved} novas notícias salvas!")
                    else:
                        st.info("Nenhuma notícia nova encontrada.")
                    st.rerun()

        total = session.query(NewsItem).count()
        with col_count:
            st.caption(f"Total no banco: **{total} notícias**")

        st.divider()

        # Filters
        col_days, col_tags = st.columns([1, 2])
        with col_days:
            days = st.selectbox("Período", [1, 3, 7, 14, 30], index=2, format_func=lambda d: f"Últimos {d} dias")
        with col_tags:
            selected_tags = st.multiselect("Filtrar por tema", _ALL_TAGS)

        items = get_recent_news(session, days=days, tags=selected_tags if selected_tags else None)

        if not items:
            st.info("Nenhuma notícia encontrada para os filtros selecionados. Clique em 'Atualizar feeds'.")
            return

        st.write(f"**{len(items)} notícias encontradas**")

        for item in items:
            tags_display = " ".join(_tag_badge(t) for t in item.tags) if item.tags else ""
            age = datetime.now(timezone.utc) - item.published_at
            age_str = (
                f"{int(age.total_seconds() // 3600)}h atrás"
                if age < timedelta(days=1)
                else f"{age.days}d atrás"
            )

            with st.container():
                col_text, col_use = st.columns([4, 1])
                with col_text:
                    st.markdown(f"**{item.title}**")
                    if item.summary:
                        st.caption(item.summary[:200])
                    st.caption(f"{item.source.replace('_', ' ').title()} · {age_str} {tags_display}")
                with col_use:
                    if st.button("Usar", key=f"news_{item.id}", use_container_width=True):
                        st.session_state["strategy_news_context"] = item.title
                        st.session_state["active_tab"] = "criar"
                        st.success("Notícia selecionada! Vá à aba Criar Conteúdo.")
                st.divider()

    finally:
        session.close()
```

- [ ] **Step 2: Quick smoke test**

```bash
cd /Users/floakii/Claudio/agro-content
python -c "from dashboard.tabs.news import render; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add dashboard/tabs/news.py
git commit -m "feat: news monitor dashboard tab"
```

---

## Task 2: Calendar Tab

**Files:**
- Create: `dashboard/tabs/calendar_tab.py`

- [ ] **Step 1: Implement calendar_tab.py**

Create `dashboard/tabs/calendar_tab.py`:

```python
import streamlit as st
from sqlalchemy.orm import Session
from src.database import get_session
from src.models import ContentCalendar, GeneratedPost
from src.generator.calendar_generator import generate_weekly_calendar

_FUNNEL_LABELS = {
    "topo": "🔵 Topo",
    "meio": "🟡 Meio",
    "fundo": "🔴 Fundo",
}

_DAY_LABELS = {
    "segunda": "Segunda-feira",
    "terca": "Terça-feira",
    "quarta": "Quarta-feira",
    "quinta": "Quinta-feira",
    "sexta": "Sexta-feira",
    "sabado": "Sábado",
    "domingo": "Domingo",
}


def render():
    st.subheader("📅 Calendário Editorial")
    session: Session = get_session()

    try:
        latest_cal = (
            session.query(ContentCalendar)
            .order_by(ContentCalendar.generated_at.desc())
            .first()
        )

        col_info, col_btn = st.columns([3, 1])
        with col_info:
            if latest_cal:
                st.success(
                    f"Calendário gerado em {latest_cal.generated_at.strftime('%d/%m/%Y %H:%M')} "
                    f"— semana de {latest_cal.week_start.strftime('%d/%m/%Y')}"
                )
            else:
                st.info("Nenhum calendário gerado ainda. Clique em 'Gerar Calendário'.")
        with col_btn:
            if st.button("✨ Gerar Calendário", use_container_width=True):
                with st.spinner("Gerando plano semanal com IA... (pode levar 30-60s)"):
                    try:
                        latest_cal = generate_weekly_calendar(session)
                        st.success("Calendário gerado!")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Erro ao gerar calendário: {e}")

        if not latest_cal:
            return

        st.divider()
        st.write(f"**Semana de {latest_cal.week_start.strftime('%d/%m/%Y')}**")

        for entry in latest_cal.entries:
            funnel_label = _FUNNEL_LABELS.get(entry.get("funnel_stage", ""), entry.get("funnel_stage", ""))
            day_label = _DAY_LABELS.get(entry.get("day", ""), entry.get("day", "").title())
            format_label = entry.get("format", "").upper()

            with st.expander(f"{day_label} · {funnel_label} · {format_label}"):
                st.write(f"**Hook sugerido:**")
                st.info(entry.get("hook", "—"))

                variations = entry.get("hook_variations", {})
                if variations:
                    st.write("**Variações de hook:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption("Provocação")
                        st.write(variations.get("provocacao", "—"))
                    with col2:
                        st.caption("Dado")
                        st.write(variations.get("dado", "—"))
                    with col3:
                        st.caption("Pergunta")
                        st.write(variations.get("pergunta", "—"))

                st.write(f"**CTA:** {entry.get('cta', '—')}")

                gp_id = entry.get("generated_post_id")
                if gp_id:
                    gp = session.get(GeneratedPost, gp_id)
                    if gp and gp.caption:
                        st.write("**Legenda completa:**")
                        st.text_area(
                            "",
                            value=gp.caption,
                            height=200,
                            key=f"cal_caption_{gp_id}",
                        )
                        if gp.status == "generated":
                            col_save, col_discard = st.columns(2)
                            with col_save:
                                if st.button("✅ Aprovar", key=f"cal_save_{gp_id}", use_container_width=True):
                                    gp.status = "approved"
                                    session.commit()
                                    st.success("Post aprovado!")
                                    st.rerun()
                            with col_discard:
                                if st.button("🗑️ Descartar", key=f"cal_disc_{gp_id}", use_container_width=True):
                                    gp.status = "discarded"
                                    session.commit()
                                    st.rerun()
                        else:
                            st.caption(f"Status: {gp.status}")

    finally:
        session.close()
```

- [ ] **Step 2: Quick smoke test**

```bash
python -c "from dashboard.tabs.calendar_tab import render; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add dashboard/tabs/calendar_tab.py
git commit -m "feat: weekly editorial calendar dashboard tab"
```

---

## Task 3: Update Content Studio with Strategy Mode

The existing content_studio.py has only "Inspiração em post" mode (pick a competitor post → generate). We add a toggle at the top to switch between:
- **Modo Inspiração:** existing flow (unchanged)
- **Modo Estratégia:** pick funnel stage → generate via strategy_engine → show 3 hook variations with radio picker

**Files:**
- Modify: `dashboard/tabs/content_studio.py`

- [ ] **Step 1: Read current content_studio.py**

The file is at `dashboard/tabs/content_studio.py`. Its `render()` function currently has:
- Voice profile section (lines 51-70)
- Competitor posts list + generation (lines 74-156)
- Saved posts section (lines 158-177)

- [ ] **Step 2: Update imports at top of content_studio.py**

Replace the existing import block:

```python
import streamlit as st
from typing import Optional, List
from sqlalchemy.orm import Session
from src.database import get_session
from src.models import Profile, Post, PostAnalysis, ProfileVoice, GeneratedPost
from src.analyzer.voice_analyzer import analyze_voice
from src.generator.content_generator import generate_post
from src.generator.strategy_engine import generate_content_idea
```

- [ ] **Step 3: Add Strategy Mode UI**

After the voice section (after `if not voice: return` and the first `st.divider()`), add a mode toggle before the competitor posts section. Replace the line `# --- Seção: Posts dos concorrentes ---` and everything after it with this new implementation:

```python
        st.divider()

        # --- Mode toggle ---
        mode = st.radio(
            "Modo de geração",
            ["✨ Ideia de Mercado", "🔍 Inspiração em Post"],
            horizontal=True,
        )

        # ================================================================
        # STRATEGY MODE: AI Market Expert
        # ================================================================
        if mode == "✨ Ideia de Mercado":
            st.caption(
                "A IA analisa notícias recentes, contexto sazonal e lacunas dos concorrentes "
                "para gerar uma ideia original — sem depender de nenhum post específico."
            )

            funnel_stage = st.selectbox(
                "Etapa do funil",
                options=["topo", "meio", "fundo"],
                format_func=lambda s: {
                    "topo": "🔵 Topo — Alcance e consciência",
                    "meio": "🟡 Meio — Autoridade e relacionamento",
                    "fundo": "🔴 Fundo — Conversão para a Confraria",
                }[s],
            )

            news_context = st.session_state.pop("strategy_news_context", None)
            if news_context:
                st.info(f"Contexto de notícia selecionado: **{news_context}**")

            strategy_generated_id = st.session_state.get("strategy_generated_id")

            if st.button("✨ Gerar Ideia", use_container_width=True):
                with st.spinner("Consultando mercado e gerando conteúdo..."):
                    try:
                        gp = generate_content_idea(funnel_stage, session)
                        st.session_state["strategy_generated_id"] = gp.id
                        strategy_generated_id = gp.id
                    except Exception as e:
                        st.error(f"Erro: {e}")

            if strategy_generated_id:
                gp = session.get(GeneratedPost, strategy_generated_id)
                if gp and gp.status == "generated":
                    st.divider()
                    st.write(f"**Funil:** {gp.funnel_stage} · **Formato:** {gp.format or 'carousel'}")

                    # Hook variations picker
                    variations = gp.hook_variations or {}
                    if variations:
                        st.write("**Escolha o hook:**")
                        hook_choice = st.radio(
                            "",
                            options=["hook_principal", "provocacao", "dado", "pergunta"],
                            format_func=lambda k: {
                                "hook_principal": f"Principal: {gp.hook}",
                                "provocacao": f"Provocação: {variations.get('provocacao', '—')}",
                                "dado": f"Dado: {variations.get('dado', '—')}",
                                "pergunta": f"Pergunta: {variations.get('pergunta', '—')}",
                            }[k],
                            key=f"hook_radio_{gp.id}",
                        )
                        chosen_hook = {
                            "hook_principal": gp.hook,
                            "provocacao": variations.get("provocacao"),
                            "dado": variations.get("dado"),
                            "pergunta": variations.get("pergunta"),
                        }[hook_choice]
                        st.info(chosen_hook or "—")
                    else:
                        st.write("**Hook:**")
                        st.info(gp.hook or "—")

                    st.write("**Legenda:**")
                    st.text_area("", value=gp.caption or "", height=250, key=f"strategy_caption_{gp.id}")
                    st.write("**CTA:**")
                    st.success(gp.cta or "—")

                    col_save, col_discard = st.columns(2)
                    with col_save:
                        if st.button("✅ Salvar", key="strategy_save", use_container_width=True):
                            gp.status = "approved"
                            session.commit()
                            st.session_state.pop("strategy_generated_id", None)
                            st.success("Post salvo como aprovado!")
                            st.rerun()
                    with col_discard:
                        if st.button("🗑️ Descartar", key="strategy_discard", use_container_width=True):
                            gp.status = "discarded"
                            session.commit()
                            st.session_state.pop("strategy_generated_id", None)
                            st.rerun()

        # ================================================================
        # INSPIRATION MODE: Competitor post → generate
        # ================================================================
        else:
            competitor_posts = _get_competitor_posts(session)
            if not competitor_posts:
                st.info("Nenhum post de concorrente analisado ainda. Vá à aba Posts e clique em 'Analisar posts'.")
            else:
                profiles = sorted(set(p.profile.handle for p in competitor_posts))
                selected_profile = st.selectbox("Filtrar por perfil", ["Todos"] + profiles)

                if selected_profile != "Todos":
                    competitor_posts = [p for p in competitor_posts if p.profile.handle == selected_profile]

                st.write(f"**{len(competitor_posts)} posts disponíveis** — ordenados por viralidade")

                col_list, col_gen = st.columns([1, 2])

                with col_list:
                    for post in competitor_posts:
                        score = post.analysis.virality_score or 0
                        label = f"@{post.profile.handle} · {score:.0%} · {post.published_at.strftime('%d/%m')}"
                        if st.button(label, key=f"post_{post.id}", use_container_width=True):
                            st.session_state["selected_post_id"] = post.id
                            st.session_state.pop("generated_post_id", None)

                with col_gen:
                    selected_id = st.session_state.get("selected_post_id")
                    generated_id = st.session_state.get("generated_post_id")

                    if not selected_id:
                        st.info("← Selecione um post para gerar conteúdo.")
                    else:
                        selected_post = session.get(Post, selected_id)
                        if not selected_post:
                            st.warning("Post não encontrado. Selecione outro.")
                            st.session_state.pop("selected_post_id", None)
                            st.stop()
                        raw = selected_post.analysis.raw_analysis if selected_post.analysis else {}

                        st.write(f"**Inspiração:** @{selected_post.profile.handle}")
                        if raw.get("hook"):
                            st.caption(f"Hook original: {raw['hook']}")

                        col_gen_btn, col_regen_btn = st.columns(2)
                        with col_gen_btn:
                            gerar = st.button("✨ Gerar conteúdo", use_container_width=True)
                        with col_regen_btn:
                            regenerar = st.button(
                                "🔄 Regenerar", use_container_width=True, disabled=not generated_id
                            )

                        if gerar or regenerar:
                            approved = _get_approved_examples(session)
                            with st.spinner("Gerando legenda..."):
                                try:
                                    gp = generate_post(selected_post, voice, approved, session)
                                    st.session_state["generated_post_id"] = gp.id
                                    generated_id = gp.id
                                except Exception as e:
                                    st.error(f"Erro ao gerar: {e}")

                        if generated_id:
                            gp = session.get(GeneratedPost, generated_id)
                            if gp and gp.status == "generated":
                                st.divider()
                                st.write("**Hook:**")
                                st.info(gp.hook or "—")
                                st.write("**Legenda:**")
                                st.text_area(
                                    "", value=gp.caption or "", height=250, key=f"caption_{gp.id}"
                                )
                                st.write("**CTA:**")
                                st.success(gp.cta or "—")

                                col_save, col_discard = st.columns(2)
                                with col_save:
                                    if st.button("✅ Salvar", use_container_width=True):
                                        gp.status = "approved"
                                        session.commit()
                                        st.session_state.pop("generated_post_id", None)
                                        st.success("Post salvo como aprovado!")
                                        st.rerun()
                                with col_discard:
                                    if st.button("🗑️ Descartar", use_container_width=True):
                                        gp.status = "discarded"
                                        session.commit()
                                        st.session_state.pop("generated_post_id", None)
                                        st.rerun()

        # --- Seção: Posts Salvos ---
        st.divider()
        st.subheader("Meus Conteúdos Salvos")
        approved_posts = (
            session.query(GeneratedPost)
            .filter_by(status="approved")
            .order_by(GeneratedPost.created_at.desc())
            .all()
        )

        if not approved_posts:
            st.info("Nenhum post salvo ainda.")
        else:
            for gp in approved_posts:
                source_label = (
                    f"inspirado em @{gp.source_post.profile.handle}"
                    if gp.source_post_id and gp.source_post
                    else "gerado via Ideia de Mercado"
                )
                funnel_label = f" · {gp.funnel_stage}" if gp.funnel_stage else ""
                with st.expander(
                    f"Post de {gp.created_at.strftime('%d/%m/%Y')} · {source_label}{funnel_label}"
                ):
                    st.write(f"**Hook:** {gp.hook}")
                    st.text_area("Legenda", value=gp.caption or "", height=200, key=f"saved_{gp.id}")
                    st.write(f"**CTA:** {gp.cta}")
```

The complete `render()` function in `content_studio.py` should now be:
- Voice section (unchanged, lines 41-70)
- `st.divider()`
- Mode toggle
- Strategy Mode block
- Inspiration Mode block (existing logic, unchanged)
- Saved posts section (updated source_label)

- [ ] **Step 4: Smoke test**

```bash
python -c "from dashboard.tabs.content_studio import render; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add dashboard/tabs/content_studio.py
git commit -m "feat: add Strategy Mode to Content Studio (hook variations, funnel stage, market expert)"
```

---

## Task 4: Register tabs in app.py

**Files:**
- Modify: `dashboard/app.py`

- [ ] **Step 1: Read current app.py**

Read `dashboard/app.py` to see the current tab list and imports.

- [ ] **Step 2: Add imports**

Add these imports alongside existing tab imports:
```python
from dashboard.tabs import news as news_tab
from dashboard.tabs import calendar_tab
```

- [ ] **Step 3: Add tabs to tab list**

Find the `st.tabs([...])` call in `app.py`. Add `"📰 Notícias"` and `"📅 Calendário"` to the list and their corresponding `render()` calls in the `with tab_X:` blocks.

The final tab order should be:
1. 📊 Concorrentes
2. 📁 Posts
3. 📈 Relatório
4. 🎠 Carrossel
5. 🎤 Voz
6. ✍️ Criar Conteúdo
7. 📰 Notícias  ← new
8. 📅 Calendário ← new

- [ ] **Step 4: Smoke test**

```bash
python -c "from dashboard.app import *; print('OK')"
```

Expected: `OK` (no import errors)

- [ ] **Step 5: Commit**

```bash
git add dashboard/app.py
git commit -m "feat: register news and calendar tabs in dashboard"
```

---

## Task 5: Full test suite + push

- [ ] **Step 1: Run all tests**

```bash
cd /Users/floakii/Claudio/agro-content
python -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 2: Push to remote**

```bash
git push
```

Expected: Branch pushed. Railway auto-deploys. Dashboard at Railway URL should show all 8 tabs.

---

## Plan C Complete — Full Feature Delivered

After this plan, the system is a true agro content strategist:

- 📰 **Notícias:** 4 RSS sources monitored, filterable by theme and period
- 📅 **Calendário:** AI-generated 7-day editorial plan with funnel balance
- ✍️ **Criar Conteúdo:** Dual mode — competitor inspiration OR market expert idea — with 3 hook variations and funnel stage tagging
- 🎠 **Carrossel:** Slide-by-slide narrative analysis (available for any carousel post via `analyze_carousel()`)
- Gap analyzer available as backend intelligence for future iterations
