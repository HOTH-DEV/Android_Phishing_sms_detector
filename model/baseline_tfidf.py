"""
baseline_tfidf.py
=================
Classical ML baseline (TF-IDF + Logistic Regression) on the same dataset, used
in the report to justify the choice of DistilBERT (bonus: model comparison).

Run:
    python model/baseline_tfidf.py
"""

from __future__ import annotations

import json
import os

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(HERE, "..", "data", "processed", "dataset.csv")
ARTIFACTS = os.path.join(HERE, "artifacts")
LABELS = {"legitimate": 0, "phishing": 1}


def main() -> None:
    os.makedirs(ARTIFACTS, exist_ok=True)
    df = pd.read_csv(DATA_CSV).dropna(subset=["text", "label"])
    y = df["label"].map(LABELS)

    X_tr, X_te, y_tr, y_te = train_test_split(
        df["text"], y, test_size=0.30, stratify=y, random_state=42)

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000)),
        ("clf", LogisticRegression(max_iter=1000, C=4.0)),
    ])
    pipe.fit(X_tr, y_tr)

    proba = pipe.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    f1 = f1_score(y_te, pred)
    auc = roc_auc_score(y_te, proba)

    print(classification_report(y_te, pred,
                                target_names=["legitimate", "phishing"], digits=4))
    print(f"[baseline] F1 = {f1:.4f} | ROC-AUC = {auc:.4f}")

    with open(os.path.join(ARTIFACTS, "baseline_metrics.json"), "w") as f:
        json.dump({"model": "TF-IDF + LogisticRegression",
                   "f1": float(f1), "roc_auc": float(auc)}, f, indent=2)


if __name__ == "__main__":
    main()
