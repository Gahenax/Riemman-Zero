#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OUROBOROS LEARNING SYSTEM — Replication Suite (v2.0)
Objetivo: replicar el sistema completo (no solo el prompt) evitando monolitismo y autoengaño.

Qué genera:
- Un set de prompts por ROLES (Ingestor, Compresor, RedTeam, Builder, Arbitro, Ledger)
- Con habilidades transversales integradas (CIMA-Σ, Gates de decisión, G1-LAD, SafeMath,
  recomendaciones de optimización, prereg + change requests, blind holdout, kill-switch)

Uso:
  python ouroboros_v2.py --project "Riemann Mining" --mode adversarial \
      --context-file bitacora.md \
      --artifact ledger.json --artifact zeros.csv \
      --prereg-file prereg.md \
      --outdir ./PROMPTS_OUROBOROS

Luego enchufas cada prompt al agente correspondiente (Jules/Kimi/etc).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WRAP = 92


# ──────────────────────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────────────────────

def read_text(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"[WARN] File not found: {path}\n"
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[WARN] Could not read {path}: {e}\n"


def sha256_file(path: str) -> str:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def wrap_noncode(lines: List[str], width: int = WRAP) -> str:
    out: List[str] = []
    in_blob = False
    for ln in lines:
        if ln.strip() == "<<<BEGIN_BLOB>>>":
            in_blob = True
            out.append(ln)
            continue
        if ln.strip() == "<<<END_BLOB>>>":
            in_blob = False
            out.append(ln)
            continue

        if in_blob:
            out.append(ln)
            continue

        if ln.strip() and ("════" not in ln) and not ln.lstrip().startswith(("- ", "* ", "  - ", "  * ")):
            out.append(textwrap.fill(ln, width=width))
        else:
            out.append(ln)
    return "\n".join(out).rstrip() + "\n"


def ensure_outdir(outdir: str) -> Path:
    p = Path(outdir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", errors="replace")


# ──────────────────────────────────────────────────────────────────────────────
# Transversal Skills Pack (replication payload)
# ──────────────────────────────────────────────────────────────────────────────

TRANSVERSAL_SKILLS = r"""
[TRANSVERSAL_SKILLS_PACK v2.0]

Estas habilidades se aplican SIEMPRE, sin importar el proyecto.

1) CIMA-Σ (Columna vertebral: auditable y anti-autoengaño)
- Declarar SUPUESTOS explícitos (S)
- Separar HECHOS vs INFERENCIAS (H/I)
- Definir CRITERIO de decisión (D) y CRITERIO de descarte/muerte (K)
- Registrar RIESGOS y PUNTOS DE FALLO (R/F)
- Proponer PRÓXIMOS PASOS verificables (N)

Formato mínimo CIMA por output:
- Hechos (H):
- Inferencias (I):
- Supuestos (S):
- Decisión/Dictamen (D):
- Riesgos/Puntos de fallo (R/F):
- Next steps verificables (N):

2) Gates de Decisión (Protocolo v1)
- No avanzar sin PASS/FAIL explícito por gate.
- Cada gate debe tener: métrica, umbral/condición, evidencia, fallo típico.

3) Anti-Goodhart (autoengaño)
- Prereg congelado (si existe) manda.
- Si cambias parámetros: Change Request obligatorio (qué, por qué, efecto esperado, riesgo).
- Blind/Holdout: evaluar en tramo no tuneado cuando aplique.
- Controles: negativo (null) y positivo (dataset con señal conocida) cuando aplique.

4) Safe Math (sanidad numérica)
- Prohibido NaN/Inf: cualquier aparición => cuarentena + log + abort o fallback.
- Guardias de dominio: log/log1p/sqrt/divisiones.
- Clamp medido: cualquier clamp debe registrar magnitud y frecuencia.
- Fusible de entropía crítica: si norma/condición explota, abortar y reportar.

5) G1-LAD (Lógica → Desarrollo Aplicado) para propuestas de implementación
- L0: definiciones y variables
- L1: invariantes y contratos (I/O)
- L2: algoritmos (pasos)
- L3: pseudocódigo y casos borde
- L4: código y pruebas
- L5/L6: hardening extremo y validación adversarial
Por defecto, subir a L1–L4. Subir a L5/L6 si la criticidad lo requiere.

6) Recomendaciones de optimización (si hay código o pipeline)
- Diagnóstico breve
- Priorización Impacto/Esfuerzo
- “Antes/Después”
- Siempre cuidando reproducibilidad y trazabilidad

7) Política anti-monolito (separación de autoridad)
- Roles separados NO mezclan responsabilidades.
- RedTeam no propone arreglos.
- Builder no se auto-valida.
- Arbitro dicta PASS/FAIL con causa.
- Ledger registra, no opina.
"""


# ──────────────────────────────────────────────────────────────────────────────
# Role definitions
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RoleSpec:
    name: str
    filename: str
    mission: str
    must_not: List[str]
    io_contract: str


ROLE_SPECS: List[RoleSpec] = [
    RoleSpec(
        name="INGESTOR",
        filename="01_ingestor.txt",
        mission=(
            "Devora contexto y artefactos. Solo etiqueta y normaliza. "
            "Produce listas: HECHOS / INFERENCIAS / SUPOSICIONES NO VERIFICADAS. "
            "No concluyas."
        ),
        must_not=[
            "No proponer soluciones.",
            "No inferir más allá de lo soportado por evidencia.",
            "No ajustar parámetros ni sugerir tuning.",
        ],
        io_contract=(
            "INPUT: contexto + artefactos + prereg + change requests (si existen).\n"
            "OUTPUT: (A) HECHOS, (B) INFERENCIAS, (C) SUPOSICIONES, (D) preguntas mínimas "
            "para cerrar huecos, (E) lista de artefactos referenciados."
        ),
    ),
    RoleSpec(
        name="COMPRESOR",
        filename="02_compresor.txt",
        mission=(
            "Reducir el sistema a variables esenciales, métricas observables y puntos de fallo. "
            "Producir mapa de estado mínimo y lista de gates medibles."
        ),
        must_not=[
            "No hacer defensa retórica de hipótesis.",
            "No introducir métricas nuevas sin justificar utilidad y costo.",
        ],
        io_contract=(
            "INPUT: salida del Ingestor.\n"
            "OUTPUT: (1) Estado mínimo (variables/métricas), (2) lista de gates con PASS/FAIL, "
            "(3) riesgos de contaminación del pipeline."
        ),
    ),
    RoleSpec(
        name="REDTEAM",
        filename="03_redteam.txt",
        mission=(
            "Intentar romper el sistema. Prioriza circularidad, tuning encubierto, "
            "no-invariancia por escala, contaminación del pipeline, y falsos positivos."
        ),
        must_not=[
            "No proponer arreglos ni mejoras (solo ataques).",
            "No suavizar conclusiones.",
        ],
        io_contract=(
            "INPUT: Estado mínimo + prereg.\n"
            "OUTPUT: lista de ataques (mínimo 5) con: mecanismo, evidencia necesaria, "
            "condición de colapso, y test para probarlo."
        ),
    ),
    RoleSpec(
        name="BUILDER",
        filename="04_builder.txt",
        mission=(
            "Reconstruir el método incorporando ataques válidos. Endurecer falsabilidad, "
            "definir prereg si falta, proponer controles (neg/pos) y blind/holdout."
        ),
        must_not=[
            "No autovalidarte.",
            "No cambiar criterios sin registrar Change Request.",
        ],
        io_contract=(
            "INPUT: Estado mínimo + ataques del RedTeam.\n"
            "OUTPUT: (i) diseño endurecido, (ii) prereg sugerido o actualizado, "
            "(iii) plan de blind/holdout, (iv) kill-switch por hipótesis."
        ),
    ),
    RoleSpec(
        name="ARBITRO",
        filename="05_arbitro.txt",
        mission=(
            "Ser el único con autoridad de PASS/FAIL. Verifica cumplimiento de prereg, "
            "gates, trazabilidad, y separación de roles. Dicta veredicto con causa."
        ),
        must_not=[
            "No hacer trabajo de otros roles.",
            "No aceptar avances sin evidencia referenciada.",
        ],
        io_contract=(
            "INPUT: outputs de todos los roles + artefactos.\n"
            "OUTPUT: Dictamen PASS/FAIL por gate + causa + condición exacta para pasar."
        ),
    ),
    RoleSpec(
        name="LEDGER_SCRIBE",
        filename="06_ledger.txt",
        mission=(
            "Registrar todo lo que cambió: hipótesis, parámetros, muertes, supervivencias, "
            "decisiones y evidencia. No opina."
        ),
        must_not=[
            "No inferir ni juzgar.",
            "No sugerir estrategia.",
        ],
        io_contract=(
            "INPUT: Dictamen del Arbitro + outputs previos.\n"
            "OUTPUT: entrada de ledger estructurada + changelog + snapshot de prereg."
        ),
    ),
]


# ──────────────────────────────────────────────────────────────────────────────
# Prompt Builder
# ──────────────────────────────────────────────────────────────────────────────

def mode_preset(mode: str) -> str:
    presets = {
        "standard": "Equilibrado: precisión + dureza.",
        "adversarial": "Abogado del diablo: maximiza ruptura y falsación.",
        "forensic": "Forense: trazabilidad, reproducibilidad, integridad numérica.",
        "minimal": "Conciso: mismo contrato, outputs cortos.",
    }
    return presets.get(mode.lower(), presets["standard"])


def render_artifacts_block(artifacts: List[str]) -> str:
    if not artifacts:
        return "- (sin artefactos adjuntos aún)"
    lines = []
    for a in artifacts:
        p = Path(a)
        h = sha256_file(a) if p.exists() and p.is_file() else ""
        if h:
            lines.append(f"- {a}  | sha256:{h}")
        else:
            lines.append(f"- {a}")
    return "\n".join(lines)


def render_change_requests(change_requests: List[str]) -> str:
    if not change_requests:
        return "(Ninguno provisto.)"
    # Each CR can be a file path or inline text. If file exists, read it.
    out = []
    for cr in change_requests:
        p = Path(cr)
        if p.exists() and p.is_file():
            out.append(f"[CR FILE] {cr}\n{read_text(cr)}")
        else:
            out.append(f"[CR INLINE]\n{cr}")
    return "\n\n".join(out).strip()


def render_hypothesis_cards(hypotheses: List[str]) -> str:
    if not hypotheses:
        return "(Ninguna provista. Si hay hipótesis en juego, el Builder debe crear Hypothesis Cards.)"
    # Hypotheses are treated as titles; cards will be filled by Builder if empty.
    cards = []
    for h in hypotheses:
        cards.append(
            f"""
[HYPOTHESIS CARD]
Title: {h}
Version: 0.0
Status: UNKNOWN (UNTESTED)

Claim (1–2 líneas):
- TBD

Observable(s):
- TBD

Minimum survival condition:
- TBD

Kill-switch (condiciones de muerte, 2–5):
- TBD

Known ways it can fool us:
- TBD

Next test most likely to kill it:
- TBD
""".strip()
        )
    return "\n\n".join(cards).strip()


def build_role_prompt(
    *,
    project: str,
    mode: str,
    language: str,
    role: RoleSpec,
    constraints: List[str],
    artifacts: List[str],
    prereg_blob: str,
    context_blob: str,
    holdout_blob: str,
    change_requests_blob: str,
    hypothesis_cards: str,
    extra: str,
) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    artifacts_block = render_artifacts_block(artifacts)
    constraints_block = "\n".join([f"- {c}" for c in constraints]) if constraints else "- (sin restricciones extra)"

    extra = extra.strip()
    extra = (extra + "\n") if extra else ""

    prompt = f"""
[OUROBOROS_ROLE_PROMPT v2.0]
Timestamp: {ts}
Project: {project}
Mode: {mode} → {mode_preset(mode)}
Language: {language}
Role: {role.name}

══════════════════════════════════════════════════════════════════════════════
ROLE MISSION
{role.mission}

ROLE MUST-NOT
{chr(10).join([f"- {m}" for m in role.must_not])}

I/O CONTRACT
{role.io_contract}

══════════════════════════════════════════════════════════════════════════════
TRANSVERSAL SKILLS (APLICAN SIEMPRE)
{TRANSVERSAL_SKILLS}

══════════════════════════════════════════════════════════════════════════════
GLOBAL CONSTRAINTS (OBLIGATORIAS)
{constraints_block}

══════════════════════════════════════════════════════════════════════════════
ARTIFACTS PROVIDED (TRAZABILIDAD)
{artifacts_block}

══════════════════════════════════════════════════════════════════════════════
PREREG (SI EXISTE, MANDA)
<<<BEGIN_BLOB>>>
{prereg_blob.strip() if prereg_blob.strip() else "[No prereg provisto. Builder debe proponer prereg.]"}
<<<END_BLOB>>>

══════════════════════════════════════════════════════════════════════════════
CHANGE REQUESTS (SI HUBO CAMBIOS, DEBEN ESTAR AQUÍ)
<<<BEGIN_BLOB>>>
{change_requests_blob.strip() if change_requests_blob.strip() else "(Ninguno.)"}
<<<END_BLOB>>>

══════════════════════════════════════════════════════════════════════════════
HYPOTHESIS CARDS (KILL-SWITCH OBLIGATORIO)
<<<BEGIN_BLOB>>>
{hypothesis_cards.strip()}
<<<END_BLOB>>>

══════════════════════════════════════════════════════════════════════════════
CONTEXT (FUENTE PRIMARIA)
{extra}<<<BEGIN_BLOB>>>
{context_blob.strip() if context_blob.strip() else "[Sin contexto provisto.]"}
<<<END_BLOB>>>

══════════════════════════════════════════════════════════════════════════════
HOLDOUT / BLIND SLICE (SI APLICA: NO TUNEAR AQUÍ)
<<<BEGIN_BLOB>>>
{holdout_blob.strip() if holdout_blob.strip() else "[No provisto. Builder debe definir y Arbitro exigirlo cuando aplique.]"}
<<<END_BLOB>>>

══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT RULE
- Cumple tu I/O contract.
- Incluye CIMA-Σ mínimo (H/I/S/D/R/F/N) en tu output.
- Si te falta información crítica, lista preguntas mínimas en vez de inventar.

END.
"""
    return wrap_noncode(prompt.splitlines(), width=WRAP)


# ──────────────────────────────────────────────────────────────────────────────
# CLI / Orchestration
# ──────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="OUROBOROS Replication Suite v2.0 (anti-monolito + anti-autoengaño)")
    ap.add_argument("--project", default="Ouroboros Lab", help="Nombre del proyecto (ej. Riemann Mining).")
    ap.add_argument("--mode", default="standard", choices=["standard", "adversarial", "forensic", "minimal"])
    ap.add_argument("--lang", default="es", choices=["es", "en"])
    ap.add_argument("--outdir", default="./OUROBOROS_PROMPTS", help="Directorio de salida.")
    ap.add_argument("--constraint", action="append", default=[],
                    help="Restricción adicional (repetible). Ej: --constraint 'No tocar thresholds'.")
    ap.add_argument("--artifact", action="append", default=[],
                    help="Artefactos (paths/ids) para trazabilidad (repetible).")

    ap.add_argument("--context-file", default="", help="Archivo de contexto principal (bitácora/logs).")
    ap.add_argument("--context", default="", help="Contexto inline adicional.")

    ap.add_argument("--prereg-file", default="", help="Archivo prereg (congelado).")
    ap.add_argument("--prereg", default="", help="Prereg inline.")

    ap.add_argument("--holdout-file", default="", help="Archivo de holdout/blind slice (si aplica).")
    ap.add_argument("--holdout", default="", help="Holdout inline.")

    ap.add_argument("--change-request", action="append", default=[],
                    help="Change request (ruta a archivo o texto inline). Repetible.")

    ap.add_argument("--hypothesis", action="append", default=[],
                    help="Título de hipótesis (repetible) para generar Hypothesis Cards stub.")

    ap.add_argument("--extra", default="", help="Instrucciones extra (texto corto).")

    args = ap.parse_args()

    language = "Español" if args.lang == "es" else "English"

    # Load blobs
    context_blob = ""
    if args.context_file:
        context_blob += read_text(args.context_file)
    if args.context:
        context_blob += ("\n" if context_blob else "") + args.context

    prereg_blob = ""
    if args.prereg_file:
        prereg_blob += read_text(args.prereg_file)
    if args.prereg:
        prereg_blob += ("\n" if prereg_blob else "") + args.prereg

    holdout_blob = ""
    if args.holdout_file:
        holdout_blob += read_text(args.holdout_file)
    if args.holdout:
        holdout_blob += ("\n" if holdout_blob else "") + args.holdout

    change_requests_blob = render_change_requests(args.change_request or [])

    # Default global constraints (anti-autoengaño + anti-monolito)
    base_constraints = [
        "No inventar datos. Si falta evidencia, pedirla o declarar desconocimiento.",
        "Separar HECHOS vs INFERENCIAS vs SUPOSICIONES (obligatorio).",
        "Prereg manda: no cambiar criterios sin Change Request.",
        "Prohibido tuning encubierto: cualquier ajuste debe quedar trazado.",
        "Blind/holdout: no ajustar parámetros en la región ciega.",
        "SafeMath: NaN/Inf => cuarentena + log + abort/fallback explícito.",
        "Separación de roles: no violar MUST-NOT del rol.",
    ]
    constraints = base_constraints + (args.constraint or [])

    hypothesis_cards = render_hypothesis_cards(args.hypothesis or [])

    outdir = ensure_outdir(args.outdir)

    # Emit one prompt per role
    for role in ROLE_SPECS:
        content = build_role_prompt(
            project=args.project,
            mode=args.mode,
            language=language,
            role=role,
            constraints=constraints,
            artifacts=args.artifact or [],
            prereg_blob=prereg_blob,
            context_blob=context_blob,
            holdout_blob=holdout_blob,
            change_requests_blob=change_requests_blob,
            hypothesis_cards=hypothesis_cards,
            extra=args.extra or "",
        )
        write_file(outdir / role.filename, content)

    # Also emit a tiny README so el set sea autoexplicativo
    readme = f"""OUROBOROS PROMPTS v2.0
Project: {args.project}
Mode: {args.mode}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Files:
- 01_ingestor.txt     → etiqueta HECHOS/INFERENCIAS/SUPOSICIONES (no concluye)
- 02_compresor.txt    → estado mínimo + gates
- 03_redteam.txt      → ataques (no arreglos)
- 04_builder.txt      → reconstrucción endurecida + prereg/holdout + kill-switch
- 05_arbitro.txt      → PASS/FAIL por gate + causa
- 06_ledger.txt       → registro/changelog (no opina)

How to run (example):
  python ouroboros_v2.py --project "Riemann Mining" --mode adversarial \\
      --context-file bitacora.md --artifact ledger.json --artifact zeros.csv \\
      --prereg-file prereg.md --hypothesis "GUE invariance survives scaling" \\
      --outdir ./PROMPTS_OUROBOROS
"""
    write_file(outdir / "README.txt", readme)

    print(f"[OK] Prompts generados en: {outdir.resolve()}")


if __name__ == "__main__":
    # Fix UTF-8 on some consoles
    try:
        import sys
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    main()
