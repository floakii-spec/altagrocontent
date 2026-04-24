# tests/test_post_intelligence_evidence.py
from unittest.mock import MagicMock, patch

from src.analyzer.post_intelligence import _extract_evidence_inventory


def _mock_gpt_response(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


_SAMPLE_DATA = {
    "technical_claims": ["patrimônio líquido negativo em R$ 427 milhões", "SAF acumulou R$ 2,5bi em passivos"],
    "data_points": [
        {"value": "R$ 2,5bi", "context": "passivos totais", "source": None},
        {"value": "R$ 427mi", "context": "patrimônio negativo", "source": None},
    ],
    "sources_referenced": ["BDO", "Demonstrações Contábeis SAF"],
    "core_argument": "modelo dependia de capital externo que nunca chegou",
}

_SAMPLE_GPT_JSON = """{
  "mechanisms": ["recuperação judicial", "patrimônio líquido negativo"],
  "causal_steps": [
    "Textor compra SAF em 2022",
    "Clube ganha Libertadores em novembro de 2024",
    "Capital prometido não chegou"
  ],
  "definitions": [
    {"term": "recuperação judicial", "definition": "proteção temporária contra credores"}
  ]
}"""


def test_extract_evidence_inventory_required_numbers():
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_gpt_response(_SAMPLE_GPT_JSON)
        result = _extract_evidence_inventory("Slide 1: conteúdo", _SAMPLE_DATA, "legenda")
    assert "R$ 2,5bi" in result["required"]["numbers"]
    assert "R$ 427mi" in result["required"]["numbers"]


def test_extract_evidence_inventory_required_mechanisms():
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_gpt_response(_SAMPLE_GPT_JSON)
        result = _extract_evidence_inventory("Slide 1", _SAMPLE_DATA, "legenda")
    assert "recuperação judicial" in result["required"]["mechanisms"]
    assert "patrimônio líquido negativo" in result["required"]["mechanisms"]


def test_extract_evidence_inventory_causal_steps():
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_gpt_response(_SAMPLE_GPT_JSON)
        result = _extract_evidence_inventory("Slide 1", _SAMPLE_DATA, "legenda")
    assert len(result["required"]["causal_steps"]) == 3
    assert "Textor compra SAF em 2022" in result["required"]["causal_steps"]


def test_extract_evidence_inventory_definitions():
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_gpt_response(_SAMPLE_GPT_JSON)
        result = _extract_evidence_inventory("Slide 1", _SAMPLE_DATA, "legenda")
    assert result["required"]["definitions"][0]["term"] == "recuperação judicial"


def test_extract_evidence_inventory_optional_fields():
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_gpt_response(_SAMPLE_GPT_JSON)
        result = _extract_evidence_inventory("Slide 1", _SAMPLE_DATA, "legenda")
    assert "BDO" in result["optional"]["sources"]
    assert result["optional"]["context"] == "modelo dependia de capital externo que nunca chegou"


def test_extract_evidence_inventory_gpt_failure_returns_partial():
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        mock_client.chat.completions.create.side_effect = Exception("timeout")
        result = _extract_evidence_inventory("Slide 1", _SAMPLE_DATA, "legenda")
    # numbers still extracted from data_points even if GPT fails
    assert "R$ 2,5bi" in result["required"]["numbers"]
    assert result["required"]["causal_steps"] == []
    assert result["required"]["definitions"] == []
