# Submission checklist

- [x] Abstract under 500 words
- [x] Reproducible code, configs, tests, and evidence format
- [x] Track 1 + Track 2a and problem statement rationale
- [x] Deterministic A1–A7 multilingual/code-mixed attack set
- [x] Strict schema/allowlist guard and false-alarm fixture
- [x] AuditKIT RedTeamRunner integration
- [x] Rule-based payload-match ASR for 900-row Global/Earth comparison
- [x] Reconcile payload-match categories with stored `injection_detected` counts
- [x] Full CuratorKIT export of clean-plus-adversarial training mixture
- [x] Train clean-only and clean-plus-adversarial SFT arms
- [x] Clean-only versus clean+adversarial SFT matched validation evaluation
- [x] Matched clean base-model evaluation for clean-retention baseline
- [x] Model-level false-alarm evaluation on benign lexical-overlap fixtures
- [x] A4 escalation/call-inflation evaluation
- [ ] Convert A4 call inflation to dollars with frozen cloud-call price
- [x] AuditKIT generic probes on the selected final adapter
- [x] Global versus Earth attacked baseline evaluation
- [x] Gradio triage/attack-lab callback tests and local shell smoke test
- [x] HF Space packaging draft and evidence-aligned article revision
- [x] Root Git hygiene, public README, and historical-agent warning
- [x] Pinned Python 3.12 requirements lock and immutable base revisions
- [x] Frozen validation-selection and final-test subsamples with hashes
- [x] English validation supplement split out and removed from final test v2
- [x] Validation-only checkpoint-selection rule and one-shot test rule
- [x] No-upload HF model/dataset publication staging inventory
- [x] Retain the predeclared 95% PII-recall gate; record that no clean
  checkpoint is eligible (clean-final is closest at 94.43%)
- [x] Calculate the predeclared empty-output and severe-repetition gross stops
  from saved validation predictions; select adversarial checkpoint-1000
- [x] Complete the one-shot base and selected-adversarial
  evaluations on the frozen test subsample; do not run an ineligible clean
  checkpoint
- [x] Registered teammate email supplied for submission form
- [ ] Public, ungated Hugging Face model collection and every member repo
- [ ] Public, ungated Hugging Face dataset collection and every member repo
- [ ] Public GitHub repository
- [ ] Hugging Face article URL
- [ ] Hugging Face Space URL
- [x] Freeze immutable Tiny Aya Global and Earth base-model revisions
- [x] Base and selected-SFT matched generation metrics
- [x] Google Gemini-assisted 60-row Yorùbá/Kiswahili review, explicitly
  labelled as non-human; native-speaker review unavailable
- [ ] Optional closed-API baseline with frozen price snapshot

Publishing is intentionally not automated: it requires credentials, licence
review, repository names, a registered email, and explicit authorization.

