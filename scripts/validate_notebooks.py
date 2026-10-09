"""Valida los cuadernos sin ejecutarlos (usado por la integración continua).

Comprueba:

* que existen los seis cuadernos portátiles y los seis originales;
* integridad JSON y esquema nbformat (si ``nbformat`` está instalado);
* sintaxis Python de cada celda, ignorando comandos mágicos y de shell;
* que las copias portátiles no guardan salidas ni montan Drive sin ``USE_GOOGLE_DRIVE``;
* que las copias portátiles no contienen rutas fijas de resultados en Google Drive.

Uso: ``python scripts/validate_notebooks.py`` (código de salida 1 si algo falla).
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PORTABLE = [
    "01_preprocessing.ipynb",
    "02a_functional_frequency.ipynb",
    "02b_functional_epoch_order.ipynb",
    "03_modeling.ipynb",
    "04_ablation_adf.ipynb",
    "05_interpretability.ipynb",
]
ORIGINAL = [
    "01_UNM_preprocesamiento.ipynb",
    "02A_UNM_enfoque_A.ipynb",
    "02B_UNM_enfoque_B.ipynb",
    "03_UNM_modelado.ipynb",
    "04_UNM_aporte_ADF.ipynb",
    "05_UNM_interpretabilidad_ADF.ipynb",
]


def _code(cell: dict) -> str:
    src = "".join(cell.get("source", []))
    return "\n".join(line for line in src.split("\n") if not line.lstrip().startswith(("!", "%")))


def check(path: Path, portable: bool) -> list[str]:
    """Devuelve la lista de problemas encontrados en un cuaderno."""
    errors: list[str] = []
    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path.name}: JSON inválido ({exc})"]
    try:
        import nbformat

        nbformat.validate(nbformat.reads(json.dumps(nb), as_version=4))
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001 - se informa cualquier error de esquema
        errors.append(f"{path.name}: esquema nbformat inválido ({exc})")
    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        code = _code(cell)
        try:
            ast.parse(code)
        except SyntaxError as exc:
            errors.append(f"{path.name}[celda {i}]: error de sintaxis ({exc.msg}, línea {exc.lineno})")
        if portable:
            if cell.get("outputs"):
                errors.append(f"{path.name}[celda {i}]: la copia portátil no debe guardar salidas")
            if "/content/drive/MyDrive/tesis_parkinson" in code:
                errors.append(f"{path.name}[celda {i}]: ruta fija de Google Drive")
            if "drive.mount('/content/drive')" in code and "USE_GOOGLE_DRIVE" not in code:
                errors.append(f"{path.name}[celda {i}]: montaje de Drive sin USE_GOOGLE_DRIVE")
    return errors


def main() -> int:
    errors: list[str] = []
    for folder, names, portable in ((REPO / "notebooks", PORTABLE, True),
                                    (REPO / "notebooks" / "original", ORIGINAL, False)):
        for name in names:
            path = folder / name
            if not path.is_file():
                errors.append(f"Falta {path.relative_to(REPO)}")
                continue
            found = check(path, portable)
            errors.extend(found)
            print(f"{'OK   ' if not found else 'ERROR'} {path.relative_to(REPO)}")
    if errors:
        print("\nProblemas encontrados:")
        for err in errors:
            print(" -", err)
        return 1
    print(f"\n{len(PORTABLE) + len(ORIGINAL)} cuadernos validados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
