"""Regenerate tests/behavioural/golden_scores.csv from the current model.

This is a DELIBERATE, REVIEWED step — never run it just to make a failing
golden-file test pass. Run it only when a model change is intentional and
justified, then include the diff in the PR as evidence for a reviewer.

Usage: python scripts/regen_golden.py
"""
import csv
import math
import pathlib

import pandas as pd

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.config import Settings

OUT = pathlib.Path(__file__).parent.parent / "tests/behavioural/golden_scores.csv"


def main() -> None:
    settings = Settings()
    model = SklearnModel.load(settings.model_path)
    df = pd.read_csv("data/transactions_sample.csv")

    rows = []
    for _, row in df.iterrows():
        amount_log = math.log1p(float(row["amount_sar"]))
        is_night = int(row["is_night"])
        prob = model.predict_proba({"amount_log": amount_log, "is_night": is_night})
        rows.append({
            "transaction_id": row["transaction_id"],
            "amount_log": amount_log,
            "is_night": is_night,
            "fraud_probability": prob,
            "model_version": model.model_version,
        })

    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} golden scores to {OUT} (model {model.model_version})")


if __name__ == "__main__":
    main()
