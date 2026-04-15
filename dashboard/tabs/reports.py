import streamlit as st
from sqlalchemy.orm import Session
from src.database import get_session
from src.models import WeeklyReport


def render():
    st.subheader("Relatório Semanal")
    session: Session = get_session()

    try:
        reports = session.query(WeeklyReport).order_by(WeeklyReport.period_start.desc()).all()

        if not reports:
            st.info("Nenhum relatório gerado ainda. Execute a coleta e gere o primeiro relatório.")
            return

        report_options = {
            f"{r.period_start.strftime('%d/%m/%Y')} – {r.period_end.strftime('%d/%m/%Y')}": r
            for r in reports
        }
        selected_label = st.selectbox("Selecionar semana", list(report_options.keys()))
        report: WeeklyReport = report_options[selected_label]

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Formatos mais virais**")
            for fmt, count in (report.top_formats or {}).items():
                st.write(f"- {fmt}: {count} posts")

            st.write("**Temas em alta**")
            for theme, count in (report.top_themes or {}).items():
                st.write(f"- {theme}: {count} posts")

        with col2:
            st.write("**Hashtags recorrentes**")
            st.write(", ".join(f"#{h}" for h in (report.top_hashtags or [])))

            st.write("**Padrões de linguagem**")
            for k, v in (report.language_patterns or {}).items():
                st.write(f"- {k}: {v}")

        st.divider()
        st.write("**Relatório completo**")
        st.markdown(report.report_text or "_Sem texto disponível._")
    finally:
        session.close()
