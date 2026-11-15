"""Transformers inference with raw-response preservation."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

from .constants import SYSTEM_PROMPT
from .prompt import task_prompt
from .schema import FULL_SCHEMA


def extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S)
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", text):
            try:
                value, _ = decoder.raw_decode(text[match.start():])
                if isinstance(value, dict):
                    return value
            except json.JSONDecodeError:
                continue
    return None


def has_complete_top_level_json(text: str) -> bool:
    """True only when a JSON object beginning at the response start closes.

    Unlike :func:`extract_json`, this must not accept a completed nested entity
    object while the outer ticket object is still being generated.
    """
    candidate = text.lstrip()
    if candidate.startswith("```json"):
        candidate = candidate[7:].lstrip()
    elif candidate.startswith("```"):
        candidate = candidate[3:].lstrip()
    try:
        value, _ = json.JSONDecoder().raw_decode(candidate)
    except json.JSONDecodeError:
        return False
    return isinstance(value, dict)


@dataclass
class Generator:
    model_name: str
    adapter_path: str | None = None
    revision: str | None = None
    max_new_tokens: int = 384

    def __post_init__(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            revision=self.revision,
            trust_remote_code=True,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            revision=self.revision,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
        )
        if self.adapter_path:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, self.adapter_path)
        self.model.eval()

    def generate(
        self, text: str, fields: list[str] | None = None,
        escalation_threshold: float = 0.5,
    ) -> dict[str, Any]:
        fields = fields or list(FULL_SCHEMA["properties"])
        model_fields = [field for field in fields if field != "escalate"]
        chat = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task_prompt(text, model_fields)},
        ]
        rendered = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(rendered, return_tensors="pt").to(self.model.device)
        from transformers import StoppingCriteria, StoppingCriteriaList

        tokenizer = self.tokenizer
        prompt_length = inputs["input_ids"].shape[1]

        class CompleteJSON(StoppingCriteria):
            """Stop once greedy decoding has produced one complete JSON object."""

            def __call__(self, input_ids, scores, **kwargs):
                generated = tokenizer.decode(
                    input_ids[0, prompt_length:], skip_special_tokens=True
                )
                return has_complete_top_level_json(generated)

        started = time.perf_counter()
        with self.torch.inference_mode():
            output = self.model.generate(
                **inputs, max_new_tokens=self.max_new_tokens, do_sample=False,
                return_dict_in_generate=True, output_scores=True,
                stopping_criteria=StoppingCriteriaList([CompleteJSON()]),
                pad_token_id=self.tokenizer.eos_token_id,
            )
        elapsed = time.perf_counter() - started
        new_ids = output.sequences[0, inputs["input_ids"].shape[1]:]
        raw = self.tokenizer.decode(new_ids, skip_special_tokens=True)
        # Mean selected-token probability is a calibration proxy, not an intent
        # posterior. It is kept explicit so the escalation curve cannot be
        # misrepresented.
        probs = []
        for score, token_id in zip(output.scores, new_ids):
            probs.append(float(score[0].softmax(-1)[token_id].item()))
        confidence = sum(probs) / max(1, len(probs))
        prediction = extract_json(raw)
        if prediction is not None and "escalate" in fields:
            # No source labels escalation. Derive it from the deployment policy
            # instead of training the model to invent a boolean.
            prediction["escalate"] = confidence < escalation_threshold
        return {
            "prediction": prediction, "raw_response": raw,
            "generation_confidence_proxy": confidence,
            "latency_seconds": elapsed, "output_tokens": len(new_ids),
        }

