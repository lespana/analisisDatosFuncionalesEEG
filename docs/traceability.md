# Trazabilidad

Correspondencia entre la tesis ([`thesis.pdf`](thesis.pdf)), los cuadernos y el código. Los cuadernos se nombran por su copia portátil; los originales con salidas están en `notebooks/original/` con el mismo número.

| N.º | Copia portátil | Original |
|---|---|---|
| 01 | `01_preprocessing.ipynb` | `01_UNM_preprocesamiento.ipynb` |
| 02A | `02a_functional_frequency.ipynb` | `02A_UNM_enfoque_A.ipynb` |
| 02B | `02b_functional_epoch_order.ipynb` | `02B_UNM_enfoque_B.ipynb` |
| 03 | `03_modeling.ipynb` | `03_UNM_modelado.ipynb` |
| 04 | `04_ablation_adf.ipynb` | `04_UNM_aporte_ADF.ipynb` |
| 05 | `05_interpretability.ipynb` | `05_UNM_interpretabilidad_ADF.ipynb` |

## 1. Metodología (Capítulo 3)

| Sección | Concepto | Cuaderno | Utilidad en `src/parkinson_eeg_fda` | Prueba |
|---|---|---|---|---|
| 3.1 | Cohorte HC vs PD-OFF | 01 | — | — |
| 3.2 | Referencia, filtro, remuestreo, ICA, canales, épocas, rechazo | 01 | — | — |
| 3.3.1 | Welch 2 s, 50 % | 01, 02A, 02B, 03 | `spectral.welch_psd` | `test_spectral` |
| 3.3.2.1 | Línea base escalar | 03 | `spectral.baseline_scalar_features` | `test_spectral.test_linea_base_03` |
| 3.3.2.2 | log10 PSD relativa por época (Enfoque A) | 02A | `spectral.relative_log_psd_epochs` | `test_spectral.test_psd_relativa_log_02A` |
| 3.3.2.3 | Potencia relativa theta/alfa (Enfoque B) | 02B | `spectral.band_relative_power_epochs` | `test_spectral.test_potencia_por_banda_02B` |
| 3.4.1 | B-spline, cresta, GCV | 02A, 02B | `functional.ridge_coefficients`, `gcv_score`, `select_knots_gcv` | `test_functional.TestEquivalenciaCuadernos` |
| 3.4.2-3.4.3 | Enfoques A (A1/A2) y B | 02A, 02B | `functional.make_bspline`, `design_matrix` | — |
| 3.4.4 | Gram y Cholesky | 02A, 02B | `functional.gram_matrix`, `cholesky_coordinates`, `validate_cholesky` | `test_functional.TestTabla44`, `TestCholesky` |
| 3.4.5 | FPCA dentro del pliegue | 03, 04 | `functional.fpca_per_channel` | `test_functional.test_fpca_03` |
| 3.5.1-3.5.2, Anexo B | Modelos clásicos y profundos | 03 | — (en el cuaderno) | — |
| 3.5.4 | Aporte del ADF | 04 | — | `test_reported_results.test_ablacion` |
| 3.5.5 | Funciones de peso | 05 | `functional.coefficients_from_cholesky` | — |
| 3.6.1 | `StratifiedGroupKFold` 5 × {42, 123, 2024} | 03, 04, 05 | `evaluation.subject_splits` | `test_evaluation.TestFuga` |
| 3.6.2 | Ajuste en entrenamiento; validación interna por sujeto en A2 | 03 | `evaluation.standardize_per_fold`, `inner_subject_split` | `test_evaluation.TestFuga` |
| 3.6.3 | Agregación época → sujeto | 03 | `evaluation.aggregate_by_subject` | `test_evaluation.TestAgregacion` |
| 3.6.4 | Métricas | 03, 04, 05 | `evaluation.classification_metrics` | `test_evaluation.TestMetricas` |
| 3.7 | Mann-Whitney y rank-biserial | 01 | — | — |
| 3.8 | Entorno | todos | `requirements.txt`, `environment.yml` | — |

