# server/controllers/tests/test_nations.py
import pytest
from flask import Flask
from types import SimpleNamespace
from unittest.mock import Mock
import pycountry
from server.controllers.nations import NationList, Nation, NATIONS_RESP
from server.controllers.nations import nations as nt

@pytest.fixture()
def app():
    app = Flask(__name__)
    app.testing = True
    return app

class TestNationsController:
    def test_post_derives_iso_code(self, app, monkeypatch):
        monkeypatch.setattr(
            pycountry.countries,
            "get",
            lambda **kw: SimpleNamespace(alpha_2="US") if kw == {"name": "United States"} else None,
        )

        create_mock = Mock(return_value="id123")
        select_mock = Mock(return_value={"_id": "id123", "code": "us", "name": "United States"})
        monkeypatch.setattr(nt, "create", create_mock)
        monkeypatch.setattr(nt, "select", select_mock)

        with app.test_request_context(json={"name": "United States"}):
            resp, status = NationList().post()

        assert status == 201
        assert resp == {NATIONS_RESP: {"_id": "id123", "code": "us", "name": "United States"}}

        sent = create_mock.call_args.args[0]
        assert sent["name"] == "United States"
        assert sent["code"] == "US"
        assert sent["_id"] == "US"
        assert create_mock.call_args.kwargs == {"recursive": False}
        select_mock.assert_called_once_with("id123")

    def test_put_with_name_recreates(self, app, monkeypatch):
        monkeypatch.setattr(
            pycountry.countries,
            "get",
            lambda **kw: SimpleNamespace(alpha_2="CA") if kw == {"name": "Canada"} else None,
        )

        delete_mock = Mock()
        create_mock = Mock(return_value="id456")
        select_mock = Mock(return_value={"_id": "id456", "code": "ca", "name": "Canada"})
        update_mock = Mock()

        monkeypatch.setattr(nt, "delete", delete_mock)
        monkeypatch.setattr(nt, "create", create_mock)
        monkeypatch.setattr(nt, "select", select_mock)
        monkeypatch.setattr(nt, "update", update_mock)

        with app.test_request_context(json={"name": "Canada"}):
            resp = Nation().put("id789")

        delete_mock.assert_called_once_with("id789")
        sent = create_mock.call_args.args[0]
        assert sent["name"] == "Canada"
        assert sent["code"] == "CA"
        update_mock.assert_not_called()
        select_mock.assert_called_once_with("id456")
        assert resp == {NATIONS_RESP: {"_id": "id456", "code": "ca", "name": "Canada"}}

    def test_put_without_name_calls_update(self, app, monkeypatch):
        delete_mock = Mock()
        create_mock = Mock()
        update_mock = Mock()
        select_mock = Mock(return_value={"_id": "id123", "code": "us", "name": "United States"})

        monkeypatch.setattr(nt, "delete", delete_mock)
        monkeypatch.setattr(nt, "create", create_mock)
        monkeypatch.setattr(nt, "update", update_mock)
        monkeypatch.setattr(nt, "select", select_mock)

        with app.test_request_context(json={"code": "ignored"}):
            resp = Nation().put("id123")

        update_mock.assert_called_once_with("id123", {"code": "ignored"})
        select_mock.assert_called_once_with("id123")
        delete_mock.assert_not_called()
        create_mock.assert_not_called()
        assert resp == {NATIONS_RESP: {"_id": "id123", "code": "us", "name": "United States"}}  