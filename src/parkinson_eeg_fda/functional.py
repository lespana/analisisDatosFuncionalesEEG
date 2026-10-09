"""Geometría funcional: bases B-spline, GCV, matriz de Gram, Cholesky y FPCA.

Funciones extraídas de los cuadernos 02A, 02B y 03 (Secciones 3.4.1-3.4.5 de la
tesis). Reproducen el cálculo de los cuadernos; ``tests/test_functional.py``
lo comprueba frente a copias literales del código original.

* Base B-spline cúbica con nudos uniformes: ``n_bases = n_nudos + grado - 1``
  (9 nudos -> 11 bases en el Enfoque A; 2 nudos -> 4 bases en el Enfoque B).
* Coeficientes por mínimos cuadrados con cresta pequeña (Ec. 3.7):
  ``c = (ΦᵀΦ + λ_r I)⁻¹ Φᵀ x`` con ``λ_r = 1e-6``.
* GCV (Ec. 3.8): ``GCV = ECM / (1 - tr(H)/n)²``.
* Gram ``G_ij = ∫ φ_i φ_j`` (Simpson, 1001 puntos) y coordenadas ``z = c L``
  con ``G = L Lᵀ`` (Ecs. 3.13-3.16): ``‖z₁ - z₂‖² = ‖x₁ - x₂‖²_{L²}``.
* FPCA por canal ajustada solo con entrenamiento (95 % de varianza).
"""

from __future__ import annotations

from typing import Literal, Sequence

import numpy as np
import pandas as pd
from scipy import linalg
from scipy.integrate import simpson
from sklearn.decomposition import PCA
from sklearn.preprocessing import SplineTransformer


# ---------------------------------------------------------------------------
# Base B-spline y coeficientes
# ---------------------------------------------------------------------------
def n_basis_from_knots(n_knots: int, degree: int = 3) -> int:
    """Número de funciones base de una B-spline con ``include_bias=True``."""
    return n_knots + degree - 1


def make_bspline(
    domain: tuple[float, float],
    n_knots: int,
    degree: int = 3,
    fit_points: np.ndarray | None = None,
) -> SplineTransformer:
    """Base B-spline con nudos uniformes sobre ``domain``.

    Los nudos uniformes de ``SplineTransformer`` dependen solo del mínimo y del
    máximo de los puntos de ajuste, por lo que ajustar sobre la malla de Welch
    (Enfoque A) o sobre una malla densa en [0, 1] (Enfoque B) reproduce la base
    de los cuadernos.
    """
    pts = np.linspace(domain[0], domain[1], 1001) if fit_points is None else np.asarray(fit_points, float)
    spline = SplineTransformer(n_knots=n_knots, degree=degree, knots="uniform",
                               include_bias=True, extrapolation="constant")
    return spline.fit(pts.reshape(-1, 1))


def design_matrix(spline: SplineTransformer, x: np.ndarray) -> np.ndarray:
    """Matriz Φ ``(len(x), n_bases)`` evaluada en los puntos ``x``."""
    return spline.transform(np.asarray(x, dtype=float).reshape(-1, 1))


def ridge_coefficients(
    design: np.ndarray,
    curves: np.ndarray,
    ridge: float = 1e-6,
    method: Literal["pinv", "solve"] = "solve",
) -> np.ndarray:
    """Coeficientes B-spline de curvas con los puntos en el **último eje** (Ec. 3.7).

    ``method="pinv"`` reproduce el cuaderno 02A y ``"solve"`` el 02B; difieren
    solo en el redondeo (~1e-14).

    Returns
    -------
    ndarray, shape (..., n_bases)
    """
    y = np.asarray(curves, dtype=float)
    n_basis = design.shape[1]
    system = design.T @ design + ridge * np.eye(n_basis)
    flat = y.reshape(-1, y.shape[-1])
    if method == "pinv":
        coef = flat @ design @ linalg.pinv(system)
    elif method == "solve":
        coef = linalg.solve(system, design.T @ flat.T, assume_a="pos").T
    else:
        raise ValueError(f"Método desconocido: {method}")
    return coef.reshape(*y.shape[:-1], n_basis)


def gcv_score(design: np.ndarray, y: np.ndarray, ridge: float = 1e-6) -> float:
    """GCV de una curva; ``inf`` si la base está saturada o el denominador es nulo."""
    n_obs, n_basis = design.shape
    if n_basis >= n_obs:
        return float("inf")
    hat = design @ linalg.pinv(design.T @ design + ridge * np.eye(n_basis)) @ design.T
    mse = float(np.mean((y - hat @ y) ** 2))
    den = (1.0 - float(np.trace(hat)) / n_obs) ** 2
    return float("inf") if den < 1e-10 else mse / den


