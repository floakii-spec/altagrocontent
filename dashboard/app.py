import streamlit as st
from dashboard.tabs import competitors, posts, reports, voice, carousel

st.set_page_config(page_title="Agro Intel", layout="wide")
st.title("Agro Intel — Inteligência Competitiva Instagram")

TABS = {
    "concorrentes": "📊 Concorrentes",
    "posts": "🖼️ Posts",
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
elif active == "relatorios":
    reports.render()
elif active == "voz":
    voice.render()
elif active == "carrossel":
    carousel.render()
