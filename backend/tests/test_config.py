"""Configuration safety tests."""

import pytest

from config import ProductionConfig


def test_production_rejects_default_secrets():
    class UnsafeProductionConfig(ProductionConfig):
        SECRET_KEY = "change-me-in-production-please"
        JWT_SECRET_KEY = "jwt-secret-change-me"

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        UnsafeProductionConfig.validate()


def test_production_accepts_long_independent_secrets():
    class SafeProductionConfig(ProductionConfig):
        SECRET_KEY = "a" * 48
        JWT_SECRET_KEY = "b" * 48

    SafeProductionConfig.validate()

