import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

from src.generator.content_generator import generate_post
from src.models import ArgumentBank, Base, Post, PostAnalysis, PostIntelligence, Profile, ProfileVoice


@pytest.fixture
def session_with_generation_context():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as session:
        competitor = Profile(handle="concorrente_agro", type="competitor", follower_count=15000)
        own = Profile(handle="nathanlimagro", type="own", follower_count=12000)
        session.add_all([competitor, own])
        session.flush()

        post = Post(
            profile_id=competitor.id,
            instagram_id="COMP-1",
            image_url="https://example.com/post.jpg",
            caption="Post original com dados sobre produtividade, margem e pressão de custo.",
            hashtags=["soja", "mercado"],
            likes=800,
            comments=45,
            post_type="feed",
            published_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
        )
        session.add(post)
        session.flush()

        analysis = PostAnalysis(
            post_id=post.id,
            trigger="resultado",
            virality_score=0.83,
            raw_analysis={
                "hook": "Quem vende soja sem olhar margem está trabalhando para o mercado.",
                "main_message": "Margem não depende só de produtividade, mas de timing comercial.",
                "problem_addressed": "Produtor olha volume e esquece margem.",
                "solution_presented": "Ler custo, preço e risco junto.",
                "target_within_agro": "agrônomo",
                "content_pillar": "educacional",
                "call_to_action": "Comenta sua realidade",
            },
        )
        intelligence = PostIntelligence(
            post_id=post.id,
            agro_topic_cluster="gestão",
            agro_segment="grãos",
            technical_depth="especialista",
            core_argument="Quem ignora margem na soja perde dinheiro mesmo colhendo bem.",
            argument_structure="dado -> comparativo -> implicacao -> CTA",
            technical_claims=[
                "Uma diferença de 12% na margem muda completamente o resultado da safra.",
                "Produtividade alta sem estrategia comercial pode destruir rentabilidade.",
            ],
            data_points=[
                {"value": "12%", "context": "diferença de margem", "source": "levantamento interno"},
                {"value": "R$ 18/sc", "context": "variacao de resultado liquido", "source": "levantamento interno"},
            ],
            sources_referenced=["levantamento interno"],
            knowledge_assumptions="Leitor entende custo por hectare e margem.",
            content_gaps="Faltou mostrar exemplo de tomada de decisao.",
            replication_template="[dado] + [erro comum] + [implicacao] + [CTA]",
        )
        voice = ProfileVoice(
            profile_id=own.id,
            vocabulary={"palavras_frequentes": ["margem", "safra", "produtor"]},
            tone="direto e provocador",
            dominant_themes=["vendas", "rentabilidade"],
            competitor_comparison={"diferencial": "fala de margem com linguagem de campo"},
            voice_summary="Vai direto ao ponto, provoca o leitor e traduz dado em decisao comercial.",
            generated_at=datetime.now(timezone.utc),
        )
        session.add_all([analysis, intelligence, voice])
        session.add_all(
            [
                ArgumentBank(
                    text="12% de margem muda o jogo na safra",
                    topic_cluster="gestão",
                    agro_segment="grãos",
                    quality_score=0.9,
                    virality_weight=0.8,
                    source_post_ids=[post.id],
                    times_seen=3,
                    origin="extracted",
                ),
                ArgumentBank(
                    text="vaca leiteira precisa de conforto termico",
                    topic_cluster="pecuária",
                    agro_segment="pecuária",
                    quality_score=0.95,
                    virality_weight=0.95,
                    source_post_ids=[999],
                    times_seen=5,
                    origin="extracted",
                ),
            ]
        )
        session.commit()
        yield session, post, voice


def _mock_response(payload: dict) -> MagicMock:
    choice = MagicMock()
    choice.message.content = json.dumps(payload)
    response = MagicMock()
    response.choices = [choice]
    return response


