---
title: Multilingual Support Triage
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.31.0
app_file: app.py
pinned: false
license: other
python_version: "3.12"
suggested_hardware: t4-small
startup_duration_timeout: 1h
fullWidth: true
short_description: Guarded triage for Yorùbá, Kiswahili, and English
models:
  - CohereLabs/tiny-aya-global
  - tiny-aya-ticket-triage-robust
---

# Multilingual Support Triage

Interactive research demo for guarded support-ticket extraction in Yorùbá,
Kiswahili, and English. The **Triage** view exposes structured output and
serving evidence. The **Attack lab** compares the raw model response with the
local containment decision.

The package pins:

- Base: `CohereLabs/tiny-aya-global`
- Base revision: `af89d219b53ed9b13b8a4645f9c8028973510324`
- Adapter package: `tiny-aya-ticket-triage-robust`
- Selected checkpoint: `checkpoint-1000`
- Adapter SHA-256:
  `68c3ba5978e61748ecc44f7cef3e3bac4a27d59d7220403cfd48b9df51b1f9b7`

Set `ADAPTER_PATH` to the final public, ungated repository ID for that exact
staged adapter after publication approval. `MODEL_NAME`, `MODEL_REVISION`, and
`MODEL_LABEL` may be set explicitly, but must retain the values above for the
submission Space.

Measured on the one-shot 3,642-row frozen test, the selected aligned adapter
improves intent accuracy from 48.03% to 77.89%, PII recall from 80.16% to
96.09%, schema validity from 81.07% to 99.62%, and entity F1 from 54.67% to
84.35% over the unaligned Global base. It also passed 52 of 63 AuditKIT
generic probe/detector checks. On the 900-row A5–A7 fixture, strict payload-match
ASR was 14.11% for the aligned adapter versus 16.56% for the Global base.
The adapter also falsely flagged all nine benign diagnostic messages (three per
language) as injections. Triage uses the independent guard's decision; Attack
Lab retains the model flag for diagnosis. Nine examples do not establish a
population false-positive rate.

Staged evidence:

- [Selected-adapter final metrics](evidence/test-v2-adversarial-1000.metrics.json)
- [Base final metrics](evidence/test-v2-base.metrics.json)
- [AuditKIT generic report](evidence/auditkit-redteam-adversarial-1000.json)
- [Real callback smoke report](evidence/gradio-selected-adversarial-1000-smoke.json)
- [Evaluation contract](evidence/evaluation_contract.json)
- [Gemini-assisted review CSV](evidence/gemini-review.csv)
- [Gemini-assisted review notes](evidence/additional_review_notes.md)

This demo does not create tickets or take account actions. Model output remains
subject to schema validation, privacy review, and human oversight.

No native speaker was available. Google Gemini reviewed a deterministic
60-row Yorùbá/Kiswahili sample and marked 44/60 correct, 59/60 fluent, one
off-language, and two privacy leaks. This is disclosed as model-assisted
review, not human or native-speaker validation.

The selected adapter was trained on a mixed-source corpus that includes
MasakhaNER 2.0 under CC 4.0 Non-Commercial. The Space and adapter are therefore
declared **research/non-commercial**; the Apache-2.0 code licence does not
override upstream data restrictions.
