"""EEG sintético para las pruebas (no son datos reales) y acceso al paquete sin instalar."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# Permite ejecutar las pruebas aunque el paquete no esté instalado con `pip install -e .`.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

CHANNELS = ["C3", "Cz", "C4", "P7", "P8", "P3", "Pz", "P4", "O1", "O2"]
SFREQ = 250.0


def synthetic_epochs(seed: int, n_epochs: int = 12, label: int = 0) -> np.ndarray:
    """Épocas de 4 s ``(n_épocas, 10, 1000)`` en µV con ruido 1/f, alfa y theta."""
    rng = np.random.default_rng(seed)
    n_t = 1000
    t = np.arange(n_t) / SFREQ
    freqs = np.fft.rfftfreq(n_t, 1 / SFREQ)
    alpha_f = 10.0 if label == 0 else 9.2
    out = np.empty((n_epochs, len(CHANNELS), n_t))
    for e in range(n_epochs):
        for c in range(len(CHANNELS)):
            spec = (rng.normal(size=freqs.size) + 1j * rng.normal(size=freqs.size)) / np.maximum(freqs, 1.0) ** 0.9
            pink = np.fft.irfft(spec, n=n_t)
            out[e, c] = (8 * pink / pink.std()
                         + (1 + 0.8 * (c >= 3)) * 12 * np.sin(2 * np.pi * alpha_f * t + rng.uniform(0, 6.28))
                         + 5 * np.sin(2 * np.pi * rng.uniform(5, 7) * t + rng.uniform(0, 6.28)))
    return out
