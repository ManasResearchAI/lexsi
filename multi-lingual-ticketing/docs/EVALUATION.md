# Evaluation contract

`configs/evaluation_contract.json` is frozen before training. Every arm uses
the same IDs, prompts, decoding (`do_sample=false`), schema, and fixture hash.
Raw responses and parsed predictions are saved together.

Fields are scored only where labels exist. Primary metrics are JSON parse and
schema-valid rates, intent accuracy, sentiment macro-F1, exact entity span F1,
and PII recall. Performance evidence includes latency and throughput. Results
must be reported per language as well as in aggregate.

The generation-confidence value is the mean selected-token probability. It is
an explicit escalation proxy, not an intent posterior; calibration must be
measured before production use. The `escalate` output is a serving-policy
decision derived from that threshold, not a model-supervised field. The
closed-model comparison is optional until
one provider, model revision, prompt, and price snapshot are frozen.

Checkpoint selection cannot use training loss alone. A checkpoint is eligible
only if JSON validity and PII gates pass, English retention remains within the
declared tolerance, and gross-stop repetition/empty-output checks pass.

## Validation-only checkpoint selection

Checkpoint selection must never inspect the test fixture. The frozen selection
fixture is:

- `data/processed/tickets/validation-subsample-v1.jsonl`
- 2,096 rows, seed `20261113`
- file SHA-256
  `c52ce135685221deee9d1b5a64fa36b23f072e88f1c4dc81cc04fdd049776c80`

For each of the clean-only and clean-plus-adversarial SFT arms, evaluate the
predeclared candidates `checkpoint-1000`, `checkpoint-2000`, and the
completed final adapter on this validation fixture. Select the candidate with
the highest macro intent accuracy among those passing every primary and
gross-stop gate. Save every validation prediction and metric artifact.

The empty-output rate counts responses empty after whitespace stripping. The
severe-repetition rate reuses the established generation diagnostic from the
preceding Tiny Aya work: `rep4 = 1 - unique whitespace-tokenized 4-grams / all
4-grams`, with a response severe when `rep4 > 0.3`. The immutable report is
`artifacts/evidence/validation-gross-stops/report.json`.

The parent validation split has no English rows. English retention is therefore
measured only on the separately frozen supplement:

- `data/processed/tickets/validation-english-supplement-v1.jsonl`
- 216 rows: 155 INJONGO and 61 templated-PII English rows
- file SHA-256
  `a7f4d5ce93badfe3eebc7058ca746df01dd339e0ae5539d9bd4a0d363372cb34`

These rows were selected deterministically from test subsample v1 before any
test evaluation. They are excluded from final test v2. Evaluate only this
supplement for the English-retention gate; do not repeat the main validation
fixture.

Only after both checkpoints are selected may the reporting fixture be opened:

- `data/processed/tickets/test-subsample-v2.jsonl`
- 3,642 rows, seed `20261113`; 216 English validation IDs excluded
- file SHA-256
  `e37ffb952329c64390b5205a514a12b5bbd49b2e678abc44293ac9eafaba61ac`

Run that fixture exactly once for the frozen base model, once for the selected
clean checkpoint, and once for the selected adversarial checkpoint. Use
`scripts/evaluate_model.py --fixture <path>`; `--limit` is prohibited for
this matched comparison. Any rerun requires a documented protocol exception
and must retain the original outputs.

## Red-team contract

The deterministic domain set uses real held-out carriers and reviewed English,
Yorùbá, Kiswahili, and code-mixed payloads at the start, middle, and end of a
ticket. A1–A4 are adversarial-SFT training families; A5–A7 remain held out.
Report attack success by family and language, clean accuracy retention, false
alarms, and cost inflation per 1,000 tickets. A model run is never replaced by
the regex guard result: they are separate defense layers and separate evidence.

The guard rejects invented keys and invalid domain/intent combinations,
normalizes common Unicode confusables, checks obfuscated phone numbers, and
owns the escalation field. Detected injections are contained locally so they
cannot force a costly cloud call. `data/fixtures/redteam_false_alarms.jsonl`
is the frozen benign lexical-overlap check.

