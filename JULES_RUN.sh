#!/usr/bin/env bash
# ============================================================
# JULES_RUN.sh — Latido Judicial Pipeline (4-step, auto-push)
# Repo: Gahenax/Riemman-Zero
# Execute: bash JULES_RUN.sh
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

OUT_DIR="run_latido/reports/jules"
CFG="run_latido/configs/latido_certified_2000.json"
MERGED="run_latido/merged_results_5000plus.jsonl"
SEED=1337
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "============================================================"
echo "  LATIDO JUDICIAL PIPELINE — $TIMESTAMP"
echo "============================================================"

# ---- PREFLIGHT ----
echo ""
echo "[PREFLIGHT] Checking environment..."
python3 -V || python -V
ls -lah "$MERGED" "$CFG" scripts/calibrate_rtilde_target.py
mkdir -p "$OUT_DIR"
echo "[PREFLIGHT] OK"

# ============================================================
# STEP 1 — Calibrate GUE baseline
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 1/4 — Calibrate GUE baseline (nmat, edge_trim)"
echo "============================================================"

python3 scripts/calibrate_rtilde_target.py \
  --target 0.610 \
  --base-n 2000 \
  --sims 120 \
  --seed $SEED \
  --config "$CFG" 2>&1 | tee "$OUT_DIR/step1_calibrate.log"

STEP1_EXIT=${PIPESTATUS[0]}
if [ "$STEP1_EXIT" -ne 0 ]; then
  echo "[FATAL] Step 1 failed with exit code $STEP1_EXIT. STOPPING."
  exit 1
fi

# Capture calibration artifact
python3 -c "
import json, time
cfg = json.load(open('$CFG', 'r', encoding='utf-8'))
payload = {
    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    'step': 'calibration',
    'config_path': '$CFG',
    'nulls': cfg.get('nulls', {}),
    'note': 'GUE baseline locked by calibrate_rtilde_target.py'
}
out = '$OUT_DIR/step1_calibration_result.json'
json.dump(payload, open(out, 'w', encoding='utf-8'), indent=2, sort_keys=True)
print(f'[STEP 1] Calibration artifact: {out}')
print(f'[STEP 1] nulls = {payload[\"nulls\"]}')
"

echo "[STEP 1] DONE"

# ============================================================
# STEP 2 — Certified Replay FULL
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 2/4 — Certified Replay FULL (300 GUE + 800 shuffle)"
echo "============================================================"

# Enable full mode in config
python3 -c "
import json
with open('$CFG', 'r') as f:
    cfg = json.load(f)
cfg.setdefault('policy', {})['allow_full_locally'] = True
cfg.setdefault('nulls', {})['gue_sims'] = 300
cfg['nulls']['shuffle_sims'] = 800
with open('$CFG', 'w') as f:
    json.dump(cfg, f, indent=2)
print('[STEP 2] Config updated: GUE=300, shuffle=800, full=True')
"

python3 scripts/latido_certified_plugin.py \
  --certified-config "$CFG" \
  --profile full \
  --seed $SEED 2>&1 | tee "$OUT_DIR/step2_certified_replay_full.log"

STEP2_EXIT=${PIPESTATUS[0]}
if [ "$STEP2_EXIT" -ne 0 ]; then
  echo "[FATAL] Step 2 failed with exit code $STEP2_EXIT. STOPPING."
  exit 2
fi

# Copy replay report to jules dir
REPLAY_REPORT=$(find run_latido/reports -name "*certified_replay_full*" -newer "$OUT_DIR/step1_calibrate.log" 2>/dev/null | head -1)
if [ -n "$REPLAY_REPORT" ]; then
  cp "$REPLAY_REPORT" "$OUT_DIR/step2_certified_replay_full.json"
  echo "[STEP 2] Report copied to $OUT_DIR/step2_certified_replay_full.json"
fi

echo "[STEP 2] DONE"

# ============================================================
# STEP 3 — Null Factory standalone
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 3/4 — Null Factory standalone (cross-check)"
echo "============================================================"

python3 scripts/latido_null_factory.py \
  --input "$MERGED" \
  --field T --mode zeros \
  --w 80 --L 1 5 10 \
  --gue_sims 300 \
  --shuffle_sims 800 \
  --bootstrap_sims 300 \
  --blocks 20 40 2>&1 | tee "$OUT_DIR/step3_null_factory.log"

STEP3_EXIT=${PIPESTATUS[0]}
if [ "$STEP3_EXIT" -ne 0 ]; then
  echo "[WARNING] Step 3 failed with exit code $STEP3_EXIT. Continuing to report."
fi

echo "[STEP 3] DONE"

# ============================================================
# STEP 4 — GUE^3 TwoNN k=5
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 4/4 — GUE^3 TwoNN k=5 (characterization)"
echo "============================================================"

python3 scripts/gue3_probe.py \
  --input "$MERGED" \
  --format jsonl \
  --t-key T \
  --tmin 5000 \
  --k 5 \
  --stride 2 \
  --unfold median \
  --null-iters 200 \
  --alpha 0.05 \
  --twonn-cap 2000 2>&1 | tee "$OUT_DIR/step4_gue3_twonn_k5.log"

STEP4_EXIT=${PIPESTATUS[0]}
if [ "$STEP4_EXIT" -ne 0 ]; then
  echo "[WARNING] Step 4 failed with exit code $STEP4_EXIT."
fi

echo "[STEP 4] DONE"

# ============================================================
# FINAL — Generate summary and push
# ============================================================
echo ""
echo "============================================================"
echo "  FINAL — Summary + Git Push"
echo "============================================================"

python3 -c "
import json, time, os, glob

summary = {
    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    'pipeline': 'Latido Judicial 4-Step',
    'steps': {}
}

logs = glob.glob('$OUT_DIR/step*.log')
for log in sorted(logs):
    step = os.path.basename(log).split('_')[0]
    with open(log, 'r') as f:
        lines = f.readlines()
    summary['steps'][step] = {
        'log': log,
        'lines': len(lines),
        'last_10': [l.strip() for l in lines[-10:]]
    }

# Check for result files
for f in glob.glob('$OUT_DIR/*.json'):
    step = os.path.basename(f).split('_')[0]
    if step not in summary['steps']:
        summary['steps'][step] = {}
    summary['steps'][step]['result_file'] = f

out = '$OUT_DIR/PIPELINE_SUMMARY.json'
json.dump(summary, open(out, 'w'), indent=2, sort_keys=True)
print(f'[FINAL] Pipeline summary: {out}')
print(f'[FINAL] Steps completed: {len(summary[\"steps\"])}')
"

# Git: stage, commit, push
echo "[GIT] Staging results..."
git add -A
git status --short

echo "[GIT] Committing..."
git commit -m "results: Latido judicial pipeline complete — calibration + replay FULL + null factory + TwoNN ($TIMESTAMP)" || true

echo "[GIT] Pushing to origin/main..."
git push origin HEAD:main

echo ""
echo "============================================================"
echo "  PIPELINE COMPLETE — $TIMESTAMP"
echo "  Results in: $OUT_DIR/"
echo "============================================================"
