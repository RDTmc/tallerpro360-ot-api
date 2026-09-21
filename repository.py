"""Capa de repositorios TallerPro360 (entidades = esquemas Pydantic en main.py).

Toda query va parametrizada ($1, $2...) — sin concatenación de SQL.
Las escrituras multi-tabla usan una única transacción sobre una conexión
adquirida del pool (el pool solo presta conexiones, no transacciona).
"""
import asyncpg


async def listar_resumen(pool: asyncpg.Pool, q: str = "") -> list[dict]:
    if q:
        like = f"%{q}%"
        rows = await pool.fetch(
            "SELECT * FROM v_ot_resumen WHERE ot_id ILIKE $1 OR cliente_id ILIKE $1"
            " OR patente ILIKE $1 OR descripcion ILIKE $1 ORDER BY created_at DESC",
            like,
        )
    else:
        rows = await pool.fetch("SELECT * FROM v_ot_resumen ORDER BY created_at DESC")
    return [dict(r) for r in rows]


async def obtener_con_items(pool: asyncpg.Pool, ot_id: str) -> dict | None:
    ot = await pool.fetchrow("SELECT * FROM ot WHERE ot_id = $1", ot_id)
    if not ot:
        return None
    items = await pool.fetch(
        "SELECT * FROM ot_item WHERE ot_id = $1 ORDER BY item_id", ot_id
    )
    return {**dict(ot), "items": [dict(i) for i in items]}


async def crear(pool: asyncpg.Pool, datos) -> dict:
    """Crea OT + ítems + evento de auditoría en una transacción."""
    async with pool.acquire() as conn, conn.transaction():
        ot_id = await conn.fetchval(
            "INSERT INTO ot (cliente_id, patente, descripcion, total)"
            " VALUES ($1,$2,$3,$4) RETURNING ot_id",
            datos.cliente_id, datos.patente, datos.descripcion, datos.total,
        )
        for it in datos.items:
            await conn.execute(
                "INSERT INTO ot_item (ot_id, concepto, cantidad, precio_unit)"
                " VALUES ($1,$2,$3,$4)",
                ot_id, it.concepto, it.cantidad, it.precio_unit,
            )
        await conn.execute(
            "INSERT INTO ot_event (ot_id, event_type, payload_json)"
            " VALUES ($1,'OtCreada',$2)",
            ot_id, f'{{"eventType":"OtCreada","otId":"{ot_id}"}}',
        )
    return await obtener_con_items(pool, ot_id)


async def actualizar(pool: asyncpg.Pool, ot_id: str, datos) -> dict | None:
    """Actualiza cabecera y reemplaza ítems (transaccional)."""
    async with pool.acquire() as conn, conn.transaction():
        row = await conn.fetchval(
            "UPDATE ot SET cliente_id=$2, patente=$3, descripcion=$4, total=$5,"
            " updated_at=now() WHERE ot_id=$1 RETURNING ot_id",
            ot_id, datos.cliente_id, datos.patente, datos.descripcion, datos.total,
        )
        if not row:
            return None
        await conn.execute("DELETE FROM ot_item WHERE ot_id=$1", ot_id)
        for it in datos.items:
            await conn.execute(
                "INSERT INTO ot_item (ot_id, concepto, cantidad, precio_unit)"
                " VALUES ($1,$2,$3,$4)",
                ot_id, it.concepto, it.cantidad, it.precio_unit,
            )
    return await obtener_con_items(pool, ot_id)


async def eliminar(pool: asyncpg.Pool, ot_id: str) -> bool:
    row = await pool.fetchval("DELETE FROM ot WHERE ot_id=$1 RETURNING ot_id", ot_id)
    return row is not None


# ---------------------------------------------------------------- clientes
async def buscar_clientes(pool: asyncpg.Pool, q: str = "") -> list[dict]:
    if q:
        like = f"%{q}%"
        rows = await pool.fetch(
            "SELECT rut, codigo, nombres, apellidos, fecha_nac, correo, telefono"
            " FROM cliente WHERE rut ILIKE $1 OR codigo ILIKE $1"
            " OR nombres ILIKE $1 OR apellidos ILIKE $1 ORDER BY nombres LIMIT 20",
            like,
        )
    else:
        rows = await pool.fetch(
            "SELECT rut, codigo, nombres, apellidos, fecha_nac, correo, telefono"
            " FROM cliente ORDER BY nombres LIMIT 20"
        )
    return [dict(r) for r in rows]


async def crear_cliente(pool: asyncpg.Pool, datos) -> dict:
    row = await pool.fetchrow(
        "INSERT INTO cliente (rut, codigo, nombres, apellidos, fecha_nac, correo, telefono)"
        " VALUES ($1,$2,$3,$4,$5,$6,$7)"
        " RETURNING rut, codigo, nombres, apellidos, fecha_nac, correo, telefono",
        datos.rut, datos.codigo, datos.nombres, datos.apellidos,
        datos.fecha_nac, datos.correo, datos.telefono,
    )
    return dict(row)


async def existe_cliente(pool: asyncpg.Pool, codigo: str) -> bool:
    return await pool.fetchval("SELECT 1 FROM cliente WHERE codigo=$1", codigo) is not None
