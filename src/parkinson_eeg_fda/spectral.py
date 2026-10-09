"""Estimación espectral común a la línea base y a los Enfoques A y B (Sección 3.3 de la tesis).

Todas las funciones reciben épocas en µV con forma ``(n_épocas, n_canales, n_muestras)``.
Parámetros por defecto: Welch con ventanas de 2 s y 50 % de solapamiento
(resolución ≈ 0,5 Hz a 250 Hz), potencia total de referencia en 1-30 Hz
integrada con la regla de Simpson y ``eps = 1e-20``.

Origen de cada función (código original refactorizado):

* :func:`relative_log_psd_epochs` - ``psd_rel_log_epochs`` (cuadernos 02A y 04) y
  ``relative_log_psd`` (cuaderno 01, con ``band=(1, 30)``).
* :func:`band_relative_power_epochs` - ``psd_linear_epochs`` + ``band_power_per_epoch`` (02B).
* :func:`average_linear_psd` y :func:`baseline_scalar_features` - ``_psd_avg_subject`` y
  ``_scalar_features`` (línea base sin ADF, cuaderno 03).
* :func:`theta_alpha_scalar_features` - cuaderno 04.
* :func:`compute_paf` - ``compute_paf_subject`` (cuaderno 01).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
from scipy.integrate import simpson
from scipy.signal import welch

EPS: float = 1e-20

#: Bandas de la línea base escalar (theta y pre-alfa se solapan en 5,5-8 Hz).
BASELINE_BANDS: dict[str, tuple[float, float]] = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "pre_alpha": (5.5, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
}


def welch_psd(
    data_uv: np.ndarray,
    sfreq: float,
    window_sec: float = 2.0,
    overlap: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """PSD de Welch (µV²/Hz) a lo largo del último eje.

    ``nperseg = min(sfreq·window_sec, n_muestras)`` y ``noverlap = nperseg·overlap``,
    con ventana de Hann, eliminación de la media y escala de densidad (valores
    por defecto de SciPy, idénticos a los usados en los cuadernos).
    """
    if sfreq <= 0:
        raise ValueError(f"Frecuencia de muestreo inválida: {sfreq}")
    nperseg = min(int(round(sfreq * window_sec)), data_uv.shape[-1])
    noverlap = int(round(nperseg * overlap))
    if noverlap >= nperseg:
        noverlap = nperseg - 1
    freqs, psd = welch(data_uv, fs=sfreq, nperseg=nperseg, noverlap=noverlap, axis=-1)
    return freqs, psd


def total_power(psd: np.ndarray, freqs: np.ndarray, fmin: float = 1.0, fmax: float = 30.0) -> np.ndarray:
    """Potencia total en ``[fmin, fmax]`` (Simpson, malla uniforme), acotada inferiormente por ``EPS``."""
    mask = (freqs >= fmin) & (freqs <= fmax)
    if mask.sum() < 2:
        raise ValueError("La banda de normalización contiene menos de dos bins.")
    df = float(freqs[1] - freqs[0])
    return np.maximum(simpson(psd[..., mask], dx=df, axis=-1), EPS)


def relative_log_psd_epochs(
    data_uv: np.ndarray,
    sfreq: float,
    band: tuple[float, float] = (4.0, 13.0),
    norm_range: tuple[float, float] = (1.0, 30.0),
    window_sec: float = 2.0,
    overlap: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """``log10(PSD relativa)`` por época y canal, restringida a ``band`` (Ecs. 3.2-3.3).

    La normalización y el logaritmo se aplican **por época, antes de cualquier
    promedio** (Enfoque A).

    Returns
    -------
    rel_log : ndarray, shape (n_épocas, n_canales, n_frecuencias_banda)
    freqs_band : ndarray
    """
    freqs, psd = welch_psd(data_uv, sfreq, window_sec, overlap)
    tot = total_power(psd, freqs, *norm_range)
    rel_log = np.log10(psd / tot[..., None] + EPS)
    band_mask = (freqs >= band[0]) & (freqs <= band[1])
    return rel_log[..., band_mask], freqs[band_mask]


def band_relative_power_epochs(
    data_uv: np.ndarray,
    sfreq: float,
    bands: Mapping[str, Sequence[float]],
    psd_range: tuple[float, float] = (1.0, 40.0),
    norm_range: tuple[float, float] = (1.0, 30.0),
    window_sec: float = 2.0,
    overlap: float = 0.5,
    log10: bool = True,
) -> dict[str, np.ndarray]:
    """Potencia relativa por banda, época y canal (Ecs. 3.4-3.5, Enfoque B).

    Ambas integrales usan Simpson con la malla de frecuencias explícita.

    Returns
    -------
    dict
        ``{banda: array (n_épocas, n_canales)}``; en escala ``log10`` si ``log10=True``.
    """
    if not np.isfinite(data_uv).all():
        raise ValueError("El EEG contiene NaN o valores infinitos.")
    freqs_all, psd_all = welch_psd(data_uv, sfreq, window_sec, overlap)
    keep = (freqs_all >= psd_range[0]) & (freqs_all <= psd_range[1])
    freqs, psd = freqs_all[keep], psd_all[..., keep]
    norm_mask = (freqs >= norm_range[0]) & (freqs <= norm_range[1])
    if norm_mask.sum() < 2:
        raise ValueError("La banda de normalización contiene menos de dos bins.")
    total = np.clip(simpson(psd[..., norm_mask], x=freqs[norm_mask], axis=-1), EPS, None)
    out: dict[str, np.ndarray] = {}
    for name, (lo, hi) in bands.items():
        mask = (freqs >= lo) & (freqs <= hi)
        if mask.sum() < 2:
            raise ValueError(f"La banda [{lo}, {hi}] contiene menos de dos bins.")
        rel = simpson(psd[..., mask], x=freqs[mask], axis=-1) / total
        out[name] = np.log10(np.clip(rel, EPS, None)) if log10 else rel
    return out


def average_linear_psd(
    data_uv: np.ndarray,
    sfreq: float,
    psd_range: tuple[float, float] = (1.0, 40.0),
    window_sec: float = 2.0,
    overlap: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """PSD lineal promediada entre épocas (una por sujeto y canal), usada por la línea base."""
    freqs, psd = welch_psd(data_uv, sfreq, window_sec, overlap)
    mask = (freqs >= psd_range[0]) & (freqs <= psd_range[1])
    return psd[..., mask].mean(axis=0), freqs[mask]


def baseline_scalar_features(
    psd_avg: np.ndarray,
    freqs: np.ndarray,
    bands: Mapping[str, Sequence[float]] = BASELINE_BANDS,
    norm_range: tuple[float, float] = (1.0, 30.0),
) -> np.ndarray:
    """Características escalares clásicas por canal (línea base sin ADF, Sección 3.3.2.1).

    Columnas: log10 de la potencia relativa de delta, theta, pre-alfa, alfa y
    beta; frecuencia dominante en 1-30 Hz (Hz); log10 del cociente alfa/theta.

    Returns
    -------
    ndarray, shape (n_canales, 7)
    """
    df = float(freqs[1] - freqs[0])
    tot = total_power(psd_avg, freqs, *norm_range)
    feats: list[np.ndarray] = []
    powers: dict[str, np.ndarray] = {}
    for name, (lo, hi) in bands.items():
        mask = (freqs >= lo) & (freqs <= hi)
        rel = simpson(psd_avg[..., mask], dx=df, axis=-1) / tot
        feats.append(np.log10(rel + EPS))
        powers[name] = rel
    fmask = (freqs >= norm_range[0]) & (freqs <= norm_range[1])
    feats.append(freqs[fmask][psd_avg[..., fmask].argmax(axis=-1)])
    feats.append(np.log10(powers["alpha"] / (powers["theta"] + EPS) + EPS))
    return np.stack(feats, axis=-1)


def theta_alpha_scalar_features(
    psd_avg: np.ndarray, freqs: np.ndarray, norm_range: tuple[float, float] = (1.0, 30.0)
) -> np.ndarray:
    """log10 de la potencia relativa theta (4-8 Hz) y alfa (8-13 Hz): ``(n_canales, 2)``."""
    df = float(freqs[1] - freqs[0])
    tot = total_power(psd_avg, freqs, *norm_range)
    values = []
    for lo, hi in [(4.0, 8.0), (8.0, 13.0)]:
        mask = (freqs >= lo) & (freqs <= hi)
        values.append(np.log10(simpson(psd_avg[..., mask], dx=df, axis=-1) / tot + EPS))
    return np.stack(values, axis=-1)


def compute_paf(
    data_uv: np.ndarray,
    sfreq: float,
    ch_names: Sequence[str],
    channels: Sequence[str] = ("O1", "O2", "Pz", "P3", "P4"),
    fmin: float = 7.0,
    fmax: float = 13.0,
) -> dict[str, float]:
    """Frecuencia del pico alfa (PAF) posterior de un sujeto.

    Se promedia la PSD lineal entre épocas y entre los canales posteriores y se
    calculan dos estimadores en ``[fmin, fmax]``: centro de gravedad (``cog``,
    estimación principal) y máximo espectral (``argmax``, complementaria).
    """
    freqs, psd = welch_psd(data_uv, sfreq)
    psd_subject = psd.mean(axis=0)
    idx = [list(ch_names).index(ch) for ch in channels if ch in ch_names]
    if not idx:
        return {"cog": float("nan"), "argmax": float("nan")}
    posterior = psd_subject[idx].mean(axis=0)
    band = (freqs >= fmin) & (freqs <= fmax)
    f_band, p_band = freqs[band], posterior[band]
    if p_band.sum() <= 0:
        return {"cog": float("nan"), "argmax": float("nan")}
    return {
        "cog": float(np.sum(f_band * p_band) / np.sum(p_band)),
        "argmax": float(f_band[np.argmax(p_band)]),
    }


def bootstrap_mean_ci(
    curves: np.ndarray, n_boot: int = 1000, seed: int = 42, alpha: float = 0.05
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Media e intervalo bootstrap percentil (remuestreo de sujetos) para curvas ``(n_sujetos, n_f)``."""
    rng = np.random.default_rng(seed)
    n = len(curves)
    boot = np.empty((n_boot, curves.shape[1]), dtype=float)
    for b in range(n_boot):
        boot[b] = curves[rng.integers(0, n, n)].mean(axis=0)
    lo, hi = 100 * alpha / 2, 100 * (1 - alpha / 2)
    return curves.mean(axis=0), np.percentile(boot, lo, axis=0), np.percentile(boot, hi, axis=0)
