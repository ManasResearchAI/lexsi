PYTHON ?= python3
export PYTHONPATH := src

.PHONY: test schema data redteam redteam-guard redteam-curator-smoke curator-smoke preflight overfit overfit-earth
test:
	$(PYTHON) -m pytest -q

schema:
	$(PYTHON) -m ticket_system.cli write-schema

data:
	$(PYTHON) -m ticket_system.cli build-data --with-hf

redteam:
	$(PYTHON) scripts/build_redteam_dataset.py

redteam-guard:
	$(PYTHON) scripts/evaluate_guard.py --output artifacts/evidence/redteam-guard/metrics.json

redteam-curator-smoke:
	PYTHONPATH=src:../CuratorKIT $(PYTHON) scripts/run_curatorkit.py --input data/processed/redteam/train.jsonl --max-samples 500 --output data/processed/curatorkit-redteam-smoke-$$(date -u +%Y%m%dT%H%M%SZ)

curator-smoke:
	PYTHONPATH=src:../CuratorKIT $(PYTHON) scripts/run_curatorkit.py --max-samples 500 --output data/processed/curatorkit-smoke-$$(date -u +%Y%m%dT%H%M%SZ)

preflight:
	$(PYTHON) scripts/preflight_model.py --samples 50

overfit:
	$(PYTHON) scripts/train_sft.py --dataset data/processed/curatorkit-smoke-v2 --output outputs/overfit-50-$$(date -u +%Y%m%dT%H%M%SZ) --max-samples 50 --max-steps 100 --epochs 20 --gradient-accumulation-steps 1

overfit-earth:
	$(PYTHON) scripts/train_sft.py --model CohereLabs/tiny-aya-earth --dataset data/processed/curatorkit-smoke-v2 --output outputs/overfit-earth-50-$$(date -u +%Y%m%dT%H%M%SZ) --max-samples 50 --max-steps 100 --epochs 20 --gradient-accumulation-steps 1

