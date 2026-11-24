"""Demo: el test de arquitectura detecta una violación de la regla hexagonal.

Crea un archivo temporal dentro de domain/ que importa de adapters/ (prohibido),
ejecuta el test de arquitectura (falla), borra el archivo y lo ejecuta otra vez
(pasa). El archivo se borra siempre, aunque la demo se interrumpa.

Uso, desde la carpeta del proyecto:
    python -m demos.romper_arquitectura
"""

import functools
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
print = functools.partial(print, flush=True)  # que los mensajes salgan en orden con la salida de pytest
ARCHIVO_TEMPORAL = RAIZ / "domain" / "violacion_demo.py"
CONTENIDO = "from adapters.monitoring_config import MonitoringConfig  # prohibido: domain no puede depender de adapters\n"


def ejecutar_test() -> None:
    subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_arquitectura.py", "-q", "--no-header", "--tb=short", "-p", "no:cacheprovider"],
        cwd=RAIZ,
    )


def main() -> None:
    print("1) Se crea domain/violacion_demo.py con este contenido:")
    print(f"     {CONTENIDO.strip()}\n")
    try:
        ARCHIVO_TEMPORAL.write_text(CONTENIDO, encoding="utf-8")
        print("2) Test de arquitectura con la violación (debe FALLAR):")
        ejecutar_test()
    finally:
        ARCHIVO_TEMPORAL.unlink(missing_ok=True)
    print("\n3) Se borra el archivo. Test de arquitectura otra vez (debe PASAR):")
    ejecutar_test()


if __name__ == "__main__":
    main()
