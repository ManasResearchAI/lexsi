# HISTORICAL — INACTIVE OROMO/ART PLAN

Everything below this notice is retained only as historical context. It is not
the active project specification and must not drive current work.

The active deliverable is
`$WORKSPACE/multi-lingual-ticketing`: Track 1 + Track 2a
multilingual support-ticket extraction and robustness evaluation using
CuratorKIT, AlignTune, AuditKIT, and Tiny Aya Global. Before work, read that
project's `.agent/IMP.md`, `.agent/SUBMIT.md`,
`.agent/ticket_system.md`, and, for robustness tasks,
`.agent/RED-TEAMING.md`.

Do not commit or push toolkit submodule changes without Om's explicit
instruction. Do not publish artifacts before final human review.

---

The idea is to check how easy would it be poison a given models and what safeguards can we prevent to solve  this challenge?
        - The activation intervention test could break these models and make them produce hate speech / racist comments etc. #MODEL Drifting
        - Then we jump in with SafeTune or something to repair it and strengthen the safeguards.
            - Ways to strengthen the safeguards:
                1. Joint Weight Perurbation
                2. Abliteration-Resistant Tuning (ART)
                3. Drift-Constrained Optimization: Optimization with these these methods or a combination of these which raise the cost beyond what the RESTA or the LOX methods in the library can produce.
        - Tiny Aya -> CuratorKit -> CircuitKit -> SafeTune -> AuditKit

## Instructions:

- For each tool that we want to use and chain together, we have the submodules setup and an agent summary in `<repo>/.agent/README.md`.
- The model that we will be using has to be : `CohereLabs/tiny-aya-global` not Qwen or any other model.
- First prepare a plan according on how we will chain these tools together and more importantly - get back with an analysis on whether it is possible to get EXACTLY the methods that we have mentioned (Joint Weight Pertubation etc.) - Also explain those methods to me in the plan so that I know we are making the right change.
- Write the plan to `$WORKSPACE/.agent/art-plan.md`.

## Oreo submission preamble

Before submission work, read `$WORKSPACE/oreo/.agent/SUBMIT.md`.
The deliverable requires a registered email, an abstract under 500 words,
public un-gated Hugging Face model and dataset collections with their repos,
a write-up, a GitHub code/notebook repository with reproducibility notes,
and explicit repos, models, tracks, and problem statements. Keep local
submission artifact symlinks under `$WORKSPACE/oreo-submission`.
For every experimental stage, regenerate the before/after metric ledger with
`oreo/scripts/44_build_submission_metrics.py`; include before, after, delta,
sample count, fixture/hash, status, and report path, or an explicit coverage
gap. Do not present English string-match proxies as multilingual safety scores.
