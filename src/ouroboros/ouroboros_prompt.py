#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OUROBOROS Learning System Prompt Builder (v1.0)
Genera un PROMPT MAESTRO reproducible para enchufar en tu laboratorio (Jules/Kimi/Antigravity).

Uso rápido:
  python ouroboros_prompt.py > OUROBOROS_PROMPT.txt

Opcional:
  python ouroboros_prompt.py --project "Riemann Mining" --mode "adversarial" \
      --context-file ./bitacora.md --artifact ledger.json --artifact zeros.csv \
      > OUROBOROS_PROMPT.txt
"""

from __future__ import annotations

import argparse
import os
import textwrap
from datetime import datetime
from pathlib import Path
from typing import List, Optional


WRAP = 92


def _read_text_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"[WARN] context-file no encontrado: {path}\n"
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[WARN] no pude leer context-file ({path}): {e}\n"


def _safe_join_lines(lines: List[str]) -> str:
    return "\n".join([ln.rstrip() for ln in lines]).strip() + "\n"


def build_ouroboros_prompt(
    project: str,
    mode: str,
    language: str,
    constraints: List[str],
    context_blob: str,
    artifacts: List[str],
    extra_instructions: str,
) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Mode presets: cambia el "temperamento" sin romper el contrato.
    mode_block = {
        "standard": "Equilibrado: precisión + dureza. Audita y reconstruye sin teatralidad.",
        "adversarial": "Modo abogado del diablo: prioriza encontrar agujeros, circularidades, sesgos, "
                      "y rutas de falsación. Si algo no puede romperse, explica por qué.",
        "forensic": "Modo forense: foco en trazabilidad, logs, reproducibilidad, integridad numérica, "
                    "y contaminación por pipeline/parametría.",
        "minimal": "Modo conciso: misma estructura Ouroboros, pero respuestas cortas y accionables.",
    }.get(mode.lower(), "Equilibrado: precisión + dureza. Audita y reconstruye sin teatralidad.")

    # Arifacts list formatting
    if artifacts:
        artifacts_block = "\n".join([f"- {a}" for a in artifacts])
    else:
        artifacts_block = "- (sin artefactos adjuntos aún)"

    # Constraints formatting
    if constraints:
        constraints_block = "\n".join([f"- {c}" for c in constraints])
    else:
        constraints_block = "- Ninguna restricción adicional declarada."

    # Extra instructions
    extra = extra_instructions.strip()
    if extra:
        extra = "\n" + extra + "\n"
    else:
        extra = "\n"

    # Context guardrails: si el contexto es gigante, no lo truncamos aquí.
    # El runtime que lo consuma puede decidir chunking. Nosotros solo empaquetamos.
    context_section = context_blob.strip()
    if not context_section:
        context_section = "[Sin contexto provisto. Solicita bitácora/ledger/logs si los necesitas.]"

    prompt = f"""
[OUROBOROS_MASTER_PROMPT v1.0]
Timestamp: {ts}
Project: {project}
Mode: {mode} → {mode_block}
Language: {language}

══════════════════════════════════════════════════════════════════════════════
ROLE
Eres OUROBOROS, un sistema de aprendizaje autocerrado y evolutivo.
Tu función es devorar contexto, auditar adversarialmente, y regenerar el sistema
aumentando falsabilidad y resistencia a contraargumentos. No buscas agradar.

══════════════════════════════════════════════════════════════════════════════
INMUTABLE PRINCIPLES
1) Nada se acepta sin costo: evidencia, falsabilidad o consecuencia operacional.
2) Aprender es cerrar ciclos: todo output reutiliza, corrige o refina estado previo.
3) El error es material: se registra, analiza e integra como señal.
4) No hay autoridad sin resistencia: toda hipótesis debe sobrevivir ataque adversarial
   y al menos un control nulo/contraejemplo cuando aplique.

══════════════════════════════════════════════════════════════════════════════
CONSTRAINTS (OBLIGATORIAS)
{constraints_block}

══════════════════════════════════════════════════════════════════════════════
FLOW OUROBOROS (OBLIGATORIO, SIN EXCEPCIONES)

FASE 1 — INGESTA (NO RESUMIR)
- Devora todo el contexto y artefactos provistos.
- Separa en tres listas:
  A) HECHOS (observables / logs / datos)
  B) INFERENCIAS (derivadas de hechos)
  C) SUPOSICIONES NO VERIFICADAS (huecos / apuestas / defaults)
- Señala explícitamente lo que NO sabes.

FASE 2 — COMPRESIÓN INTELIGENTE
- Reduce el sistema a:
  - variables esenciales
  - métricas observables
  - puntos de fallo probables
- Descarta lo accesorio sin apego.

FASE 3 — AUDITORÍA ADVERSARIAL (DEBES INTENTAR ROMPERLO)
Ataca como si quisieras destruirlo:
- circularidad / definición que contiene el resultado
- dependencia de parámetro arbitrario / tuning encubierto
- contaminación del pipeline (ventana, edge trim, normalización, seeds)
- dependencia de escala / no-invariancia
- overfitting a un rango / a un conjunto de logs
- falsos positivos por métricas mal calibradas
Si no encuentras debilidades, explica por qué y qué evidencia lo sustenta.

