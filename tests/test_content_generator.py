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

from src.generator.content_generator import (
    _build_evidence_pack,
    _build_validated_data_catalog,
    _evaluate_generation,
    _select_top_arguments,
    generate_post,
)
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
            visual_transcript=(
                "Slide 1: 12% de margem muda o jogo na safra.\n"
                "Slide 2: R$ 18/sc de variação no resultado líquido.\n"
                "Slide 3: Produtividade alta sem estratégia comercial destrói rentabilidade."
            ),
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


def _mock_raw_response(content: str) -> MagicMock:
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


def _with_planning_narrative(payload: dict, *, thesis: str = "Margem boa depende de decisao comercial") -> dict:
    slides = payload.get("slides") or []
    if not slides:
        return payload
    proof_points = [
        slide["title"]
        for slide in slides
        if slide.get("slide_type") in {"PROVA", "DADO", "DADOS_HISTORICOS"} and slide.get("title")
    ] or ["12% de margem", "R$ 18/sc"]
    planning = {
        "tensao_central": "Quem ignora margem na soja perde dinheiro mesmo colhendo bem.",
        "angulo_de_adaptacao": thesis,
        "camadas": [
            {
                "numero": slide["slide_number"],
                "tipo_slide": slide["slide_type"],
                "funcao_narrativa": slide["title"],
                "pergunta_que_abre": slides[index]["title"] if index < len(slides) else "Qual a decisao pratica para o agro?",
                "emocao_alvo": ["espanto", "admiracao", "revelacao", "indignacao", "analise", "leveza", "sintese"][min(index - 1, 6)],
            }
            for index, slide in enumerate(slides, start=1)
        ],
        "total_slides": len(slides),
        "provas_que_nao_podem_sumir": proof_points[:2],
        "onde_termina": "Quando o leitor entende o mecanismo, a prova e a decisao pratica no agro.",
    }
    return {
        **payload,
        "planejamento_narrativo": planning,
    }


_with_adaptation_map = _with_planning_narrative


def test_evaluate_generation_rejects_short_generic_carousel_source(session_with_generation_context):
    session, post, _voice = session_with_generation_context
    post.post_type = "carousel"
    top_args = _select_top_arguments(session, post)
    catalog = _build_validated_data_catalog(post, top_args)
    evidence_pack = _build_evidence_pack(post, top_args, catalog)
    generic = _with_planning_narrative(
        {
            "slides": [
                {"slide_number": 1, "slide_type": "CAPA", "title": "De Importador a Potencia Agro", "copy": "O Brasil mudou sua historia.", "cta": ""},
                {"slide_number": 2, "slide_type": "HOOK", "title": "A Revolucao da Embrapa", "copy": "Mas qual foi o impacto real dessa historia?", "cta": ""},
                {"slide_number": 3, "slide_type": "MODELO", "title": "3 Inovacoes Cruciais", "copy": "Como essas inovacoes podem ser usadas hoje?", "cta": ""},
                {"slide_number": 4, "slide_type": "ESCALADA", "title": "Impacto Atual", "copy": "Qual estrategia voce pode aplicar ja?", "cta": ""},
                {"slide_number": 5, "slide_type": "SINTESE", "title": "Transformacao Economica", "copy": "Desafios se tornam oportunidades.", "cta": ""},
                {"slide_number": 6, "slide_type": "CTA", "title": "A Hora da Acao", "copy": "Vamos juntos?", "cta": "Entre na Confraria e transforme desafios em resultados."},
            ],
            "caption": (
                "O agro brasileiro mudou muito nas ultimas decadas e essa transformacao mostra a importancia da tecnologia.\n\n"
                "Quando olhamos para sementes, solo e gestao hidrica, percebemos que desafios podem se tornar oportunidades para quem sabe aplicar conhecimento.\n\n"
                "Na pratica, isso inspira produtores, consultores e vendedores a buscarem mais estrategia no campo e mais resultado no caixa.\n\n"
                "Se voce quer transformar desafios em resultados, conheca a Confraria de Vendas no Agro e domine o comercial no agro."
            ),
            "cta": "Entre na Confraria e transforme desafios em resultados.",
            "funnel_stage": "fundo",
            "format": "carousel",
        }
    )

    evaluation = _evaluate_generation(generic, post, evidence_pack, target_slide_count=12)

    assert any(issue.startswith("carrossel curto demais") for issue in evaluation["problems"])
    assert any(issue.startswith("copy em formato de roteiro generico") for issue in evaluation["problems"])


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
    strong = _with_adaptation_map(strong)

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
    assert generated.planning_narrative == strong["planejamento_narrativo"]


