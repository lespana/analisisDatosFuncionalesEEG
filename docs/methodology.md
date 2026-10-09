# Metodología

Resumen del Capítulo 3 de la tesis ([`thesis.pdf`](thesis.pdf)). Las ecuaciones y la justificación completa están en el documento; aquí se recogen los parámetros que implementan los cuadernos.

## 1. Cohorte (§3.1)

OpenNeuro ds003490 (Universidad de Nuevo México): 64 canales, 500 Hz, referencia CPz. Se analizan los segmentos de **ojos cerrados** de 25 controles (HC) y de 25 pacientes en su sesión **OFF** de medicación. Tras el control de calidad, la muestra efectiva es de **24 HC y 24 PD-OFF**. El registro OFF se obtuvo tras la retirada temporal del tratamiento dopaminérgico, según el protocolo del conjunto de datos.

## 2. Preprocesamiento (§3.2, cuaderno 01)

| Etapa | Parámetro |
|---|---|
| Referencia | promedio común |
| Filtro | FIR pasa-banda 1-40 Hz (`firwin`) |
| Remuestreo | 250 Hz |
| Artefactos oculares | FastICA (máx. 20 componentes), `find_bads_eog` con umbral 3 sobre VEOG/HEOG; máx. 2 componentes excluidos |
| Canales del análisis | C3, Cz, C4, P7, P8, P3, Pz, P4, O1, O2 (seleccionados después de ICA) |
| Épocas | 4 s, sin solapamiento |
| Rechazo | amplitud pico a pico > 100 µV o \|z de curtosis\| > 5 en cualquier canal |
| Inclusión | al menos 6 épocas válidas |

## 3. Estimación espectral (§3.3)

Welch por época con ventanas de 2 s y 50 % de solapamiento (resolución 0,5 Hz). La potencia total de referencia se integra en 1-30 Hz con la regla de Simpson.

- **Línea base sin ADF.** Por sujeto: promedio de la PSD lineal entre épocas, potencias relativas (log10) de delta, theta, pre-alfa (5,5-8 Hz), alfa y beta, frecuencia dominante y cociente alfa/theta. Son 7 variables × 10 canales.
- **Enfoque A.** `log10(PSD relativa)` por época y canal, restringida a 4-13 Hz (19 puntos). La normalización y el logaritmo se aplican antes de cualquier promedio.
- **Enfoque B.** `log10` de la potencia relativa theta (4-8 Hz) y alfa (8-13 Hz) por época, ordenada sobre `t = (e-1)/(E-1) ∈ [0, 1]`. Este dominio representa la posición relativa de las épocas válidas, no el tiempo físico.

## 4. Representación funcional (§3.4, cuadernos 02A y 02B)

| Elemento | Enfoque A | Enfoque B |
|---|---|---|
| Dominio | 4-13 Hz | [0, 1] |
| Base | B-spline cúbica, nudos uniformes | B-spline cúbica, nudos uniformes |
| Selección de nudos | GCV sobre 300 curvas época-canal; k ∈ {4,…,10, 12, 15} | GCV sobre todas las trayectorias; k ∈ [2, min(8, E_min − 3)] |
| Resultado | k = 9 → 11 bases | k = 2 → 4 bases por banda |
| Coeficientes | mínimos cuadrados con cresta 10⁻⁶ | mínimos cuadrados con cresta 10⁻⁶ |
| Observaciones | A1: 1 curva promedio por sujeto; A2: 1 curva por época | 1 trayectoria por sujeto, canal y banda |

Como análisis de sensibilidad se compara la B-spline con una P-spline (17 bases, penalización de diferencias de segundo orden, λ por GCV), que no alimenta los modelos.

**Geometría L².** La matriz de Gram `G_ij = ∫ φ_i φ_j` se calcula por Simpson en 1001 puntos. Las coordenadas de Cholesky `z = c L`, con `G = L Lᵀ`, cumplen `‖z₁ − z₂‖² = ‖x₁ − x₂‖²_{L²}`.

**FPCA.** Se aplica PCA sobre `z` por canal (y por canal y banda en B), ajustada **solo con el entrenamiento** de cada pliegue, reteniendo el 95 % de la varianza. Los scores se estandarizan después.

Cada configuración se evalúa con tres entradas: `X_raw` (coeficientes B-spline), `X_chol` (coordenadas de Cholesky) y `X_chol_fpca` (scores FPCA).

## 5. Modelos (§3.5, cuaderno 03; Anexo B)

- **Clásicos.** Regresión logística L2 (C = 1) y Random Forest (200 árboles, profundidad 10), ambos con `class_weight='balanced'`.
- **Profundos.** MLP, Transformer sobre canales, CNN1D, FNN, FDNN, AdaFNN y EEGNet, todos con la misma configuración:
  - optimizador AdamW (lr 10⁻³, weight decay 10⁻⁴), lote de 32 y máximo 80 épocas;
  - programación coseno y parada temprana con paciencia 15;
  - dropout 0,3 y `pos_weight` calculado en entrenamiento.

  FNN, FDNN y AdaFNN son adaptaciones a coeficientes finito-dimensionales; en CNN1D y EEGNet la convolución recorre el eje de coeficientes.

## 6. Validación (§3.6)

- **Particiones externas.** `StratifiedGroupKFold` con 5 pliegues y semillas 42, 123 y 2024, lo que da 15 evaluaciones; el sujeto es la variable de grupo.
- **Transformaciones.** FPCA y estandarización se ajustan en entrenamiento. En A2 + DL se ajustan solo con el entrenamiento interno, cuya separación por sujeto se hace antes.
- **Validación interna.** Alrededor del 20 % se reserva únicamente para la parada temprana de los modelos profundos.
- **Agregación.** En A2 las probabilidades por época se promedian por sujeto.
- **Métricas.** Se reportan a nivel de sujeto: exactitud balanceada, sensibilidad, especificidad, F1 y AUC, con umbral 0,5 y PD-OFF como clase positiva.
- **Resumen.** Media ± DE sobre las 15 evaluaciones. Son resúmenes descriptivos, no intervalos de confianza.

## 7. Análisis complementarios

- **Aporte del ADF (§3.5.4, cuaderno 04).** Con regresión logística y las mismas 15 particiones se comparan seis representaciones: escalares theta + alfa + PAF; PSD discreta 4-13 Hz; PSD + PCA; y A1 en sus tres variantes (B-spline, Cholesky, Cholesky + FPCA). Las diferencias se reportan como deltas pareados descriptivos.
- **Interpretabilidad (§3.5.5, cuaderno 05).** A partir de la regresión logística sobre A1 + Cholesky se reconstruyen las funciones de peso `β_c(f) = Σ_k b_ck φ_k(f)`, con `b_c = L⁻ᵀ a_c`. Se verifica numéricamente que el logit funcional coincide con el de scikit-learn y se resume la estabilidad entre pliegues, las integrales por banda y la sensibilidad de borde.
- **Estadística descriptiva (§3.7).** Mann-Whitney bilateral con tamaño de efecto rank-biserial para variables de la cohorte (PAF, componentes ICA, épocas conservadas).
