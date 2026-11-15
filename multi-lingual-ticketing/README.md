# Multilingual Support Triage & Structured Extraction

An evidence-first Track 1 + Track 2a project for structured customer-support extraction
in Yorùbá, Kiswahili, and English. It chains CuratorKIT → AlignTune → AuditKIT
around `CohereLabs/tiny-aya-global` and never trains on invented labels.

The canonical output is one JSON object containing language, one of five
domains, one of 40 INJONGO intents, sentiment, entities, redacted text, and an
escalation decision. Training rows are partial JSON: a field is present only
when its source actually labels it. Evaluation follows the same rule.

## What is implemented

- Native INJONGO, AfriSenti, and MasakhaNER 2.0 ingestion.
- Correct handling of INJONGO's misnamed Unicode-character offsets.
- Deterministic ₦/TSh amounts, order IDs, and phone templates.
- Frozen official held-out splits; train-only exact and near deduplication.
- Full and partial JSON-schema validation and stable prompts.
- CuratorKIT message export with provenance and checksums.
- AlignTune TRL LoRA training, immutable output guards, and a 50-row overfit path.
- Raw-preserving inference, field-aware metrics, escalation curves, AuditKIT
  reports, performance stats, evidence ledgers, and review artifacts.
- Gradio demo, robustness fixtures, submission abstract/article/checklist, and tests.
- Deterministic A1–A7 multilingual/code-mixed attacks, adversarial SFT export,
  a strict serving guard, AuditKIT generic probes, and an interactive attack lab.

The complete data build currently contains 31,460 train, 5,364 validation, and
11,768 test examples. Its held-out hash is in
`data/processed/tickets/manifest.json`. A 500-row CuratorKIT integration run
removed 85 near duplicates and exported 415 message rows with full provenance.

The 50-row Global/Earth adapter runs are diagnostics, not final model-quality
claims. The submission model is validation-selected adversarial
checkpoint-1000. On the one-shot 3,642-row frozen test it improves intent
accuracy from 0.4803 to 0.7789, PII recall from 0.8016 to 0.9609, schema
validity from 0.8107 to 0.9962, and entity F1 from 0.5467 to 0.8435 relative
to the unaligned Global base. No clean checkpoint passed the predeclared 95%
PII-recall gate, so the clean arm was not opened on the final test. The
900-row held-out A5–A7 aligned-model attack evaluation is reported with the
submission evidence.

## Reproduce

Use Python 3.12 and the exact package pins:

```bash
python3.12 -m venv .venv
export PYTHON=.venv/bin/python
$PYTHON -m pip install -r requirements-lock.txt
$PYTHON -m pip install -e .
export PYTHONPATH=src
```

Clone the root repository with its toolkit submodules before running the
commands below:

```bash
git clone --recurse-submodules https://github.com/ManasResearchAI/lexsi.git lexsi
cd lexsi/multi-lingual-ticketing
```

The public repository does not mirror raw upstream downloads or generated
model/data artifacts. Obtain the published HF dataset/model packages described
in `submission/PUBLISHING_PLAN.md`, place the dataset exports at their documented
`data/processed/` paths, and set the adapter path to the downloaded
`tiny-aya-ticket-triage-robust` package. The data build requires network access
to the cited upstream sources when those packages are not used.

A machine-specific interpreter may be supplied through the optional `PYTHON`
Make variable; no private absolute path is required. Invoke that interpreter
directly rather than through an additional symlink, because nested interpreter
symlinks can change environment/package resolution.

The immutable model revisions used were:

- `CohereLabs/tiny-aya-global@af89d219b53ed9b13b8a4645f9c8028973510324`
- `CohereLabs/tiny-aya-earth@0624fafbe200f930b89566fc4ec4da314ba48d89`

All model runs use seed `20261112`. Evaluation uses greedy decoding
(`do_sample=false`), `max_new_tokens=384`, and stops after one complete
top-level JSON object.

