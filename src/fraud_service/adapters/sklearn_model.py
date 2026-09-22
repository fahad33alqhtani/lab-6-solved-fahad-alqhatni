"""The ONLY file in this service allowed to import sklearn/joblib.

If the team ever moves to ONNX or a remote model server, they add a
sibling adapter and change one line in the composition root.
"""
from pathlib import Path
from typing import Any

import joblib  # type: ignore[import-untyped]
import pandas as pd


class SklearnModel:
    def __init__(self, pipeline: Any, model_version: str) -> None:
        self._pipeline = pipeline
        self.model_version = model_version

    @classmethod
    def load(cls, path: str | Path) -> "SklearnModel":
        """Explicit, failable loading — called ONLY from the composition
        root (batch.py here; the FastAPI lifespan in Lab 2), never at
        import time."""
        bundle = joblib.load(path)  # {"pipeline": ..., "version": "v3.2.0"}
        return cls(bundle["pipeline"], bundle["version"])

    def predict_proba(self, features: dict[str, float]) -> float:
        frame = pd.DataFrame([features])
        return float(self._pipeline.predict_proba(frame)[0, 1])
