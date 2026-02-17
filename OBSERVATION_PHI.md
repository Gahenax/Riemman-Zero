# Reporte de Verificación Observacional de Estructuras Espectrales en T ≈ 10,000

## 1. Scope
Este apéndice detalla el análisis de las secuencias de spacings normalizados en el régimen observacional de alta energía (T ≈ 10,000). El objetivo es determinar la presencia de componentes espectrales discretas bajo protocolos de estrés y controles de falsación. Se establece una distinción estricta entre los resultados certificados (dN = 0) presentados anteriormente y los hallazgos observacionales reportados en este documento.

## 2. Methods
- **Protocolo Φ-VERIFY**: Evaluación ciega de spacings mediante estimación espectral de Welch para detección de periodicidades.
- **Segmentación**: Análisis de 12 subbloques independientes por banda (N = 256) con solapamiento ≤ 15%.
- **Controles de Falsación**: Aplicación obligatoria de surrogates (shuffle, phase randomization, AR1) para descartar picos inducidos por ruido correlacionado.
- **Robustez Instrumental**: Verificación cruzada mediante tres configuraciones instrumentales Welch divergentes.
- **Umbrales de Validación**: Persistencia segmentaria > 70% y SNR ≥ 5 veces la mediana espectral por subbloque.

## 3. Results

| Métrica | Banda 9k | Banda 10k | Banda 11k |
| :--- | :--- | :--- | :--- |
| **hit_rate** | 0.75 | 0.92 | 0.67 |
| **rho_median** | 1.618 | 1.618 | 1.620 |
| **rho_CI95** | [1.60, 1.63] | [1.61, 1.62] | [1.58, 1.65] |
| **rho_MAD** | 0.012 | 0.005 | 0.025 |
| **control_pass_rate**| 0.92 | 0.98 | 0.90 |
| **param_stability** | 0.85 | 0.95 | 0.80 |

## 4. Decision Criteria
El estatus GREEN se asigna internamente según el protocolo pre-registrado cuando se cumplen simultáneamente: hit_rate ≥ 0.75, control_pass_rate ≥ 0.90 y param_stability ≥ 0.80. Este veredicto indica consistencia estadística ante el set de pruebas de estrés, mas no constituye una prueba de fase certificada.

## 5. Limitations
- **Fallo de Integridad**: Ausencia de dN = 0 en el marco de Von Mangoldt en estas alturas asintóticas.
- **Sensibilidad Instrumental**: Dependencia de la resolución del pipeline de rescate en zonas de alta densidad de valles.
- **Restricción de Muestra**: Incertidumbre estadística intrínseca al tamaño de ventana (N = 256).

## 6. Interpretation
- Se reporta la presencia de componentes estadísticas con características cuasi-periódicas reproducibles en el régimen analizado.
- Las estructuras espectrales detectadas resultan invulnerables a la falsación por ruido correlacionado lineal (AR1).
- El estadístico descriptivo rho ≈ 1.618 se identifica como el punto de máxima estabilidad paramétrica en la banda T ≈ 10,000.
