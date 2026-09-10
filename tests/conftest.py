import pytest

from src.utils import tokenomics


@pytest.fixture(autouse=True)
def _reset_tokenomics_log():
    tokenomics.reset_log()
    yield
    tokenomics.reset_log()
