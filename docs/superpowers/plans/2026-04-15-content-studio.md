# Content Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar aba "Criar Conteúdo" ao dashboard que gera legendas para Instagram adaptadas à voz do usuário (`@nathanlimagro`), usando posts de concorrentes como inspiração e posts aprovados como auto-refinamento.

**Architecture:** Quatro camadas: (1) migração de banco para `generated_posts` + `voice_summary` na `profile_voice`, (2) `voice_analyzer.py` que extrai perfil de voz dos posts do usuário via GPT-4o, (3) `content_generator.py` que gera legenda combinando análise do concorrente + voz + exemplos aprovados, (4) aba Streamlit `content_studio.py` que orquestra tudo com UI interativa.

**Tech Stack:** Python 3.9, SQLAlchemy 2.0, Alembic, Streamlit 1.35, OpenAI GPT-4o, PostgreSQL

---

## File Structure

| Ação | Arquivo | Responsabilidade |
|---|---|---|
| Criar | `alembic/versions/002_content_studio.py` | Migração: tabela `generated_posts` + coluna `voice_summary` em `profile_voice` |
| Modificar | `src/models.py` | Adicionar modelo `GeneratedPost` + campo `voice_summary` em `ProfileVoice` |
| Criar | `src/analyzer/voice_analyzer.py` | Extrai perfil de voz dos posts do usuário via GPT-4o |
| Criar | `src/generator/__init__.py` | Arquivo vazio |
| Criar | `src/generator/content_generator.py` | Gera legenda combinando contextos |
| Criar | `dashboard/tabs/content_studio.py` | Aba "Criar Conteúdo" no Streamlit |
| Modificar | `dashboard/app.py` | Adicionar aba content_studio |

---

## Task 1: Migração de banco e modelos

**Files:**
- Modify: `src/models.py`
- Create: `alembic/versions/002_content_studio.py`

- [ ] **Step 1: Adicionar `GeneratedPost` e `voice_summary` em `src/models.py`**

Abrir `src/models.py` e adicionar ao final da classe `ProfileVoice` o campo `voice_summary`, e criar a nova classe `GeneratedPost`:

```python
# Em ProfileVoice, adicionar após competitor_comparison:
voice_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

# Após a classe ProfileVoice, adicionar:
class GeneratedPost(Base):
    __tablename__ = "generated_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False)
    hook: Mapped[Optional[str]] = mapped_column(Text)
    caption: Mapped[Optional[str]] = mapped_column(Text)
    cta: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="generated")  # generated | approved | discarded
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    source_post: Mapped["Post"] = relationship()
```

- [ ] **Step 2: Criar migration `alembic/versions/002_content_studio.py`**

```python
"""content_studio

Revision ID: 002
Revises: a1b2c3d4e5f6
Create Date: 2026-04-15 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("profile_voice", sa.Column("voice_summary", sa.Text(), nullable=True))

    op.create_table(
        "generated_posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_post_id", sa.Integer(), nullable=False),
        sa.Column("hook", sa.Text(), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("cta", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_post_id"], ["posts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("generated_posts")
    op.drop_column("profile_voice", "voice_summary")
```

- [ ] **Step 3: Rodar migration localmente para verificar**

```bash
cd /Users/floakii/Claudio/agro-content
alembic upgrade head
```

Esperado: `Running upgrade a1b2c3d4e5f6 -> 002, content_studio`

- [ ] **Step 4: Commit**

```bash
git add src/models.py alembic/versions/002_content_studio.py
git commit -m "feat: add GeneratedPost model and voice_summary migration"
```

---

## Task 2: Voice Analyzer

**Files:**
- Create: `src/analyzer/voice_analyzer.py`

- [ ] **Step 1: Criar `src/analyzer/voice_analyzer.py`**

