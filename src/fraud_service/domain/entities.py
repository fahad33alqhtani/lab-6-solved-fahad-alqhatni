"""Domain entities: the vocabulary of the fraud problem.

Rules for this file:
- imports from stdlib + pydantic ONLY
- no I/O, no framework types, no ML library types
"""
import math

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    transaction_id: str
    amount_sar: float = Field(gt=0)
    is_night: int = Field(ge=0, le=1)

    def to_features(self) -> "FeatureVector":
        """Single source of feature logic shared by training AND serving —
        the primary defence against training/serving skew."""
        return FeatureVector(values={
            "amount_log": math.log1p(self.amount_sar),
            "is_night": self.is_night,
        })


class FeatureVector(BaseModel):
    values: dict[str, float | int]
