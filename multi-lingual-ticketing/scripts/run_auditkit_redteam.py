#!/usr/bin/env python3
"""Run AuditKIT's generic probes against a Tiny Aya base or adapter."""

import argparse
import json
from pathlib import Path

from auditkit.redteam import RedTeamRunner

from ticket_system.inference import Generator

parser = argparse.ArgumentParser()
parser.add_argument("--model", default="CohereLabs/tiny-aya-global")
parser.add_argument("--revision")
parser.add_argument("--adapter")
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

generator = Generator(args.model, args.adapter, revision=args.revision)


def generate(prompts: list[str]) -> list[str]:
    return [generator.generate(prompt)["raw_response"] for prompt in prompts]


result = RedTeamRunner(model=generate).run(
    probes=["prompt_injection", "jailbreak", "encoding"],
    detectors=["keyword", "injection_success", "system_prompt_leak"],
)
report = {
    "model": args.model,
    "model_revision": args.revision,
    "adapter": args.adapter,
    "total_probes": result.total_probes,
    "passed_probes": result.passed_probes,
    "failed_probes": result.failed_probes,
    "pass_rate": result.pass_rate,
    "probes_used": result.probes_used,
    "detectors_used": result.detectors_used,
    "results": [
        {
            "probe": row.probe_name,
            "detector": row.detector_name,
            "prompt": row.prompt,
            "output": row.output,
            "passed": row.passed,
            "metadata": row.metadata,
        }
        for row in result.results
    ],
}
args.output.mkdir(parents=True, exist_ok=False)
(args.output / "redteam_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(result.summary())
