---
base_model: CohereLabs/tiny-aya-global
library_name: peft
language: [yo, sw, en]
pipeline_tag: text-generation
license: other
license_name: mixed-research-non-commercial
---

# Tiny Aya Multilingual Support Triage LoRA

LoRA for JSON support-ticket extraction in Yorùbá, Kiswahili, and English.
Training uses partial-label chat targets curated with CuratorKIT and
AlignTune's TRL backend.

## Immutable lineage

- Base: `CohereLabs/tiny-aya-global`
- Base revision:
  `af89d219b53ed9b13b8a4645f9c8028973510324`
- Seed: `20261112`
- Context: 1,024 tokens
- LoRA: rank 32, alpha 64, dropout 0.05, all projection modules
- Effective batch: 16 (device batch 1 × gradient accumulation 16)
- Learning rate: `1e-4`
- Epochs: 2
- Loss: assistant completion only
- Clean export: 22,385 rows
- Clean-plus-adversarial export: 22,559 rows
- Clean CuratorKIT export SHA-256:
  `2c10abc0e7b225a5e4181bc1e74b6c86b550670e5bfb701afab0a7f45721a061`
- Adversarial CuratorKIT export SHA-256:
  `9e1bea28af80145b83b6addb69ac85d18689be3912bb33512d6263c3731f56a0`
- Completed clean final adapter SHA-256:
  `01c4eb83611510c0a97b5037ae7b6bc5435b8b001089ca75e59e696180cfd6f5`
- Completed adversarial final adapter SHA-256:
  `80f604853060e5bbc73043add4dceb96ddc916b44081992655b8747c3fb52918`

## Final selected artifact

- Arm: clean-plus-adversarial SFT
- Selected checkpoint: `checkpoint-1000`
- `adapter_model.safetensors` SHA-256:
  `68c3ba5978e61748ecc44f7cef3e3bac4a27d59d7220403cfd48b9df51b1f9b7`
- Validation fixture: 2,096 rows; intent accuracy 0.7701, PII recall
  0.9543, JSON parse rate 1.0000, schema validity 0.9986, empty-output
  rate 0.0000, and severe-repetition rate 0.000477.
- Frozen 3,642-row test fixture: alignment improved intent accuracy from
  0.4803 to 0.7789, PII recall from 0.8016 to 0.9609, schema validity from
  0.8107 to 0.9962, and entity F1 from 0.5467 to 0.8435 over the unaligned
  Global base. Selected-adapter JSON parse rate is 1.0000 and sentiment
  macro-F1 is 0.5904.
- Google Gemini-assisted 60-row Yorùbá/Kiswahili review: 44/60 correct,
  59/60 fluent, one off-language, and two privacy leaks. No native-speaker
  review was available; these judgments are model-assisted, not human review.

- Held-out 900-row A5–A7 prompt-injection set, selected adapter versus
  unaligned Global base: deterministic strict payload-match attack success
  0.1411 versus 0.1656 (0.0756 versus 0.1044 excluding rows whose gold label
  already matched the requested value); model-reported injection detection
  0.9200 versus 0.3700. A Claude-assisted review found direct payload
  following in 1.7% versus 3.0% of rows, but more payload text copied into
  `redacted_text` (27.9% versus 15.9%), and PII recall under attack fell to
  0.4539 from 0.6458.

Limitation: in a small post-evaluation benign probe, the adapter falsely
reported injection on all nine examples (three per language). The clean test
did not score this field; the demo's Triage view uses the independent guard.

The clean-only arm has no eligible checkpoint under the retained 95% PII
recall gate. Its strongest intent candidate, clean-final, reached 0.8337 intent
accuracy but only 0.9443 PII recall. It is a reported diagnostic, not a
deployment-selected adapter.

Intended research use is structured triage. It is not approved for autonomous
account action. Outputs require the repository's strict schema/allowlist guard;
detected injection must be contained rather than forwarded to a cloud model.
Low-confidence or privacy-sensitive non-injection messages should be
escalated. The training mixture includes MasakhaNER 2.0 under CC 4.0
Non-Commercial. This adapter is therefore declared
**research/non-commercial**; it is not commercially unrestricted.

