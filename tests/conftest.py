import pytest
from fastapi.testclient import TestClient

from fraud_service.api.app import create_app
from fraud_service.api.routes import get_scorer
from fraud_service.domain.entities import Transaction
from fraud_service.service.scorer import FraudScorer


class ConstantModel:
    """Test double standing in for sklearn — ten lines drive every decision branch."""
    def __init__(self, probability, version="test-1"):
        self._p = probability
        self.model_version = version

    def predict_proba(self, features: dict) -> float:
        return self._p


@pytest.fixture
def client_factory():
    def _make(probability=0.10, threshold=0.85):
        app = create_app()
        scorer = FraudScorer(model=ConstantModel(probability),
                              block_threshold=threshold)
        app.dependency_overrides[get_scorer] = lambda: scorer
        return TestClient(app, raise_server_exceptions=False)
    return _make


@pytest.fixture(scope="session")
def real_model():
    from fraud_service.adapters.sklearn_model import SklearnModel
    return SklearnModel.load("models/fraud_model.joblib")


@pytest.fixture
def sample_txn():
    return Transaction(transaction_id="TXN-TEST-00001",
                        amount_sar=500.0, is_night=0)