```python
import json
import logging
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import Profile, Post, ProfileVoice
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

VOICE_PROMPT = """Você é um especialista em análise de linguagem e comunicação para Instagram no agronegócio.

Analise os posts abaixo do perfil @{handle} e extraia o perfil de voz desta pessoa.

POSTS:
{posts_text}

Retorne JSON com exatamente estes campos:
{{
  "tone": "<tom predominante: ex. direto e provocador, técnico e acessível, inspirador e motivacional>",
  "dominant_themes": ["<tema1>", "<tema2>", "<tema3>"],
  "vocabulary": {{
    "palavras_frequentes": ["<palavra1>", "<palavra2>", "<palavra3>", "<palavra4>", "<palavra5>"],
    "expressoes_caracteristicas": ["<expressao1>", "<expressao2>"]
  }},
  "competitor_comparison": {{
    "diferencial": "<o que diferencia este perfil dos concorrentes>",
    "estilo_de_hook": "<como esta pessoa tipicamente abre seus posts>",
    "estilo_de_cta": "<como esta pessoa tipicamente fecha seus posts>"
  }},
  "voice_summary": "<parágrafo de 3-5 frases descrevendo a voz desta pessoa de forma que um ghostwriter possa replicá-la: tom, vocabulário, estrutura, o que evitar>"
}}
Responda APENAS com o JSON, sem markdown."""


def analyze_voice(profile: Profile, session: Session) -> ProfileVoice:
    """
    Analisa os posts do perfil próprio e gera/atualiza o perfil de voz.
    """
    posts = (
        session.query(Post)
        .filter_by(profile_id=profile.id)
        .order_by(Post.published_at.desc())
        .limit(15)
        .all()
    )

    if not posts:
        raise ValueError(f"Perfil @{profile.handle} não tem posts coletados.")

    posts_text = "\n\n".join([
        f"Post {i+1}:\n{p.caption or '(sem legenda)'}"
        for i, p in enumerate(posts)
        if p.caption
    ])

    if not posts_text.strip():
        raise ValueError(f"Perfil @{profile.handle} não tem legendas para analisar.")

    prompt = VOICE_PROMPT.format(handle=profile.handle, posts_text=posts_text)

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
    )

    content = response.choices[0].message.content or ""
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    raw = json.loads(content)

    voice = ProfileVoice(
        profile_id=profile.id,
        tone=raw.get("tone"),
        dominant_themes=raw.get("dominant_themes", []),
        vocabulary=raw.get("vocabulary", {}),
        competitor_comparison=raw.get("competitor_comparison", {}),
        voice_summary=raw.get("voice_summary"),
        generated_at=datetime.now(timezone.utc),
    )
    session.add(voice)
    session.commit()
    logger.info("Voice profile generated for @%s", profile.handle)
    return voice
```

- [ ] **Step 2: Testar manualmente que o módulo importa sem erro**

```bash
cd /Users/floakii/Claudio/agro-content
python3 -c "from src.analyzer.voice_analyzer import analyze_voice; print('OK')"
```

Esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/analyzer/voice_analyzer.py
git commit -m "feat: add voice analyzer for own profile"
```

---

## Task 3: Content Generator

**Files:**
- Create: `src/generator/__init__.py`
- Create: `src/generator/content_generator.py`

- [ ] **Step 1: Criar `src/generator/__init__.py`**

Arquivo vazio:
```python
```

- [ ] **Step 2: Criar `src/generator/content_generator.py`**

```python
import json
import logging
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import Post, ProfileVoice, GeneratedPost
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

CONFRARIA_CONTEXT = """
SOBRE O AUTOR:
- Engenheiro Agrônomo com 15+ anos em vendas, varejo e cooperativismo no agronegócio brasileiro
- Fundador da Confraria de Vendas no Agro: comunidade para quem quer dominar o comercial no campo
- A Confraria inclui: curso Agroroot completo + encontros ao vivo quinzenais com especialistas do agro
- Público-alvo: agrônomos, consultores e profissionais de vendas no agro que querem crescer na carreira comercial
"""

GENERATION_PROMPT = """Você é um ghostwriter especializado em conteúdo para Instagram no agronegócio brasileiro.

{confraria_context}

ESTILO DE VOZ DO AUTOR:
{voice_summary}

{approved_section}

POST DO CONCORRENTE PARA INSPIRAÇÃO:
- Perfil: @{competitor_handle}
- Hook original: {hook}
- Mensagem central: {main_message}
- Dor abordada: {problem_addressed}
- Estrutura narrativa: {narrative_structure}
- Gatilho usado: {trigger}
- CTA original: {call_to_action}
- Score de viralidade: {virality_score:.0%}

Crie um post para o Instagram do autor adaptando a estrutura e abordagem acima para a sua voz e realidade. Use a voz do autor fielmente. O post deve falar para agrônomos e profissionais de vendas no agro.

Retorne JSON:
{{
  "hook": "<primeira linha que prende — máximo 1 frase impactante>",
  "caption": "<legenda completa com quebras de linha, máximo 300 palavras, sem hashtags>",
  "cta": "<call-to-action direto para a Confraria>"
}}
Responda APENAS com o JSON, sem markdown."""


def _build_approved_section(approved: list[GeneratedPost]) -> str:
    if not approved:
        return ""
    examples = "\n\n".join([
        f"Exemplo aprovado {i+1}:\nHook: {p.hook}\nLegenda: {p.caption[:200]}..."
        for i, p in enumerate(approved)
    ])
    return f"EXEMPLOS DE POSTS QUE O AUTOR APROVOU (replique o estilo):\n{examples}\n"


