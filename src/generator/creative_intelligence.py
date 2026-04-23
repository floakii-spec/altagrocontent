import re
from collections import Counter
from typing import Any


CREATIVE_INTELLIGENCE_DIRECTIVES = (
    "Comece pela tensao real do agro: dinheiro parado, margem comprimida, risco tecnico, decisao atrasada ou oportunidade mal lida.",
    "Transforme cada dado em consequencia pratica: o que muda para produtor, consultor, revenda, vendedor ou gestor.",
    "Use contraste concreto: antes/depois, campo/escritorio, volume/margem, tecnico/comercial, achismo/criterio.",
    "Troque generalidade por situacao vivida: safra, talhao, custo por hectare, negociacao, visita, carteira, revenda ou cooperativa.",
    "Mantenha criatividade com lastro: a ideia pode ser ousada, mas o dado, a fonte e a implicacao precisam vir do material validado.",
    "Ao adaptar um case de outro contexto, troque o cenario, nao a logica: preserve fato disparador, mecanismo, prova e consequencia.",
    "Nao transforme um caso analitico em licao moral generica sobre gestao, mentalidade ou disciplina.",
)

_FIELD_CONTEXTS = {
    "grãos": ("safra", "margem por saca", "custo por hectare", "plantio", "comercializacao"),
    "fibras": ("janela de manejo", "qualidade da fibra", "custo operacional", "risco climatico"),
    "pecuária": ("arroba", "lotacao", "conversao", "sanidade", "pastagem"),
    "horticultura": ("perecibilidade", "maior giro", "padrao comercial", "mao de obra"),
    "cafeicultura": ("qualidade de bebida", "peneira", "colheita", "pos-colheita", "preco"),
    "geral": ("margem", "risco", "decisao", "produtividade", "caixa"),
}

_ENGAGEMENT_ARCHETYPES = (
    {
        "name": "erro caro",
        "use_when": "quando houver margem, custo, perda, risco ou decisao atrasada",
        "shape": "Mostre o erro comum, quantifique o impacto e entregue o criterio de decisao.",
    },
    {
        "name": "dado que muda a conversa",
        "use_when": "quando houver numero forte, comparativo ou fonte reconhecivel",
        "shape": "Abra com o numero, explique o que ele mede e traduza a implicacao no campo/comercial.",
    },
    {
        "name": "mito de produtividade",
        "use_when": "quando o post confunde volume com rentabilidade ou tecnica com resultado",
        "shape": "Contraponha o que parece certo com o que realmente protege resultado.",
    },
    {
        "name": "criterio de profissional",
        "use_when": "quando a audiencia precisa de metodo para orientar produtor ou vender melhor",
        "shape": "Diferencie achismo de criterio e mostre como aplicar em uma conversa real.",
    },
)

_STOPWORDS = {
    "a", "as", "ao", "aos", "da", "das", "de", "do", "dos", "e", "em", "na", "nas",
    "no", "nos", "o", "os", "ou", "para", "por", "que", "se", "sem", "um", "uma",
    "mais", "menos", "como", "isso", "essa", "esse", "sua", "seu", "sao", "são",
    "ser", "foi", "tem", "porque", "quando", "entre", "sobre", "com", "num", "numa",
    "ate", "até", "dos", "das", "pela", "pelo", "pelos", "pelas", "mas",
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _trim(value: Any, limit: int = 900) -> str:
    text = _clean(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}...[truncado]"


def _unique(values: list[Any], limit: int = 8) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _clean(value)
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
        if len(result) >= limit:
            break
    return result


def _data_labels(data_points: list[Any]) -> list[str]:
    labels: list[str] = []
    for point in data_points or []:
        if not isinstance(point, dict):
            continue
        value = _clean(point.get("value"))
        context = _clean(point.get("context"))
        source = _clean(point.get("source"))
        if value and context and source:
            labels.append(f"{value} = {context} ({source})")
        elif value and context:
            labels.append(f"{value} = {context}")
        elif value:
            labels.append(value)
    return labels


def _field_contexts(segment: str | None) -> list[str]:
    normalized = _clean(segment).lower()
    return list(_FIELD_CONTEXTS.get(normalized, _FIELD_CONTEXTS["geral"]))


def _tokenize(text: Any) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-zA-ZÀ-ÿ0-9$%]+", _clean(text).lower())
        if len(token) >= 4 and token not in _STOPWORDS
    ]


def _salient_terms(values: list[Any], limit: int = 10) -> list[str]:
    tokens_by_order: list[str] = []
    counts: Counter[str] = Counter()
    seen: set[str] = set()
    for value in values:
        for token in _tokenize(value):
            counts[token] += 1
            if token not in seen:
                seen.add(token)
                tokens_by_order.append(token)

    ranked = sorted(
        tokens_by_order,
        key=lambda token: (-counts[token], tokens_by_order.index(token)),
    )
    return ranked[:limit]


