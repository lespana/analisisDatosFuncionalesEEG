# Auditoría técnica de conversión a repositorio

Esta auditoría separa las **evidencias presentes en los archivos entregados** de las decisiones de empaquetado realizadas para GitHub. No modifica conclusiones científicas.

## Archivos analizados

- 1 tesis final en PDF, 123 páginas.
- 6 notebooks Jupyter correspondientes a preprocesamiento, Enfoques A/B, modelado, ablación O1 e interpretabilidad O3.
- Todos los notebooks entregados pudieron analizarse como JSON y sus celdas de Python no mostraron errores sintácticos al excluir comandos mágicos/shell de Jupyter.
- Las salidas almacenadas no contienen un `error` de Jupyter de nivel superior.

## Hallazgos que conviene conservar explícitos

### 1. Diferencia de versión MNE

El manuscrito documenta **MNE-Python 1.12.1** como entorno final. La salida guardada en el notebook 01 muestra **MNE 1.13.2**. Para este repositorio, `requirements.txt` sigue la versión declarada en la tesis y esta diferencia queda registrada para auditoría.

### 2. Verificación de archivo obsoleta en 02A

El notebook 02A genera la reconstrucción del Enfoque A con el nombre:

```text
fig_4_13_reconstruccion_A_Pz.png
```

pero su lista `expected_files` comprueba:

```text
fig_4_12_reconstruccion_A_Pz.png
```

La ejecución almacenada marca ese archivo como `OK`, lo que es compatible con la presencia de una salida antigua en el Google Drive usado durante el desarrollo. En una ejecución limpia, esa comprobación puede fallar o validar un artefacto obsoleto. **Solo la copia portátil** corrige la comprobación a `fig_4_13_reconstruccion_A_Pz.png`; el original se conserva intacto.

### 3. Numeración de figuras de notebooks vs tesis final

Algunos nombres de archivo en 02B y 04 conservan números anteriores a la versión final del manuscrito. Ejemplos:

- reconstrucciones B guardadas durante el desarrollo con prefijo `fig_4_13_...`, mientras la tesis final las presenta como Fig. 4.14 y 4.15;
- matrices de confusión y curva de aprendizaje usan nombres internos anteriores, mientras la tesis final las enumera como Fig. 4.16-4.18;
- la interpretabilidad final corresponde a Fig. 4.19.

No se renombraron masivamente esos productos para evitar romper trazabilidad con los cuadernos. La correspondencia se documenta en `traceability.md`.

### 4. Dependencia original de Google Colab/Drive

Los notebooks originales usan rutas absolutas bajo `/content/drive/MyDrive/...`. Las copias portátiles aceptan:

- `PARKINSON_EEG_DATA`
- `PARKINSON_EEG_ROOT`
- `USE_GOOGLE_DRIVE`

Esta modificación afecta solo la infraestructura de archivos, no parámetros científicos.

### 5. Celdas con contador de ejecución ausente en 04

En el notebook de modelado hay celdas finales de visualización con `execution_count = null` aunque una celda posterior sí contiene salida almacenada. La versión portátil elimina todos los contadores y outputs para favorecer una ejecución limpia y secuencial de arriba hacia abajo.

## Decisiones de diseño del repositorio

- Los originales se preservan bajo `notebooks/original/`.
- Las copias portátiles se mantienen como notebooks para conservar narrativa, ecuaciones y trazabilidad experimental.
- Solo se extraen a `src/` utilidades pequeñas y testeables; no se reescribe el experimento completo como pipeline de producción porque eso podría alterar el flujo científico sin una nueva validación integral.
- Los EEG crudos y los artefactos grandes generados se excluyen de Git.
- No se asigna una licencia por defecto porque los materiales de origen no especifican una.

## Riesgos científicos que el propio trabajo reconoce

- muestra final limitada a 48 sujetos;
- una sola cohorte y una sola condición principal de registro;
- ausencia de contraste inferencial formal entre clasificadores;
- posible sesgo al destacar máximos observados entre múltiples configuraciones;
- hiperparámetros profundos comunes/fijos, no optimizados por arquitectura;
- localidad de CNN1D/EEGNet no necesariamente interpretable después de Cholesky/FPCA;
- el resultado es experimental y no un sistema diagnóstico.
