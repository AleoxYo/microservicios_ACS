"""Test de arquitectura: verifica automáticamente la regla de dependencias del estilo Hexagonal.

Las dependencias apuntan siempre hacia el dominio:
    domain       -> (nada del proyecto)
    ports        -> domain
    application  -> domain, ports
    adapters     -> domain, ports, adapters   (nunca application)
Solo main.py (composition root) puede importar de todas las capas.
"""

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
CAPAS = ("domain", "ports", "application", "adapters")

PERMITIDAS = {
    "domain": {"domain"},
    "ports": {"domain", "ports"},
    "application": {"domain", "ports", "application"},
    "adapters": {"domain", "ports", "adapters"},
}


def capas_importadas(archivo: Path) -> set[str]:
    """Retorna las capas del proyecto que importa un archivo .py."""
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    modulos: list[str] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.extend(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            modulos.append(nodo.module)
    return {m.split(".")[0] for m in modulos} & set(CAPAS)


@pytest.mark.parametrize("capa", CAPAS)
def test_capa_respeta_regla_de_dependencias(capa: str) -> None:
    violaciones = []
    for archivo in (RAIZ / capa).rglob("*.py"):
        prohibidas = capas_importadas(archivo) - PERMITIDAS[capa]
        if prohibidas:
            violaciones.append(f"{archivo.relative_to(RAIZ)} importa {sorted(prohibidas)}")
    assert not violaciones, "Violaciones de la arquitectura hexagonal:\n" + "\n".join(violaciones)
