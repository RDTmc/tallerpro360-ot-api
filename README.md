# TallerPro360 OT API
Microservicio de órdenes de trabajo y clientes: FastAPI + PostgreSQL + JWT (Entra ID).

## Requisitos
Python 3.12 · PostgreSQL 16 (RDS) · `pip install -r requirements.txt`.

## Correr local
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql://tallerpro360:<password>@<host>:5432/tallerpro360'
uvicorn main:app --host 127.0.0.1 --port 5001
```
Docs interactivas: `http://127.0.0.1:5001/docs` (solo desarrollo).

## Estructura
`main.py` (rutas + auth + esquemas Pydantic), `repository.py` (SQL parametrizado + transacciones),
`test_smoke.py` / `test_validacion.py` (sin BD), `.env.example`, `.github/workflows/` (CI + deploy).

## Endpoints (`/api`)
| Método | Ruta | Auth | Respuestas |
|---|---|---|---|
| GET | `/saludo`, `/health` | pública | `200` / `503` sin DB |
| GET | `/ot?q=` | scope | `200`, `401` |
| GET | `/ot/{id}` | scope | `200`, `401`, `404` |
| POST | `/ot` | Admin/Operador | `201`, `401`, `403`, `422` |
| PUT | `/ot/{id}` | Admin/Operador | `200` (reemplaza ítems), `404`, `422` |
| DELETE | `/ot/{id}` | Admin | `200`, `403`, `404` |
| GET/POST | `/clientes[?q=]` | scope / Admin+Operador | `200`, `201`, `409`, `422` |

## Variables (ningún secreto en el código)
| Variable | Ejemplo |
|---|---|
| `DATABASE_URL` (**requerida**, sin default) | `postgresql://user:pass@host:5432/tallerpro360` |
| `TENANT_ID`, `APP_CLIENT_ID` | IDs públicos de Entra (default del curso) |
| `REQUIRED_SCOPE` | `productos.read` |

## Seguridad
JWT v2.0 (firma JWKS, vigencia, issuer, audience) + scope + roles `OT.Admin/Operador/Lector` por endpoint.
En producción el secreto va en `/etc/ot-api.env` (600) vía `EnvironmentFile` de systemd.

## Deploy
Push a `main` → CI (`pytest`) → Deploy (Solo si CI ok): S3 + SSM (`pull`, `compile`, `restart`, `health`).

## Tests y CI
`pytest -q` (10 tests: auth, roles, validación, OpenAPI; sin BD). Ver `.github/workflows/`.
