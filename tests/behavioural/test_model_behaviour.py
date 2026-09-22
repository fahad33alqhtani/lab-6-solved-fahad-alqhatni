import csv
import pathlib

import pytest

pytestmark = [pytest.mark.behavioural, pytest.mark.slow]

GOLDEN_FILE = pathlib.Path(__file__).parent / "golden_scores.csv"


def _score(model, txn):
    return model.predict_proba(txn.to_features().values)


def test_invariance_to_transaction_id_casing(real_model, sample_txn):
    a = _score(real_model, sample_txn)
    b = _score(real_model, sample_txn.model_copy(
        update={"transaction_id": sample_txn.transaction_id.lower()}))
    assert a == pytest.approx(b, abs=1e-9)


def test_directional_amount(real_model, sample_txn):
    small = _score(real_model, sample_txn.model_copy(
        update={"amount_sar": 50.0}))
    large = _score(real_model, sample_txn.model_copy(
        update={"amount_sar": 50_000.0}))
    assert large >= small - 1e-6


def test_golden_scores_match_reference(real_model):
    """5,000 reference scores, regenerated only through a deliberate,
    reviewed step (scripts/regen_golden.py) — never silently, just to
    make a failing test pass. A failure here means the model changed
    or training/serving has drifted (skew): stop and investigate.
    """
    assert GOLDEN_FILE.exists(), (
        "golden_scores.csv is missing — run scripts/regen_golden.py once "
        "to create the initial reference file (a reviewed, deliberate step)."
    )
    with GOLDEN_FILE.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5000

    mismatches = []
    for row in rows:
        features = {
            "amount_log": float(row["amount_log"]),
            "is_night": int(row["is_night"]),
        }
        actual = real_model.predict_proba(features)
        expected = float(row["fraud_probability"])
        if abs(actual - expected) > 1e-6:
            mismatches.append((row["transaction_id"], expected, actual))

    assert not mismatches, (
        f"{len(mismatches)} of {len(rows)} rows drifted from the golden "
        f"reference (showing first 5): {mismatches[:5]}"
    )
