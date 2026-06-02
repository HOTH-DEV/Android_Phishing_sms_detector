"""
evaluate.py
===========
Load the fine-tuned model from model/artifacts/ and evaluate it on the test
split of data/processed/dataset.csv. Saves:
  - confusion_matrix.png
  - classification_report.txt

Run:
    python model/evaluate.py
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from sklearn.metrics import (ConfusionMatrixDisplay, classification_report,
                             confusion_matrix)
from sklearn.model_selection import train_test_split
from transformers import AutoModelForSequenceClassification, AutoTokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(HERE, "..", "data", "processed", "dataset.csv")
ARTIFACTS = os.path.join(HERE, "artifacts")
LABELS = {"legitimate": 0, "phishing": 1}
NAMES = ["legitimate", "phishing"]


def get_test_split(seed: int = 42) -> pd.DataFrame:
    df = pd.read_csv(DATA_CSV).dropna(subset=["text", "label"])
    df["labels"] = df["label"].map(LABELS)
    _, temp = train_test_split(df, test_size=0.30, stratify=df["labels"],
                               random_state=seed)
    _, test = train_test_split(temp, test_size=0.50, stratify=temp["labels"],
                               random_state=seed)
    return test


@torch.no_grad()
def predict(texts, tokenizer, model, max_len=128, batch=32):
    preds = []
    for i in range(0, len(texts), batch):
        chunk = list(texts[i:i + batch])
        enc = tokenizer(chunk, truncation=True, max_length=max_len,
                        padding=True, return_tensors="pt")
        logits = model(**enc).logits
        preds.extend(torch.argmax(logits, dim=-1).tolist())
    return preds


def main() -> None:
    if not os.path.exists(os.path.join(ARTIFACTS, "config.json")):
        raise SystemExit("No model found in model/artifacts/. Run train.py first.")

    tokenizer = AutoTokenizer.from_pretrained(ARTIFACTS)
    model = AutoModelForSequenceClassification.from_pretrained(ARTIFACTS).eval()

    test = get_test_split()
    y_true = test["labels"].tolist()
    y_pred = predict(test["text"].tolist(), tokenizer, model)

    report = classification_report(y_true, y_pred, target_names=NAMES, digits=4)
    print(report)
    with open(os.path.join(ARTIFACTS, "classification_report.txt"), "w") as f:
        f.write(report)

    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(cm, display_labels=NAMES)
    disp.plot(cmap="Blues", values_format="d")
    plt.title("Matrice de confusion — DistilBERT")
    plt.tight_layout()
    out = os.path.join(ARTIFACTS, "confusion_matrix.png")
    plt.savefig(out, dpi=120)
    print(f"[plot] saved -> {out}")


if __name__ == "__main__":
    main()
