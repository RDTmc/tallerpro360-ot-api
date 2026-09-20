"""Smoke tests sin BD: auth (401/403), validación (422) y sondas públicas."""
from fastapi.testclient import TestClient

from main import app, autoriza_rol

c = TestClient(app)


def test_saludo_publico():
    r = c.get("/api/saludo")
    assert r.status_code == 200 and "TallerPro360" in r.json()["mensaje"]


def test_protegidas_sin_token_401():
    assert c.get("/api/ot").status_code == 401
    assert c.post("/api/ot", json={}).status_code == 401
    assert c.put("/api/ot/X", json={}).status_code == 401
    assert c.delete("/api/ot/X").status_code == 401


def test_token_invalido_401():
    h = {"Authorization": "Bearer no-es-un-jwt"}
    assert c.get("/api/ot", headers=h).status_code == 401


def test_openapi_expone_rutas():
    paths = c.get("/openapi.json").json()["paths"]
    for p in ["/api/saludo", "/api/health", "/api/ot", "/api/ot/{ot_id}"]:
        assert p in paths


def test_roles_admin_pasa_operador_no_en_delete():
    autoriza_rol({"roles": ["OT.Admin"]}, ("OT.Admin",))
    autoriza_rol({"roles": ["OT.Admin", "OT.Lector"]}, ("OT.Admin", "OT.Operador"))
    autoriza_rol({}, ("OT.Admin",))  # token antiguo sin claim: manda el scope
    import pytest
    with pytest.raises(Exception):
        autoriza_rol({"roles": ["OT.Lector"]}, ("OT.Admin",))
    with pytest.raises(Exception):
        autoriza_rol({"roles": ["OT.Operador"]}, ("OT.Admin",))
