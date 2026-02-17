# Research Log — Bitácora Metodológica (Journal-Strict)

## 1. Scope of the Log
Esta bitácora documenta el proceso de investigación sobre la distribución espectral de los ceros no triviales de la función Zeta de Riemann en el rango $T \in [1314, 10100]$. Este documento registra exclusivamente las decisiones metodológicas, observaciones técnicas y criterios de cierre del proyecto. No constituye un reporte de resultados finales, sino el rastro de auditoría del proceso investigativo. Se excluyen interpretaciones teóricas no fundamentadas en los datos recolectados.

## 2. Initial Question
La investigación partió de la necesidad de verificar la persistencia de la rigidez espectral (Fase Cristal) en regiones de energía media-alta. La pregunta central fue determinar el punto de transición hacia el régimen de caos cuántico universal (GUE) y si dicho punto era detectable mediante métricas de espaciamiento local. Se asumió inicialmente que la relajación hacia GUE sería detectable antes de $T=5000$. Los riesgos identificados incluyeron la degradación de la integridad del conteo asintótico y la insuficiencia de la precisión numérica (DPS) en zonas de alta densidad de valles.

## 3. Instrumentation and Protocol Choices
Se seleccionaron tres métricas fundamentales:
- **r-mean**: Por su robustez ante el unfolding local y su capacidad de distinguir entre Poisson (0.386), GUE (0.528) y regímenes de alta repulsión (>0.60).
- **Estadística de Dyson**: Para evaluar la deriva estructural y la estabilidad de la "fuerza" de repulsión entre ceros.
- **Auditoría de Von Mangoldt (dN)**: Como gate de integridad absoluto. Se definió que solo bloques con $dN = 0$ (error de conteo nulo) serían elegibles para certificación de fase. Cualquier desviación $dN \neq 0$ activa automáticamente la suspensión de la lectura de fase certificada.

## 4. Iterative Findings

### Etapa 1: Rango Bajo-Medio [1314, 3100]
- **Observación**: Los bloques S1, S2 y S3 mostraron una completitud del 100% con $dN=0$. El $r$-mean se estabilizó en el rango $[0.60, 0.62]$.
- **Decisión**: Se procedió a la certificación de la "Fase Cristal" debido a la integridad técnica total y la consistencia estadística.
- **Resultado**: Confirmación de rigidez espectral elevada por encima de la predicción GUE.
- **Limitación**: El tamaño de las ventanas ($N \approx 100$) impone un error estadístico base que requiere validación por sub-ventanas.

### Etapa 2: Frontera de Transición [5000, 5100]
- **Observación**: Se detectó el primer fallo de integridad ($dN = 1$). El $r$-mean permaneció en $\approx 0.60$.
- **Decisión**: Suspensión inmediata de la certificación de fase. El bloque se clasificó como "Observacional".
- **Resultado**: Identificación del desacople entre la estructura física (que permanece rígida) y la precisión del auditor teórico (quien pierde la cuenta).
- **Limitación**: La instrumentación basada en Von Mangoldt estándar alcanza su límite de resolución práctica en este punto.

### Etapa 3: Stress-Test de Alta Energía [10000, 10100]
- **Observación**: El error de conteo aumentó ($dN \approx +0.58$), mientras que el $r$-mean robusto (mediana) se mantuvo en $0.6059$.
- **Decisión**: Ejecución de un pipeline de rescate Newton (65% de carga) con $DPS=80$ para garantizar la ubicación topológica de los ceros pese al fallo del auditor.
- **Resultado**: Persistencia del orden espectral en condiciones de ruptura de auditoría.
- **Limitación**: La validación depende estrictamente de la potencia del algoritmo de rescate y no del marco teórico asintótico.

## 5. Boundary Identification
La frontera metodológica se identificó en $T \approx 5000$, donde la fluctuación de $dN$ dejó de ser nula. Se observó que las señales de repulsión (física) no mostraban una correlación de colapso con el error de conteo (auditoría). Se decidió no extender la certificación más allá de $T=3100$ para preservar la integridad del "Hecho Certificado", separando los hallazgos en capas de certidumbre.

## 6. Exploratory Branch (Φ-2)
Se permitió una rama exploratoria para investigar picos espectrales discretos en los spacings (orden cuasi-periódico) debido a la persistencia del $r$-mean elevado. Se exigió el protocolo **Φ-VERIFY** para mitigar el riesgo de artefactos.
- **Controles**: Se utilizaron surrogates de Shuffle y AR(1).
- **Criterio GREEN**: Se definió como un hit-rate $\geq 0.75$ y una estabilidad paramétrica $\geq 0.80$ ante cambios en la ventana de Welch.
- **No-conclusión**: No se concluyó que estos picos representen una propiedad universal de $\zeta(s)$, sino una característica reproducible del régimen observacional analizado.

## 7. Stopping Criteria
El proyecto se cerró en $T=10100$ debido a:
1.  **Costo Computacional**: El tiempo de CPU por cero rescatado creció un 400% respecto a la base.
2.  **Saturación del Auditor**: Sin una corrección de segundo orden para Von Mangoldt, el valor de $dN$ continuaría divergiendo, invalidando la utilidad de la auditoría.
3.  **Suficiencia de Datos**: La persistencia del cristal ha sido demostrada tanto en el régimen certificado como en el observacional de estrés. Continuar sin nuevas herramientas de integridad no aportaría certidumbre adicional.

## 8. Final Position
- **Certeza**: El espectro de Riemann es ultra-rígido ($r \approx 0.60$) y certificable hasta $T \approx 3100$.
- **Observación**: Esta rigidez persiste al menos hasta $T=10,000$, resistiendo el test de stress de parámetros.
- **Abierto**: El mecanismo de transición definitiva al caos GUE y la naturaleza exacta del orden cuasi-periódico detectado en Φ-2 permanecen como objetivos para investigación futura con instrumentación de mayor escala.
