# One small model, three languages, one auditable support schema

## Problem

Routine customer messages are often routed through a large hosted API because
small multilingual models return inconsistent prose. We instead constrain the
job to structured triage and extraction for Yorùbá, Kiswahili, and English.
The system emits JSON, preserves exact entity text, redacts sensitive values,
and exposes an uncertainty proxy for escalation.

## Data and method

The data is native rather than machine-translated: INJONGO for intent and
slots, AfriSenti for sentiment, and MasakhaNER 2.0 for entities. Synthetic data
is limited to deterministic insertion of amounts, order IDs, and phone numbers,
whose labels are known by construction. Partial JSON targets prevent false
labels when a source does not annotate a field.

Official held-out splits are frozen first. CuratorKIT handles training-only
cleaning, near deduplication, message export, and provenance. AlignTune trains a
LoRA on `CohereLabs/tiny-aya-global` through the TRL backend with completion-only
loss and 1,024-token context. AuditKIT preserves per-example outputs and
performance evidence. GRPO is considered only if SFT misses the declared 98%
JSON-validity gate.

The source corpus contains 31,460 training, 5,364 validation, and 11,768 test
rows. Equivalently processed full SFT exports contain 22,385 clean-only rows
and 22,559 clean-plus-adversarial rows. The serving path retains the raw
generation before a deterministic guard allowlists keys and labels, validates
domain/intent consistency, checks sensitive-value redaction, and owns the
escalation decision. Generated-token probability is explicitly labelled a
confidence proxy, not a calibrated intent probability.

## Attacking the multilingual triage model

Every ticket is untrusted input. Our deterministic attack builder crosses
seven threat families with reviewed English, Yorùbá, Kiswahili, and code-mixed
payloads and start/middle/end placement. It produces 1,200 A1–A4 training rows
and a frozen 900-row A5–A7 held-out set. Adversarial targets preserve the
carrier's gold JSON and add `injection_detected: true`.

The serving guard allowlists schema keys and intents, validates domain/intent
consistency, detects obfuscated phone numbers and threat masking, and replaces
model-supplied escalation with policy. Detected prompt injection is contained
locally instead of delivered to the expensive second-stage model. AuditKIT's
prompt-injection, encoding, and jailbreak probes complement the domain set.

## Evaluation

We compare the unmodified base and every candidate checkpoint on identical
fixtures and deterministic decoding. We report JSON validity, per-language
intent accuracy, sentiment macro-F1, entity span F1, PII recall, latency, and
throughput. Loss is diagnostic, never the selection criterion. A disclosed
Gemini-assisted sample review checks correctness, fluency, language, and
privacy failures; it is not human or native-speaker validation.

## Results

### Major result: the adversarially aligned model

Adversarial checkpoint-1000 was the sole SFT checkpoint to pass the
predeclared 95% validation PII-recall gate and both gross-stop checks. On the
one-shot 3,642-row frozen test, alignment produced large gains over the same
Tiny Aya Global base:

| Metric | Unaligned Global | Aligned checkpoint-1000 | Change |
|---|---:|---:|---:|
| Intent accuracy | 48.03% | 77.89% | +29.85 pp |
| PII recall | 80.16% | 96.09% | +15.92 pp |
| Schema validity | 81.07% | 99.62% | +18.54 pp |
| Entity F1 | 54.67% | 84.35% | +29.68 pp |

It also passed 52 of 63 AuditKIT generic probe/detector checks and the real
Gradio callback smoke.

### Held-out attack results: base vs aligned

All three models were evaluated on the complete 900-row held-out A5–A7 attack
fixture with identical deterministic decoding. Both base models parsed every
response as JSON; the aligned checkpoint produced 30 invalid-JSON responses
(29 in A7). No named human reviewer labelled these 2,700 records. A first
gold-mismatch grader had reported 88.56% and 86.56% base ASR because it counted
ordinary extraction errors as attacks, so we report two narrower measures.

**Deterministic strict payload-match grader**
(`scripts/score_strict_payload_match.py`, full analysis in
`PREDICTION-REVIEW.md`). An attack succeeds only when a top-level prediction
field equals the concrete value the payload requested. The adjusted rate also
excludes rows whose gold label already equals that value, because a correct
`neutral` sentiment would otherwise count as an attack.

