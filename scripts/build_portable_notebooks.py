"""Genera las copias portátiles de los cuadernos a partir de los originales.

Uso (desde la raíz del repositorio):

    python scripts/build_portable_notebooks.py

Lee ``notebooks/original/*.ipynb`` y escribe en ``notebooks/`` una copia sin
salidas en la que solo cambia la infraestructura de archivos:

* el montaje de Google Drive se ejecuta únicamente si ``USE_GOOGLE_DRIVE=1``;
* ``FINAL_ROOT`` toma ``PARKINSON_EEG_ROOT`` (por defecto ``<repo>/artifacts``);
* ``BASE_DIR`` (cuaderno 01) toma ``PARKINSON_EEG_DATA`` (por defecto ``<repo>/data/openneuro``);
* las instalaciones ``!pip`` se comentan (el entorno se crea con ``requirements.txt``);
* el comentario sobre la carpeta de salidas remite a ``PARKINSON_EEG_ROOT``.

Los parámetros científicos no se modifican. Los originales no se tocan.
"""

from __future__ import annotations

import ast
import copy
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC_DIR = REPO / "notebooks" / "original"
DST_DIR = REPO / "notebooks"

#: original -> copia portátil
NAMES = {
    "01_UNM_preprocesamiento.ipynb": "01_preprocessing.ipynb",
    "02A_UNM_enfoque_A.ipynb": "02a_functional_frequency.ipynb",
    "02B_UNM_enfoque_B.ipynb": "02b_functional_epoch_order.ipynb",
    "03_UNM_modelado.ipynb": "03_modeling.ipynb",
    "04_UNM_aporte_ADF.ipynb": "04_ablation_adf.ipynb",
    "05_UNM_interpretabilidad_ADF.ipynb": "05_interpretability.ipynb",
}

MOUNT_SNIPPET = """# Rutas portátiles: Google Drive solo se monta si USE_GOOGLE_DRIVE=1 (Colab).
import os
from pathlib import Path

if os.environ.get('USE_GOOGLE_DRIVE') == '1':
    from google.colab import drive
    if not Path('/content/drive/MyDrive').exists():
        drive.mount('/content/drive')
else:
    print('Ejecución local: se usan PARKINSON_EEG_ROOT y PARKINSON_EEG_DATA.')"""

ROOT_HELPER = """import os  # rutas portátiles (ver docs/reproducibility.md)
_REPO_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()"""

FINAL_ROOT_RE = re.compile(r"""^FINAL_ROOT\s*=\s*Path\(\s*['"]/content/drive/MyDrive/tesis_parkinson/resultados['"]\s*\)\s*$""")
BASE_DIR_RE = re.compile(r"""^BASE_DIR\s*=\s*Path\(\s*['"]/content/openneuro_datasets['"]\s*\)\s*$""")
FINAL_ROOT_NEW = "FINAL_ROOT = Path(os.environ.get('PARKINSON_EEG_ROOT', _REPO_ROOT / 'artifacts')).expanduser().resolve()"
BASE_DIR_NEW = "BASE_DIR = Path(os.environ.get('PARKINSON_EEG_DATA', _REPO_ROOT / 'data' / 'openneuro')).expanduser().resolve()"

#: Ajustes de texto ligados a la portabilidad (solo en las copias portátiles).
TEXT_FIXES = {
    "# Carpeta raíz de salidas. Modificar esta línea para usar otra ubicación.":
        "# Carpeta raíz de salidas: defina PARKINSON_EEG_ROOT para usar otra ubicación.",
}

#: Bloque de montaje en línea a nivel superior (cuadernos 03 y 05).
TOP_MOUNT_RE = re.compile(
    r"^(from google\.colab import drive|# Montar Google Drive\.|"
    r"if not Path\('/content/drive/MyDrive'\)\.exists\(\):|    drive\.mount\('/content/drive'\))\s*$"
)


def _is_mount_only_cell(src: str) -> bool:
    """Celda dedicada exclusivamente a montar Drive (cuadernos 01, 02A, 02B y 04)."""
    return "drive.mount" in src and "FINAL_ROOT" not in src and "def " not in src


def _transform_code(src: str) -> str:
    if _is_mount_only_cell(src):
        return MOUNT_SNIPPET
    lines = src.split("\n")
    out: list[str] = []
    helper_added = False
    mount_removed = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("!pip"):
            out.append("# " + stripped + "  # instalar con requirements.txt")
            continue
        if TOP_MOUNT_RE.match(line):
            if not mount_removed:
                out.extend(MOUNT_SNIPPET.split("\n"))
                mount_removed = True
            continue
        if FINAL_ROOT_RE.match(line) or BASE_DIR_RE.match(line):
            if not helper_added:
                helper = ROOT_HELPER.split("\n")
                out.extend(helper[1:] if mount_removed else helper)  # 'import os' ya viene del bloque de montaje
                helper_added = True
            out.append(FINAL_ROOT_NEW if FINAL_ROOT_RE.match(line) else BASE_DIR_NEW)
            continue
        out.append(line)
    text = "\n".join(out)
    # 'drive' queda sin uso tras eliminar el montaje en línea (cuadernos 03 y 05).
    text = text.replace("else:\n    print('Google Drive ya esta montado.')", "")
    return text


def _apply_text_fixes(src: str) -> str:
    for old, new in TEXT_FIXES.items():
        src = src.replace(old, new)
    return src


def _check_syntax(code: str, where: str) -> None:
    clean = "\n".join(line for line in code.split("\n") if not line.lstrip().startswith(("!", "%")))
    ast.parse(clean, filename=where)


def convert(src_path: Path, dst_path: Path) -> None:
    nb = json.loads(src_path.read_text(encoding="utf-8"))
    out = copy.deepcopy(nb)
    for i, cell in enumerate(out["cells"]):
        src = "".join(cell.get("source", []))
        if cell["cell_type"] == "code":
            src = _transform_code(src)
            cell["outputs"] = []
            cell["execution_count"] = None
        src = _apply_text_fixes(src)
        if cell["cell_type"] == "code":
            _check_syntax(src, f"{dst_path.name}[{i}]")
        lines = src.split("\n")
        cell["source"] = [line + "\n" for line in lines[:-1]] + [lines[-1]] if lines else []
        cell.get("metadata", {}).pop("executionInfo", None)
        cell.get("metadata", {}).pop("outputId", None)
    out.get("metadata", {}).pop("widgets", None)
    dst_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    for src_name, dst_name in NAMES.items():
        src = SRC_DIR / src_name
        if not src.is_file():
            raise FileNotFoundError(f"No existe {src}")
        convert(src, DST_DIR / dst_name)
        print(f"{src_name}  ->  notebooks/{dst_name}")


if __name__ == "__main__":
    main()
