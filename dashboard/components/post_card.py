import streamlit as st
from src.models import Post


def render_post_card(post: Post):
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(post.image_url, use_column_width=True)
        with col2:
            st.write(f"**@{post.profile.handle}** · {post.post_type.upper()} · {post.published_at.strftime('%d/%m/%Y')}")
            st.write(f"❤️ {post.likes}  💬 {post.comments}")
            if post.caption:
                st.caption(post.caption[:200] + ("..." if len(post.caption) > 200 else ""))
            if post.analysis:
                score = post.analysis.virality_score
                st.write(f"**Score de viralidade:** {score:.2%}" if score is not None else "**Score de viralidade:** —")
                with st.expander("Ver análise completa"):
                    raw = post.analysis.raw_analysis or {}
                    st.write(f"**Tema visual:** {post.analysis.visual_theme} · **Formato:** {post.analysis.visual_format} · **Tom:** {post.analysis.emotional_tone} · **Gatilho:** {post.analysis.trigger}")
                    if raw.get("hook"):
                        st.markdown(f"**Hook:** {raw['hook']}")
                    if raw.get("main_message"):
                        st.markdown(f"**Mensagem central:** {raw['main_message']}")
                    if raw.get("problem_addressed"):
                        st.markdown(f"**Dor abordada:** {raw['problem_addressed']}")
                    if raw.get("solution_presented"):
                        st.markdown(f"**Solução apresentada:** {raw['solution_presented']}")
                    if raw.get("data_and_numbers"):
                        st.markdown(f"**Dados/números:** {raw['data_and_numbers']}")
                    if raw.get("narrative_structure"):
                        st.markdown(f"**Estrutura narrativa:** {raw['narrative_structure']}")
                    if raw.get("target_within_agro"):
                        st.markdown(f"**Público-alvo:** {raw['target_within_agro']} · **Pilar:** {raw.get('content_pillar', '—')}")
                    if raw.get("call_to_action"):
                        st.markdown(f"**CTA:** {raw['call_to_action']}")
                    if raw.get("replication_insights"):
                        st.info(f"💡 {raw['replication_insights']}")
