# Reproducibility check

Run: 2026-11-15 16:24–16:36 IST  
Root commit cloned: `e120893d23db69917f0a35af8a0794a7f7448690`  
Temporary clone: `/tmp/lexsi-repro-20261115/lexsi`  
Environment: the pre-existing approved AlignTune Python environment; no
packages were installed and no environment was created.

## Outcome

| Check | Result | Evidence |
|---|---|---|
| Fresh local Git clone contains the submission project | **FAIL** | The cloned commit contains zero paths under `multi-lingual-ticketing/`; it also lacks the root README. A stranger cannot begin the documented procedure until the current working tree is committed by Om. |
| README environment creation/install commands | **NOT RUN — scoped limit** | The check was explicitly forbidden from installing packages or creating an environment. The approved existing environment was used instead. |
| Snapshot-overlay test suite | **PASS** | 24/24 tests passed. This is not promoted to a clean-clone pass. |
| Rebuild validation subsample v1 | **PASS** | SHA-256 matches the ledger. |
| Rebuild test subsample v1 | **PASS** | SHA-256 matches the ledger. |
| Rebuild English validation supplement | **PASS** | SHA-256 matches the ledger. |
| Rebuild leak-free test subsample v2 | **PASS** | SHA-256 matches the ledger. |
| Selected-adapter greedy evaluation, first 20 rows | **PASS** | 20/20 IDs, parsed predictions, raw responses, and output-token counts match exactly. |
| Clean SFT command, five steps | **PASS** | `checkpoint-5/trainer_state.json` records `global_step=5`, `max_steps=5`. |
| Adversarial SFT command, five steps | **PASS** | `checkpoint-5/trainer_state.json` records `global_step=5`, `max_steps=5`. |
| Red-team fixture rebuild | **PASS** | All three JSONL files and manifest match canonical SHA-256 values. |
| Guard evaluation rebuild | **PASS** | Report SHA-256 matches exactly. |

The strict end-to-end result is therefore **FAIL until the working tree is
committed**. The deterministic code/data/model checks all pass after a clearly
labelled snapshot overlay supplies the files and immutable inputs absent from
the commit.

## Clean-clone failure and controlled continuation

The strict commands were:

```bash
export REPRO=/tmp/lexsi-repro-20261115
git clone --no-local "$(git rev-parse --show-toplevel)" "$REPRO/lexsi"
git -C "$REPRO/lexsi" rev-parse HEAD
git -C "$REPRO/lexsi" ls-tree -r --name-only HEAD -- multi-lingual-ticketing
```

The last command returned no paths. To complete the requested component
checks without committing, publishing, or modifying source artifacts, the
current project source was copied into that clone as a **non-stranger snapshot
overlay**. Immutable parent ticket JSONL files, curated exports, the selected
adapter, and saved reference predictions were hard-linked into the clone under
documented temporary paths. All subsequent commands ran from inside the clone.

This overlay is a diagnostic fallback, not evidence that the Git clone is
self-contained.

## Fixture rebuild commands and hashes

```bash
cd "$REPRO/lexsi/multi-lingual-ticketing"
export PYTHON=/path/to/the/approved/aligntune_env/bin/python
export PYTHONPATH=src
mkdir -p repro_outputs/fixtures

$PYTHON scripts/build_eval_subsample.py \
  --input data/processed/tickets/validation.jsonl \
  --output repro_outputs/fixtures/validation-subsample-v1.jsonl
$PYTHON scripts/build_eval_subsample.py \
  --input data/processed/tickets/test.jsonl \
  --output repro_outputs/fixtures/test-subsample-v1.jsonl
$PYTHON scripts/split_english_validation.py \
  --input repro_outputs/fixtures/test-subsample-v1.jsonl \
  --validation-output repro_outputs/fixtures/validation-english-supplement-v1.jsonl \
  --test-output repro_outputs/fixtures/test-subsample-v2.jsonl
```