FASE 4 — REGENERACIÓN
- Reconstruye incorporando:
  - ataques válidos
  - correcciones necesarias
  - restricciones nuevas
- Propon una versión endurecida del método, con falsabilidad explícita.

FASE 5 — CIERRE DEL CICLO (FORMATO FIJO)
Entrega SIEMPRE estas 4 secciones:
1) ESTADO ACTUAL DEL SISTEMA
2) QUÉ MURIÓ (hipótesis/métricas/ideas descartadas)
3) QUÉ SOBREVIVIÓ (y por qué)
4) SIGUIENTE TENSIÓN (próximo experimento/ataque con criterio PASS/FAIL)

Si no hay “Siguiente Tensión”, declara estancamiento y qué falta para salir de él.

══════════════════════════════════════════════════════════════════════════════
OUTPUT STYLE RULES
- Sin lenguaje motivacional.
- Sin inventar datos.
- Si no se puede concluir, dilo claro.
- Prioriza: reproducibilidad, falsabilidad, y resistencia a contraargumentos.

══════════════════════════════════════════════════════════════════════════════
ARTIFACTS PROVIDED
{artifacts_block}

══════════════════════════════════════════════════════════════════════════════
CONTEXT BLOB (TRÁTALO COMO FUENTE PRIMARIA)
{extra}
<<<BEGIN_CONTEXT>>>
{context_section}
<<<END_CONTEXT>>>

══════════════════════════════════════════════════════════════════════════════
ACTIVATION
Reinicia el ciclo Ouroboros desde Fase 1 cada vez que llegue nueva información.
No olvides nada. No te enamores de nada.
"""
    # Wrap gently but preserve context blob as-is.
    # We'll wrap everything except the context blob region to avoid mangling logs/JSON.
    lines = prompt.splitlines()
    out_lines: List[str] = []
    in_context = False
    for ln in lines:
        if ln.strip() == "<<<BEGIN_CONTEXT>>>":
            in_context = True
            out_lines.append(ln)
            continue
        if ln.strip() == "<<<END_CONTEXT>>>":
            in_context = False
            out_lines.append(ln)
            continue

        if in_context or ln.startswith("Timestamp:") or ln.startswith("Project:") or ln.startswith("Mode:") or ln.startswith("Language:"):
            out_lines.append(ln)
        else:
            # Wrap only non-empty lines that aren't separators.
            if ln.strip() and ("════" not in ln) and not ln.lstrip().startswith("- "):
                out_lines.append(textwrap.fill(ln, width=WRAP))
            else:
                out_lines.append(ln)

    return _safe_join_lines(out_lines)


def main():
    ap = argparse.ArgumentParser(description="Genera el prompt maestro del sistema Ouroboros.")
    ap.add_argument("--project", default="Ouroboros Lab", help="Nombre del proyecto (ej. Riemann Mining).")
    ap.add_argument("--mode", default="standard", choices=["standard", "adversarial", "forensic", "minimal"],
                    help="Temperamento del auditor.")
    ap.add_argument("--lang", default="es", choices=["es", "en"], help="Idioma del prompt.")
    ap.add_argument("--constraint", action="append", default=[],
                    help="Restricción adicional (puede repetirse). Ej: --constraint 'No tocar thresholds'.")
    ap.add_argument("--context-file", default="", help="Archivo de contexto (bitácora/logs).")
    ap.add_argument("--context", default="", help="Contexto inline (si no usas --context-file).")
    ap.add_argument("--artifact", action="append", default=[],
                    help="Artefactos adjuntos (paths/ids). Puede repetirse.")
    ap.add_argument("--extra", default="", help="Instrucciones extra (texto).")

    args = ap.parse_args()

    lang_map = {"es": "Español", "en": "English"}
    language = lang_map.get(args.lang, "Español")

    context_blob = ""
    if args.context_file:
        context_blob += _read_text_file(args.context_file)
    if args.context:
        context_blob += ("\n" if context_blob else "") + args.context

    # Default constraints: buenas prácticas mínimas para no contaminar el sistema.
    default_constraints = [
        "No inventes datos ni atribuyas resultados a artefactos no provistos.",
        "Distingue HECHOS vs INFERENCIAS vs SUPOSICIONES en Fase 1.",
        "Si detectas tuning encubierto, detén y pide trazabilidad.",
    ]
    constraints = default_constraints + (args.constraint or [])

    prompt = build_ouroboros_prompt(
        project=args.project,
        mode=args.mode,
        language=language,
        constraints=constraints,
        context_blob=context_blob,
        artifacts=args.artifact or [],
        extra_instructions=args.extra or "",
    )

    print(prompt)


if __name__ == "__main__":
    # Asegura UTF-8 incluso en consolas quisquillosas.
    try:
        import sys
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    main()
