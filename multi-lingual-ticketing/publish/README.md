# Hugging Face publication staging — plan only

**No files have been uploaded.** Final staging occurs only after training,
validation-only checkpoint selection, one-shot test evaluation, speaker
review, and Om's approval.

MasakhaNER 2.0 is CC 4.0 Non-Commercial. Every derived adapter and mixed
dataset below is therefore research/non-commercial.

## Model collection: `multilingual-ticket-triage-models`

| Repository | Planned source | Size | Publish only |
|---|---|---:|---|
| `tiny-aya-ticket-triage-clean-diagnostic` | clean-final; failed 95% PII gate | 263,278,006 | adapter config/weights, chat template, tokenizer, diagnostic model card |
| `tiny-aya-ticket-triage-robust` | selected adversarial checkpoint-1000 | 263,279,437 | adapter config/weights, chat template, tokenizer, model card |
| `tiny-aya-global-ticket-triage-diagnostic` | Global 50-row adapter | 263,277,817 | same allowlist; diagnostic label |
| `tiny-aya-earth-ticket-triage-diagnostic` | Earth 50-row adapter | 263,277,814 | same allowlist; diagnostic label |

Allowed filenames are `adapter_config.json`,
`adapter_model.safetensors`, `chat_template.jinja`, tokenizer files, and
`README.md`. Exclude `optimizer.pt`, `scheduler.pt`,
`rng_state.pth`, `trainer_state.json`, `training_args.bin`, and event
logs.

## Dataset collection: `multilingual-ticket-triage-data`

| Repository | Planned contents | Current size | Licence |
|---|---|---:|---|
| `multilingual-ticket-triage-curated` | both CuratorKIT exports, manifests, checksums, provenance | 60,582,639 | mixed; research/non-commercial |
| `multilingual-ticket-triage-redteam` | A1–A7, combined train, matched clean, A4 fixture, manifest | 87,244,001 | derived/generated; research/non-commercial |
| `multilingual-ticket-triage-evaluation` | main validation, English supplement, preserved test v1, final test v2, manifests, evidence, predictions, AuditKIT reports, logs/traces | 242,193,418 | mixed; research/non-commercial |

Publish `payload_match_review.json`, not the superseded historical
`human_review.json` filename. Raw upstream downloads and unrestricted raw
tweet mirrors are excluded.

The detailed file/licence checklist is
[`submission/PUBLISHING_PLAN.md`](../submission/PUBLISHING_PLAN.md).
