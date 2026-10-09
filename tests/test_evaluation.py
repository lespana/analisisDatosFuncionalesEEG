"""Métricas, agregación por sujeto y ausencia de fuga de sujetos."""

from __future__ import annotations

import unittest

import _synthetic  # noqa: F401 - añade src/ al path si el paquete no está instalado
import numpy as np

from parkinson_eeg_fda.evaluation import (
    aggregate_by_subject,
    assert_no_subject_leakage,
    classification_metrics,
    inner_subject_split,
    standardize_per_fold,
    subject_splits,
)


def _epochs_design(n_subjects: int = 20, n_ep: int = 8) -> tuple[np.ndarray, np.ndarray]:
    y = np.repeat(np.arange(n_subjects) % 2, n_ep)
    groups = np.repeat(np.arange(n_subjects), n_ep)
    return y, groups


class TestMetricas(unittest.TestCase):
    def test_ejemplo(self) -> None:
        m = classification_metrics(np.array([0, 0, 1, 1]), np.array([0.2, 0.6, 0.7, 0.4]))
        self.assertEqual((m["sensitivity"], m["specificity"], m["balanced_acc"]), (0.5, 0.5, 0.5))
        self.assertAlmostEqual(m["auc"], 0.75)

    def test_auc_una_clase(self) -> None:
        self.assertTrue(np.isnan(classification_metrics(np.array([1, 1]), np.array([0.2, 0.9]))["auc"]))


class TestAgregacion(unittest.TestCase):
    def test_promedio_por_sujeto(self) -> None:
        y_s, p_s = aggregate_by_subject(np.array([0.2, 0.4, 0.9, 0.7, 0.8]), np.array([0, 0, 1, 1, 1]),
                                        np.array(["a", "a", "b", "b", "b"]))
        np.testing.assert_array_equal(y_s, [0, 1])
        np.testing.assert_allclose(p_s, [0.3, 0.8])

    def test_etiquetas_inconsistentes(self) -> None:
        with self.assertRaises(ValueError):
            aggregate_by_subject(np.array([0.1, 0.2]), np.array([0, 1]), np.array(["a", "a"]))


class TestFuga(unittest.TestCase):
    def test_particiones_externas(self) -> None:
        y, groups = _epochs_design()
        splits = list(subject_splits(y, groups))
        self.assertEqual(len(splits), 15)
        for _, _, tr, te in splits:
            self.assertFalse(set(groups[tr]) & set(groups[te]))

    def test_validacion_interna_por_sujeto(self) -> None:
        y, groups = _epochs_design()
        tr, val = inner_subject_split(y, groups, seed=42, fold=0)
        self.assertFalse(set(groups[tr]) & set(groups[val]))
        self.assertEqual(set(y[val]), {0, 1})
        self.assertEqual(len(tr) + len(val), len(y))

    def test_detecta_fuga(self) -> None:
        with self.assertRaises(AssertionError):
            assert_no_subject_leakage(np.array([1, 2]), np.array([2, 3]))

    def test_estandarizacion_solo_con_entrenamiento(self) -> None:
        rng = np.random.default_rng(0)
        X_tr, X_te = rng.normal(size=(30, 3, 5)), rng.normal(size=(10, 3, 5)) + 100
        tr, te = standardize_per_fold(X_tr, X_te)
        np.testing.assert_allclose(tr.reshape(30, -1).mean(0), 0, atol=1e-10)
        self.assertGreater(te.mean(), 10)


if __name__ == "__main__":
    unittest.main()
