"""LoRA fine-tuning scaffold for the COA T5 concept model (design section 6.4).

Fine-tunes ``t5-small`` (or ``COA_BASE_MODEL``) with a LoRA adapter on the COA
concept-coverage dataset. Kept dependency-light and guarded so the repository
imports cleanly without the heavy ML stack installed.

Install the optional stack first:
    pip install -r app/ai/requirements-ai.txt

Generate data and train:
    python -m app.ai.build_dataset > app/ai/data/coa_concepts.jsonl
    python -m app.ai.train_lora --data app/ai/data/coa_concepts.jsonl --out app/ai/adapters/coa-lora

Then run the API with the trained adapter:
    COA_T5_MODEL=t5-small COA_T5_LORA_ADAPTER=app/ai/adapters/coa-lora uvicorn app.main:app
"""
from __future__ import annotations

import argparse
import json
import os


def _load_jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def train(data_path: str, out_dir: str, base_model: str, epochs: int) -> None:
    # Imports are inside the function so the module stays importable without
    # torch/transformers/peft present.
    from datasets import Dataset  # type: ignore
    from peft import LoraConfig, TaskType, get_peft_model  # type: ignore
    from transformers import (  # type: ignore
        AutoModelForSeq2SeqLM,
        AutoTokenizer,
        DataCollatorForSeq2Seq,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
    )

    rows = _load_jsonl(data_path)
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForSeq2SeqLM.from_pretrained(base_model)

    lora = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        target_modules=["q", "v"],
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    def tokenize(batch):
        model_inputs = tokenizer(
            batch["input"], max_length=256, truncation=True
        )
        labels = tokenizer(
            text_target=batch["target"], max_length=128, truncation=True
        )
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    dataset = Dataset.from_list(rows).map(tokenize, batched=True)

    args = Seq2SeqTrainingArguments(
        output_dir=out_dir,
        per_device_train_batch_size=4,
        num_train_epochs=epochs,
        learning_rate=3e-4,
        logging_steps=10,
        save_strategy="epoch",
        report_to=[],
    )
    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
    )
    trainer.train()

    os.makedirs(out_dir, exist_ok=True)
    model.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)
    print(f"Saved LoRA adapter to {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LoRA fine-tune COA T5 model")
    parser.add_argument("--data", default="app/ai/data/coa_concepts.jsonl")
    parser.add_argument("--out", default="app/ai/adapters/coa-lora")
    parser.add_argument("--base-model", default=os.getenv("COA_BASE_MODEL", "t5-small"))
    parser.add_argument("--epochs", type=int, default=5)
    args = parser.parse_args()
    train(args.data, args.out, args.base_model, args.epochs)


if __name__ == "__main__":
    main()