def test_generate_post_recovers_from_empty_or_invalid_json_response(session_with_generation_context):
    session, post, voice = session_with_generation_context
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
    strong = _with_adaptation_map(strong)

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        side_effect=[_mock_raw_response(""), _mock_response(strong)],
    ) as mock_create:
        generated = generate_post(post, voice, approved_examples=[], session=session)

    assert mock_create.call_count == 2
    assert generated.caption == strong["caption"]
    retry_prompt = mock_create.call_args_list[-1].kwargs["messages"][1]["content"]
    assert "A resposta anterior veio vazia ou em JSON invalido" in retry_prompt


def test_generate_post_retries_after_rate_limit(session_with_generation_context):
    session, post, voice = session_with_generation_context
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
    strong = _with_adaptation_map(strong)

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        side_effect=[
            Exception("Error code: 429 - Rate limit reached for gpt-4o. Please try again in 0.01s."),
            _mock_response(strong),
        ],
    ) as mock_create, patch("src.openai_utils.time.sleep") as mock_sleep:
        generated = generate_post(post, voice, approved_examples=[], session=session)

    assert mock_create.call_count == 2
    assert mock_sleep.called
    assert generated.caption == strong["caption"]
    assert generated.planning_narrative == strong["planejamento_narrativo"]


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
    almost_strong = _with_adaptation_map(almost_strong)
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

    assert mock_create.call_count == 2
    assert len(generated.caption.split()) >= 140
    assert generated.format == "carousel"
    assert "12%" in generated.caption
    assert "levantamento interno" in generated.caption


def test_generate_post_applies_local_repairs_for_caption_and_proof(session_with_generation_context):
    session, post, voice = session_with_generation_context
    weak = {
        "hook": "Olha isso.",
        "caption": "Texto curto demais sem dado nenhum.",
        "cta": "Comenta ai",
        "funnel_stage": "meio",
        "format": "feed",
    }
    almost_strong = {
        "slides": [
            {"slide_number": 1, "slide_type": "CAPA", "title": "Alta producao nao garante caixa", "copy": "No agro, produtividade sem criterio comercial ainda pode destruir margem.", "cta": ""},
            {"slide_number": 2, "slide_type": "HOOK", "title": "Voce pode colher bem e perder resultado do mesmo jeito", "copy": "O problema aparece quando a decisao comercial fica atrasada.", "cta": ""},
            {"slide_number": 3, "slide_type": "DESENVOLVIMENTO", "title": "O erro nao nasce na colheita", "copy": "Ele comeca quando custo, preco e timing sao lidos de forma isolada.", "cta": ""},
            {"slide_number": 4, "slide_type": "DESENVOLVIMENTO", "title": "Volume sem leitura vira ilusao de seguranca", "copy": "A operacao parece forte, mas a margem continua exposta.", "cta": ""},
            {"slide_number": 5, "slide_type": "PROVA", "title": "A conta fecha no comercial", "copy": "O problema fica evidente quando o resultado sai do planejado.", "cta": ""},
            {"slide_number": 6, "slide_type": "CTA", "title": "Aprenda a defender margem com metodo", "copy": "Quem vende no agro precisa transformar numero em criterio.", "cta": "Entre na Confraria e aprenda a defender margem no agro."},
        ],
        "caption": (
            "Tem muita lavoura que parece forte no campo, mas continua vulneravel no comercial.\n\n"
            "Quando a equipe separa custo, preco e momento de venda, a margem deixa de ser defendida do jeito certo.\n\n"
            "No fim, produtividade boa sozinha nao garante resultado para quem precisa vender melhor no agro."
        ),
        "cta": "Entre na Confraria e aprenda a defender margem no agro.",
        "funnel_stage": "fundo",
        "format": "carousel",
    }
    almost_strong = _with_adaptation_map(almost_strong)

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        side_effect=[_mock_response(weak), _mock_response(almost_strong)],
    ) as mock_create:
        generated = generate_post(post, voice, approved_examples=[], session=session)

    assert mock_create.call_count == 2
    assert len(generated.caption.split()) >= 140
    proof_slide = generated.slides[-2]
    assert proof_slide["slide_type"] in {"DADO", "MECANISMO", "SINTESE"}
    assert "12%" in proof_slide["copy"] or "R$ 18/sc" in proof_slide["copy"]
    assert "levantamento interno" in proof_slide["copy"]