def _extract_causal_chain(intel: Any) -> dict[str, Any]:
    slide_breakdown = getattr(intel, "slide_breakdown", []) or []
    trigger_candidates: list[str] = []
    for slide in slide_breakdown[:2]:
        if not isinstance(slide, dict):
            continue
        trigger_candidates.extend([
            slide.get("title", ""),
            slide.get("summary", ""),
            slide.get("main_point", ""),
        ])

    argument_steps = [
        step.strip()
        for step in re.split(r"->|→|\||/+", _clean(getattr(intel, "argument_structure", "")))
        if step.strip()
    ]
    mechanism_candidates = list(getattr(intel, "technical_claims", []) or [])
    mechanism_candidates.extend(argument_steps)
    mechanism_candidates.append(getattr(intel, "content_gaps", ""))

    return {
        "fato_disparador": _unique(trigger_candidates + [getattr(intel, "core_argument", "")], limit=2),
        "mecanismos": _unique(mechanism_candidates, limit=5),
        "provas": _unique(
            _data_labels(getattr(intel, "data_points", []) or [])
            + list(getattr(intel, "sources_referenced", []) or []),
            limit=6,
        ),
        "regra_de_transferencia": (
            "Troque o contexto do case, mas preserve a logica: o que disparou o problema, "
            "por que ele aconteceu, qual prova o sustenta e o que isso muda no agro."
        ),
    }


def build_source_creative_brief(source_post: Any, top_args: list[Any], validated_catalog: dict[str, Any]) -> dict[str, Any]:
    intel = source_post.intelligence
    core_argument = _clean(getattr(intel, "core_argument", ""))
    content_gaps = _clean(getattr(intel, "content_gaps", ""))
    data_points = getattr(intel, "data_points", []) or []
    claims = [claim for claim in getattr(intel, "technical_claims", []) or [] if _clean(claim)]
    bank_refs = [getattr(arg, "text", "") for arg in top_args]
    transcript = _trim(getattr(intel, "visual_transcript", ""), limit=1200)
    segment = getattr(intel, "agro_segment", None)

    tension_candidates = _unique([
        core_argument,
        content_gaps,
        *claims,
        *bank_refs,
    ], limit=5)
    data_to_dramatize = _unique(
        _data_labels(data_points)
        + list(validated_catalog.get("numeros_obrigatoriamente_ancorados_no_material_base") or []),
        limit=6,
    )
    causal_chain = _extract_causal_chain(intel)
    mechanism_terms = _salient_terms(
        [
            core_argument,
            content_gaps,
            *claims,
            *(point.get("context", "") for point in data_points if isinstance(point, dict)),
            getattr(intel, "argument_structure", ""),
            transcript,
        ],
        limit=10,
    )

    return {
        "mandato_criativo": "Gerar um carrossel tecnicamente fiel, mas com alto potencial de retencao e compartilhamento no agro.",
        "tensoes_para_explorar": tension_candidates,
        "dados_para_dramatizar": data_to_dramatize,
        "cadeia_causal_a_preservar": causal_chain,
        "mecanismos_que_nao_podem_sumir": mechanism_terms,
        "contextos_de_campo": _field_contexts(segment),
        "territorios_de_engajamento": list(_ENGAGEMENT_ARCHETYPES),
        "perguntas_de_retencao": [
            "Qual decisao muda quando este dado entra na conversa?",
            "Onde o produtor, consultor ou vendedor costuma errar por falta de criterio?",
            "Que contraste deixa o problema impossivel de ignorar?",
        ],
        "o_que_nao_fazer": [
            "Nao resumir um case complexo em 'gestao importa'.",
            "Nao pular da provocacao para o CTA sem explicar o mecanismo.",
            "Nao apagar a prova numerica ou a origem do argumento.",
        ],
        "transcricao_literal_resumida_para_criacao": transcript,
        "diretrizes": list(CREATIVE_INTELLIGENCE_DIRECTIVES),
    }


def build_theme_creative_brief(
    theme: str,
    posts: list[Any],
    top_args: list[Any],
    report: Any | None,
) -> dict[str, Any]:
    top_posts = posts[:5]
    post_tensions = _unique(
        [
            getattr(post.intelligence, "core_argument", "")
            for post in top_posts
        ]
        + [
            claim
            for post in top_posts
            for claim in (getattr(post.intelligence, "technical_claims", []) or [])[:2]
        ],
        limit=8,
    )
    data_to_dramatize = _unique(
        [
            label
            for post in top_posts
            for label in _data_labels(getattr(post.intelligence, "data_points", []) or [])
        ],
        limit=8,
    )
    segments = _unique([getattr(post.intelligence, "agro_segment", "") for post in top_posts], limit=3)
    field_contexts = _unique(
        [context for segment in segments for context in _field_contexts(segment)],
        limit=8,
    )
    report_patterns = getattr(report, "language_patterns", {}) if report else {}

    return {
        "tema": theme,
        "mandato_criativo": "Encontrar o angulo mais forte entre dado validado, dor real do agro e conversa comercial memoravel.",
        "tensoes_para_explorar": post_tensions,
        "dados_para_dramatizar": data_to_dramatize,
        "contextos_de_campo": field_contexts or list(_FIELD_CONTEXTS["geral"]),
        "territorios_de_engajamento": list(_ENGAGEMENT_ARCHETYPES),
        "argumentos_do_banco_para_cruzar": _unique([getattr(arg, "text", "") for arg in top_args], limit=5),
        "padroes_de_linguagem_vencedores": report_patterns,
        "perguntas_de_retencao": [
            "Que abertura faria um profissional do agro parar o scroll?",
            "Qual implicacao pratica torna este tema salvavel?",
            "Qual prova deixa o carrossel impossivel de parecer opiniao solta?",
        ],
        "diretrizes": list(CREATIVE_INTELLIGENCE_DIRECTIVES),
    }
