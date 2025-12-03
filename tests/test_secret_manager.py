import os
from types import SimpleNamespace

import pytest

from my_agent import secret_manager


class DummySecretManagerClient:
    def __init__(self, payload: bytes):
        self._payload = payload

    def access_secret_version(self, name: str):  # pragma: no cover - exercised via wrapper
        return SimpleNamespace(payload=SimpleNamespace(data=self._payload))


def test_load_secret_into_env_sets_value(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY_SECRET_ID", "my-secret")
    monkeypatch.setenv("GCP_PROJECT_ID", "demo-project")

    dummy_client = DummySecretManagerClient(b"from-secret")
    monkeypatch.setattr(
        secret_manager.secretmanager,
        "SecretManagerServiceClient",
        lambda: dummy_client,
    )

    secret_manager.load_secret_into_env("GOOGLE_API_KEY", "GOOGLE_API_KEY_SECRET_ID")
    assert os.getenv("GOOGLE_API_KEY") == "from-secret"


def test_load_secret_into_env_no_secret_id(monkeypatch):
    monkeypatch.delenv("TEST_VAR", raising=False)
    monkeypatch.delenv("TEST_VAR_SECRET_ID", raising=False)

    secret_manager.load_secret_into_env("TEST_VAR", "TEST_VAR_SECRET_ID")
    assert os.getenv("TEST_VAR") is None


def test_get_secret_requires_project_for_short_name(monkeypatch):
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    with pytest.raises(ValueError):
        secret_manager.get_secret_value("short-secret-name")
