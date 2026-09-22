"""Lab 6: the config/secret/log disciplines, locked in as tests.

The lab demos each rule once by hand. These tests make the demo permanent —
a future edit that loosens a bound or drops the mask fails the per-commit
gate instead of being noticed in production.
"""
import pytest
from pydantic import ValidationError

from fraud_service.config import Settings
from fraud_service.logging_setup import _mask_sensitive


@pytest.mark.unit
def test_defaults_build_from_a_clean_environment() -> None:
    s = Settings()
    assert s.block_threshold == 0.85
    assert s.model_path.exists()
    assert s.registry_token is None


@pytest.mark.unit
def test_unknown_prefixed_variable_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """A typo must crash at startup, not fall back to a silent default."""
    monkeypatch.setenv("FRAUD_MODLE_PATH", "models/fraud_model.joblib")
    with pytest.raises(ValidationError, match="FRAUD_MODLE_PATH"):
        Settings()


@pytest.mark.unit
@pytest.mark.parametrize("bad", ["8.5", "0.49", "1.0"])
def test_threshold_is_bounded(monkeypatch: pytest.MonkeyPatch, bad: str) -> None:
    monkeypatch.setenv("FRAUD_BLOCK_THRESHOLD", bad)
    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.unit
def test_missing_model_artefact_fails_fast_with_a_readable_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FRAUD_MODEL_PATH", "/nope/does-not-exist.joblib")
    with pytest.raises(ValidationError, match="model artefact not found"):
        Settings()


@pytest.mark.unit
def test_registry_token_never_renders_in_the_clear(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FRAUD_REGISTRY_TOKEN", "ghp_notarealtokenvalue")
    s = Settings()
    assert s.registry_token is not None
    assert "notarealtoken" not in repr(s)
    assert "notarealtoken" not in str(s.registry_token)
    # the single explicit seam for an intentional read
    assert s.registry_token.get_secret_value() == "ghp_notarealtokenvalue"


@pytest.mark.unit
@pytest.mark.parametrize("key", ["token", "Token", "PASSWORD", "secret",
                                 "national_id", "card_number"])
def test_sensitive_keys_are_masked_before_rendering(key: str) -> None:
    out = _mask_sensitive(None, "info", {"event": "x", key: "ghp_leakedvalue"})
    assert out[key] == "***MASKED***"


@pytest.mark.unit
def test_ordinary_fields_are_left_alone() -> None:
    out = _mask_sensitive(None, "info", {"event": "prediction_served", "decision": "block"})
    assert out["decision"] == "block"
