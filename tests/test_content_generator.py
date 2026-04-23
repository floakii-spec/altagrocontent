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


def _with_adaptation_map(payload: dict, *, thesis: str = "Margem boa depende de decisao comercial") -> dict:
    slides = payload.get("slides") or []
    if not slides:
        return payload
    proof_points = [
        slide["title"]
        for slide in slides
        if slide.get("slide_type") == "PROVA" and slide.get("title")
    ] or ["12% de margem", "R$ 18/sc"]
    adaptation_map = {
        "tese_original": "Quem ignora margem na soja perde dinheiro mesmo colhendo bem.",
        "tese_adaptada": thesis,
        "fato_disparador_original": slides[0]["title"],
        "mecanismo_original": "O erro aparece quando margem, preco, timing e estrategia comercial sao lidos de forma isolada na soja.",
        "ponte_para_agro": "Traduzir o caso em decisao pratica para produtor, consultor e vendedor no agro, mostrando como margem e resultado liquido se perdem.",
        "angulo_autoral_do_nathan": "Ler o problema pela lente de margem, risco, estrategia comercial e argumento de campo.",
        "prova_que_nao_pode_sumir": proof_points[:2],
        "plano_estrutural": [
            {
                "slide_number": slide["slide_number"],
                "slide_type": slide["slide_type"],
                "papel": f"Cumprir a funcao de {slide['slide_type']} mantendo progressao logica.",
                "origem": slide["title"],
                "adaptacao": slide["copy"] or slide["title"],
            }
            for slide in slides
        ],
    }
    return {
        **payload,
        "adaptation_map": adaptation_map,
    }


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

    assert mock_create.call_count == 3
    assert generated.caption == repaired_caption
    assert len(generated.caption.split()) >= 140
    assert generated.format == "carousel"
    assert "Corrija somente a legenda" in mock_create.call_args_list[-1].kwargs["messages"][1]["content"]


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
            {"slide_number": 4, "slide_type": "DESENVOLVIMENTO", "title": "Preco e custo precisam andar juntos", "copy": "Isso muda a recomendacao comercial porque obriga o vendedor a defender timing, nao apenas desconto.", "cta": ""},
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

    assert mock_create.call_count == 3
    assert generated.caption == refined["caption"]
    revision_prompt = mock_create.call_args_list[-1].kwargs["messages"][1]["content"]
    assert "impacto pratico" in revision_prompt
    assert "150 a 240 palavras" in revision_prompt


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
    assert "cadeia causal do material-base" in revision_prompt
    assert "nao vire sermao generico" in revision_prompt.lower()


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

    assert mock_create.call_count == 4
    assert generated.caption == usable_but_imperfect["caption"]
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
    assert "MAPA ESTRUTURAL DE TRANSFERÊNCIA" in user_prompt
    assert "\"adaptation_map\"" in system_prompt
    assert "Troque o cenario, nao a logica" in system_prompt


def test_generate_post_requires_adaptation_map_before_approving(session_with_generation_context):
    session, post, voice = session_with_generation_context
    without_map = {
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
    with_map = _with_adaptation_map(without_map)

    with patch("src.generator.content_generator.load_studio_context", return_value={}), patch(
        "src.generator.content_generator.openai_client.chat.completions.create",
        side_effect=[_mock_response(without_map), _mock_response(with_map)],
    ) as mock_create:
        generated = generate_post(post, voice, approved_examples=[], session=session)

    assert mock_create.call_count == 2
    assert generated.caption == with_map["caption"]
    revision_prompt = mock_create.call_args_list[-1].kwargs["messages"][1]["content"]
    assert "faltou adaptation_map" in revision_prompt
    assert "mapa estrutural de transferencia" in revision_prompt.lower()
