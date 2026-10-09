# Reproducibilidad

## Entorno documentado en el manuscrito

El cierre de la tesis registra el siguiente entorno:

| Componente | Versión |
|---|---:|
| Python | 3.13.15 |
| MNE-Python | 1.12.1 |
| NumPy | 2.1.3 |
| SciPy | 1.16.3 |
| pandas | 2.2.3 |
| scikit-learn | 1.6.1 |
| PyTorch | 2.11.0 |
| Matplotlib | 3.10.0 |

El entorno de trabajo original fue Google Colab con almacenamiento en Google Drive y aceleración GPU NVIDIA T4 para las arquitecturas profundas.

## Versión de MNE-Python

La salida almacenada en el notebook `notebooks/original/01_UNM_preprocesamiento.ipynb` registra **MNE-Python 1.13.2**, mientras el manuscrito final documenta **1.12.1**. El archivo `requirements.txt` adopta **1.12.1** porque es la versión declarada en la tesis.

## Semillas

Los experimentos de clasificación se repiten con:

```python
SEEDS = [42, 123, 2024]
```

El preprocesamiento/ICA y otros componentes aleatorios fijan asimismo una semilla de referencia 42 cuando corresponde.

## Variables de entorno

Las copias portátiles eliminan la dependencia obligatoria de rutas absolutas de Google Drive:

```bash
export PARKINSON_EEG_DATA="$PWD/data/openneuro"
export PARKINSON_EEG_ROOT="$PWD/artifacts"
```

- `PARKINSON_EEG_DATA`: directorio padre de `ds003490`.
- `PARKINSON_EEG_ROOT`: raíz para productos intermedios y resultados.
- `USE_GOOGLE_DRIVE=1`: opcional; permite montar Drive al ejecutar en Colab.

## Orden reproducible

1. `01_preprocessing.ipynb`
2. `02a_functional_frequency.ipynb`
3. `02b_functional_epoch_order.ipynb`
4. `03_modeling.ipynb`
5. `04_ablation_adf.ipynb`
6. `05_interpretability.ipynb`

Los pasos 2A y 2B comparten el mismo preprocesamiento y pueden ejecutarse independientemente después de 01. El cuaderno 05 lee el resumen del 04 si existe, pero no lo requiere.

Si se modifican los originales, las copias portátiles se regeneran con:

```bash
python scripts/build_portable_notebooks.py
```

## Datos

Los datos EEG crudos no se incluyen en Git. El script `scripts/download_openneuro.sh` reproduce el mecanismo de descarga utilizado por el cuaderno de preprocesamiento mediante el bucket público S3 de OpenNeuro.

## Variabilidad de los modelos profundos

Los modelos profundos se entrenaron en GPU sin forzar el determinismo de cuDNN (`set_seed` fija `numpy` y `torch.manual_seed`, pero no `torch.backends.cudnn.deterministic`). Una reejecución en GPU puede producir diferencias pequeñas en sus métricas. Regresión logística y Random Forest son deterministas y deben reproducirse exactamente.

## Detalles de implementación

Aspectos del diseño que conviene conocer al replicar o extender el experimento. Ninguno modifica las conclusiones de la tesis.

1. **Particiones.** `StratifiedGroupKFold` asigna los mismos sujetos a cada pliegue en A1, B y la línea base, siempre que el orden de sujetos sea el del manifiesto. En A2 la estratificación pondera por número de épocas, por lo que la comparación A1 vs A2 no está pareada pliegue a pliegue.
2. **Validación interna en A1, B y la línea base.** La separación para la parada temprana de los modelos profundos es una permutación aleatoria (mínimo 4 sujetos). El escalador y la FPCA se ajustan con todo el entrenamiento externo antes de separarla, lo que afecta solo a la parada temprana y no al conjunto de prueba (Sección 3.6.2). En A2, la separación por sujeto precede al ajuste.
3. **Random Forest.** Usa `random_state=42` en todas las semillas; la variabilidad entre semillas proviene de las particiones (Tabla B.2).
4. **Dropout.** El modelado aplica `dropout=0.3` a todas las arquitecturas profundas, incluidas Transformer y EEGNet (Tabla B.1).
5. **Alineación de sujetos.** El cuaderno 04 verifica la alineación entre el dataset A1 y el manifiesto mediante la secuencia de etiquetas. Una extensión natural es guardar los identificadores de sujeto en el NPZ y compararlos directamente.

## Comparar una réplica con los resultados de la tesis

Las cifras originales están en `results/reported/tabla_comparativa_reportada.csv`. Tras ejecutar `03_modeling.ipynb`:

```python
import pandas as pd
new = pd.read_csv("artifacts/03_modelado/resultados/tabla_comparativa_completa.csv")
ref = pd.read_csv("results/reported/tabla_comparativa_reportada.csv")
key = ["scenario", "repr", "model", "nivel"]
cmp = new[new.status == "ok"].merge(ref, on=key, suffixes=("_replica", "_tesis"))
cmp["dif_balacc"] = (cmp.balanced_acc_mean_replica - cmp.balanced_acc_mean_tesis).round(3)
print(cmp[key + ["balanced_acc_mean_tesis", "balanced_acc_mean_replica", "dif_balacc"]])
```

Las filas de LogReg y RandomForest deberían diferir en 0,000.

## Recomendación para una réplica estricta

Para una reproducción académica, utilice las versiones fijadas en `requirements.txt`, ejecute desde una carpeta limpia, borre `artifacts/` antes de iniciar y conserve los logs completos. Para consultar lo que se ejecutó originalmente, revise `notebooks/original/`, que conserva las salidas y los metadatos de ejecución.

## Qué verifica CI y qué no

La integración continua valida:

- integridad JSON de los notebooks portátiles;
- sintaxis Python de las celdas (ignorando comandos mágicos/shell de Jupyter);
- pruebas unitarias de las utilidades extraídas;
- coincidencia entre las cifras del README y `results/reported/`.

CI **no** descarga `ds003490`, no ejecuta el preprocesamiento completo y no reentrena modelos profundos, porque esas tareas requieren datos externos y recursos de cómputo sustancialmente mayores.