Rebuild the deterministic evaluation fixtures from the parent validation/test
JSONL files into a fresh directory:

```bash
mkdir -p /tmp/ticket-fixtures
$PYTHON scripts/build_eval_subsample.py \
  --input data/processed/tickets/validation.jsonl \
  --output /tmp/ticket-fixtures/validation-subsample-v1.jsonl
$PYTHON scripts/build_eval_subsample.py \
  --input data/processed/tickets/test.jsonl \
  --output /tmp/ticket-fixtures/test-subsample-v1.jsonl
$PYTHON scripts/split_english_validation.py \
  --input /tmp/ticket-fixtures/test-subsample-v1.jsonl \
  --validation-output /tmp/ticket-fixtures/validation-english-supplement-v1.jsonl \
  --test-output /tmp/ticket-fixtures/test-subsample-v2.jsonl
sha256sum /tmp/ticket-fixtures/*.jsonl
```

```bash

$PYTHON -m pytest -q
$PYTHON -m ticket_system.cli write-schema
$PYTHON -m ticket_system.cli build-data --with-hf
$PYTHON scripts/build_redteam_dataset.py
$PYTHON scripts/evaluate_guard.py \
  --output artifacts/evidence/redteam-guard-v2/metrics.json
PYTHONPATH=src:../CuratorKIT $PYTHON scripts/run_curatorkit.py \
  --max-samples 500 --output data/processed/curatorkit-smoke
```

With approved Tiny Aya access:

```bash
$PYTHON scripts/preflight_model.py --samples 50
$PYTHON scripts/evaluate_model.py \
  --output artifacts/evidence/base --limit 200
$PYTHON scripts/train_sft.py \
  --dataset data/processed/curatorkit-smoke-v2 \
  --output outputs/overfit-50-v2 --max-samples 50 --max-steps 100 --epochs 20 \
  --gradient-accumulation-steps 1
$PYTHON scripts/evaluate_model.py \
  --adapter outputs/overfit-50-v2 --output artifacts/evidence/overfit --limit 200
```

Only after the trusted-set run produces valid free generations should the
matched full SFT arms be launched. These are the exact initial commands used:

```bash
PYTHONPATH=src:../aligntune/src $PYTHON scripts/train_sft.py \
  --model CohereLabs/tiny-aya-global \
  --dataset data/processed/curatorkit-clean-full \
  --output outputs/sft-clean-full-20261113 \
  --epochs 2 --gradient-accumulation-steps 16 --save-steps 500

PYTHONPATH=src:../aligntune/src $PYTHON scripts/train_sft.py \
  --model CohereLabs/tiny-aya-global \
  --dataset data/processed/curatorkit-adversarial-full \
  --output outputs/sft-adversarial-full-20261113 \
  --epochs 2 --gradient-accumulation-steps 16 --save-steps 500
```

Both arms were recovered from their first durable checkpoint while requesting
a safer 100-step save cadence. The installed Trainer restored the original
500-step cadence from `trainer_state.json`; a subsequently added resume
callback makes future recoveries honor the requested 100-step value. The
adversarial arm used this exact recovery command; the clean arm used the
corresponding clean paths:

```bash
PYTHONPATH=src:../aligntune/src $PYTHON scripts/train_sft.py \
  --model CohereLabs/tiny-aya-global \
  --dataset data/processed/curatorkit-adversarial-full \
  --output outputs/sft-adversarial-full-20261113 \
  --epochs 2 --gradient-accumulation-steps 16 --save-steps 100 \
  --resume-from-checkpoint \
  outputs/sft-adversarial-full-20261113/checkpoint-500
```

For a bounded command/interface smoke test, append `--max-steps 5
--gradient-accumulation-steps 1` and use fresh output directories. Do not use
the production output names for this smoke test.

The current CuratorKIT MinHash implementation takes roughly 16 minutes for the
31k-row corpus on this CPU; the bounded smoke command validates the interface
quickly. Full runs use new output directories and refuse to overwrite results.

## Evaluate and audit

