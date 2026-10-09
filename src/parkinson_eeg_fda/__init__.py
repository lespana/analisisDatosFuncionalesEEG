"""Utilidades reutilizables del proyecto EEG + ADF + Deep Learning para Parkinson.

Funciones pequeñas y probadas, extraídas de los cuadernos; los cuadernos de
``notebooks/`` siguen siendo la fuente ejecutable principal del experimento.

Módulos
-------
spectral
    Welch, PSD relativa logarítmica, potencia relativa por banda, línea base y PAF.
functional
    B-spline, GCV, matriz de Gram, coordenadas de Cholesky y FPCA dentro del pliegue.
evaluation
    Métricas, agregación por sujeto y particiones sin fuga de sujetos.
"""

__version__ = "1.0.0"