| Fixture | Rebuilt SHA-256 | Ledger SHA-256 | Result |
|---|---|---|---|
| `validation-subsample-v1.jsonl` | `c52ce135685221deee9d1b5a64fa36b23f072e88f1c4dc81cc04fdd049776c80` | same | PASS |
| `test-subsample-v1.jsonl` | `40001f0e264252c0595c63ee991d3a83d3758ed3d0810073dfecda224d50f7f9` | same | PASS |
| `validation-english-supplement-v1.jsonl` | `a7f4d5ce93badfe3eebc7058ca746df01dd339e0ae5539d9bd4a0d363372cb34` | same | PASS |
| `test-subsample-v2.jsonl` | `e37ffb952329c64390b5205a514a12b5bbd49b2e678abc44293ac9eafaba61ac` | same | PASS |

## Twenty-row greedy reproduction

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src $PYTHON scripts/evaluate_model.py \
  --model CohereLabs/tiny-aya-global \
  --revision af89d219b53ed9b13b8a4645f9c8028973510324 \
  --adapter repro_inputs/selected-adapter \
  --fixture repro_outputs/fixtures/test-subsample-v2.jsonl \
  --output repro_outputs/eval-selected-20 \
  --limit 20
```

The reproduction prediction file SHA-256 is
`5dca88f61fcb7eaad602264579ea90bc479aa350957f7405de9292757e0d4588`.
Every compared deterministic field matched. Latency and the floating-point
confidence proxy were deliberately excluded from exact comparison because
they are runtime/hardware measurements rather than decoded predictions.

An initial attempt invoked the approved environment through an additional
symlink and exposed an incompatible system package set. It failed before model
loading and produced no predictions. Direct invocation of the approved
interpreter passed; the README now recommends a direct `PYTHON` path rather
than an interpreter symlink.

## Five-step SFT command smokes

The two commands ran concurrently on separate GPUs:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src:../aligntune/src $PYTHON scripts/train_sft.py \
  --model CohereLabs/tiny-aya-global \
  --dataset data/processed/curatorkit-clean-full \
  --output repro_outputs/sft-clean-5 \
  --epochs 2 --gradient-accumulation-steps 1 --save-steps 5 --max-steps 5

CUDA_VISIBLE_DEVICES=1 PYTHONPATH=src:../aligntune/src $PYTHON scripts/train_sft.py \
  --model CohereLabs/tiny-aya-global \
  --dataset data/processed/curatorkit-adversarial-full \
  --output repro_outputs/sft-adversarial-5 \
  --epochs 2 --gradient-accumulation-steps 1 --save-steps 5 --max-steps 5
```

Both reached and saved step 5. AlignTune preprocesses and tokenizes the full
export before applying the five-step trainer limit, so the bounded smoke still
has roughly one minute of CPU preprocessing per arm.

## Red-team and guard reproduction

```bash
PYTHONPATH=src $PYTHON scripts/build_redteam_dataset.py \
  --tickets data/processed/tickets \
  --output repro_outputs/redteam
PYTHONPATH=src $PYTHON scripts/evaluate_guard.py \
  --attacks repro_outputs/redteam/test.jsonl \
  --false-alarms data/fixtures/redteam_false_alarms.jsonl \
  --output repro_outputs/redteam-guard-metrics.json
```

| Output | Rebuilt/canonical SHA-256 | Result |
|---|---|---|
| `train.jsonl` | `62a55cc0ce37f76078452ba95801955dbb33c01762a1b0cb881a108f0ce7d548` | PASS |
| `test.jsonl` | `6b391904a6851ec058268cb9355470df7dc46bf5cdad2af048018f237d49c49c` | PASS |
| `clean_plus_adversarial_train.jsonl` | `21ca143324777125311acb9d35d1b87f79be7f55beeb573b177969cb7f3e79f2` | PASS |
| `manifest.json` | `88ca8293cf72d53193db08c4eced6742f65855a70df67145a87f3ebe42808cf2` | PASS |
| Guard metrics | `b672d8f18c02652a66a4e22124466699021faa0b6a512da94a24cb752d9ee19e` | PASS |

## README gaps found and fixed in the main tree

- Added the required recursive-submodule clone step.
- Added the generated HF dataset/model artifact prerequisites; these are not
  present in Git by design.
- Added exact commands for rebuilding all four evaluation fixtures.
- Replaced stale text saying full SFT evaluation remained with final results.
- Added a bounded five-step SFT smoke procedure using fresh outputs.
- Replaced the selected-adapter placeholder with the staged package name.

One issue cannot be fixed without the forbidden commit operation: the current
root commit does not contain the project or public root README. Om must review
and commit the prepared root/project tree before a clean-clone rerun can pass.
