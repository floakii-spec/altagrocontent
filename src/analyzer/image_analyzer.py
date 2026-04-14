import json
import logging
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import Post, PostAnalysis
from src.analyzer.virality import calculate_virality_score

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Você é um especialista em marketing digital para agronegócio brasileiro.
Analise a imagem e legenda do post e retorne um JSON com exatamente estes campos:
{
  "visual_theme": "<maquinário|insumo|campo|pessoa|dado|outro>",
  "visual_format": "<infográfico|foto real|montagem|outro>",
  "emotional_tone": "<inspirador|técnico|humorístico|urgente|educativo|outro>",
  "trigger": "<autoridade|escassez|pertencimento|resultado|outro>",
  "summary": "<resumo em 1 frase do que torna este post relevante para o público do agro>"
}
Responda APENAS com o JSON, sem markdown."""


def analyze_post(post: Post, session: Session) -> PostAnalysis:
    """
    Analisa um post com GPT-4o Vision. Se já analisado, retorna análise existente.
    """
    existing = session.query(PostAnalysis).filter_by(post_id=post.id).first()
    if existing:
        return existing

    follower_count = post.profile.follower_count or 1

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": post.image_url},
                    },
                    {
                        "type": "text",
                        "text": f"Legenda: {post.caption}\nHashtags: {', '.join(post.hashtags)}",
                    },
                ],
            },
        ],
        max_tokens=300,
    )

    raw = json.loads(response.choices[0].message.content)
    score = calculate_virality_score(
        likes=post.likes,
        comments=post.comments,
        follower_count=follower_count,
    )

    analysis = PostAnalysis(
        post_id=post.id,
        visual_theme=raw.get("visual_theme"),
        visual_format=raw.get("visual_format"),
        emotional_tone=raw.get("emotional_tone"),
        trigger=raw.get("trigger"),
        virality_score=score,
        raw_analysis=raw,
    )
    session.add(analysis)
    session.commit()
    return analysis
