import pytest

from fraud_service.domain.policies import decide


@pytest.mark.unit
@pytest.mark.parametrize("p, expected", [
    (0.849999, "review"),   # just under the block threshold
    (0.85,     "block"),    # boundary is inclusive
    (0.699999, "allow"),
    (0.70,     "review"),
    (0.0,      "allow"),
    (1.0,      "block"),
])
def test_decision_bands(p, expected):
    assert decide(p, block_threshold=0.85) == expected
