"""Batch entrypoint — the composition root for offline scoring.

This is the ONE place concrete implementations get wired together.
Compare this file to the messy Cell 6 loop in
notebooks/fraud_exploration.ipynb: same outcome (read CSV, score every
row, write scored.csv), but every piece here is swappable and testable
in isolation.
"""
import time

import pandas as pd

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.config import Settings
from fraud_service.domain.entities import Transaction
from fraud_service.service.scorer import FraudScorer


def main() -> None:
    settings = Settings()

    t0 = time.perf_counter()
    model = SklearnModel.load(settings.model_path)
    load_duration = time.perf_counter() - t0
    print(f"Loaded model version {model.model_version} in {load_duration:.2f}s")

    scorer = FraudScorer(model=model, block_threshold=settings.block_threshold)

    df = pd.read_csv("data/transactions_sample.csv")

    t1 = time.perf_counter()
    results = []
    for _, row in df.iterrows():
        txn = Transaction(
            transaction_id=row["transaction_id"],
            amount_sar=float(row["amount_sar"]),
            is_night=int(row["is_night"]),
        )
        results.append(scorer.score(txn))
    batch_duration = time.perf_counter() - t1

    out_df = pd.DataFrame(results)
    out_df.to_csv("scored.csv", index=False)

    counts = out_df["decision"].value_counts().to_dict()
    print(f"Scored {len(out_df)} transactions in {batch_duration:.2f}s -> scored.csv")
    print(f"Summary: {counts}")


if __name__ == "__main__":
    main()
