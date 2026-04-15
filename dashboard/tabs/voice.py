import streamlit as st
from sqlalchemy.orm import Session
from src.database import get_session
from src.models import Profile, ProfileVoice


def render():
    st.subheader("Meu Perfil de Voz")
    session: Session = get_session()

    try:
        own_profile = session.query(Profile).filter_by(type="own", active=True).first()
        if not own_profile:
            st.warning("Nenhum perfil próprio cadastrado. Adicione seu perfil na aba Concorrentes com o tipo 'Meu perfil'.")
            return

        voice = (
            session.query(ProfileVoice)
            .filter_by(profile_id=own_profile.id)
            .order_by(ProfileVoice.generated_at.desc())
            .first()
        )

        if not voice:
            st.info("Perfil de voz ainda não gerado.")
            return

        st.write(f"_Última atualização: {voice.generated_at.strftime('%d/%m/%Y às %H:%M')}_")
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Tom predominante**")
            st.info(voice.tone or "—")

            st.write("**Temas dominantes**")
            for theme in (voice.dominant_themes or []):
                st.write(f"- {theme}")

        with col2:
            st.write("**Vocabulário característico**")
            vocab = voice.vocabulary or {}
            words = vocab.get("palavras_frequentes", [])
            if words:
                st.write(", ".join(words))

            st.write("**Diferencial vs concorrentes**")
            for k, v in (voice.competitor_comparison or {}).items():
                st.write(f"- **{k}:** {v}")
    finally:
        session.close()
