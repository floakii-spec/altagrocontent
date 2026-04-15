import streamlit as st
from sqlalchemy.orm import Session
from src.database import get_session
from src.models import Carousel
from src.carousel.generator import generate_carousel


def render():
    st.subheader("Gerador de Carrossel")
    session: Session = get_session()

    try:
        with st.form("carousel_form"):
            theme = st.text_area("Qual é o tema ou pauta do carrossel?", placeholder="Ex: 5 técnicas de manejo do solo para aumentar produtividade")
            submitted = st.form_submit_button("✨ Gerar Carrossel")

        if submitted and theme.strip():
            with st.spinner("Gerando carrossel com base nos dados dos concorrentes e na sua voz..."):
                carousel = generate_carousel(theme=theme.strip(), session=session)
            st.success("Carrossel gerado!")
            _render_carousel(carousel)

        st.divider()
        st.subheader("Histórico de Carrosséis")
        past = session.query(Carousel).order_by(Carousel.generated_at.desc()).limit(10).all()
        if not past:
            st.info("Nenhum carrossel gerado ainda.")
        else:
            for c in past:
                with st.expander(f"📱 {c.theme[:60]} — {c.generated_at.strftime('%d/%m/%Y %H:%M')}"):
                    _render_carousel(c)
    finally:
        session.close()


def _render_carousel(carousel: Carousel):
    for slide in carousel.slides:
        with st.container(border=True):
            st.write(f"**Slide {slide.get('slide_number', '?')}: {slide.get('title', '')}**")
            st.write(slide.get("copy", ""))
            if slide.get("cta"):
                st.success(f"CTA: {slide['cta']}")
