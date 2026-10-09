"""Geometría funcional: Tabla 4.4, Cholesky, GCV, coeficientes y FPCA frente al código original."""

from __future__ import annotations

import unittest

import numpy as np
from _synthetic import SFREQ, synthetic_epochs
from scipy import linalg
from scipy.integrate import simpson
from sklearn.decomposition import PCA
from sklearn.preprocessing import SplineTransformer

from parkinson_eeg_fda import functional as fn
from parkinson_eeg_fda.spectral import relative_log_psd_epochs

FREQS_A = np.arange(4.0, 13.0 + 1e-9, 0.5)


def orig_gcv_a(x, y, n_knots, ridge=1e-6):  # cuaderno 02A (_bspline_gcv)
    B = SplineTransformer(n_knots=n_knots, degree=3, include_bias=True).fit_transform(x.reshape(-1, 1))
    n, nb = B.shape
    if nb >= n:
        return np.inf
    H = B @ linalg.pinv(B.T @ B + ridge * np.eye(nb)) @ B.T
    den = (1.0 - np.trace(H) / n) ** 2
    return np.inf if den < 1e-10 else ((y - H @ y) ** 2).mean() / den


def orig_coefs_and_gram_a(y, freqs, k, ridge=1e-6):  # cuaderno 02A
    sp = SplineTransformer(n_knots=k, degree=3, include_bias=True)
    B = sp.fit_transform(freqs.reshape(-1, 1))
    coef = y @ B @ linalg.pinv(B.T @ B + ridge * np.eye(B.shape[1]))
    fg = np.linspace(4.0, 13.0, 1001)
    Bg = sp.transform(fg.reshape(-1, 1))
    G = simpson(Bg[:, :, None] * Bg[:, None, :], x=fg, axis=0)
    return coef, 0.5 * (G + G.T)


def orig_fpca(X_train, X_test, thr=0.95):  # cuaderno 03
    n_ch, n_basis = X_train.shape[1], X_train.shape[2]
    ncs, pcas = [], []
    for ch in range(n_ch):
        cum = np.cumsum(PCA().fit(X_train[:, ch, :]).explained_variance_ratio_)
        n = min(max(int(np.searchsorted(cum, thr) + 1), 1), n_basis)
        pcas.append(PCA(n_components=n).fit(X_train[:, ch, :]))
        ncs.append(n)
    tr, te = np.zeros((len(X_train), n_ch, max(ncs))), np.zeros((len(X_test), n_ch, max(ncs)))
    for ch, pca in enumerate(pcas):
        tr[:, ch, :ncs[ch]] = pca.transform(X_train[:, ch, :])
        te[:, ch, :ncs[ch]] = pca.transform(X_test[:, ch, :])
    return tr, te, ncs


class TestTabla44(unittest.TestCase):
    """λ_mín(G) y cond(G) solo dependen de la base: deben coincidir con la Tabla 4.4."""

    def test_enfoque_A(self) -> None:
        gram = fn.gram_matrix(fn.make_bspline((4.0, 13.0), 9), (4.0, 13.0))
        self.assertEqual(gram.shape, (11, 11))
        self.assertAlmostEqual(np.linalg.eigvalsh(gram).min() / 7.72e-4, 1.0, delta=5e-3)
        self.assertAlmostEqual(np.linalg.cond(gram) / 1.40e3, 1.0, delta=5e-3)

    def test_enfoque_B(self) -> None:
        gram = fn.gram_matrix(fn.make_bspline((0.0, 1.0), 2), (0.0, 1.0))
        self.assertEqual(gram.shape, (4, 4))
        self.assertAlmostEqual(np.linalg.eigvalsh(gram).min() / 6.09e-5, 1.0, delta=5e-3)
        self.assertAlmostEqual(np.linalg.cond(gram) / 6.97e3, 1.0, delta=5e-3)


class TestCholesky(unittest.TestCase):
    def test_preserva_distancia_L2(self) -> None:
        rng = np.random.default_rng(0)
        sp = fn.make_bspline((4.0, 13.0), 9)
        gram = fn.gram_matrix(sp, (4.0, 13.0))
        chol = fn.cholesky_factor(gram)
        coefs = rng.normal(size=(30, 11))
        report = fn.validate_cholesky(gram, chol, coefs)
        self.assertLess(report["error_max_distancia"], 1e-12)
        grid = np.linspace(4, 13, 4001)
        diff = (coefs[0] - coefs[1]) @ fn.design_matrix(sp, grid).T
        l2 = simpson(diff**2, x=grid)
        z = fn.cholesky_coordinates(coefs, chol)
        self.assertAlmostEqual(np.sum((z[0] - z[1]) ** 2) / l2, 1.0, delta=1e-4)
        np.testing.assert_allclose(fn.coefficients_from_cholesky(z, chol), coefs, atol=1e-10)

    def test_gram_no_definida_positiva(self) -> None:
        with self.assertRaises(ValueError):
            fn.cholesky_factor(np.array([[1.0, 2.0], [2.0, 1.0]]))


class TestEquivalenciaCuadernos(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.curves, cls.freqs = relative_log_psd_epochs(synthetic_epochs(seed=3), SFREQ)

    def test_gcv_02A(self) -> None:
        for k in (4, 9, 12):
            design = fn.design_matrix(fn.make_bspline((4.0, 13.0), k, fit_points=self.freqs), self.freqs)
            for y in self.curves.reshape(-1, self.freqs.size)[:15]:
                self.assertAlmostEqual(fn.gcv_score(design, y) / orig_gcv_a(self.freqs, y, k), 1.0, delta=1e-9)

    def test_coeficientes_y_gram_02A(self) -> None:
        flat = self.curves.reshape(-1, self.freqs.size)
        old_coef, old_gram = orig_coefs_and_gram_a(flat, self.freqs, 9)
        sp = fn.make_bspline((4.0, 13.0), 9, fit_points=self.freqs)
        design = fn.design_matrix(sp, self.freqs)
        np.testing.assert_allclose(fn.ridge_coefficients(design, flat, method="pinv"), old_coef, atol=1e-12)
        np.testing.assert_allclose(fn.ridge_coefficients(design, flat, method="solve"), old_coef, atol=1e-8)
        np.testing.assert_allclose(fn.gram_matrix(sp, (4.0, 13.0)), old_gram, atol=1e-15)

    def test_seleccion_gcv(self) -> None:
        pairs = [(self.freqs, c) for c in self.curves.reshape(-1, self.freqs.size)[:60]]
        k_opt, table = fn.select_knots_gcv(pairs, [4, 6, 9, 12], (4.0, 13.0))
        self.assertIn(k_opt, [4, 6, 9, 12])
        self.assertTrue({"k", "n_bases", "gcv_medio", "gcv_sd"} <= set(table.columns))

    def test_fpca_03(self) -> None:
        rng = np.random.default_rng(1)
        X = rng.normal(size=(40, 10, 11)) @ np.diag(np.linspace(3, 0.1, 11))
        new_tr, new_te, new_n = fn.fpca_per_channel(X[:30], X[30:])
        old_tr, old_te, old_n = orig_fpca(X[:30], X[30:])
        self.assertEqual(new_n, old_n)
        np.testing.assert_allclose(new_tr, old_tr, atol=1e-10)
        np.testing.assert_allclose(new_te, old_te, atol=1e-10)


if __name__ == "__main__":
    unittest.main()
