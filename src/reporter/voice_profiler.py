import json
import logging
from openai import OpenAI
from sqlalchemy.orm import Session, joinedload
from src.config import OPENAI_API_KEY
from src.models import Profile, Post, PostIntelligence, ProfileVoice

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Você é um especialista em branding e linguagem para agronegócio.
Analise os posts abaixo. Cada post contém:
- "caption": legenda do Instagram
- "hashtags": tags usadas
- "core_argument": tese central do card visual (quando disponível)
- "technical_claims": afirmações técnicas com dados do card visual
- "data_points": números e percentuais extraídos do card visual

Use tudo isso para construir o perfil de voz. Retorne um JSON:
{
  "vocabulary": {"palavras_frequentes": ["<palavra>"]},
  "tone": "<descrição do tom predominante em 1-2 frases>",
  "dominant_themes": ["<tema>"],
  "competitor_comparison": {"<insight>": "<descrição>"},
  "voice_summary": "<resumo do estilo de comunicação em 3-4 frases diretas, descrevendo como a pessoa se comunica, qual linguagem usa e o que diferencia sua voz>"
}
Responda APENAS com o JSON."""


def generate_voice_profile(profile: Profile, session: Session) -> ProfileVoice:
    posts = (
        session.query(Post)
        .filter_by(profile_id=profile.id)
        .options(joinedload(Post.intelligence))
        .order_by(Post.published_at.desc())
        .limit(50)
        .all()
    )

    payload = []
    for p in posts:
        entry = {"caption": p.caption or "", "hashtags": p.hashtags or []}
        if p.intelligence:
            if p.intelligence.core_argument:
                entry["core_argument"] = p.intelligence.core_argument
            if p.intelligence.technical_claims:
                entry["technical_claims"] = p.intelligence.technical_claims
            if p.intelligence.data_points:
                entry["data_points"] = p.intelligence.data_points
        payload.append(entry)

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Posts do perfil @{profile.handle}:\n{json.dumps(payload, ensure_ascii=False)}"},
        ],
        max_tokens=800,
    )

    raw_text = response.choices[0].message.content or ""
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```", 2)[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.rstrip("`").strip()

    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for voice profile of %s: %s", profile.handle, exc)
        raise

    voice = ProfileVoice(
        profile_id=profile.id,
        vocabulary=raw.get("vocabulary", {}),
        tone=raw.get("tone", ""),
        dominant_themes=raw.get("dominant_themes", []),
        competitor_comparison=raw.get("competitor_comparison", {}),
        voice_summary=raw.get("voice_summary", ""),
    )
    session.add(voice)
    session.commit()
    logger.info("Voice profile generated for @%s", profile.handle)
    return voice
