"""Use-case orchestration: score one transaction.

Note what is ABSENT here: no FastAPI, no sklearn, no file paths, no
logging configuration. Pure orchestration = trivially testable.
"""
from dataclasses import dataclass
from typing import Any

from fraud_service.domain.entities import Transaction
from fraud_service.domain.policies import decide
from fraud_service.service.interfaces import Model


@dataclass
class FraudScorer:
    model: Model
    block_threshold: float

    def score(self, txn: Transaction) -> dict[str, Any]:
        features = txn.to_features()
        raw_prob = self.model.predict_proba(features.values)
        decision = decide(raw_prob, self.block_threshold)
        return {
            "transaction_id": txn.transaction_id,
            "probability": raw_prob,
            "decision": decision,
            "model_version": self.model.model_version,
        }