def test_generate_post_refines_mixed_quality_issues_instead_of_aborting(session_with_generation_context):
    session, post, voice = session_with_generation_context
    weak = {
        "hook": "Olha isso.",
        "caption": "Texto curto demais sem dado nenhum.",
        "cta": "Comenta ai",
        "funnel_stage": "meio",
        "format": "feed",
    }
    mixed_issues = {
        "slides": [
            {"slide_number": 1, "slide_type": "CAPA", "title": "Sua margem pode sumir mesmo com boa produtividade", "copy": "O erro nao esta so na lavoura.", "cta": ""},
            {"slide_number": 2, "slide_type": "HOOK", "title": "12% de margem mudam toda a conversa comercial da safra", "copy": "Esse numero redefine como o consultor orienta a venda.", "cta": ""},
            {"slide_number": 3, "slide_type": "DESENVOLVIMENTO", "title": "Volume sozinho nao fecha conta", "copy": "Produtividade alta pode conviver com leitura comercial fraca.", "cta": ""},
            {"slide_number": 4, "slide_type": "DESENVOLVIMENTO", "title": "Preco e custo precisam andar juntos", "copy": "Separar essas variaveis enfraquece a tomada de decisao.", "cta": ""},
            {"slide_number": 5, "slide_type": "DESENVOLVIMENTO", "title": "O vendedor precisa defender criterio", "copy": "Sem essa leitura, a conversa vira achismo e urgencia.", "cta": ""},
            {"slide_number": 6, "slide_type": "PROVA", "title": "O levantamento interno mostrou perda de R$ 18/sc", "copy": "Quando a margem cede 12% no levantamento interno, a pressao aparece antes da colheita.", "cta": ""},
            {"slide_number": 7, "slide_type": "CTA", "title": "Aprenda a defender margem com metodo", "copy": "Quem vende no agro precisa conectar dado e argumento.", "cta": "Entre na Confraria e aprenda a defender margem no agro."},
        ],
        "caption": (
            "Tem produtor comemorando produtividade enquanto a margem escorre pelo comercial.\n\n"
            "Quando a diferenca de margem chega a 12%, a decisao comercial muda o caixa da safra.\n\n"
            "No levantamento interno, essa variacao chegou a R$ 18/sc e deixou claro que vender melhor protege a rentabilidade.\n\n"
            "Se voce trabalha com vendas no agro, precisa olhar margem com mais criterio e menos impulso."
        ),
        "cta": "Entre na Confraria e aprenda a defender margem no agro.",
        "funnel_stage": "fundo",
        "format": "carousel",
    }
    mixed_issues = _with_adaptation_map(mixed_issues)
    refined = {
            "slides": [
                {"slide_number": 1, "slide_type": "CAPA", "title": "Sua margem pode sumir mesmo com boa produtividade", "copy": "O erro nao esta so na lavoura. Ele aparece quando a estrategia comercial fica rasa.", "cta": ""},
                {"slide_number": 2, "slide_type": "HOOK", "title": "12% de margem mudam toda a conversa comercial da safra", "copy": "Esse numero redefine como o consultor orienta a venda e como o produtor percebe risco.", "cta": ""},
                {"slide_number": 3, "slide_type": "DESENVOLVIMENTO", "title": "Volume sozinho nao fecha conta", "copy": "Quando a equipe olha so produtividade, deixa de perceber onde a margem esta escorrendo na negociacao.", "cta": ""},
                {"slide_number": 4, "slide_type": "DESENVOLVIMENTO", "title": "Preco e custo precisam andar juntos", "copy": "Isso significa mudar a recomendacao no comercial e obrigar o vendedor a defender timing, nao apenas desconto.", "cta": ""},
                {"slide_number": 5, "slide_type": "DESENVOLVIMENTO", "title": "O vendedor precisa defender criterio", "copy": "Na pratica, essa leitura ajuda o agronomo a provar valor e evita decisao feita na pressa.", "cta": ""},
                {"slide_number": 6, "slide_type": "PROVA", "title": "O levantamento interno mostrou perda de R$ 18/sc", "copy": "Quando a margem cede 12% no levantamento interno, fica claro que a decisao comercial mexeu direto no caixa.", "cta": ""},
                {"slide_number": 7, "slide_type": "CTA", "title": "Aprenda a defender margem com metodo", "copy": "Quem vende no agro precisa conectar dado, risco e argumento.", "cta": "Entre na Confraria e aprenda a defender margem no agro."},
            ],
        "caption": (
            "Tem produtor comemorando produtividade enquanto a margem escorre pelo comercial, e esse erro continua porque muita gente ainda trata venda como etapa final da safra, nao como parte da estrategia.\n\n"
            "Quando a diferenca de margem chega a 12%, nao estamos falando de detalhe. Estamos falando de uma decisao que muda caixa, pressao sobre custo e poder de negociacao em um mercado apertado.\n\n"
            "No levantamento interno, essa variacao chegou a R$ 18/sc. Para quem vende no agro, isso significa defender melhor timing, argumento tecnico e leitura de risco antes que o produtor aceite uma condicao ruim.\n\n"
            "O agronomo que traduz esse dado em implicacao pratica consegue orientar o produtor com mais criterio, mostra valor comercial e deixa de discutir apenas volume.\n\n"
            "Se voce quer aprender a defender margem com metodo, entra na Confraria e aprofunda essa leitura comercial aplicada ao campo."
        ),
        "cta": "Entre na Confraria e aprenda a defender margem no agro.",
        "funnel_stage": "fundo",
        "format": "carousel",
    }
    refined = _with_adaptation_map(refined)

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        side_effect=[
            _mock_response(weak),
            _mock_response(mixed_issues),
            _mock_response(refined),
        ],
    ) as mock_create:
        generated = generate_post(post, voice, approved_examples=[], session=session)

    assert mock_create.call_count == 2
    assert len(generated.caption.split()) >= 140
    practical_hits = sum("na pratica" in slide["copy"].lower() for slide in generated.slides[2:-1])
    assert practical_hits >= 2


