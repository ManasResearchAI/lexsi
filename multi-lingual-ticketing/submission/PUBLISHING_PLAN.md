# Publication staging plan — no upload authorized

Nothing in this plan may be uploaded until both SFT arms, validation-only
checkpoint selection, one-shot test evaluation, the disclosed Gemini-assisted
sample review, and Om's final review are complete.

All repositories below must be public and ungated only after that approval.
MasakhaNER 2.0 is CC 4.0 Non-Commercial, so every derived dataset and adapter
is declared **research/non-commercial**.

## Hugging Face model collection

Collection: `multilingual-ticket-triage-models`

| Repository | Source | Current staged size | Licence/status |
|---|---|---:|---|
| `tiny-aya-ticket-triage-clean-diagnostic` | clean-final; failed the 95% PII gate; adapter SHA `01c4eb83…` | 263,277,984 | mixed; research/non-commercial; diagnostic/ineligible |
| `tiny-aya-ticket-triage-robust` | selected adversarial checkpoint-1000; adapter SHA `68c3ba59…` | 263,279,415 | mixed; research/non-commercial; selected |
| `tiny-aya-global-ticket-triage-diagnostic` | Global 50-row diagnostic; adapter SHA `e6e642ac…` | 263,277,795 | mixed; research/non-commercial; diagnostic only |
| `tiny-aya-earth-ticket-triage-diagnostic` | Earth 50-row diagnostic; adapter SHA `9dac3104…` | 263,277,792 | mixed; research/non-commercial; diagnostic only |

The upstream bases are referenced, not republished:

- `CohereLabs/tiny-aya-global@af89d219b53ed9b13b8a4645f9c8028973510324`
- `CohereLabs/tiny-aya-earth@0624fafbe200f930b89566fc4ec4da314ba48d89`

### Strict model-repository allowlist

Each repository contains only:

- `adapter_config.json`
- `adapter_model.safetensors`
- `chat_template.jinja`
- tokenizer files (`tokenizer.json`, `tokenizer_config.json`, and any
  selected-checkpoint special-token files)
- `README.md` containing the completed model card

Never upload `optimizer.pt`, `scheduler.pt`, `rng_state.pth`,
`trainer_state.json`, `training_args.bin`, TensorBoard events, or whole
checkpoint directories to a model repository. Training state belongs in the
evidence dataset repository.

The completion-loss smoke adapter is excluded because it is a pipeline
diagnostic, not a reported submission model.

## Hugging Face dataset collection

Collection: `multilingual-ticket-triage-data`

| Repository | Included local material | Current bytes | Licence/status |
|---|---|---:|---|
| `multilingual-ticket-triage-curated` | both CuratorKIT exports, manifests, checksums, provenance, cards | 60,582,631 | mixed CC BY 4.0 / generated / CC 4.0 NC; research/non-commercial |
| `multilingual-ticket-triage-redteam` | A1–A7 fixtures, combined training mixture, matched clean fixture, A4 cost fixture, manifest | 87,244,000 | derived carriers plus generated payloads; conservatively research/non-commercial |
| `multilingual-ticket-triage-evaluation` | validation/test subsamples and manifests, evidence, training/evaluation traces | 242,193,410 | mixed evidence; fixtures include CC 4.0 NC rows; research/non-commercial |

Exact per-file sizes and SHA-256 values are stored outside the upload payloads
under `publish/manifests/`. This keeps every model repository limited to its
six allowlisted files.

The evaluation repository must include:

- `validation-subsample-v1.jsonl` and its manifest
- `validation-english-supplement-v1.jsonl` and its manifest
- preserved pre-split `test-subsample-v1.jsonl` plus the leak-free final
  `test-subsample-v2.jsonl` and both manifests
- immutable base/clean/adversarial predictions and metrics
- AuditKIT reports and red-team comparison artifacts
- payload-match rule artifact, Gemini-reviewed sample CSV, and review notes
- aligned checkpoint-1000 red-team predictions (merged plus both source
  shards), strict payload-match grader outputs for all three models, the
  review-export files, and `reviews/` (PREDICTION-REVIEW, CLAUDE-REVIEW and
  its raw reviewer output)
- CuratorKIT/AlignTune/AuditKIT logs, TensorBoard events, trainer states,
  training arguments, and provenance files
- a checksum inventory and licence/source table

Exclude the superseded historical filename `human_review.json`; publish the
self-contained `payload_match_review.json` artifact instead.

Raw upstream downloads are not mirrored. Tweet redistribution remains subject
to platform terms; publish only the reviewed processed form or permitted IDs.

## Other public repositories

- GitHub: `multilingual-ticket-triage` (this root repository with toolkit
  submodules and generated/private material excluded)
- Space: `multilingual-ticket-triage-demo` — 148,592 staged bytes; manifest
  SHA-256 `f8f40233155a37e46aa25d2502a900ecdd93279d5810cb1f62e9e4abe567aa07`
- Article: **Auditable Multilingual Ticket Triage with Tiny Aya**

## Final staging checks

1. Verify selected checkpoint, adapter SHA-256, validation/test metrics, and
   Gemini-review limitation in every staged card.
2. Recompute staged sizes and SHA-256 inventories.
3. Verify no model repo contains optimizer, scheduler, RNG, or trainer state.
4. Verify every dataset/model repo declares MasakhaNER 2.0 CC 4.0
   Non-Commercial and research/non-commercial use.
5. Obtain Om's explicit final approval before any upload.
