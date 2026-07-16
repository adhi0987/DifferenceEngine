"""Shared pytest fixtures: isolated DB + TestClient with seeded demo data."""
from __future__ import annotations

import os
import tempfile

# Configure the environment BEFORE any application module is imported, so the
# module-level SQLAlchemy engine binds to an isolated temporary database.
_TMP_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TMP_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.name}"
os.environ["JWT_SECRET"] = "test-secret-key-that-is-long-enough-32b"
os.environ["STORAGE_ROOT"] = tempfile.mkdtemp(prefix="attendiq-storage-")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.main as main  # noqa: E402
import app.seed as seed  # noqa: E402
from app.database import Base, engine  # noqa: E402


@pytest.fixture()
def client():
    """A TestClient over a freshly recreated + seeded database per test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed.seed()
    with TestClient(main.app) as c:
        yield c


def login(client, email, password="Password@123"):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["accessToken"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}
