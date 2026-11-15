---
language: [yo, sw, en]
license: other
license_name: mixed-research-non-commercial
task_categories: [text-classification, token-classification, text-generation]
pretty_name: Multilingual Support Triage
---

# Multilingual Support Triage

Native Yorùbá, Kiswahili, and English examples mapped to partial structured
support-ticket JSON. Sources: INJONGO (CC BY 4.0), AfriSenti (CC BY 4.0), and
MasakhaNER 2.0 (CC 4.0 Non-Commercial), plus deterministic PII templates.

Each row contains stable/source IDs, language, official split, text, labelled
fields, a partial target, chat messages, source licence, and metadata. A target
contains only fields labelled by its source. Official held-out splits were
frozen before train-only filtering and deduplication.

## Counts and immutable fixtures

- Source build: 31,460 train / 5,364 validation / 11,768 test rows
- Clean CuratorKIT SFT export: 22,385 rows
- Clean-plus-adversarial CuratorKIT SFT export: 22,559 rows
- Red-team data: 1,200 A1–A4 training rows / 900 A5–A7 held-out rows
- Validation selection subsample: 2,096 rows,
  SHA-256 `c52ce135685221deee9d1b5a64fa36b23f072e88f1c4dc81cc04fdd049776c80`
- English validation supplement: 216 rows,
  SHA-256 `a7f4d5ce93badfe3eebc7058ca746df01dd339e0ae5539d9bd4a0d363372cb34`
- Final test subsample v2: 3,642 rows,
  SHA-256 `e37ffb952329c64390b5205a514a12b5bbd49b2e678abc44293ac9eafaba61ac`
- Full test JSONL file SHA-256:
  `c1861c9817a9fca2f756798c562f6b73374c8597f701a1da4e4079e736219890`
- Validation-plus-test canonical-row digest:
  `a603a3fa23363857f0471ee9d6337a0ba5a56ad7d415701dc2558894ceb354bc`

MasakhaNER 2.0 is CC 4.0 Non-Commercial. The combined dataset is therefore
declared **research/non-commercial** and is not commercially unrestricted.
Review tweet redistribution/platform terms before public mirroring. Full
provenance, counts, checksums, and source citations must accompany the data.

The red-team companion set contains reviewed multilingual and code-mixed A1–A7
payloads placed into real carriers. A1–A4 are training-only adversarial SFT
rows; A5–A7 are held out. Adversarial targets retain carrier labels and add
`injection_detected: true`. Do not merge the held-out families into training.

## Final evaluation evidence

The base model and the sole validation-eligible adapter were each evaluated
exactly once on final test subsample v2. The clean-only arm was not opened on
the test fixture because no clean checkpoint met the predeclared 95% PII-recall
gate.

| Metric | Base | Selected adversarial checkpoint-1000 |
|---|---:|---:|
| JSON parse rate | 0.9995 | 1.0000 |
| Schema validity | 0.8107 | 0.9962 |
| Intent accuracy | 0.4803 | 0.7789 |
| Sentiment macro-F1 | 0.4667 | 0.5904 |
| Entity F1 | 0.5467 | 0.8435 |
| PII recall | 0.8016 | 0.9609 |

Base metric SHA-256:
`57cf0e1d2819529614a458d2cd20058ded03190bec093abf7d586d5827e88312`.
Selected-adapter metric SHA-256:
`9204e7171e0b29181c7e09ac330d0d8a1295721962c2514f6d1849f1678a1d5d`.
The deterministic 60-row Yorùbá/Kiswahili packet was reviewed with Google
Gemini because no native speaker was available. It marked 44/60 correct,
59/60 fluent, one off-language, and two privacy leaks. The CSV and additional
notes are model-assisted evidence, not human or native-speaker validation.

The selected adapter's later nine-row benign diagnostic flagged all nine
messages as injections (three per language). The frozen clean test did not
request that field, and this small probe cannot estimate a general false-positive rate.

