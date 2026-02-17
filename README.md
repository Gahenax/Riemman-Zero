# Riemman Zero

Este repositorio está dedicado a la investigación, consolidación y minería avanzada de los ceros no triviales de la función Zeta. 

## Objetivos
- Consolidar la base de datos de ceros rescatados.
- Implementar herramientas de visualización y análisis espectral.
- Explorar la frontera de integridad en altos valores de T.

## Modelo Axiomático del Desacople

Se define el estado del sistema mediante el par $(\Delta R, I)$ donde:
- $\Delta R(T) := E[r(T)] - 0.528$ (Exceso de Rigidez Espectral)
- $I(T) := \mathbb{1}\{dN(T) = 0\}$ (Indicador de Integridad)

$$
\exists T_c < T_m : 
\begin{cases} 
I(T)=1 \land \Delta R(T) \geq \epsilon & T \leq T_c \quad \text{[CRISTAL]} \\
I(T)=0 \land \Delta R(T) > 0 & T_c < T \leq T_m \quad \text{[FRONTERA]}
\end{cases}
$$

En $T \approx 10^4$, se observa bajo **Φ-VERIFY**:
$$P_s(f; T) \implies \frac{f_2}{f_1} = \rho \pm \delta$$

---
*Investigación Autónoma en curso por Jules & Antigravity (2026)*
