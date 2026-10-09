"""Equivalencia de ``parkinson_eeg_fda.spectral`` con el código original de los cuadernos.

Las funciones ``orig_*`` son copias literales de los cuadernos 01, 02A, 02B y 03.
"""

from __future__ import annotations

import unittest

import numpy as np
from _synthetic import CHANNELS, SFREQ, synthetic_epochs
from scipy.integrate import simpson
from scipy.signal import welch

from parkinson_eeg_fda import spectral


def orig_psd_rel_log_epochs(data_uv, sfreq):  # cuaderno 02A
    nps = min(int(sfreq * 2.0), data_uv.shape[-1])
    f, psd = welch(data_uv, fs=sfreq, nperseg=nps, noverlap=int(nps * 0.5), axis=-1)
    nm = (f >= 1.0) & (f <= 30.0)
    tot = simpson(psd[..., nm], dx=f[1] - f[0], axis=-1)
    tot = np.where(tot < 1e-20, 1e-20, tot)
    rel_log = np.log10(psd / tot[..., None] + 1e-20)
    bm = (f >= 4.0) & (f <= 13.0)
    return rel_log[..., bm], f[bm]


def orig_relative_log_psd(epochs_uv, sfreq):  # cuaderno 01
    nperseg = min(int(sfreq * 2.0), epochs_uv.shape[-1])
    freqs, psd = welch(epochs_uv, fs=sfreq, nperseg=nperseg, noverlap=int(nperseg * 0.5), axis=-1)
    mask = (freqs >= 1.0) & (freqs <= 30.0)
    total = np.maximum(simpson(psd[..., mask], x=freqs[mask], axis=-1), 1e-20)
    return np.log10(psd[..., mask] / total[..., None] + 1e-20).mean(axis=0), freqs[mask]


def orig_band_power(data_uv, sfreq, lo, hi):  # cuaderno 02B
    nperseg = min(int(round(sfreq * 2.0)), data_uv.shape[-1])
    freqs, psd = welch(data_uv, fs=sfreq, window="hann", nperseg=nperseg, noverlap=int(round(nperseg * 0.5)),
                       detrend="constant", scaling="density", axis=-1)
    keep = (freqs >= 1.0) & (freqs <= 40.0)
    freqs, psd = freqs[keep], psd[..., keep]
    bm, nm = (freqs >= lo) & (freqs <= hi), (freqs >= 1.0) & (freqs <= 30.0)
    band = simpson(psd[..., bm], x=freqs[bm], axis=-1)
    total = np.clip(simpson(psd[..., nm], x=freqs[nm], axis=-1), 1e-20, None)
    return np.log10(np.clip(band / total, 1e-20, None))


BANDS_N0 = {"delta": (1.0, 4.0), "theta": (4.0, 8.0), "pre_alpha": (5.5, 8.0), "alpha": (8.0, 13.0), "beta": (13.0, 30.0)}


def orig_baseline(data_uv, sfreq):  # cuaderno 03 (_psd_avg_subject + _scalar_features)
    n_ep, _, n_t = data_uv.shape
    nperseg = min(int(sfreq * 2.0), n_t)
    nov = int(nperseg * 0.5)
    psd = np.stack([welch(data_uv[i], fs=sfreq, nperseg=nperseg, noverlap=nov, axis=-1)[1] for i in range(n_ep)])
    f = welch(data_uv[0], fs=sfreq, nperseg=nperseg, noverlap=nov, axis=-1)[0]
    m = (f >= 1.0) & (f <= 40.0)
    psd_avg, freqs = psd[:, :, m].mean(axis=0), f[m]
    df = freqs[1] - freqs[0]
    tm = (freqs >= 1.0) & (freqs <= 30.0)
    tot = np.where(simpson(psd_avg[..., tm], dx=df, axis=-1) < 1e-20, 1e-20, simpson(psd_avg[..., tm], dx=df, axis=-1))
    feats, bp = [], {}
    for name, (lo, hi) in BANDS_N0.items():
        mm = (freqs >= lo) & (freqs <= hi)
        p = simpson(psd_avg[..., mm], dx=df, axis=-1) / tot
        feats.append(np.log10(p + 1e-20))
        bp[name] = p
    feats.append(freqs[tm][psd_avg[..., tm].argmax(axis=-1)])
    feats.append(np.log10(bp["alpha"] / (bp["theta"] + 1e-20) + 1e-20))
    return np.stack(feats, axis=-1)


class TestSpectral(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.epochs = synthetic_epochs(seed=7, label=1)

    def test_psd_relativa_log_02A(self) -> None:
        new, f_new = spectral.relative_log_psd_epochs(self.epochs, SFREQ)
        old, f_old = orig_psd_rel_log_epochs(self.epochs, SFREQ)
        np.testing.assert_array_equal(f_new, f_old)
        np.testing.assert_allclose(new, old, atol=1e-12)
        self.assertEqual(new.shape, (12, 10, 19))

    def test_psd_relativa_log_01(self) -> None:
        new, _ = spectral.relative_log_psd_epochs(self.epochs, SFREQ, band=(1.0, 30.0))
        old, _ = orig_relative_log_psd(self.epochs, SFREQ)
        np.testing.assert_allclose(new.mean(axis=0), old, atol=1e-12)

    def test_potencia_por_banda_02B(self) -> None:
        new = spectral.band_relative_power_epochs(self.epochs, SFREQ, {"theta": (4.0, 8.0), "alpha": (8.0, 13.0)})
        np.testing.assert_allclose(new["theta"], orig_band_power(self.epochs, SFREQ, 4.0, 8.0), atol=1e-12)
        np.testing.assert_allclose(new["alpha"], orig_band_power(self.epochs, SFREQ, 8.0, 13.0), atol=1e-12)

    def test_linea_base_03(self) -> None:
        psd_avg, freqs = spectral.average_linear_psd(self.epochs, SFREQ)
        np.testing.assert_allclose(spectral.baseline_scalar_features(psd_avg, freqs),
                                   orig_baseline(self.epochs, SFREQ), atol=1e-10)

    def test_paf_recupera_frecuencia(self) -> None:
        t = np.arange(1000) / SFREQ
        data = np.tile(np.sin(2 * np.pi * 9.5 * t), (6, len(CHANNELS), 1)) * 10
        paf = spectral.compute_paf(data, SFREQ, CHANNELS)
        self.assertAlmostEqual(paf["argmax"], 9.5)
        self.assertLess(abs(paf["cog"] - 9.5), 0.3)


if __name__ == "__main__":
    unittest.main()
