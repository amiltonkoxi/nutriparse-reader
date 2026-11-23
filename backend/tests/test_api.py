import pytest
from fastapi.testclient import TestClient

from nutriparse import api


@pytest.fixture
def client():
    return TestClient(api.app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_rejects_non_pdf(client):
    r = client.post("/extract", files={"file": ("x.pdf", b"hello, not a pdf", "application/pdf")})
    assert r.status_code == 415


def test_rejects_large_upload(client, monkeypatch):
    monkeypatch.setattr(api, "MAX_UPLOAD_MB", 0.001)
    r = client.post("/extract", files={"file": ("big.pdf", b"%PDF-" + b"0" * 5000, "application/pdf")})
    assert r.status_code == 413


def test_rejects_broken_pdf(client):
    r = client.post("/extract", files={"file": ("bad.pdf", b"%PDF-1.4 broken", "application/pdf")})
    assert r.status_code == 422


def test_rejects_too_many_pages(client, monkeypatch, spec_pdf):
    monkeypatch.setattr(api, "MAX_PAGES", 0)
    with open(spec_pdf, "rb") as fh:
        r = client.post("/extract", files={"file": ("spec.pdf", fh, "application/pdf")})
    assert r.status_code == 422


def test_extract_end_to_end(client, spec_pdf):
    with open(spec_pdf, "rb") as fh:
        r = client.post("/extract", files={"file": ("spec.pdf", fh, "application/pdf")})
    assert r.status_code == 200
    body = r.json()
    a = body["allergens"]
    assert len(a) == 14
    assert a["gluten"]["status"] == "contains"
    assert a["sesame"]["status"] == "contains"
    assert a["milk"]["status"] == "traces"
    assert a["gluten"]["evidence"] and a["gluten"]["page"] == 1
    assert body["meta"]["pages"] == 1
    assert body["meta"]["extraction_mode"] == "text"
    assert body["nutrition_per_100g"]["protein_g"] == pytest.approx(9.5)
    assert body["nutrition_per_100g"]["salt_g"] == pytest.approx(1.2)


def test_cors_does_not_allow_credentials(client):
    r = client.options("/extract", headers={"Origin": "http://localhost:3000",
                                            "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-credentials") is None
    r = client.options("/extract", headers={"Origin": "https://evil.vercel.app",
                                            "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers
