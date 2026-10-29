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
    assert {p.name for p in REUTILIZABLES} == {"cohorte.yml", "evaluar.yml", "proctoring.yml", "proctoring-audit.yml"}


EJECUTA_CODIGO = re.compile(r"\b(ripley|dredd|make|gcc|mother)\b")


@pytest.mark.parametrize("ruta", REUTILIZABLES, ids=lambda p: p.name)
def test_es_reutilizable_y_con_permisos_minimos(ruta):
    datos = _cargar(ruta)
    assert "workflow_call" in datos["on"]
    # A nivel del workflow, lectura o nada (evaluar.yml: nada, para que `comentar` herede del llamador).
    assert datos.get("permissions") in (None, {"contents": "read"})
    for nombre, entrada in datos["on"]["workflow_call"].get("inputs", {}).items():
        assert entrada.get("description"), f"{nombre} sin descripción"


@pytest.mark.parametrize("ruta", REUTILIZABLES, ids=lambda p: p.name)
def test_el_codigo_de_la_entrega_corre_con_token_de_solo_lectura(ruta):
    """Un job que compila o ejecuta código (ripley, dredd, make, gcc) declara permisos de lectura,
    sin escritura aunque el llamador otorgue más, y su checkout no guarda credenciales (Ola 25)."""
    for nombre, trabajo in _cargar(ruta)["jobs"].items():
        pasos = trabajo.get("steps", [])
        if not any(EJECUTA_CODIGO.search(p.get("run", "")) for p in pasos):
            continue
        assert trabajo.get("permissions") == {"contents": "read"}, nombre
        for paso in pasos:
            if str(paso.get("uses", "")).startswith("actions/checkout"):
                assert paso.get("with", {}).get("persist-credentials") is False, nombre


@pytest.mark.parametrize("ruta", REUTILIZABLES, ids=lambda p: p.name)
def test_los_secretos_nunca_llegan_al_codigo_de_los_alumnos(ruta):
    """Ni en el env del job ni en un paso que compile o ejecute código."""
    for trabajo in _cargar(ruta)["jobs"].values():
        assert "secrets." not in str(trabajo.get("env", {}))
        for paso in trabajo.get("steps", []):
            if re.search(r"\b(ripley|dredd|make|gcc)\b", paso.get("run", "")):
                assert "secrets." not in str(paso.get("env", {})), paso.get("name")


def test_evaluar_separa_la_ejecucion_de_la_publicacion():
    jobs = _cargar(RAIZ / ".github" / "workflows" / "evaluar.yml")["jobs"]
    assert set(jobs) == {"evaluar", "comentar", "sarif"}
    for publicador in ("comentar", "sarif"):
        assert jobs[publicador]["needs"] == "evaluar"
        assert not any(EJECUTA_CODIGO.search(p.get("run", "")) for p in jobs[publicador]["steps"])
    assert "pull_request_target" in jobs["evaluar"]["steps"][0]["if"]
    script = next(p["run"] for p in jobs["comentar"]["steps"] if "PATCH" in p.get("run", ""))
    assert "sulaco:devolucion" in script  # un solo comentario, actualizado en cada push
    paso_ripley = next(p for p in jobs["evaluar"]["steps"] if p.get("id") == "ripley")
    assert "--sarif ripley.sarif" in paso_ripley["run"] and paso_ripley["run"].count("ripley check") == 1


def test_cohorte_quita_el_token_antes_de_ejecutar_codigo():
    pasos = _cargar(RAIZ / ".github" / "workflows" / "cohorte.yml")["jobs"]["cohorte"]["steps"]
    clonar = next(p for p in pasos if p.get("name") == "Clonar las entregas")
    assert "secrets.token" in clonar["env"]["GH_TOKEN"] and "remote set-url origin" in clonar["run"]
    dredd = next(p for p in pasos if "dredd" in p.get("run", ""))
    assert "secrets." not in str(dredd.get("env", {}))


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


def test_la_integridad_por_push_no_usa_la_clave_privada():
    """proctoring-audit.yml corre en el repositorio del alumno: sólo la clave pública, sin descifrar
    la evidencia, y las alertas heurísticas no se publican salvo `detalle: true` (Ola 28)."""
    datos = _cargar(RAIZ / ".github" / "workflows" / "proctoring-audit.yml")
    assert set(datos["on"]["workflow_call"]["secrets"]) == {"clave_publica"}
    texto = (RAIZ / ".github" / "workflows" / "proctoring-audit.yml").read_text(encoding="utf-8")
    assert "--decrypt-key" not in texto.split("name: Integridad")[1]
    assert datos["on"]["workflow_call"]["inputs"]["detalle"]["default"] is False
    verificar = next(p for p in _pasos(datos) if p.get("name") == "Verificar la cadena")
    assert "%0A" in verificar["run"]  # los mensajes se escapan antes de volverlos anotaciones
