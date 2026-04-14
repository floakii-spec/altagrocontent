import json
import logging
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import Profile, Post, ProfileVoice

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Você é um especialista em branding e linguagem para agronegócio.
Analise as legendas dos posts abaixo e retorne um JSON com o perfil de voz do perfil:
{
  "vocabulary": {"palavras_frequentes": ["<palavra>"]},
  "tone": "<descrição do tom predominante>",
  "dominant_themes": ["<tema>"],
  "competitor_comparison": {"<insight>": "<descrição>"}
}
Responda APENAS com o JSON."""


def generate_voice_profile(profile: Profile, session: Session) -> ProfileVoice:
    """Analisa os posts do perfil próprio e gera um perfil de voz atualizado."""
    posts = session.query(Post).filter_by(profile_id=profile.id).order_by(Post.published_at.desc()).limit(50).all()
    captions = [{"caption": p.caption, "hashtags": p.hashtags} for p in posts]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Posts do perfil @{profile.handle}:\n{json.dumps(captions, ensure_ascii=False)}"},
        ],
        max_tokens=800,
    )

    try:
        raw = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for voice profile of %s: %s", profile.handle, exc)
        raise

    voice = ProfileVoice(
        profile_id=profile.id,
        vocabulary=raw.get("vocabulary", {}),
        tone=raw.get("tone", ""),
        dominant_themes=raw.get("dominant_themes", []),
        competitor_comparison=raw.get("competitor_comparison", {}),
    )
    session.add(voice)
    session.commit()
    logger.info("Voice profile generated for @%s", profile.handle)
    return voice
