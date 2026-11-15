# Abstract

Customer-support automation often excludes African languages or sends every
message to a costly hosted model. We build a small, auditable structured
extractor for native Yorùbá, Kiswahili, and English messages using Tiny Aya
Global. A single JSON interface predicts language, support domain and intent,
sentiment, entities, redacted text, and escalation, while partial-label
training ensures that no dataset label is invented.

Our curation pipeline combines native-speaker INJONGO intent/slot data,
AfriSenti, and MasakhaNER 2.0 with deterministic amount, order-ID, and phone
templates. Official validation and test splits are frozen before train-only
cleaning and deduplication. CuratorKIT produces trainer-ready chat data and
provenance; AlignTune trains a TRL LoRA on Tiny Aya; AuditKIT records matched
before/after evidence, latency, throughput, and uncertainty-based escalation.
Evaluation is field-aware and emphasizes JSON validity, per-language intent
accuracy, sentiment macro-F1, entity span F1, and PII recall because a missed
identifier is a privacy failure.

Every ticket is also treated as adversarial input. A deterministic attack set
crosses routing, schema, redaction, escalation, threat masking, code-mixed
injection, and long-context attacks with English, Yorùbá, and Kiswahili. A1–A4
augment SFT while A5–A7 remain held out. A strict allowlist guard owns the
escalation decision and contains detected injection before cloud forwarding;
AuditKIT adds generic prompt-injection, encoding, and jailbreak probes.

On 900 held-out A5–A7 attacks, a deterministic strict payload-match grader,
which counts an attack as successful only when a field equals the value the
malicious payload requested, finds attack success rates of 16.6% for Tiny Aya
Global, 16.6% for Tiny Aya Earth, and 14.1% for the adversarially aligned
checkpoint. Excluding rows where the gold label already equals the requested
value, the rates are 10.4%, 10.4%, and 7.6%. Alignment raises model-reported
injection detection from 37.0% and 33.1% to 92.0%. A Claude-assisted review of
all 2,700 responses finds direct follows in 3.0%, 3.1%, and 1.7% of rows
(only on A6 explicit overrides), but more payload text copied into redacted
output after alignment (27.9% vs 15.9% and 12.8%). No named human reviewer
labelled these records; raw outputs and rule definitions are preserved.

Detection has a serious limitation: the selected adapter flagged all nine
benign checks (three per language) as injections. This small probe is not a
population estimate; the demo's Triage view uses an independent guard instead.

Adversarial SFT produces the sole checkpoint meeting our predeclared 95% PII-
recall gate. On the one-shot 3,642-row frozen test, the selected checkpoint
improves intent accuracy from 48.0% to 77.9%, PII recall from 80.2% to 96.1%,
schema validity from 81.1% to 99.6%, and entity F1 from 54.7% to 84.3% over the
unaligned Global base. It passes 52 of 63 AuditKIT generic probe/detector
checks. Deterministic guard results are reported separately from model
behavior.

Fixture hashes, generations, and model lineage make the results auditable.
Google Gemini reviewed 60 Yorùbá/Kiswahili responses because no native speaker
was available; this is model-assisted, not human validation.

