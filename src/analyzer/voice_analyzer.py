import json
import logging
from datetime import datetime, timezone
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import Profile, Post, ProfileVoice

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