def test_generate_post_retries_when_initial_draft_is_weak(session_with_generation_context):
    session, post, voice = session_with_generation_context
    weak = {
        "hook": "Olha isso.",
        "caption": "Texto curto demais sem dado nenhum.",
        "cta": "Comenta ai",
        "funnel_stage": "meio",
        "format": "feed",
    }
    strong = {
        "slides": [
            {"slide_number": 1, "slide_type": "CAPA", "title": "Sua soja pode render bem e mesmo assim sobrar pouca margem", "copy": "Alta produtividade nao compensa decisao comercial ruim.", "cta": ""},
            {"slide_number": 2, "slide_type": "HOOK", "title": "Quando a margem muda 12%, muda o caixa inteiro da safra", "copy": "Esse nao e um detalhe financeiro. E uma decisao comercial que altera o resultado final.", "cta": ""},
            {"slide_number": 3, "slide_type": "DESENVOLVIMENTO", "title": "R$ 18/sc nao some por acaso", "copy": "Na pratica, essa variacao aparece quando custo, preco e momento de venda sao lidos de forma isolada.", "cta": ""},
            {"slide_number": 4, "slide_type": "PROVA", "title": "Na pratica, margem e onde a safra mostra a verdade", "copy": "Quando a conta fecha R$ 18/sc abaixo no levantamento interno, o erro quase sempre esteve na leitura comercial.", "cta": ""},
            {"slide_number": 5, "slide_type": "CTA", "title": "Aprenda a defender margem com metodo", "copy": "Quem trabalha com vendas no agro precisa traduzir dado em decisao.", "cta": "Entre na Confraria e aprenda a defender margem no agro."},
        ],
        "caption": (
            "Tem produtor comemorando produtividade enquanto a margem escorre pelo comercial.\n\n"
            "Quando a diferenca de margem chega a 12%, nao estamos falando de detalhe. Estamos falando de uma decisao que muda o caixa da safra.\n\n"
            "E quando essa variacao bate R$ 18/sc no resultado liquido, como apareceu no levantamento interno, fica claro que vender bem vale tanto quanto produzir bem.\n\n"
            "No campo, produtividade sem estrategia comercial vira numero bonito com rentabilidade fraca. O agronomo e o vendedor que entendem isso param de discutir so volume e passam a discutir decisao.\n\n"
            "Esse e o tipo de leitura que separa quem repete processo de quem construi margem de verdade, porque mostra onde o resultado realmente nasce e onde a margem se perde no campo.\n\n"
            "Se voce trabalha com vendas no agro e quer aprender a fazer essa leitura com metodo, entra na Confraria."
        ),
        "cta": "Entre na Confraria e aprenda a defender margem no agro.",
        "funnel_stage": "fundo",
        "format": "carousel",
    }

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        side_effect=[_mock_response(weak), _mock_response(strong)],
    ) as mock_create:
        generated = generate_post(post, voice, approved_examples=[], session=session)

    assert mock_create.call_count == 2
    assert generated.caption == strong["caption"]
    assert generated.funnel_stage == "fundo"
    assert generated.format == "carousel"
    assert generated.slides[0]["slide_type"] == "CAPA"
    assert generated.hook == strong["slides"][1]["title"]


def test_generate_post_repairs_caption_when_only_remaining_issue_is_length(session_with_generation_context):
    session, post, voice = session_with_generation_context
    weak = {
        "hook": "Olha isso.",
        "caption": "Texto curto demais sem dado nenhum.",
        "cta": "Comenta ai",
        "funnel_stage": "meio",
        "format": "feed",
    }
    short_caption = (
        "Tem produtor comemorando produtividade enquanto a margem escorre pelo comercial.\n\n"
        "Quando a diferenca de margem chega a 12%, a decisao comercial muda o caixa da safra.\n\n"
        "E quando essa variacao bate R$ 18/sc no levantamento interno, fica claro que vender melhor protege a rentabilidade.\n\n"
        "Se voce trabalha com vendas no agro, precisa olhar margem com mais criterio."
    )
    almost_strong = {
        "slides": [
            {"slide_number": 1, "slide_type": "CAPA", "title": "Sua soja pode render bem e mesmo assim sobrar pouca margem", "copy": "Alta produtividade nao compensa decisao comercial ruim.", "cta": ""},
            {"slide_number": 2, "slide_type": "HOOK", "title": "Quando a margem muda 12%, muda o caixa inteiro da safra", "copy": "Esse nao e um detalhe financeiro. E uma decisao comercial que altera o resultado final.", "cta": ""},
            {"slide_number": 3, "slide_type": "DESENVOLVIMENTO", "title": "R$ 18/sc nao somem por acaso", "copy": "Na pratica, essa variacao aparece quando custo, preco e momento de venda sao lidos de forma isolada.", "cta": ""},
            {"slide_number": 4, "slide_type": "PROVA", "title": "O levantamento interno mostra onde a margem se perde", "copy": "Quando a conta fecha R$ 18/sc abaixo, o erro quase sempre esteve na leitura comercial e nao na lavoura.", "cta": ""},
            {"slide_number": 5, "slide_type": "CTA", "title": "Aprenda a defender margem com metodo", "copy": "Quem trabalha com vendas no agro precisa traduzir dado em decisao.", "cta": "Entre na Confraria e aprenda a defender margem no agro."},
        ],
        "caption": short_caption,
        "cta": "Entre na Confraria e aprenda a defender margem no agro.",
        "funnel_stage": "fundo",
        "format": "carousel",
    }
    repaired_caption = (
        "Tem produtor comemorando produtividade enquanto a margem escorre pelo comercial, e esse erro continua acontecendo porque muita gente ainda trata venda como etapa final, nao como parte da estrategia da safra.\n\n"
        "Quando a diferenca de margem chega a 12%, nao estamos falando de ajuste fino. Estamos falando de uma decisao comercial que muda o caixa, a pressao sobre o custo e a capacidade de defender resultado em um mercado apertado.\n\n"
        "Se essa variacao bate R$ 18/sc no resultado liquido, como apareceu no levantamento interno, o agronomo e o vendedor precisam olhar para risco, timing e argumento tecnico com muito mais criterio.\n\n"
        "No campo, produtividade alta sem estrategia comercial vira numero bonito com rentabilidade fraca. E quem atende produtor precisa traduzir esse dado em decisao, nao em discurso generico.\n\n"
        "Se voce quer aprender a defender margem com metodo, entra na Confraria e aprofunda essa leitura comercial do agro."
    )

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        side_effect=[
            _mock_response(weak),
            _mock_response(almost_strong),
            _mock_response({"caption": repaired_caption}),
        ],
    ) as mock_create:
        generated = generate_post(post, voice, approved_examples=[], session=session)

    assert mock_create.call_count == 3
    assert generated.caption == repaired_caption
    assert len(generated.caption.split()) >= 140
    assert generated.format == "carousel"
    assert "Corrija somente a legenda" in mock_create.call_args_list[-1].kwargs["messages"][1]["content"]