## 2. Figuras del Capítulo 4

Los cuadernos guardan las figuras con nombres por contenido, sin número. Las de 02A y 02B se escriben en `figuras/tesis/`.

| Figura | Contenido | Cuaderno | Archivo |
|---|---|---|---|
| 4.1 | Señal antes y después del preprocesamiento | 01 | `comparacion_temporal_4canales.png` |
| 4.2 / 4.3 | Espectro antes y después en Pz (HC / PD-OFF) | 01 | `espectro_HC_Pz.png`, `espectro_PD_OFF_Pz.png` |
| 4.4 | PSD relativa por región | 01 | `psd_relativa_por_region.png` → `docs/assets/psd_by_region.png` |
| 4.5 | Distribución de la PAF | 01 | `paf_HC_vs_PD_OFF.png` → `docs/assets/paf_distribution.png` |
| 4.6 | B-spline frente a P-spline | 02A | `comparacion_bspline_pspline_A.png` |
| 4.7 | GCV del Enfoque A | 02A | `gcv_enfoque_A.png` |
| 4.8 | Curvas funcionales del Enfoque A | 02A | `curvas_funcionales_A.png` → `docs/assets/approach_a_functional_curves.png` |
| 4.9 | GCV de theta y alfa | 02B | `gcv_enfoque_B_theta_alfa.png` |
| 4.10 / 4.11 | Trayectorias de alfa / theta | 02B | `curvas_funcionales_B_alfa.png`, `curvas_funcionales_B_theta.png` |
| 4.12 | Componentes FPCA del Enfoque B | 03 | `componentes_FPCA_B.png` |
| 4.13 | Reconstrucción del Enfoque A en Pz | 02A | `reconstruccion_A_Pz.png` |
| 4.14 / 4.15 | Reconstrucción del Enfoque B en Pz (alfa / theta) | 02B | `reconstruccion_B_alfa_Pz.png`, `reconstruccion_B_theta_Pz.png` |
| 4.16 | Matrices de confusión | 03 | `matrices_confusion.png` |
| 4.17 | AUC de entrenamiento y validación | 03 | `curvas_entrenamiento.png` |
| 4.18 | Curva de aprendizaje por número de sujetos | 03 | `curva_aprendizaje_sujetos.png` |
| 4.19 | Funciones de peso 4-10 Hz | 05 | `funciones_peso_theta_pre_alfa.png` → `docs/assets/functional_weights.png` |

La figura de ablación del README (`docs/assets/ablation_adf.png`) corresponde a `comparacion_representaciones_LogReg.png` del cuaderno 04.

## 3. Tablas

| Tabla | Contenido | Cuaderno | Archivo del cuaderno | En el repositorio |
|---|---|---|---|---|
| 4.1 | Componentes ICA excluidos | 01 | `ica_resumen_por_grupo.csv`, `ica_estadistica.csv` | — |
| 4.2 / 4.3 | Conservación y marcado de épocas | 01 | `descriptiva_preprocesamiento.csv` | `results/reported/cohorte_y_paf_reportada.csv` |
| 4.4 | Validación de Cholesky | 02A, 02B | `validacion_cholesky_A.csv`, `validacion_cholesky_B.csv` | `results/reported/validacion_cholesky_reportada.csv` |
| 4.5 | Componentes FPCA por canal (A) | 03 | `tabla_fpca_componentes.csv` | `results/reported/fpca_componentes_A_reportada.csv` |
| 4.6-4.8, A.1-A.4 | Desempeño por representación y modelo | 03 | `tabla_comparativa_completa.csv` | `results/reported/tabla_comparativa_reportada.csv` |
| 4.9 | Aporte del ADF | 04 | `resumen_LogReg.csv` | `results/reported/ablacion_LogReg_reportada.csv` |
| B.3 | Parámetros entrenables | 03 | `params_chol_vs_fpca.csv` | `results/reported/parametros_entrenables_reportados.csv` |
