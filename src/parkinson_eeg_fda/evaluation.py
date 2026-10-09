"""Evaluación por sujeto: métricas, agregación época→sujeto y control de fuga.

Funciones extraídas del cuaderno 03 (Sección 3.6 de la tesis):

* las particiones externas usan ``StratifiedGroupKFold`` con el sujeto como grupo;
* la estandarización se ajusta solo con el entrenamiento;
* en A2 las probabilidades por época se promedian por sujeto (Ec. 3.24);
* todas las métricas se calculan con umbral 0,5 y PD-OFF como clase positiva.
"""

from __future__ import annotations

from typing import Iterator, Sequence

import numpy as np
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold, StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler

METRIC_KEYS: tuple[str, ...] = ("balanced_acc", "auc", "sensitivity", "specificity", "f1")


def classification_metrics(y_true: np.ndarray, y_proba: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    """Exactitud balanceada, AUC, sensibilidad, especificidad y F1 (Ecs. 3.25-3.27).

    El AUC es ``nan`` si el conjunto contiene una sola clase.
    """
    y_true = np.asarray(y_true)
    y_pred = (np.asarray(y_proba) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    try:
        auc = float(roc_auc_score(y_true, y_proba))
    except ValueError:
        auc = float("nan")
    return {
        "balanced_acc": float(balanced_accuracy_score(y_true, y_pred)),
        "auc": auc,
        "sensitivity": float(tp / (tp + fn)) if (tp + fn) else 0.0,
        "specificity": float(tn / (tn + fp)) if (tn + fp) else 0.0,
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


def aggregate_by_subject(y_proba: np.ndarray, y_true: np.ndarray, groups: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Promedia las probabilidades por sujeto y devuelve ``(y_sujeto, p_sujeto)``.

    Cada sujeto pesa lo mismo, independientemente de su número de épocas.

    Raises
    ------
    ValueError
        Si un sujeto tiene épocas con etiquetas distintas.
    """
    y_proba, y_true, groups = map(np.asarray, (y_proba, y_true, groups))
    y_s, p_s = [], []
    for subject in np.unique(groups):
        mask = groups == subject
        labels = np.unique(y_true[mask])
        if len(labels) != 1:
            raise ValueError(f"Etiquetas inconsistentes para el sujeto {subject}: {labels}")
        y_s.append(int(labels[0]))
        p_s.append(float(np.mean(y_proba[mask])))
    return np.asarray(y_s), np.asarray(p_s)


def assert_no_subject_leakage(groups_train: np.ndarray, groups_test: np.ndarray) -> None:
    """Falla si algún sujeto aparece a la vez en entrenamiento y prueba."""
    shared = set(np.asarray(groups_train).tolist()) & set(np.asarray(groups_test).tolist())
    if shared:
        raise AssertionError(f"Fuga de sujetos entre entrenamiento y prueba: {sorted(shared)[:5]}")


def subject_splits(
    y: np.ndarray, groups: np.ndarray, seeds: Sequence[int] = (42, 123, 2024), n_folds: int = 5
) -> Iterator[tuple[int, int, np.ndarray, np.ndarray]]:
    """Particiones externas por sujeto: genera ``(semilla, pliegue, idx_train, idx_test)``."""
    y, groups = np.asarray(y), np.asarray(groups)
    dummy = np.zeros((len(y), 1))
    for seed in seeds:
        splitter = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=seed)
        for fold, (idx_tr, idx_te) in enumerate(splitter.split(dummy, y, groups)):
            assert_no_subject_leakage(groups[idx_tr], groups[idx_te])
            yield seed, fold, idx_tr, idx_te


def inner_subject_split(
    y_train: np.ndarray, groups_train: np.ndarray, seed: int, fold: int, val_fraction: float = 0.20
) -> tuple[np.ndarray, np.ndarray]:
    """Validación interna de A2: todas las épocas de un sujeto quedan del mismo lado.

    Estratifica por la etiqueta del sujeto con ``random_state = seed + fold``,
    como en el cuaderno 03.
    """
    y_train, groups_train = np.asarray(y_train), np.asarray(groups_train)
    subjects = np.unique(groups_train)
    labels = np.asarray([int(np.unique(y_train[groups_train == s])[0]) for s in subjects])
    splitter = StratifiedShuffleSplit(n_splits=1, test_size=val_fraction, random_state=seed + fold)
    sub_tr, sub_val = next(splitter.split(np.zeros((len(subjects), 1)), labels))
    idx_tr = np.flatnonzero(np.isin(groups_train, subjects[sub_tr]))
    idx_val = np.flatnonzero(np.isin(groups_train, subjects[sub_val]))
    assert_no_subject_leakage(groups_train[idx_tr], groups_train[idx_val])
    return idx_tr, idx_val


def standardize_per_fold(X_train: np.ndarray, X_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """``StandardScaler`` ajustado solo con ``X_train`` (aplana y restaura la forma)."""
    scaler = StandardScaler()
    tr = scaler.fit_transform(X_train.reshape(len(X_train), -1)).reshape(X_train.shape)
    te = scaler.transform(X_test.reshape(len(X_test), -1)).reshape(X_test.shape)
    return tr, te