def test_generate_post_prioritizes_arguments_from_same_topic(session_with_generation_context):
    session, post, voice = session_with_generation_context
    good = {
        "slides": [
            {"slide_number": 1, "slide_type": "CAPA", "title": "Margem ruim pode destruir uma boa safra", "copy": "O problema nao esta so na produtividade.", "cta": ""},
            {"slide_number": 2, "slide_type": "HOOK", "title": "12% de diferenca na margem muda o jogo", "copy": "Quando isso acontece, a conversa precisa sair do volume e entrar na decisao.", "cta": ""},
            {"slide_number": 3, "slide_type": "DESENVOLVIMENTO", "title": "R$ 18/sc mostram o tamanho do erro", "copy": "Na pratica, essa variacao aparece quando estrategia comercial e leitura de risco falham.", "cta": ""},
            {"slide_number": 4, "slide_type": "PROVA", "title": "Quem vende melhor protege a rentabilidade", "copy": "No levantamento interno, o time que le melhor margem defende rentabilidade com muito mais consistencia.", "cta": ""},
            {"slide_number": 5, "slide_type": "CTA", "title": "Quer que eu aprofunde essa serie?", "copy": "Se esse tema faz sentido para voce, eu sigo daqui.", "cta": "Comenta MARGEM."},
        ],
        "caption": (
            "Uma safra boa no papel pode esconder uma margem ruim no caixa, e esse e o tipo de detalhe que muita gente do agro ignora porque continua olhando so para volume produzido.\n\n"
            "Quando a diferenca de margem bate 12%, a conversa deixa de ser teorica. Isso muda a forma como o produtor avalia a venda, como o consultor orienta a decisao e como a revenda enxerga o momento de negociar.\n\n"
            "Se essa decisao ainda representa R$ 18/sc no resultado liquido, como mostrou o levantamento interno, o problema nao e produtividade: e estrategia comercial. E nesse ponto muita gente boa tecnicamente continua deixando dinheiro na mesa por nao traduzir dado em acao.\n\n"
            "Nathan fala com agronomo e vendedor que precisam transformar informacao em decisao pratica. Nao basta saber que o custo apertou. E preciso defender margem, ler risco e ajustar abordagem antes que o mercado faca isso por voce.\n\n"
            "Isso e conteudo de meio de funil com profundidade real para quem vive a pressao do campo, atende produtor toda semana e precisa provar valor com argumento tecnico, nao com frase vazia.\n\n"
            "Comenta MARGEM se esse tema merece uma serie e eu aprofundo os erros que mais destroem rentabilidade no comercial da safra."
        ),
        "cta": "Comenta MARGEM.",
        "funnel_stage": "meio",
        "format": "carousel",
    }

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        return_value=_mock_response(good),
    ) as mock_create:
        generate_post(post, voice, approved_examples=[], session=session)

    user_prompt = mock_create.call_args.kwargs["messages"][1]["content"]
    assert "12% de margem muda o jogo na safra" in user_prompt
    assert "vaca leiteira precisa de conforto termico" not in user_prompt
    assert "CATÁLOGO DE DADOS VALIDADOS" in user_prompt
    assert "levantamento interno" in user_prompt