def generate_post(
    source_post: Post,
    voice: ProfileVoice,
    approved_examples: list[GeneratedPost],
    session: Session,
) -> GeneratedPost:
    """
    Gera um post adaptado com base no post do concorrente, voz do autor e exemplos aprovados.
    """
    raw_analysis = source_post.analysis.raw_analysis if source_post.analysis else {}
    virality = source_post.analysis.virality_score or 0.0 if source_post.analysis else 0.0

    prompt = GENERATION_PROMPT.format(
        confraria_context=CONFRARIA_CONTEXT,
        voice_summary=voice.voice_summary or "Tom direto, experiente, próximo do produtor rural.",
        approved_section=_build_approved_section(approved_examples),
        competitor_handle=source_post.profile.handle,
        hook=raw_analysis.get("hook", "—"),
        main_message=raw_analysis.get("main_message", "—"),
        problem_addressed=raw_analysis.get("problem_addressed", "—"),
        narrative_structure=raw_analysis.get("narrative_structure", "—"),
        trigger=raw_analysis.get("trigger", source_post.analysis.trigger if source_post.analysis else "—"),
        call_to_action=raw_analysis.get("call_to_action", "—"),
        virality_score=virality,
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
    )

    content = response.choices[0].message.content or ""
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    result = json.loads(content)

    generated = GeneratedPost(
        source_post_id=source_post.id,
        hook=result.get("hook"),
        caption=result.get("caption"),
        cta=result.get("cta"),
        status="generated",
        created_at=datetime.now(timezone.utc),
    )
    session.add(generated)
    session.commit()
    logger.info("Generated post from source post %s", source_post.id)
    return generated
```

- [ ] **Step 3: Testar que o módulo importa sem erro**

```bash
python3 -c "from src.generator.content_generator import generate_post; print('OK')"
```

Esperado: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/generator/__init__.py src/generator/content_generator.py
git commit -m "feat: add content generator with voice + approved examples"
```

---

## Task 4: Aba Content Studio no Dashboard

**Files:**
- Create: `dashboard/tabs/content_studio.py`
- Modify: `dashboard/app.py`

- [ ] **Step 1: Criar `dashboard/tabs/content_studio.py`**

```python
import streamlit as st
from typing import Optional
from sqlalchemy.orm import Session
from src.database import get_session
from src.models import Profile, Post, PostAnalysis, ProfileVoice, GeneratedPost
from src.analyzer.voice_analyzer import analyze_voice
from src.generator.content_generator import generate_post


def _get_voice(session: Session, own_profile: Profile) -> Optional[ProfileVoice]:
    return (
        session.query(ProfileVoice)
        .filter_by(profile_id=own_profile.id)
        .order_by(ProfileVoice.generated_at.desc())
        .first()
    )


def _get_approved_examples(session: Session, limit: int = 3) -> list[GeneratedPost]:
    return (
        session.query(GeneratedPost)
        .filter_by(status="approved")
        .order_by(GeneratedPost.created_at.desc())
        .limit(limit)
        .all()
    )


def _get_competitor_posts(session: Session) -> list[Post]:
    return (
        session.query(Post)
        .join(Post.profile)
        .join(Post.analysis)
        .filter(Profile.type == "competitor")
        .order_by(PostAnalysis.virality_score.desc())
        .limit(50)
        .all()
    )


def render():
    st.subheader("Criar Conteúdo")
    session: Session = get_session()

    try:
        own_profile = session.query(Profile).filter_by(type="own", active=True).first()
        if not own_profile:
            st.warning("Adicione seu perfil (@nathanlimagro) na aba Concorrentes com tipo 'Meu perfil'.")
            return

        # --- Seção: Perfil de Voz ---
        voice = _get_voice(session, own_profile)
        col_voice, col_btn = st.columns([3, 1])
        with col_voice:
            if voice:
                st.success(f"Perfil de voz ativo · Última atualização: {voice.generated_at.strftime('%d/%m/%Y')}")
            else:
                st.warning("Perfil de voz não gerado ainda. Clique em 'Gerar Perfil de Voz'.")
        with col_btn:
            if st.button("🎙️ Gerar Perfil de Voz", use_container_width=True):
                with st.spinner("Analisando seus posts..."):
                    try:
                        voice = analyze_voice(own_profile, session)
                        st.success("Perfil de voz gerado!")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

        if not voice:
            return

        st.divider()

        # --- Seção: Posts dos concorrentes ---
        competitor_posts = _get_competitor_posts(session)
        if not competitor_posts:
            st.info("Nenhum post de concorrente analisado ainda. Vá à aba Posts e clique em 'Analisar posts'.")
            return

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
                raw = selected_post.analysis.raw_analysis if selected_post.analysis else {}

                st.write(f"**Inspiração:** @{selected_post.profile.handle}")
                if raw.get("hook"):
                    st.caption(f"Hook original: {raw['hook']}")

                col_gen_btn, col_regen_btn = st.columns(2)
                with col_gen_btn:
                    gerar = st.button("✨ Gerar conteúdo", use_container_width=True)
                with col_regen_btn:
                    regenerar = st.button("🔄 Regenerar", use_container_width=True, disabled=not generated_id)

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
                        st.text_area("", value=gp.caption or "", height=250, key=f"caption_{gp.id}")
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
                with st.expander(f"Post de {gp.created_at.strftime('%d/%m/%Y')} · inspirado em @{gp.source_post.profile.handle}"):
                    st.write(f"**Hook:** {gp.hook}")
                    st.text_area("Legenda", value=gp.caption or "", height=200, key=f"saved_{gp.id}")
                    st.write(f"**CTA:** {gp.cta}")
    finally:
        session.close()
```

