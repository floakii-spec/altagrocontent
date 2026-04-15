import streamlit as st
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session, joinedload
from src.database import get_session
from src.models import Profile, Post, PostAnalysis
from dashboard.components.post_card import render_post_card


def render():
    st.subheader("Feed de Posts")
    session: Session = get_session()

    try:
        profiles = session.query(Profile).filter_by(active=True).all()
        profile_options = {"Todos": None} | {f"@{p.handle}": p.id for p in profiles}

        col1, col2, col3, col4 = st.columns(4)
        selected_profile = col1.selectbox("Perfil", list(profile_options.keys()))
        period = col2.selectbox("Período", ["Últimos 7 dias", "Últimos 30 dias", "Últimos 6 meses"])
        post_type = col3.selectbox("Tipo", ["Todos", "feed", "reel", "carousel"])
        min_score = col4.slider("Score mínimo de viralidade", 0.0, 1.0, 0.0, step=0.01)

        period_map = {"Últimos 7 dias": 7, "Últimos 30 dias": 30, "Últimos 6 meses": 180}
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_map[period])

        query = (
            session.query(Post)
            .options(joinedload(Post.profile), joinedload(Post.analysis))
            .filter(Post.published_at >= cutoff)
        )
        if profile_options[selected_profile]:
            query = query.filter(Post.profile_id == profile_options[selected_profile])
        if post_type != "Todos":
            query = query.filter(Post.post_type == post_type)
        if min_score > 0:
            query = query.join(PostAnalysis).filter(PostAnalysis.virality_score >= min_score)

        all_posts = query.order_by(Post.published_at.desc()).limit(50).all()

        st.write(f"{len(all_posts)} posts encontrados")
        for post in all_posts:
            render_post_card(post)
    finally:
        session.close()