def test_generate_post_rejects_generic_moralization_and_recovers_source_logic(session_with_generation_context):
    session, post, voice = session_with_generation_context
    flat_but_formatted = {
        "slides": [
            {"slide_number": 1, "slide_type": "CAPA", "title": "Producao boa nao resolve tudo", "copy": "No fim, tudo depende de maturidade na gestao.", "cta": ""},
            {"slide_number": 2, "slide_type": "HOOK", "title": "Um numero bonito pode esconder fragilidade", "copy": "Tem muita operacao que parece forte por fora.", "cta": ""},
            {"slide_number": 3, "slide_type": "DESENVOLVIMENTO", "title": "Gestao precisa acompanhar o crescimento", "copy": "Negocios fortes exigem mais consciencia no dia a dia.", "cta": ""},
            {"slide_number": 4, "slide_type": "DESENVOLVIMENTO", "title": "O produtor precisa pensar no todo", "copy": "Planejamento e disciplina continuam sendo fundamentais.", "cta": ""},
            {"slide_number": 5, "slide_type": "DESENVOLVIMENTO", "title": "Visao ampla evita sustos", "copy": "Quem cuida da operacao com atencao reduz problemas futuros.", "cta": ""},
            {"slide_number": 6, "slide_type": "PROVA", "title": "O levantamento interno reforca o alerta", "copy": "Os 12% e os R$ 18/sc mostram que qualquer negocio precisa de atencao constante, segundo o levantamento interno.", "cta": ""},
            {"slide_number": 7, "slide_type": "CTA", "title": "Busque evolucao constante", "copy": "Gestao melhor gera negocios melhores.", "cta": "Entre na Confraria para evoluir sua visao de negocio."},
        ],
        "caption": (
            "Tem muita operacao no agro que parece forte no campo, mas ainda convive com vulnerabilidades que nascem da falta de visao mais ampla sobre o negocio.\n\n"
            "Por isso, desenvolvimento profissional, consciencia de gestao e disciplina continuam sendo pilares para quem quer crescer com consistencia e evitar erros repetidos ao longo do tempo.\n\n"
            "Os 12% e os R$ 18/sc reforcam esse sinal no levantamento interno, mostrando que toda empresa precisa de organizacao e acompanhamento continuo para nao perder resultado de maneira silenciosa.\n\n"
            "No fim, a mensagem principal e simples: quem amadurece a gestao toma decisoes melhores, protege o negocio e constroi uma operacao mais preparada para o futuro.\n\n"
            "Se voce quer dar esse proximo passo com mais clareza, entra na Confraria e aprofunda sua visao de negocio no agro."
        ),
        "cta": "Entre na Confraria para evoluir sua visao de negocio.",
        "funnel_stage": "fundo",
        "format": "carousel",
    }
    flat_but_formatted = _with_adaptation_map(flat_but_formatted, thesis="No fim, o agro precisa de mais maturidade na gestao.")
    recovered = {
        "slides": [
            {"slide_number": 1, "slide_type": "CAPA", "title": "Voce pode colher bem e ainda perder dinheiro na soja", "copy": "O problema aparece quando a produtividade mascara erro comercial.", "cta": ""},
            {"slide_number": 2, "slide_type": "HOOK", "title": "12% de margem mudam o caixa inteiro da safra", "copy": "Esse numero muda a leitura do produtor porque revela o impacto real da decisao comercial.", "cta": ""},
            {"slide_number": 3, "slide_type": "DESENVOLVIMENTO", "title": "O erro nao nasce na colheita", "copy": "Ele aparece quando preco, custo e momento de venda sao lidos de forma isolada e a rentabilidade escapa antes de virar caixa.", "cta": ""},
            {"slide_number": 4, "slide_type": "DESENVOLVIMENTO", "title": "R$ 18/sc mostram o tamanho da distorcao", "copy": "Quando essa variacao aparece no levantamento interno, fica claro que a estrategia comercial mexeu no resultado final da safra.", "cta": ""},
            {"slide_number": 5, "slide_type": "DESENVOLVIMENTO", "title": "Isso muda a conversa com o produtor", "copy": "Na pratica, o vendedor e o agronomo passam a defender timing, margem e risco em vez de discutir so volume.", "cta": ""},
            {"slide_number": 6, "slide_type": "PROVA", "title": "O dado prova onde a rentabilidade se perde", "copy": "No levantamento interno, a diferenca de 12% na margem e de R$ 18/sc no resultado mostra por que produtividade alta sem estrategia comercial destroi rentabilidade.", "cta": ""},
            {"slide_number": 7, "slide_type": "CTA", "title": "Aprenda a defender margem com metodo", "copy": "Quem vende no agro precisa transformar dado em decisao comercial.", "cta": "Entre na Confraria e aprenda a defender margem no agro."},
        ],
        "caption": (
            "Tem produtor comemorando produtividade enquanto a margem escorre pelo comercial, e esse erro continua porque muita gente ainda trata venda como etapa final da safra, nao como parte da estrategia.\n\n"
            "Quando a diferenca chega a 12% na margem, nao estamos falando de detalhe. Estamos falando de uma decisao que muda caixa, pressao sobre custo e poder de negociacao em um mercado apertado.\n\n"
            "No levantamento interno, essa distorcao chegou a R$ 18/sc. Isso significa que a equipe tecnica e comercial precisa ler risco, preco e timing junto, porque produtividade alta sem estrategia comercial pode destruir rentabilidade.\n\n"
            "Na pratica, esse e o tipo de argumento que ajuda vendedor, consultor e agronomo a sair do discurso generico e orientar o produtor com criterio de negocio.\n\n"
            "Se voce quer aprender a defender margem com metodo e usar dado para vender melhor no agro, entra na Confraria."
        ),
        "cta": "Entre na Confraria e aprenda a defender margem no agro.",
        "funnel_stage": "fundo",
        "format": "carousel",
    }
    recovered = _with_adaptation_map(recovered)

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        side_effect=[
            _mock_response(flat_but_formatted),
            _mock_response(recovered),
        ],
    ) as mock_create:
        generated = generate_post(post, voice, approved_examples=[], session=session)

    assert mock_create.call_count == 2
    assert generated.caption == recovered["caption"]
    revision_prompt = mock_create.call_args_list[-1].kwargs["messages"][1]["content"]
    assert "impacto pratico" in revision_prompt.lower() or "cadeia causal do material-base" in revision_prompt