- [ ] **Step 2: Adicionar aba em `dashboard/app.py`**

Substituir o conteúdo de `dashboard/app.py`:

```python
import streamlit as st
from dashboard.tabs import competitors, posts, reports, voice, carousel, content_studio

st.set_page_config(page_title="Agro Intel", layout="wide")
st.title("Agro Intel — Inteligência Competitiva Instagram")

TABS = {
    "concorrentes": "📊 Concorrentes",
    "posts": "🖼️ Posts",
    "criar": "✍️ Criar Conteúdo",
    "relatorios": "📋 Relatório Semanal",
    "voz": "🎙️ Meu Perfil de Voz",
    "carrossel": "✨ Gerador de Carrossel",
}

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "concorrentes"

cols = st.columns(len(TABS))
for col, (key, label) in zip(cols, TABS.items()):
    if col.button(label, use_container_width=True):
        st.session_state.active_tab = key

st.divider()

active = st.session_state.active_tab
if active == "concorrentes":
    competitors.render()
elif active == "posts":
    posts.render()
elif active == "criar":
    content_studio.render()
elif active == "relatorios":
    reports.render()
elif active == "voz":
    voice.render()
elif active == "carrossel":
    carousel.render()
```

- [ ] **Step 3: Verificar que o dashboard inicia sem erro**

```bash
cd /Users/floakii/Claudio/agro-content
streamlit run dashboard/app.py --server.port=8502
```

Abrir `http://localhost:8502` — verificar que a aba "✍️ Criar Conteúdo" aparece e carrega sem erro de importação.

- [ ] **Step 4: Commit**

```bash
git add dashboard/tabs/content_studio.py dashboard/app.py
git commit -m "feat: add Content Studio tab with voice + generation + approval flow"
```

---

## Task 5: Garantir que `@nathanlimagro` está cadastrado como perfil próprio

**Files:**
- Nenhum arquivo novo — verificação via dashboard

- [ ] **Step 1: Verificar no banco se o perfil existe**

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
from src.database import get_session
from src.models import Profile
s = get_session()
p = s.query(Profile).filter_by(handle='nathanlimagro').first()
print(p.type if p else 'NAO ENCONTRADO')
s.close()
"
```

- [ ] **Step 2: Se não existir ou tipo errado, inserir via Python**

Se o resultado for `NAO ENCONTRADO` ou `competitor`, rodar:

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
from src.database import get_session
from src.models import Profile
s = get_session()
existing = s.query(Profile).filter_by(handle='nathanlimagro').first()
if existing:
    existing.type = 'own'
    print('Tipo atualizado para own')
else:
    from datetime import datetime, timezone
    p = Profile(handle='nathanlimagro', type='own', active=True, created_at=datetime.now(timezone.utc))
    s.add(p)
    print('Perfil criado')
s.commit()
s.close()
"
```

- [ ] **Step 3: Coletar posts do `@nathanlimagro` via script local**

```bash
python3 scripts/sync_local.py
```

O script coleta todos os perfis ativos, incluindo `@nathanlimagro`. Verificar que aparece `X novos posts salvos` para esse perfil.

- [ ] **Step 4: No dashboard, gerar o Perfil de Voz**

Abrir `http://localhost:8502`, ir em "✍️ Criar Conteúdo", clicar em **🎙️ Gerar Perfil de Voz**.

Esperado: mensagem "Perfil de voz gerado!" em verde.
