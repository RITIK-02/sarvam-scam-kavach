"""Offline smoke tests for CI: no Sarvam calls, a dummy key is enough."""
import os

os.environ.setdefault("SARVAM_API_KEY", "ci-dummy")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "Scam Kavach" in r.text


def test_health():
    assert client.get("/api/health").json() == {"ok": True}


def test_languages():
    langs = client.get("/api/languages").json()
    assert "hi-IN" in langs and "en-IN" in langs


def test_check_rejects_empty():
    assert client.post("/api/check", data={"language": "hi-IN"}).status_code == 400


def test_check_rejects_unknown_language():
    assert client.post("/api/check", data={"language": "xx-XX", "text": "hi"}).status_code == 400
