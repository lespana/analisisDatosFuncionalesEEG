# Cuadernos

El experimento se ejecuta con seis cuadernos. La numeración coincide con la de la tesis.

| Orden | Copia portátil | Original (con salidas) | Propósito | Salidas principales (en `$PARKINSON_EEG_ROOT`) |
|---|---|---|---|---|
| 1 | `01_preprocessing.ipynb` | `original/01_UNM_preprocesamiento.ipynb` | Descarga, preprocesamiento, calidad, PSD por región y PAF | `01_preprocesamiento/epochs_manifest.csv`, `preprocessed_epochs/*.npy` |
| 2 | `02a_functional_frequency.ipynb` | `original/02A_UNM_enfoque_A.ipynb` | Enfoque A: GCV, P-spline, curvas, A1/A2, Cholesky | `02A_enfoque_A/enfoque_A_sujeto_dataset.npz`, `enfoque_A_dataset.npz` |
| 3 | `02b_functional_epoch_order.ipynb` | `original/02B_UNM_enfoque_B.ipynb` | Enfoque B: trayectorias theta y alfa | `02B_enfoque_B/enfoque_B_dataset_theta_alpha.npz` |
| 4 | `03_modeling.ipynb` | `original/03_UNM_modelado.ipynb` | FPCA en el pliegue, 9 modelos, línea base, diagnósticos | `03_modelado/resultados/tabla_comparativa_completa.csv` |
| 5 | `04_ablation_adf.ipynb` | `original/04_UNM_aporte_ADF.ipynb` | Aporte específico del ADF (LogReg) | `04_aporte_ADF/resumen_LogReg.csv` |
| 6 | `05_interpretability.ipynb` | `original/05_UNM_interpretabilidad_ADF.ipynb` | Funciones de peso β_c(f) | `05_interpretabilidad/funciones_peso.npz` |

## Originales y copias portátiles

- **`original/`** contiene los cuadernos con los que se produjeron las figuras y tablas de la tesis, con todas sus salidas. No se editan.
- **Las copias portátiles** (en esta carpeta) se generan con `python scripts/build_portable_notebooks.py`. No tienen salidas y solo cambian la infraestructura de archivos:
  - Drive se monta únicamente si `USE_GOOGLE_DRIVE=1`;
  - las rutas se leen de `PARKINSON_EEG_DATA` y `PARKINSON_EEG_ROOT`;
  - las instalaciones `!pip` quedan comentadas.

  Los parámetros científicos son idénticos a los de los originales.

## Ejecución

**Local.** Desde la raíz del repositorio, con el entorno activado:

```bash
export PARKINSON_EEG_DATA="$PWD/data/openneuro"
export PARKINSON_EEG_ROOT="$PWD/artifacts"
jupyter lab notebooks/
```

En Windows (PowerShell):

```powershell
$env:PARKINSON_EEG_DATA = "$PWD\data\openneuro"
$env:PARKINSON_EEG_ROOT = "$PWD\artifacts"
jupyter lab notebooks/
```

**Google Colab.** Ejecute al inicio `import os; os.environ['USE_GOOGLE_DRIVE'] = '1'` y defina `PARKINSON_EEG_ROOT` con una carpeta de su Drive, por ejemplo `/content/drive/MyDrive/tesis_parkinson/resultados`. El cuaderno de modelado se beneficia de una GPU.

## Orden y dependencias

`01` → `02a` y `02b` (independientes entre sí) → `03`. El `04` necesita `01` y `02a`; el `05` necesita `02a` y, de forma opcional, el resumen del `04`.
