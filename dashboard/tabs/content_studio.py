import streamlit as st
from typing import Optional, List
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


def _get_approved_examples(session: Session, limit: int = 3) -> List[GeneratedPost]:
    return (
        session.query(GeneratedPost)
        .filter_by(status="approved")
        .order_by(GeneratedPost.created_at.desc())
        .limit(limit)
        .all()
    )


def _get_competitor_posts(session: Session) -> List[Post]:
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