def test_generate_post_returns_best_effort_when_only_non_blocking_issues_remain(session_with_generation_context):
    session, post, voice = session_with_generation_context
    weak = {
        "hook": "Olha isso.",
        "caption": "Texto curto demais sem dado nenhum.",
        "cta": "Comenta ai",
        "funnel_stage": "meio",
        "format": "feed",
    }
    usable_but_imperfect = {
        "slides": [
            {"slide_number": 1, "slide_type": "CAPA", "title": "Margem boa exige mais do que produtividade", "copy": "O problema aparece quando a decisao comercial fica rasa.", "cta": ""},
            {"slide_number": 2, "slide_type": "HOOK", "title": "12% de margem mudam a safra inteira", "copy": "Esse numero altera a conversa entre produtor, consultor e vendedor.", "cta": ""},
            {"slide_number": 3, "slide_type": "DESENVOLVIMENTO", "title": "Volume nao protege caixa sozinho", "copy": "Produtividade alta nao impede erro de leitura comercial.", "cta": ""},
            {"slide_number": 4, "slide_type": "DESENVOLVIMENTO", "title": "Preco sem criterio enfraquece venda", "copy": "Separar custo e negociacao cria leitura fraca do mercado.", "cta": ""},
            {"slide_number": 5, "slide_type": "DESENVOLVIMENTO", "title": "Argumento tecnico precisa aparecer antes", "copy": "Sem isso, a conversa escorrega para urgencia e opiniao.", "cta": ""},
            {"slide_number": 6, "slide_type": "PROVA", "title": "O levantamento interno mostrou R$ 18/sc de diferenca", "copy": "Quando a margem cede 12% no levantamento interno, a pressao comercial fica evidente.", "cta": ""},
            {"slide_number": 7, "slide_type": "CTA", "title": "Quer aprender a defender margem?", "copy": "A decisao comercial precisa de metodo no agro.", "cta": "Entre na Confraria e aprenda a defender margem no agro."},
        ],
        "caption": (
            "Tem produtor comemorando produtividade enquanto a margem escorre pelo comercial.\n\n"
            "Quando a diferenca de margem chega a 12%, a decisao comercial muda o caixa da safra.\n\n"
            "No levantamento interno, essa variacao chegou a R$ 18/sc e mostrou que vender melhor protege a rentabilidade.\n\n"
            "Se voce trabalha com vendas no agro, precisa olhar margem com mais criterio e menos impulso."
        ),
        "cta": "Entre na Confraria e aprenda a defender margem no agro.",
        "funnel_stage": "fundo",
        "format": "carousel",
    }
    usable_but_imperfect = _with_adaptation_map(usable_but_imperfect)

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        side_effect=[
            _mock_response(weak),
            _mock_response(usable_but_imperfect),
            _mock_response(usable_but_imperfect),
            _mock_response(usable_but_imperfect),
        ],
    ) as mock_create:
        generated = generate_post(post, voice, approved_examples=[], session=session)

    assert mock_create.call_count == 2
    assert len(generated.caption.split()) >= len(usable_but_imperfect["caption"].split())
    assert generated.format == "carousel"
    assert generated.slides[-1]["slide_type"] == "CTA"


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
    good = _with_adaptation_map(good)

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        return_value=_mock_response(good),
    ) as mock_create:
        generate_post(post, voice, approved_examples=[], session=session)

    system_prompt = mock_create.call_args.kwargs["messages"][0]["content"]
    user_prompt = mock_create.call_args.kwargs["messages"][1]["content"]
    assert "12% de margem muda o jogo na safra" in user_prompt
    assert "vaca leiteira precisa de conforto termico" not in user_prompt
    assert "CATÁLOGO DE DADOS VALIDADOS" in user_prompt
    assert "levantamento interno" in user_prompt
    assert "Transcrição literal dos cards/slides" in user_prompt
    assert "R$ 18/sc de variação no resultado líquido" in user_prompt
    assert "INTELIGÊNCIA CRIATIVA AGRO" in user_prompt
    assert "erro caro" in user_prompt
    assert "cadeia_causal_a_preservar" in user_prompt
    assert "mecanismos_que_nao_podem_sumir" in user_prompt
    assert "MAPA DE LÓGICA DO MATERIAL-BASE" in user_prompt
    assert "\"planejamento_narrativo\"" in system_prompt
    assert "Troque o cenário, não a lógica" in system_prompt


