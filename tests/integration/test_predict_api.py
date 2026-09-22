import json
import pathlib

import pytest

MALFORMED = sorted(
    pathlib.Path("payloads/malformed").glob("*.json"))


@pytest.mark.integration
def test_predict_contract(client_factory, sample_txn):
    client = client_factory(probability=0.93)  # forces block
    r = client.post("/v1/predict",
        json=json.loads(sample_txn.model_dump_json()))
    assert r.status_code == 200
    assert r.json()["decision"] == "block"


@pytest.mark.integration
@pytest.mark.parametrize("payload_file", MALFORMED)
def test_malformed_corpus_rejected(client_factory, payload_file):
    r = client_factory().post("/v1/predict",
        content=payload_file.read_bytes(),
        headers={"content-type": "application/json"})
    assert 400 <= r.status_code < 500, payload_file.name


@pytest.mark.integration
def test_predict_500_hides_stack_trace(client_factory, sample_txn, monkeypatch):
    client = client_factory()
    def boom(self, txn):
        raise ZeroDivisionError("seeded failure")
    monkeypatch.setattr(
        "fraud_service.service.scorer.FraudScorer.score", boom)
    r = client.post("/v1/predict",
        json=json.loads(sample_txn.model_dump_json()))
    assert r.status_code == 500
    assert "ZeroDivisionError" not in r.text


@pytest.mark.integration
def test_health():
    from fastapi.testclient import TestClient

    from fraud_service.api.app import app
    with TestClient(app) as client:
        response = client.get("/v1/health")
        assert response.status_code == 200


@pytest.mark.integration
def test_ready_ok_once_lifespan_has_run():
    from fastapi.testclient import TestClient

    from fraud_service.api.app import app
    with TestClient(app) as client:
        response = client.get("/v1/ready")
        assert response.status_code == 200


@pytest.mark.integration
def test_ready_503_before_lifespan_runs():
    # a fresh app whose lifespan has never run has no scorer yet —
    # /ready must say so, not silently look ready.
    from fastapi.testclient import TestClient

    from fraud_service.api.app import create_app
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.get("/v1/ready")
    assert response.status_code == 503


@pytest.mark.integration
def test_predict_503_before_lifespan_runs(sample_txn):
    # same idea, but through the predict route's get_scorer dependency
    from fastapi.testclient import TestClient

    from fraud_service.api.app import create_app
    client = TestClient(create_app(), raise_server_exceptions=False)
    r = client.post("/v1/predict", json=json.loads(sample_txn.model_dump_json()))
    assert r.status_code == 503
    assert r.headers.get("retry-after") == "5"