Each evaluation directory contains raw responses, parsed predictions, latency,
token counts, the exact fixture hash, and aggregate metrics:

```bash
$PYTHON scripts/auditkit_report.py artifacts/evidence/base/predictions.jsonl \
  --output artifacts/evidence/base-auditkit
$PYTHON scripts/build_escalation_curve.py artifacts/evidence/sft/predictions.jsonl \
  --output artifacts/evidence/sft/escalation.json
$PYTHON -m ticket_system.cli ledger \
  artifacts/evidence/base/metrics.json artifacts/evidence/sft/metrics.json \
  --output artifacts/evidence/metric-ledger.json
$PYTHON scripts/make_review_sheet.py artifacts/evidence/sft/predictions.jsonl \
  --output artifacts/evidence/speaker-review.csv
$PYTHON scripts/evaluate_model.py --fixture data/processed/redteam/test.jsonl \
  --adapter outputs/sft-adversarial --output artifacts/evidence/redteam-sft
$PYTHON scripts/evaluate_redteam_predictions.py \
  artifacts/evidence/redteam-sft/predictions.jsonl \
  --output artifacts/evidence/redteam-sft/attack_metrics.json
$PYTHON scripts/run_auditkit_redteam.py --adapter outputs/sft-adversarial \
  --output artifacts/evidence/auditkit-redteam-sft
```

Checkpoint selection uses only
`data/processed/tickets/validation-subsample-v1.jsonl`. After selection, run
the base and every eligible selected SFT checkpoint exactly once each on
`data/processed/tickets/test-subsample-v2.jsonl`:

```bash
$PYTHON scripts/evaluate_model.py \
  --revision af89d219b53ed9b13b8a4645f9c8028973510324 \
  --fixture data/processed/tickets/test-subsample-v2.jsonl \
  --output artifacts/evidence/base-test-subsample-v1

$PYTHON scripts/evaluate_model.py \
  --revision af89d219b53ed9b13b8a4645f9c8028973510324 \
  --fixture data/processed/tickets/test-subsample-v2.jsonl \
  --adapter <path-to-tiny-aya-ticket-triage-robust> \
  --output <immutable-output-directory>
```

Do not use `--limit` for checkpoint selection or the final matched comparison.

The frozen acceptance and gross-stop rules are in
`configs/evaluation_contract.json`. Generated-token probability is labelled as
a confidence proxy; it is not presented as calibrated intent confidence.

## Demo

```bash
HF_HUB_OFFLINE=1 PYTHONPATH=.:src MODEL_NAME=CohereLabs/tiny-aya-global \
MODEL_REVISION=af89d219b53ed9b13b8a4645f9c8028973510324 \
ADAPTER_PATH=outputs/sft-adversarial-full-20261113/checkpoint-1000 \
$PYTHON app/app.py
```

The model loads on the first request so the interface can start and be tested
without allocating weights at import time. The Space has separate **Triage**
and **Attack lab** views and exposes raw model output beside the guarded
decision. It is a research demonstration, not a persistent ticketing system.
For local use, `HF_HUB_OFFLINE=1` uses the cached pinned base revision and
avoids a remote lookup. Omit this setting on a fresh Space that must download
the base model.

## Data and licensing

INJONGO and AfriSenti are CC BY 4.0. The MasakhaNER 2.0 card states CC 4.0
Non-Commercial, so the combined corpus and models trained on it are not
commercially unrestricted. Tweet redistribution also deserves a separate
platform-terms review. See `docs/DATA.md` for the complete contract.

Code in this repository is Apache-2.0; upstream data and model licences remain
independent and controlling.

## Submission scope

Tracks 1 and 2a: Fine-tuning and Data Curation plus Red-teaming and Robustness
Evaluation. Problem statements include structured extraction, low-resource
multilingual and code-mixed safety, and adversarial evaluation sets. Public
publishing is deliberately left as an explicit human
step because it needs credentials, licence review, final repository names, a
registered teammate email, and authorization.

