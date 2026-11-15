# Data contract

All examples are native-language data. No source message is machine translated.

The canonical row stores a stable ID, source ID, language, official split,
original and normalized text, labelled fields, partial JSON target, chat
messages, licence, and source metadata. Targets contain only fields explicitly
supported by that source:

- INJONGO: language, domain, intent, mapped entities, redacted text.
- AfriSenti: language and sentiment.
- MasakhaNER 2.0: language, PER/ORG/LOC/DATE entities, and redacted text.
- deterministic templates: AMOUNT, ORDER_ID, and PHONE on INJONGO banking or
  utility examples, with seed `20261112`.

No source labels escalation. The serving layer derives `escalate` from the
calibrated confidence threshold; it is never invented as a supervised target.

Official validation/test splits are frozen before cleaning. Exact and near
deduplication only remove training rows. The full 2026-11-12 build produced
31,460 train, 5,364 validation, and 11,768 test rows after rejecting 948 train
rows matching held-out text and 130 exact duplicates. The held-out fixture hash
is recorded in `data/processed/tickets/manifest.json`.

MasakhaNER 2.0 is non-commercial. Do not represent the combined dataset or a
model trained on it as commercially unrestricted. AfriSenti tweet text may also
carry platform/redistribution considerations; review those before publishing a
derived public dataset.

