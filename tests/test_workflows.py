"""Controles estáticos de los workflows reutilizables de sulaco."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
REUTILIZABLES = sorted(p for p in (RAIZ / ".github" / "workflows").glob("*.yml") if p.name != "ci.yml")
EJEMPLOS = sorted((RAIZ / "ejemplos").glob("*.yml"))


def _cargar(ruta: Path) -> dict:
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    # PyYAML interpreta la clave `on:` como el booleano True.
    datos["on"] = datos.pop(True, datos.get("on"))
    return datos


def _pasos(datos: dict):
    for trabajo in datos.get("jobs", {}).values():
        yield from trabajo.get("steps", [])


def test_hay_workflows():
    assert {p.name for p in REUTILIZABLES} == {"evaluar.yml", "proctoring.yml"}


@pytest.mark.parametrize("ruta", REUTILIZABLES, ids=lambda p: p.name)
def test_es_reutilizable_y_con_permisos_minimos(ruta):
    datos = _cargar(ruta)
    assert "workflow_call" in datos["on"]
    assert datos["permissions"] == {"contents": "read"}
    for nombre, entrada in datos["on"]["workflow_call"].get("inputs", {}).items():
        assert entrada.get("description"), f"{nombre} sin descripción"


@pytest.mark.parametrize("ruta", REUTILIZABLES, ids=lambda p: p.name)
def test_acciones_fijadas_por_version(ruta):
    for paso in _pasos(_cargar(ruta)):
        if "uses" in paso:
            assert re.search(r"@(v\d+|[0-9a-f]{40})$", paso["uses"]), paso["uses"]


@pytest.mark.parametrize("ruta", REUTILIZABLES, ids=lambda p: p.name)
def test_sin_inyeccion_de_entradas_en_scripts(ruta):
    """Las entradas y los datos del evento pasan por env:, nunca interpolados en run:."""
    for paso in _pasos(_cargar(ruta)):
        script = paso.get("run", "")
        assert "${{ inputs." not in script and "${{ github.event." not in script, script


@pytest.mark.parametrize("ruta", REUTILIZABLES, ids=lambda p: p.name)
def test_herramientas_propias_solo_desde_git(ruta):
    for paso in _pasos(_cargar(ruta)):
        for linea in paso.get("run", "").splitlines():
            if re.search(r"uv tool install|uvx|pip install", linea):
                assert "git+https://github.com/" in linea, linea


@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=lambda p: p.name)
def test_los_ejemplos_usan_entradas_declaradas(ejemplo):
    for trabajo in _cargar(ejemplo)["jobs"].values():
        destino = re.match(r"INGCOM-UNRN-P1/sulaco/\.github/workflows/([\w-]+\.yml)@v\d+\.\d+\.\d+$", trabajo["uses"])
        assert destino, trabajo["uses"]
        llamado = _cargar(RAIZ / ".github" / "workflows" / destino.group(1))["on"]["workflow_call"]
        assert set(trabajo.get("with", {})) <= set(llamado.get("inputs", {}))
        requeridos = {n for n, s in llamado.get("secrets", {}).items() if s.get("required")}
        assert requeridos <= set(trabajo.get("secrets", {}))
