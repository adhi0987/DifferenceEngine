"""COA T5 (+ LoRA) model wrapper.

Loads a fine-tuned T5 text-to-text model to summarise/label COA concept coverage
when ``transformers`` (and optionally ``peft`` for LoRA adapters) are installed
and a model path is configured via the ``COA_T5_MODEL`` env var.

When the ML stack is unavailable the wrapper reports ``available = False`` and
callers fall back to the deterministic heuristic extractor. This mirrors the
design's "Edge AI, free/open-source-first" constraint: the platform runs
everywhere, and upgrades to a real model without code changes.
"""
from __future__ import annotations

import os
from functools import lru_cache


class T5ConceptModel:
    def __init__(self) -> None:
        self._pipe = None
        self.model_name = os.getenv("COA_T5_MODEL", "")
        self.adapter_path = os.getenv("COA_T5_LORA_ADAPTER", "")

    @property
    def available(self) -> bool:
        return self._pipe is not None

    def load(self) -> bool:
        if self._pipe is not None:
            return True
        if not self.model_name:
            return False
        try:
            from transformers import (  # type: ignore
                AutoModelForSeq2SeqLM,
                AutoTokenizer,
                pipeline,
            )
        except Exception:
            return False
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            if self.adapter_path:
                try:
                    from peft import PeftModel  # type: ignore

                    model = PeftModel.from_pretrained(model, self.adapter_path)
                except Exception:
                    pass
            self._pipe = pipeline(
                "text2text-generation", model=model, tokenizer=tokenizer
            )
            return True
        except Exception:
            self._pipe = None
            return False

    def summarize_coverage(self, text: str) -> str | None:
        """Return a short model-generated summary of concept coverage, or None."""
        if not self.load():
            return None
        prompt = (
            "Summarize the COA concepts covered in the following student answer "
            "and list any missing key concepts:\n" + text
        )
        try:
            out = self._pipe(prompt, max_new_tokens=128, truncation=True)
            return out[0]["generated_text"].strip()
        except Exception:
            return None


@lru_cache
def get_model() -> T5ConceptModel:
    return T5ConceptModel()
