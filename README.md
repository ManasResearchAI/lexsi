# Lexsi multilingual ticket triage

The active hackathon project is
[multi-lingual-ticketing/](multi-lingual-ticketing/README.md): auditable
support-ticket extraction and prompt-injection evaluation for Yorùbá,
Kiswahili, and English using CuratorKIT, AlignTune, AuditKIT, and Tiny Aya.

The toolkit directories are Git submodules. Clone reproducibly with:

```bash
git clone --recurse-submodules <repository-url>
cd lexsi
git submodule update --init --recursive
```

## Reproducibility snapshot

- Tiny Aya Global revision:
  `af89d219b53ed9b13b8a4645f9c8028973510324`
- Tiny Aya Earth revision:
  `0624fafbe200f930b89566fc4ec4da314ba48d89`
- Global seed: `20261112`
- Generation: greedy decoding, `do_sample=false`,
  `max_new_tokens=384`, stop after one complete top-level JSON object.
- Exact Python package pins:
  [requirements-lock.txt](multi-lingual-ticketing/requirements-lock.txt)
- Evaluation and training commands:
  [multi-lingual-ticketing/README.md](multi-lingual-ticketing/README.md)

Create any compatible Python 3.12 environment, install the lock, and set
`PYTHONPATH=multi-lingual-ticketing/src`. A machine-specific interpreter may
be supplied through the optional `PYTHON` Make variable.

Generated datasets, model weights, optimizer states, evidence, private planning
files, and legacy experiments are intentionally excluded from Git. Their
public Hugging Face staging plan is documented in
[PUBLISHING_PLAN.md](multi-lingual-ticketing/submission/PUBLISHING_PLAN.md).

No model, dataset, Space, or repository is published until final review.
