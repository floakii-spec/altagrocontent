import streamlit as st
from sqlalchemy.orm import Session
from src.database import get_session
from src.models import Profile, Post


def render():
    st.subheader("Perfis Monitorados")
    session: Session = get_session()

    try:
        profiles = session.query(Profile).filter_by(active=True).order_by(Profile.handle).all()

        if profiles:
            for profile in profiles:
                post_count = session.query(Post).filter_by(profile_id=profile.id).count()
                last_post = session.query(Post).filter_by(profile_id=profile.id).order_by(Post.collected_at.desc()).first()
                last_sync = last_post.collected_at.strftime("%d/%m/%Y %H:%M") if last_post else "Nunca"

                col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
                col1.write(f"**@{profile.handle}**")
                col2.write(f"{'Meu perfil' if profile.type == 'own' else 'Concorrente'}")
                col3.write(f"{post_count} posts · Último sync: {last_sync}")
                if col4.button("Remover", key=f"remove_{profile.id}"):
                    profile.active = False
                    session.commit()
                    st.rerun()
        else:
            st.info("Nenhum perfil cadastrado ainda.")

        st.divider()
        st.subheader("Adicionar Perfil")
        with st.form("add_profile_form"):
            handle = st.text_input("Username do Instagram (sem @)")
            profile_type = st.selectbox("Tipo", ["competitor", "own"], format_func=lambda x: "Concorrente" if x == "competitor" else "Meu perfil")
            submitted = st.form_submit_button("Adicionar")
            if submitted and handle:
                existing = session.query(Profile).filter_by(handle=handle).first()
                if existing:
                    existing.active = True
                    session.commit()
                    st.success(f"@{handle} reativado.")
                else:
                    session.add(Profile(handle=handle.strip().lstrip("@"), type=profile_type, niche="agronegócio"))
                    session.commit()
                    st.success(f"@{handle} adicionado com sucesso.")
                st.rerun()
    finally:
        session.close()
