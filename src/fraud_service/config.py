"""Typed, fail-fast configuration. One place to read every environment
variable — never scatter os.environ["X"] across the codebase.

Lab 6 hardening: unknown FRAUD_* variables are a startup crash, not a
silent default; block_threshold is bounded; the model artefact must
exist before any loading code runs; the registry token is a SecretStr
so it cannot leak through a repr, a print, or a log line.
"""
import os
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FRAUD_",      # FRAUD_MODEL_PATH -> model_path
        env_file=".env",          # dev only; prod uses real env vars
        extra="forbid",           # unknown FRAUD_* = crash, not a silent default
    )

    model_path: Path = Field(
        default=Path("models/fraud_model.joblib"),
        description="Path to the joblib model bundle",
    )
    # NOTE: defaults are passed as default=..., not positionally. mypy --strict
    # (a Lab 5 CI gate) only recognises the keyword form as "this field has a
    # default"; Field(0.85, ...) makes every call site fail with
    # "Missing named argument block_threshold for Settings".
    block_threshold: float = Field(
        default=0.85, ge=0.5, le=0.99,
        description="Risk-approved block threshold",
    )
    log_level: str = Field(default="INFO", description="Root log level for structlog/stdlib")
    git_sha: str = Field(
        default="dev", description="Commit the image was built from; CI injects FRAUD_GIT_SHA"
    )
    registry_token: SecretStr | None = Field(
        default=None,
        description="Registry credential; masked in reprs — read via .get_secret_value()",
    )

    @field_validator("model_path")
    @classmethod
    def model_file_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"model artefact not found: {v}")
        return v

    @model_validator(mode="before")
    @classmethod
    def reject_unknown_prefixed_vars(cls, data: Any) -> Any:
        """extra="forbid" only sees what a source actually collected: it
        catches a stray FRAUD_* line in .env, but pydantic-settings reads
        os.environ by known field name only, so a typo'd PROCESS env var
        (FRAUD_MODLE_PATH=...) would be silently ignored. This is the ONE
        sanctioned os.environ read in the codebase — it exists to make the
        typo crash, not to fetch a value.
        """
        prefix = "FRAUD_"
        known = {f"{prefix}{name}".upper() for name in cls.model_fields}
        stray = sorted(k for k in os.environ if k.upper().startswith(prefix) and k.upper() not in known)
        if stray:
            raise ValueError(
                f"unknown {prefix}* environment variable(s): {', '.join(stray)} "
                f"— known: {', '.join(sorted(known))}"
            )
        return data


settings = Settings()
