"""
train.py
========
Fine-tune a multilingual DistilBERT model for binary phishing classification
(phishing vs legitimate) on data/processed/dataset.csv.

Outputs (to model/artifacts/):
  - the fine-tuned model + tokenizer (HF format, used later by export_tflite.py)
  - training_curves.png  (loss & accuracy)
  - test_metrics.json    (accuracy, precision, recall, F1)

Run:
    python model/train.py --epochs 3 --batch-size 16 --lr 2e-5

Acceptance criterion (Phase 2): F1 >= 0.90 on the test set.
"""

from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt

import torch
from datasets import Dataset
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score)
from sklearn.model_selection import train_test_split
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          DataCollatorWithPadding, Trainer, TrainingArguments)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(HERE, "..", "data", "processed", "dataset.csv")
ARTIFACTS = os.path.join(HERE, "artifacts")
MODEL_NAME = "distilbert-base-multilingual-cased"
LABELS = {"legitimate": 0, "phishing": 1}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fine-tune DistilBERT for phishing detection")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--lr", type=float, default=2e-5)
    p.add_argument("--max-len", type=int, default=128)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def load_splits(seed: int):
    """Load the CSV and return stratified train/val/test splits."""
    df = pd.read_csv(DATA_CSV)
    df = df.dropna(subset=["text", "label"])
    df["labels"] = df["label"].map(LABELS)

    train, temp = train_test_split(df, test_size=0.30, stratify=df["labels"],
                                   random_state=seed)
    val, test = train_test_split(temp, test_size=0.50, stratify=temp["labels"],
                                 random_state=seed)
    return train, val, test


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "precision": precision_score(labels, preds, zero_division=0),
        "recall": recall_score(labels, preds, zero_division=0),
        "f1": f1_score(labels, preds, zero_division=0),
    }


def plot_curves(log_history: list, out_path: str) -> None:
    """Extract loss/eval metrics from the Trainer log and save a figure."""
    train_loss = [(e["epoch"], e["loss"]) for e in log_history if "loss" in e]
    eval_acc = [(e["epoch"], e["eval_accuracy"]) for e in log_history
                if "eval_accuracy" in e]

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    if train_loss:
        ep, ls = zip(*train_loss)
        ax[0].plot(ep, ls, marker="o")
    ax[0].set_title("Training loss"); ax[0].set_xlabel("epoch"); ax[0].set_ylabel("loss")
    if eval_acc:
        ep, ac = zip(*eval_acc)
        ax[1].plot(ep, ac, marker="o", color="green")
    ax[1].set_title("Validation accuracy"); ax[1].set_xlabel("epoch"); ax[1].set_ylabel("accuracy")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    print(f"[plot] saved -> {out_path}")


def main() -> None:
    args = parse_args()
    os.makedirs(ARTIFACTS, exist_ok=True)
    torch.manual_seed(args.seed)

    train_df, val_df, test_df = load_splits(args.seed)
    print(f"[data] train={len(train_df)} val={len(val_df)} test={len(test_df)}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tok(batch):
        return tokenizer(batch["text"], truncation=True, max_length=args.max_len)

    ds = {name: Dataset.from_pandas(d[["text", "labels"]], preserve_index=False)
          for name, d in [("train", train_df), ("val", val_df), ("test", test_df)]}
    ds = {k: v.map(tok, batched=True) for k, v in ds.items()}

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=2,
        id2label={0: "legitimate", 1: "phishing"},
        label2id=LABELS,
    )

    targs = TrainingArguments(
        output_dir=os.path.join(ARTIFACTS, "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_steps=50,
        seed=args.seed,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=targs,
        train_dataset=ds["train"],
        eval_dataset=ds["val"],
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )

    trainer.train()

    # Final evaluation on the held-out test set.
    test_metrics = trainer.evaluate(ds["test"], metric_key_prefix="test")
    print("[test]", test_metrics)

    # Persist artifacts.
    trainer.save_model(ARTIFACTS)        # model weights + config
    tokenizer.save_pretrained(ARTIFACTS) # tokenizer + vocab.txt (used on Android)
    with open(os.path.join(ARTIFACTS, "test_metrics.json"), "w") as f:
        json.dump({k: float(v) for k, v in test_metrics.items()}, f, indent=2)
    plot_curves(trainer.state.log_history,
                os.path.join(ARTIFACTS, "training_curves.png"))

    f1 = test_metrics.get("test_f1", 0.0)
    print(f"\n[result] test F1 = {f1:.4f}  "
          f"({'PASS' if f1 >= 0.90 else 'BELOW TARGET'} vs target 0.90)")


if __name__ == "__main__":
    main()
