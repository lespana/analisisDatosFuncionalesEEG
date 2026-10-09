"""Las cifras del README coinciden con las salidas originales de los cuadernos.

Los CSV de ``results/reported/`` transcriben las salidas guardadas en
``notebooks/original/`` (no se reejecutó ningún modelo). Solo requiere pandas.

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

REPORTED = Path(__file__).resolve().parents[1] / "results" / "reported"
DL_MODELS = {"MLP", "Transformer", "FDNN_Direct", "FNN", "AdaFNN", "EEGNet", "CNN1D"}


class TestReportedResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.table = pd.read_csv(REPORTED / "tabla_comparativa_reportada.csv")
        cls.subject = cls.table[cls.table["nivel"] == "sujeto"]

    def _row(self, scenario: str, repr_: str, model: str) -> pd.Series:
        sub = self.subject[(self.subject.scenario == scenario) & (self.subject.repr == repr_)
                           & (self.subject.model == model)]
        self.assertEqual(len(sub), 1, f"{scenario}/{repr_}/{model}")
        return sub.iloc[0]

    def test_dimensiones(self) -> None:
        # Línea base (4 modelos compatibles) + A1, B y A2 × 3 representaciones × 9 modelos.
        self.assertEqual(len(self.subject), 4 + 3 * 3 * 9)
        self.assertEqual(int((self.table["nivel"] == "epoca").sum()), 27)

    def test_cifras_del_readme(self) -> None:
        expected = [
            ("A_epoca", "X_chol_fpca", "LogReg", 0.824, 0.902),
            ("A", "X_chol", "LogReg", 0.818, 0.879),
            ("B", "X_chol_fpca", "RandomForest", 0.781, 0.849),
            ("A_epoca", "X_chol_fpca", "FDNN_Direct", 0.781, 0.875),
            ("Baseline_sin_ADF", "Baseline_sin_ADF", "Transformer", 0.732, 0.814),
        ]
        for scenario, repr_, model, balacc, auc in expected:
            with self.subTest(config=f"{scenario}/{repr_}/{model}"):
                row = self._row(scenario, repr_, model)
                self.assertAlmostEqual(row.balanced_acc_mean, balacc, places=9)
                self.assertAlmostEqual(row.auc_mean, auc, places=9)

    def test_ningun_dl_supera_a_logreg_en_A(self) -> None:
        for scenario in ("A", "A_epoca"):
            with self.subTest(scenario=scenario):
                sub = self.subject[self.subject.scenario == scenario]
                self.assertLess(sub[sub.model.isin(DL_MODELS)].balanced_acc_mean.max(),
                                sub[sub.model == "LogReg"].balanced_acc_mean.max())

    def test_ablacion(self) -> None:
        abl = pd.read_csv(REPORTED / "ablacion_LogReg_reportada.csv").set_index("metodo")
        self.assertAlmostEqual(abl.loc["PSD discreta 4-13 Hz", "balanced_acc_mean"], 0.818)
        self.assertEqual(abl.loc["A1 Cholesky", "balanced_acc_mean"],
                         self._row("A", "X_chol", "LogReg").balanced_acc_mean)


if __name__ == "__main__":
    unittest.main()
