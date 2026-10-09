# Resultados de referencia (no re-ejecutados)

Los archivos de esta carpeta transcriben **salidas impresas por los cuadernos
originales** ejecutados en Google Colab (GPU NVIDIA T4) y coinciden con las tablas
de la tesis. Sirven como referencia de trazabilidad y como insumo de las pruebas
`tests/test_reported_results.py`.

| Archivo | Origen | Tabla de la tesis |
|---|---|---|
| `tabla_comparativa_reportada.csv` | cuaderno 03, sección 13 (niveles sujeto y época) | 4.6, 4.7, 4.8, A.1-A.4 |
| `ablacion_LogReg_reportada.csv` | cuaderno 04, sección 7 | 4.9 |
| `fpca_componentes_A_reportada.csv` | cuaderno 03, sección 6 | 4.5 |
| `validacion_cholesky_reportada.csv` | cuadernos 02A y 02B | 4.4 |
| `parametros_entrenables_reportados.csv` | cuaderno 03, sección 11.2 y Anexo B | B.3 |
| `cohorte_y_paf_reportada.csv` | cuadernos 01, 02A, 02B, 03 y 05 | 3.1, 4.2, 4.5 y texto |

Notas:

* Las métricas son media ± DE sobre 15 evaluaciones externas (5 pliegues × 3
  semillas) a nivel de sujeto. No son intervalos de confianza: los pliegues
  repetidos comparten sujetos y no son independientes.
* Los modelos profundos se entrenaron sin forzar determinismo cuDNN; una nueva
  ejecución en GPU puede producir diferencias pequeñas en estas cifras.
