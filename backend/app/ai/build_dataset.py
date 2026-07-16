"""Generate a T5 fine-tuning dataset for COA concept coverage from the KB.

Produces JSONL rows of the form:
    {"input": "<student answer text>", "target": "<concept coverage summary>"}

This is intentionally small/synthetic — a scaffold to demonstrate the LoRA
fine-tuning workflow. In production, replace/augment with real anonymised
student submissions and faculty-reviewed labels.

Run:
    python -m app.ai.build_dataset > app/ai/data/coa_concepts.jsonl
"""
from __future__ import annotations

import json

from .knowledge_base import COA_CONCEPTS


def _sentence(concept: str, keyword: str) -> str:
    return f"The answer discusses {keyword}, demonstrating the concept of {concept}."


def build_rows() -> list[dict]:
    rows: list[dict] = []
    for topic, concepts in COA_CONCEPTS.items():
        all_names = [c for c, _ in concepts]
        # Positive example: covers first two concepts, misses the rest.
        for split in range(1, len(concepts)):
            covered = concepts[:split]
            missing = [c for c, _ in concepts[split:]]
            text = " ".join(_sentence(c, kws[0]) for c, kws in covered)
            covered_names = [c for c, _ in covered]
            score = round((len(covered_names) / len(all_names)) * 100)
            target = (
                f"Topic: {topic}. Coverage: {score}%. "
                f"Covered: {', '.join(covered_names)}. "
                f"Missing: {', '.join(missing) if missing else 'none'}."
            )
            rows.append({"input": text, "target": target})
    return rows


def main() -> None:
    for row in build_rows():
        print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
