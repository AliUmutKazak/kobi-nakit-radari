"""Testlerde ortak sentetik veri."""
import pytest

from radar.synthetic import generate

AS_OF = "2026-10-01"


@pytest.fixture(scope="module")
def full():
    return generate(seed=3, n_customers=25, months=18, as_of=AS_OF)
