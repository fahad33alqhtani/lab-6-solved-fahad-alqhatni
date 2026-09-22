"""Service-layer interfaces (ports). The service depends on THESE, never
on a concrete ML framework — this is what lets you swap sklearn for
XGBoost, ONNX, or a remote model server later by changing exactly one
adapter file.
"""
from typing import Protocol


class Model(Protocol):
    """Anything that can score a feature vector.

    Implementations: SklearnModel (prod), ConstantModel (tests),
    RemoteModel (future). The service layer knows ONLY this signature.
    """

    model_version: str

    def predict_proba(self, features: dict[str, float]) -> float: ...
