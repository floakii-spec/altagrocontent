import streamlit as st
from src.models import Post


def render_post_card(post: Post):
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(post.image_url, use_container_width=True)
        with col2:
            st.write(f"**@{post.profile.handle}** · {post.post_type.upper()} · {post.published_at.strftime('%d/%m/%Y')}")
            st.write(f"❤️ {post.likes}  💬 {post.comments}")
            if post.caption:
                st.caption(post.caption[:200] + ("..." if len(post.caption) > 200 else ""))
            if post.analysis:
                with st.expander("Ver análise"):
                    st.write(f"**Tema:** {post.analysis.visual_theme}")
                    st.write(f"**Formato:** {post.analysis.visual_format}")
                    st.write(f"**Tom:** {post.analysis.emotional_tone}")
                    st.write(f"**Gatilho:** {post.analysis.trigger}")
                    st.write(f"**Score de viralidade:** {post.analysis.virality_score:.2%}")
