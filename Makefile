# Atajos del proyecto. En Windows sin `make`, ejecute los comandos de cada regla directamente.
PYTHON ?= python

.PHONY: install data validate test portable check clean

install:        ## Instala dependencias y el paquete en modo editable
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e . --no-deps

data:           ## Descarga OpenNeuro ds003490
	bash scripts/download_openneuro.sh

validate:       ## Valida los cuadernos (JSON, sintaxis, rutas)
	$(PYTHON) scripts/validate_notebooks.py

test:           ## Ejecuta las pruebas unitarias
	$(PYTHON) -m unittest discover -s tests -v

portable:       ## Regenera las copias portátiles desde notebooks/original
	$(PYTHON) scripts/build_portable_notebooks.py

check: validate test

clean:          ## Borra artefactos locales (no toca datos ni cuadernos)
	rm -rf artifacts build dist src/*.egg-info
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
