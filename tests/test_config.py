import os
import pytest
from unittest.mock import patch


def test_config_loads_from_env():
    env = {
        "DATABASE_URL": "postgresql://u:p@localhost/test",
        "OPENAI_API_KEY": "sk-test",
        "APIFY_API_TOKEN": "apify-test",
    }
    with patch.dict(os.environ, env):
        from importlib import reload
        import src.config as config
        reload(config)
        assert config.DATABASE_URL == "postgresql://u:p@localhost/test"
        assert config.OPENAI_API_KEY == "sk-test"
        assert config.APIFY_API_TOKEN == "apify-test"


def test_config_raises_if_missing_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(KeyError):
            from importlib import reload
            import src.config as config
            reload(config)
