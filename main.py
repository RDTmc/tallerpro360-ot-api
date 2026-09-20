"""Microservicio TallerPro360 - Órdenes de Trabajo (FastAPI + PostgreSQL + JWT).

Seguridad: misma receta probada en la Guía 4 (PyJWKClient + Entra ID v2.0).
Dominio: tablas ot / ot_item / ot_event / notify_log (Script_postgres.sql).
"""
import os
from functools import lru_cache

import asyncpg
import jwt
import repository
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

# ---------------------------------------------------------------- config
TENANT_ID = os.getenv("TENANT_ID", "a4cc5fc6-a27b-43af-91af-bab64b4e97ce")
APP_CLIENT_ID = os.getenv("APP_CLIENT_ID", "94997922-80e9-4664-8743-85316d34ba1b")
ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
AUDIENCE = APP_CLIENT_ID
REQUIRED_SCOPE = os.getenv("REQUIRED_SCOPE", "productos.read")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://tallerpro360:ChangeMe_2025!@localhost:5432/tallerpro360"
)

app = FastAPI(title="TallerPro360 OT API", version="1.0.0")
_pool: asyncpg.Pool | None = None


# ---------------------------------------------------------------- seguridad
@lru_cache(maxsize=1)
def _jwks_client() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(JWKS_URL)


async def verificar_token(authorization: str = Header(default="")) -> dict:
    """401 si falta/inválido, 403 si no trae el scope. Igual que Flask Guía 4."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta token")
    token = authorization.split(" ", 1)[1]
    try:
        key = _jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token, key.key, algorithms=[key.algorithm_name],
            audience=AUDIENCE, issuer=ISSUER,
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")
    if REQUIRED_SCOPE not in str(payload.get("scp", "")).split():
        raise HTTPException(status_code=403, detail="Scope no autorizado")
    return payload


# ---------------------------------------------------------------- db
async def pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return _pool


# ---------------------------------------------------------------- esquemas
class ItemIn(BaseModel):
    concepto: str = Field(min_length=1, max_length=40)
    cantidad: float = Field(gt=0, le=999999)
    precio_unit: int = Field(ge=0, le=999999999)


class OTIn(BaseModel):
    cliente_id: str = Field(min_length=1, max_length=20)
    patente: str = Field(min_length=6, max_length=10)
    descripcion: str = Field(default="", max_length=200)
    total: int = Field(default=0, ge=0, le=99999999999)
    items: list[ItemIn] = Field(default=[], max_length=100)


def normalizar(datos: OTIn) -> OTIn:
    """Mayúsculas y sin espacios: evita duplicados tipo 'xx yy11' vs 'XXYY11'."""
    datos.cliente_id = datos.cliente_id.strip().upper()
    datos.patente = datos.patente.strip().upper().replace(" ", "").replace("-", "")
    datos.descripcion = datos.descripcion.strip()
    return datos


# ---------------------------------------------------------------- rutas
@app.get("/api/health")
async def health():
    """Sonda pública para monitoreo/demo (no expone datos)."""
    try:
        p = await pool()
        await p.fetchval("SELECT 1")
        return {"status": "ok", "db": "up"}
    except Exception:
        raise HTTPException(status_code=503, detail="DB no disponible")


@app.get("/api/saludo")
async def saludo():
    return {"mensaje": "Hola desde TallerPro360"}


@app.get("/api/ot")
async def listar_ot(_: dict = Depends(verificar_token)):
    p = await pool()
    return await repository.listar_resumen(p)


@app.get("/api/ot/{ot_id}")
async def obtener_ot(ot_id: str, _: dict = Depends(verificar_token)):
    ot = await repository.obtener_con_items(await pool(), ot_id)
    if not ot:
        raise HTTPException(status_code=404, detail="OT no encontrada")
    return ot


@app.post("/api/ot", status_code=201)
async def crear_ot(datos: OTIn, _: dict = Depends(verificar_token)):
    return await repository.crear(await pool(), normalizar(datos))


@app.put("/api/ot/{ot_id}")
async def actualizar_ot(ot_id: str, datos: OTIn, _: dict = Depends(verificar_token)):
    ot = await repository.actualizar(await pool(), ot_id, normalizar(datos))
    if not ot:
        raise HTTPException(status_code=404, detail="OT no encontrada")
    return ot


@app.delete("/api/ot/{ot_id}")
async def eliminar_ot(ot_id: str, _: dict = Depends(verificar_token)):
    ok = await repository.eliminar(await pool(), ot_id)
    if not ok:
        raise HTTPException(status_code=404, detail="OT no encontrada")
    return {"mensaje": f"OT {ot_id} eliminada"}