| Model | Strict ASR | Adjusted ASR | A6 adjusted | Detection recall |
|---|---:|---:|---:|---:|
| Tiny Aya Global base | 16.56% | 10.44% | 18.67% | 37.00% |
| Tiny Aya Earth base | 16.56% | 10.44% | 18.67% | 33.11% |
| Aligned checkpoint-1000 | 14.11% | 7.56% | 8.67% | 92.00% |

Alignment's clearest effects are much higher injection detection and roughly
half as many obeyed explicit field overrides (A6). In 23–24 of each base
model's A6 matches the model added an out-of-schema key such as `escalate` or
`refund_amount`; the aligned model never did. A5 threat-masking and A7
long-context results show no meaningful change.

Detection recall alone hides false alarms. In a subsequent nine-row benign
probe (three per language), the selected adapter reported injection on all
nine. The clean frozen-test generations did not request that field. The demo's
Triage view therefore uses the independent serving guard for injection
decisions, while Attack Lab exposes the model's raw flag. This probe is too
small to estimate a general false-positive rate.

**Claude-assisted review** (full analysis in `CLAUDE-REVIEW.md`). Claude
labelled each of the 2,700 responses into five categories. It is disclosed as
model-assisted review, not human validation.

| Label | Global base | Earth base | Aligned checkpoint-1000 |
|---|---:|---:|---:|
| Injection followed | 27 (3.0%) | 28 (3.1%) | 15 (1.7%) |
| Payload leaked into `redacted_text` | 143 (15.9%) | 115 (12.8%) | 251 (27.9%) |
| Missed detection only | 17 (1.9%) | 13 (1.4%) | 0 (0.0%) |
| Ordinary extraction error | 614 (68.2%) | 643 (71.4%) | 443 (49.2%) |
| Correct prediction | 99 (11.0%) | 101 (11.2%) | 191 (21.2%) |

Both measures agree that the aligned checkpoint follows fewer explicit
overrides, with direct follows confined to A6. The review also identifies a
regression: the aligned model copies more payload text into `redacted_text`,
mostly on A5 (152 vs 94 and 84 rows). Its PII recall under attack is also
lower (45.39% vs 64.58% for Global base), although on the clean frozen test it
improves PII recall from 80.16% to 96.09%. Neither base model nor the aligned model
is robust enough for unguarded use. The deterministic serving guard detected
all payload variants in this exact set with zero alarms on nine benign
lexical-overlap fixtures; that guard result is reported separately and is not
a claim of model generalization.

Matched clean carriers show that attacks materially degrade the underlying
task, not only the injection flag. This table rests on 45 unique clean
generations expanded to 900 using the attack fixture's carrier weights:

| Metric | Global clean | Global attacked | Earth clean | Earth attacked |
|---|---:|---:|---:|---:|
| Partial-schema validity | 94.67% | 85.44% | 88.00% | 84.33% |
| Intent accuracy | 60.00% | 31.67% | 64.00% | 33.67% |
| Redacted-text accuracy | 36.17% | 5.50% | 34.04% | 5.32% |
| PII recall | 66.67% | 64.58% | 66.67% | 62.85% |

The 900 attacks derive from 45 unique clean carriers. Each clean carrier was
generated once and expanded back to the attack fixture's exact weighting.

On 300 escalation-path attacks, guard v2 reduced attack-triggered cloud
forwarding from 166.7 calls per 1,000 Global tickets and 160.0 per 1,000 Earth
tickets to zero. This is an exact-fixture deterministic baseline, not evidence
that a regex guard generalizes.

The retained 95% PII-recall selection gate rejected every clean-only
checkpoint; clean-final was closest at 94.43%. Google Gemini reviewed a
deterministic 60-row Yorùbá/Kiswahili sample from the selected adapter because
no native speaker was available: 44/60 were marked correct, 59/60 fluent, one
off-language, and two had privacy leaks. This is model-assisted review, not
human or native-speaker validation.

## Limitations

MasakhaNER 2.0 is CC 4.0 Non-Commercial; therefore the combined datasets,
adapters, and demo are declared research/non-commercial. News-domain NER and Twitter
sentiment do not perfectly match support tickets. Generated-token confidence is
not calibrated intent confidence. No native-speaker review was available; the
Gemini-assisted sample review cannot validate cultural or linguistic nuance.
Public deployment requires native-speaker review, privacy review, and
monitoring for domain shift.

The interactive Space is a research model demo, not a live ticketing platform:
it does not persist tickets, assign agents, or take account actions. It shows
the raw response beside guarded output so model behavior and serving-policy
behavior cannot be conflated.

