#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ANTIGRAVITY_INTEGRATION_OUROBOROS_LAB.py

Este script imprime el prompt oficial para que Antigravity
integre el experimento OUROBOROS_LAB al pipeline experimental
y al sistema de validación automática.

Ejecutar:
  python ANTIGRAVITY_INTEGRATION_OUROBOROS_LAB.py
"""

def main():
    prompt = """
ANTIGRAVITY :: INSTRUCCIÓN DE INTEGRACIÓN EXPERIMENTAL
=====================================================

OBJETIVO
--------
Integrar el experimento "OUROBOROS LAB (Demonio y Horno)" como
módulo experimental estándar dentro del framework de Antigravity,
siguiendo principios de reproducibilidad, falsación y auditoría.

CONTEXTO
--------
Existe un manifiesto heurístico (OUROBOROS_HYPOTHESIS.md) y un
experimento auditado (experiments/ouroboros_lab/OUROBOROS_LAB.py)
que demuestra un mecanismo general de sistemas complejos:
optimización local + costo global -> dinámica oscilatoria (ciclo límite).

Este experimento NO es ontológico ni metafísico. Es un toy model
mecanístico con semáforo automático (GREEN/AMBER/RED).

TAREAS DE INTEGRACIÓN
--------------------
1. Registrar OUROBOROS_LAB como experimento oficial:
   - categoría: systems / feedback / entropy
   - tipo: toy-model falsable
   - estado: reproducible

2. Enchufar al pipeline estándar:
   - input: parámetros (N, density, steps, alpha, gamma, seed)
   - ejecución headless (--outdir obligatorio)
   - output artefactos:
        - omega_control.npy
        - omega_ouroboros.npy
        - heat_ouroboros.npy
        - verdict.json
        - plots/*.png
        - params.json

3. Interpretar verdict.json:
   - GREEN  -> ciclo límite confirmado (autocorrelación + causalidad H->Ω)
   - AMBER  -> oscilación débil / intermitente
   - RED    -> estasis o ruido sin estructura

4. Añadir a la capa de reporte:
   - resumen de métricas
   - gráfico Ω vs H
   - conclusión automática basada en semáforo

CRITERIOS DE MUERTE
------------------
Abortar integración si:
- el experimento no produce artefactos deterministas con misma seed
- el detector de ciclos no es estable bajo reruns
- no se puede falsar (siempre GREEN sin importar parámetros)

REGLA DE ORO
------------
Antigravity NO debe presentar este experimento como "ley física".
Debe describirlo como:
"Demostración mecanística de retroalimentación negativa en sistemas abiertos."

CIERRE
------
Confirmar integración devolviendo:
- ruta del módulo
- hash del script integrado
- ejemplo de ejecución reproducible
"""

    print(prompt.strip())


if __name__ == "__main__":
    main()
