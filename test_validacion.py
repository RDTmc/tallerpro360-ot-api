"""Validaciones de dominio sin BD: esquemas Pydantic y normalización."""
import pytest

from main import ClienteIn, OTIn, normalizar


def test_ot_valida_minima():
    ot = OTIn(cliente_id="CLI-001", patente="AABB11")
    assert ot.total == 0 and ot.items == []


def test_ot_rechaza_datos_malos():
    with pytest.raises(Exception):
        OTIn(cliente_id="CLI-001", patente="X", total=-5,
             items=[{"concepto": "", "cantidad": -1, "precio_unit": -1}])


def test_normalizar_mayusculas_sin_espacios():
    ot = normalizar(OTIn(cliente_id="cli-001", patente="zz xx99"))
    assert ot.cliente_id == "CLI-001" and ot.patente == "ZZXX99"


def test_cliente_fecha_invalida():
    with pytest.raises(Exception):
        ClienteIn(rut="1-9", codigo="CLI-9", nombres="A", apellidos="B",
                  fecha_nac="20-01-1995")


def test_cliente_ok_sin_opcionales():
    c = ClienteIn(rut="55555555-5", codigo="CLI-005", nombres="Ana", apellidos="Rojas")
    assert c.fecha_nac is None and c.correo is None