def select_knots_gcv(
    curves: Sequence[tuple[np.ndarray, np.ndarray]],
    k_range: Sequence[int],
    domain: tuple[float, float],
    degree: int = 3,
    ridge: float = 1e-6,
) -> tuple[int, pd.DataFrame]:
    """Número de nudos que minimiza el GCV medio sobre pares ``(x, y)``.

    Returns
    -------
    k_opt, tabla con ``k``, ``n_bases``, ``gcv_medio``, ``gcv_sd`` y ``n_usadas``.
    """
    rows = []
    for k in k_range:
        spline = make_bspline(domain, k, degree)
        values = np.asarray([gcv_score(design_matrix(spline, x), y, ridge) for x, y in curves])
        finite = values[np.isfinite(values)]
        if finite.size:
            rows.append({"k": int(k), "n_bases": n_basis_from_knots(k, degree), "gcv_medio": float(finite.mean()),
                         "gcv_sd": float(finite.std(ddof=1)) if finite.size > 1 else 0.0, "n_usadas": int(finite.size)})
    table = pd.DataFrame(rows)
    if table.empty:
        raise ValueError("Ningún valor de k produjo un GCV finito.")
    return int(table.loc[table["gcv_medio"].idxmin(), "k"]), table


# ---------------------------------------------------------------------------
# Gram y Cholesky
# ---------------------------------------------------------------------------
def gram_matrix(spline: SplineTransformer, domain: tuple[float, float], n_grid: int = 1001) -> np.ndarray:
    """Matriz de Gram ``G_ij = ∫_D φ_i φ_j`` por Simpson en una malla uniforme (simetrizada)."""
    grid = np.linspace(domain[0], domain[1], n_grid)
    basis = design_matrix(spline, grid)
    gram = simpson(basis[:, :, None] * basis[:, None, :], x=grid, axis=0)
    return 0.5 * (gram + gram.T)


def cholesky_factor(gram: np.ndarray) -> np.ndarray:
    """Factor triangular inferior ``L`` con ``G = L Lᵀ``; falla si ``G`` no es definida positiva."""
    eig_min = float(np.linalg.eigvalsh(gram).min())
    if eig_min <= 0:
        raise ValueError(f"La matriz de Gram no es definida positiva (λ_min = {eig_min:.3e}).")
    return np.linalg.cholesky(gram)


def cholesky_coordinates(coefs: np.ndarray, chol: np.ndarray) -> np.ndarray:
    """Coordenadas de Cholesky ``z = c L`` (coeficientes como vectores fila, último eje)."""
    return np.asarray(coefs) @ chol


def coefficients_from_cholesky(z: np.ndarray, chol: np.ndarray) -> np.ndarray:
    """Inversa de :func:`cholesky_coordinates`: ``c = z L⁻¹``."""
    z = np.asarray(z, dtype=float)
    flat = z.reshape(-1, z.shape[-1])
    return linalg.solve_triangular(chol.T, flat.T, lower=False).T.reshape(z.shape)


def validate_cholesky(gram: np.ndarray, chol: np.ndarray, coefs: np.ndarray) -> dict[str, float]:
    """λ_mín, cond(G) y errores máximos de factorización y de distancia entre todos los pares (Tabla 4.4)."""
    err_dist = 0.0
    for i in range(coefs.shape[0] - 1):
        delta = coefs[i + 1:] - coefs[i]
        via_gram = np.einsum("ij,jk,ik->i", delta, gram, delta)
        via_chol = np.sum((delta @ chol) ** 2, axis=1)
        err_dist = max(err_dist, float(np.abs(via_gram - via_chol).max()))
    eig = np.linalg.eigvalsh(gram)
    return {"lambda_min": float(eig.min()), "cond_G": float(np.linalg.cond(gram)),
            "error_max_factorizacion": float(np.abs(gram - chol @ chol.T).max()),
            "error_max_distancia": err_dist}


# ---------------------------------------------------------------------------
# FPCA dentro del pliegue
# ---------------------------------------------------------------------------
def fpca_per_channel(
    X_train: np.ndarray,
    X_test: np.ndarray,
    variance_threshold: float = 0.95,
) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """FPCA independiente por canal ajustada **solo** con ``X_train`` (cuaderno 03).

    Entradas ``(n_obs, n_canales, n_bases)`` en coordenadas de Cholesky. Los
    canales con menos componentes se rellenan con ceros hasta el máximo.

    Returns
    -------
    X_train_fpca, X_test_fpca, componentes retenidos por canal
    """
    n_tr, n_ch, n_basis = X_train.shape
    pcas, n_comps = [], []
    for ch in range(n_ch):
        cum = np.cumsum(PCA().fit(X_train[:, ch, :]).explained_variance_ratio_)
        n_comp = min(max(int(np.searchsorted(cum, variance_threshold) + 1), 1), n_basis)
        pcas.append(PCA(n_components=n_comp).fit(X_train[:, ch, :]))
        n_comps.append(n_comp)
    n_max = max(n_comps)
    tr = np.zeros((n_tr, n_ch, n_max))
    te = np.zeros((X_test.shape[0], n_ch, n_max))
    for ch, pca in enumerate(pcas):
        tr[:, ch, :n_comps[ch]] = pca.transform(X_train[:, ch, :])
        te[:, ch, :n_comps[ch]] = pca.transform(X_test[:, ch, :])
    return tr, te, n_comps
