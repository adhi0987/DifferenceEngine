"""COA concept extraction (design section 4.4 / FR-18).

Detects which COA concepts a student's extracted text covers, infers the most
likely topic, computes a coverage score, and lists missing concepts. Uses the
optional T5 model for a natural-language summary when available, and always
returns deterministic structured results via the keyword knowledge base.
"""
from __future__ import annotations

import re

from ..ai import knowledge_base as kb
from ..ai.model import get_model


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def detect_concepts(text: str) -> dict:
    """Return detected/missing concepts, inferred topic, and coverage score."""
    norm = _normalize(text)

    detected: list[str] = []
    topic_hits: dict[str, int] = {}
    for topic, concept, keywords in kb.keyword_index():
        if any(kw in norm for kw in keywords):
            detected.append(concept)
            topic_hits[topic] = topic_hits.get(topic, 0) + 1

    inferred_topic = max(topic_hits, key=topic_hits.get) if topic_hits else None

    if inferred_topic:
        topic_concepts = kb.concepts_for_topic(inferred_topic)
        detected_in_topic = [c for c in detected if c in topic_concepts]
        missing = [c for c in topic_concepts if c not in detected_in_topic]
        coverage = (
            round((len(detected_in_topic) / len(topic_concepts)) * 100)
            if topic_concepts
            else 0
        )
    else:
        missing = []
        coverage = 0

    # Deduplicate while preserving order.
    detected = list(dict.fromkeys(detected))

    summary = get_model().summarize_coverage(text)

    return {
        "inferredTopic": inferred_topic,
        "conceptCoverageScore": coverage,
        "detectedConcepts": detected,
        "missingConcepts": missing,
        "modelSummary": summary,
    }
