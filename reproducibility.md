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

## Diferencia observada en el notebook de preprocesamiento

La salida almacenada en el notebook `01_UNM_preprocesamiento_FINAL_270926(3).ipynb` registra **MNE-Python 1.13.2**, mientras el manuscrito final documenta **1.12.1**. El archivo `requirements.txt` adopta **1.12.1** porque es la versión declarada en la tesis; la discrepancia se conserva explícitamente en `docs/repository_audit.md`.

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
4. `04_modeling.ipynb`
5. `05_ablation_adf.ipynb`
6. `06_interpretability.ipynb`

Los pasos 2A y 2B comparten el mismo preprocesamiento y pueden ejecutarse independientemente después de 01.

## Datos

Los datos EEG crudos no se incluyen en Git. El script `scripts/download_openneuro.sh` reproduce el mecanismo de descarga utilizado por el cuaderno de preprocesamiento mediante el bucket público S3 de OpenNeuro.

## Recomendación para una réplica estricta

Para una reproducción académica, utilice las versiones fijadas en `requirements.txt`, ejecute desde una carpeta limpia, borre `artifacts/` antes de iniciar y conserve los logs completos. Para una auditoría histórica de lo que se ejecutó originalmente, consulte `notebooks/original/`, que retiene outputs y metadatos de ejecución.

## Qué verifica CI y qué no

La integración continua valida:

- integridad JSON de los notebooks portátiles;
- sintaxis Python de las celdas (ignorando comandos mágicos/shell de Jupyter);
- pruebas unitarias de las utilidades extraídas.

CI **no** descarga `ds003490`, no ejecuta el preprocesamiento completo y no reentrena modelos profundos, porque esas tareas requieren datos externos y recursos de cómputo sustancialmente mayores.
