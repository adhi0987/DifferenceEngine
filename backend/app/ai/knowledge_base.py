"""COA concept knowledge base.

A curated map of COA topics to their canonical concepts and keyword aliases.
Used by the concept-extraction service (heuristic path) and by the LoRA training
data generator. Keeping this as data makes the domain knowledge auditable and
easy to extend without touching model code.
"""
from __future__ import annotations

# topic -> list of (canonical concept, [aliases/keywords])
COA_CONCEPTS: dict[str, list[tuple[str, list[str]]]] = {
    "Pipelining": [
        ("Data hazard", ["data hazard", "raw hazard", "read after write"]),
        ("Control hazard", ["control hazard", "branch hazard"]),
        ("Structural hazard", ["structural hazard", "resource conflict"]),
        ("Forwarding", ["forwarding", "operand forwarding", "bypassing"]),
        ("Pipeline stall", ["stall", "bubble", "pipeline stall"]),
        ("Branch prediction", ["branch prediction", "predictor", "speculative"]),
    ],
    "Cache Memory": [
        ("Direct mapping", ["direct mapping", "direct mapped"]),
        ("Associative mapping", ["fully associative", "associative mapping"]),
        ("Set-associative mapping", ["set associative", "set-associative"]),
        ("Cache hit", ["cache hit", "hit ratio"]),
        ("Cache miss", ["cache miss", "miss penalty", "compulsory miss"]),
        ("Write-back", ["write back", "write-back", "write through", "write-through"]),
    ],
    "Memory Hierarchy": [
        ("Locality of reference", ["locality", "spatial locality", "temporal locality"]),
        ("Virtual memory", ["virtual memory", "paging", "page table"]),
        ("TLB", ["tlb", "translation lookaside buffer"]),
        ("Memory interleaving", ["interleaving", "memory bank"]),
    ],
    "CPU Organization": [
        ("Control unit", ["control unit", "hardwired", "microprogrammed"]),
        ("ALU", ["alu", "arithmetic logic unit"]),
        ("Register file", ["register file", "general purpose register"]),
        ("Instruction cycle", ["instruction cycle", "fetch decode execute"]),
        ("Datapath", ["datapath", "data path"]),
    ],
    "Addressing Modes": [
        ("Immediate addressing", ["immediate addressing", "immediate mode"]),
        ("Direct addressing", ["direct addressing", "absolute addressing"]),
        ("Indirect addressing", ["indirect addressing"]),
        ("Indexed addressing", ["indexed addressing", "index register"]),
        ("Register addressing", ["register addressing", "register mode"]),
    ],
    "I/O Organization": [
        ("Interrupt", ["interrupt", "isr", "interrupt service"]),
        ("DMA", ["dma", "direct memory access"]),
        ("Programmed I/O", ["programmed i/o", "polling"]),
        ("Memory-mapped I/O", ["memory mapped", "memory-mapped i/o"]),
    ],
    "Arithmetic": [
        ("Booth's algorithm", ["booth", "booth's algorithm"]),
        ("Carry look-ahead", ["carry look ahead", "carry-lookahead", "cla"]),
        ("Floating point", ["floating point", "ieee 754", "mantissa", "exponent"]),
        ("Two's complement", ["two's complement", "twos complement"]),
    ],
}


def all_concepts() -> list[str]:
    return [c for topic in COA_CONCEPTS.values() for c, _ in topic]


def concepts_for_topic(topic: str) -> list[str]:
    return [c for c, _ in COA_CONCEPTS.get(topic, [])]


def keyword_index() -> list[tuple[str, str, list[str]]]:
    """Flatten to (topic, concept, keywords) rows for matching."""
    rows: list[tuple[str, str, list[str]]] = []
    for topic, concepts in COA_CONCEPTS.items():
        for concept, keywords in concepts:
            rows.append((topic, concept, keywords))
    return rows
