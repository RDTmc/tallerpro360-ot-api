# TallerPro360 OT API
Microservicio de órdenes de trabajo: FastAPI + PostgreSQL + JWT (Entra ID).

## Correr local
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql://tallerpro360:<password>@<host>:5432/tallerpro360'
uvicorn main:app --host 127.0.0.1 --port 5001
```
Docs interactivas: `http://127.0.0.1:5001/docs` (solo desarrollo).

## Variables (ningún secreto en el código)
| Variable | Ejemplo |
|---|---|
| `DATABASE_URL` (**requerida**, sin default) | `postgresql://user:pass@host:5432/tallerpro360` |
| `TENANT_ID`, `APP_CLIENT_ID` | IDs públicos de Entra (tienen default del curso) |
| `REQUIRED_SCOPE` | `productos.read` |

## Seguridad
JWT v2.0 (firma, vigencia, issuer, audience) + scope + roles `OT.Admin/Operador/Lector` por endpoint. Códigos: `401` sin/inválido, `403` sin permiso, `404`, `422` validación, `201/200`.

## Tests y CI
`pytest -q` (smoke + validación, sin BD). Ver `.github/workflows/`.