def test_generate_post_requires_planning_narrative_before_approving(session_with_generation_context):
    session, post, voice = session_with_generation_context
    without_planning = {
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
            "Comenta MARGEM se esse tema merece uma serie e eu aprofundo os erros que mais destroem rentabilidade no comercial da safra."
        ),
        "cta": "Comenta MARGEM.",
        "funnel_stage": "meio",
        "format": "carousel",
    }
    with_planning = _with_planning_narrative(without_planning)

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        side_effect=[_mock_response(without_planning), _mock_response(with_planning)],
    ) as mock_create:
        generated = generate_post(post, voice, approved_examples=[], session=session)

    assert mock_create.call_count == 2
    assert generated.caption == with_planning["caption"]
    revision_prompt = mock_create.call_args_list[-1].kwargs["messages"][1]["content"]
    assert "planejamento_narrativo" in revision_prompt
    assert "Monte o planejamento_narrativo completo antes dos slides" in revision_prompt


def test_generate_post_snapshots_source_data_inventory(session_with_generation_context):
    """GeneratedPost.source_data_inventory must be a copy of the source intelligence evidence_inventory."""
    session, post, voice = session_with_generation_context

    inventory = {
        "required": {
            "numbers": ["12%", "R$ 18/sc"],
            "mechanisms": ["margem"],
            "causal_steps": [],
            "definitions": [],
        },
        "optional": {"claims": [], "sources": [], "context": ""},
    }
    post.intelligence.evidence_inventory = inventory

    good_response = _with_adaptation_map({
        "slides": [
            {"slide_number": 1, "slide_type": "CAPA", "title": "Margem ruim pode destruir uma boa safra", "copy": "O problema nao esta so na produtividade.", "cta": ""},
            {"slide_number": 2, "slide_type": "HOOK", "title": "12% de diferenca na margem muda o jogo", "copy": "Quando isso acontece, a conversa precisa sair do volume e entrar na decisao. 12%", "cta": ""},
            {"slide_number": 3, "slide_type": "DESENVOLVIMENTO", "title": "R$ 18/sc mostram o tamanho do erro", "copy": "Na pratica, essa variacao de R$ 18/sc aparece quando estrategia comercial e leitura de risco falham.", "cta": ""},
            {"slide_number": 4, "slide_type": "DESENVOLVIMENTO", "title": "Volume nao protege caixa sozinho", "copy": "Produtividade alta nao impede erro de leitura comercial. A margem define o resultado.", "cta": ""},
            {"slide_number": 5, "slide_type": "DESENVOLVIMENTO", "title": "Preco sem criterio enfraquece venda", "copy": "Separar custo e negociacao cria leitura fraca do mercado no agro.", "cta": ""},
            {"slide_number": 6, "slide_type": "PROVA", "title": "Levantamento interno confirmou a diferenca", "copy": "Quando a margem cede 12% no levantamento interno, a pressao comercial fica evidente para o produtor.", "cta": ""},
            {"slide_number": 7, "slide_type": "CTA", "title": "Quer aprender a defender margem?", "copy": "A decisao comercial precisa de metodo no agro.", "cta": "Entre na Confraria e aprenda a defender margem no agro."},
        ],
        "caption": (
            "Tem produtor comemorando produtividade enquanto a margem escorre pelo comercial.\n\n"
            "Quando a diferenca de margem chega a 12%, a decisao comercial muda o caixa da safra.\n\n"
            "No levantamento interno, essa variacao chegou a R$ 18/sc e mostrou que vender melhor protege a rentabilidade.\n\n"
            "Se voce trabalha com vendas no agro, precisa olhar margem com mais criterio e menos impulso."
        ),
        "cta": "Entre na Confraria e aprenda a defender margem no agro.",
        "funnel_stage": "fundo",
        "format": "carousel",
        "hook": "12% de diferenca na margem muda o jogo",
    })

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        return_value=_mock_response(good_response),
    ):
        generated = generate_post(post, voice, approved_examples=[], session=session)

    assert generated.source_data_inventory == inventory
