from unittest.mock import patch
from src.generator.seasonal import get_seasonal_context


def test_returns_string():
    ctx = get_seasonal_context()
    assert isinstance(ctx, str)
    assert len(ctx) > 20


def test_march_april_context():
    with patch("src.generator.seasonal.datetime") as mock_dt:
        mock_dt.now.return_value.month = 3
        ctx = get_seasonal_context()
    assert "soja" in ctx.lower()
    assert "colheita" in ctx.lower()


def test_july_august_context():
    with patch("src.generator.seasonal.datetime") as mock_dt:
        mock_dt.now.return_value.month = 7
        ctx = get_seasonal_context()
    assert "soja" in ctx.lower()
    assert "plantio" in ctx.lower() or "planejamento" in ctx.lower()


def test_november_december_context():
    with patch("src.generator.seasonal.datetime") as mock_dt:
        mock_dt.now.return_value.month = 11
        ctx = get_seasonal_context()
    assert "soja" in ctx.lower()
