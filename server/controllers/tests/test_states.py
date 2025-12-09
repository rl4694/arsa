# server/controllers/tests/test_states.py
import pytest
from flask import Flask
from types import SimpleNamespace
from unittest.mock import Mock
import pycountry
from server.controllers.states import StateList, State, STATES_RESP
from server.controllers.states import states as st

@pytest.fixture()
def app():
    app = Flask(__name__)
    app.testing = True
    return app

class TestStatesController:
    def test_post_derives_state_iso_code(self, app, monkeypatch):
        monkeypatch.setattr(
            pycountry.subdivisions,
            "get",
            lambda **kw: [SimpleNamespace(code="US-NY", name="New York")] if kw == {"country_code": "US"} else [],
        )

        create_mock = Mock(return_value="id123")
        select_mock = Mock(return_value={
            "_id": "id123",
            "name": "New York",
            "nation_code": "US",
            "code": "ny",
            "state_id": "us-ny",
        })
        monkeypatch.setattr(st, "create", create_mock)
        monkeypatch.setattr(st, "select", select_mock)

        with app.test_request_context(json={"name": "New York", "nation_code": "us"}):
            resp, status = StateList().post()

        assert status == 201
        assert resp == {STATES_RESP: {
            "_id": "id123",
            "name": "New York",
            "nation_code": "US",
            "code": "ny",
            "state_id": "us-ny",
        }}

        sent = create_mock.call_args.args[0]
        assert sent["name"] == "New York"
        assert sent["nation_code"] == "US"
        assert sent["code"] == "NY"
        assert sent["state_id"] == "US-NY"
        assert create_mock.call_args.kwargs == {"recursive": False}
        select_mock.assert_called_once_with("id123")

    def test_put_with_name_recreates_state(self, app, monkeypatch):
        monkeypatch.setattr(
            pycountry.subdivisions,
            "get",
            lambda **kw: [SimpleNamespace(code="CA-ON", name="Ontario")] if kw == {"country_code": "CA"} else [],
        )

        delete_mock = Mock()
        create_mock = Mock(return_value="id456")
        select_mock = Mock(side_effect=[
            {"_id": "oldid", "name": "Ontario", "nation_code": "CA", "code": "on", "state_id": "ca-on"},
            {"_id": "oldid", "name": "Ontario", "nation_code": "CA", "code": "on", "state_id": "ca-on"},
            {"_id": "id456", "name": "Ontario", "nation_code": "CA", "code": "on", "state_id": "ca-on"},
        ])
        update_mock = Mock()

        monkeypatch.setattr(st, "delete", delete_mock)
        monkeypatch.setattr(st, "create", create_mock)
        monkeypatch.setattr(st, "select", select_mock)
        monkeypatch.setattr(st, "update", update_mock)

        with app.test_request_context(json={"nation_code": "ca"}):
            resp = State().put("oldid")

        delete_mock.assert_called_once_with("oldid")
        sent = create_mock.call_args.args[0]
        assert sent["nation_code"] == "ca"
        assert sent["code"] == "ON"
        assert sent["state_id"] == "ca-ON"
        update_mock.assert_not_called()
        assert resp == {STATES_RESP: {"_id": "id456", "name": "Ontario", "nation_code": "CA", "code": "on", "state_id": "ca-on"}}

    def test_put_without_name_updates_state(self, app, monkeypatch):
        delete_mock = Mock()
        create_mock = Mock()
        update_mock = Mock()
        select_mock = Mock(return_value={"_id": "id123", "name": "New York", "nation_code": "US", "code": "ny", "state_id": "us-ny"})

        monkeypatch.setattr(st, "delete", delete_mock)
        monkeypatch.setattr(st, "create", create_mock)
        monkeypatch.setattr(st, "update", update_mock)
        monkeypatch.setattr(st, "select", select_mock)

        with app.test_request_context(json={"nation_name": "ignored"}):
            resp = State().put("id123")

        update_mock.assert_called_once_with("id123", {"nation_name": "ignored"})
        select_mock.assert_called_once_with("id123")
        delete_mock.assert_not_called()
        create_mock.assert_not_called()
        assert resp == {STATES_RESP: {"_id": "id123", "name": "New York", "nation_code": "US", "code": "ny", "state_id": "us-ny"}}