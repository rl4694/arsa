from http.client import (
    BAD_REQUEST,
    FORBIDDEN,
    NOT_ACCEPTABLE,
    NOT_FOUND,
    OK,
    SERVICE_UNAVAILABLE,
)

from unittest.mock import patch

import pytest

import server.endpoints as ep
import server.controllers.cities as ct
import server.controllers.states as st
import server.controllers.nations as nt

TEST_CLIENT = ep.app.test_client()


@pytest.fixture(autouse=True)
def _reset_stores():
    """Reset all data stores before and after each test to prevent state leakage."""
    # Clear all stores before test
    if hasattr(ct, "cities") and isinstance(ct.cities, dict):
        ct.cities.clear()
    if hasattr(st, "states") and isinstance(st.states, dict):
        st.states.clear()
    if hasattr(nt, "nations") and isinstance(nt.nations, dict):
        nt.nations.clear()
    
    yield
    
    # Clear all stores after test
    if hasattr(ct, "cities") and isinstance(ct.cities, dict):
        ct.cities.clear()
    if hasattr(st, "states") and isinstance(st.states, dict):
        st.states.clear()
    if hasattr(nt, "nations") and isinstance(nt.nations, dict):
        nt.nations.clear()


def test_hello():
    resp = TEST_CLIENT.get(ep.HELLO_EP)
    resp_json = resp.get_json()
    assert ep.HELLO_RESP in resp_json
