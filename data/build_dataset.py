"""
build_dataset.py
================
Builds a reproducible, labelled phishing-detection dataset combining:
  - a real public SMS corpus (SMS Spam Collection, downloaded if reachable);
  - realistic synthetic samples for SMS, email and URL inputs so that all three
    input modalities of the app are represented and the classes stay balanced.

Output: data/processed/dataset.csv with columns:
  text      : the raw content to analyse
  type      : one of {sms, email, url}
  label     : one of {phishing, legitimate}
  source    : provenance tag (real / synthetic)

Design goals
------------
* Reproducible: fixed random seed; runs fully offline thanks to a synthetic
  fallback if the public corpus cannot be downloaded.
* Honest labelling: spam from the SMS corpus is used as a *proxy* for smishing
  and is labelled `phishing`; this limitation is documented in the report.
* Educational only: synthetic phishing samples are generic textbook templates
  meant to train a *defensive* classifier, not operational attack content.

Run:
    python data/build_dataset.py
"""

from __future__ import annotations

import io
import os
import random
import urllib.request
from collections import Counter

import pandas as pd

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 42
random.seed(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "raw")
PROCESSED_DIR = os.path.join(HERE, "processed")
OUTPUT_CSV = os.path.join(PROCESSED_DIR, "dataset.csv")
EDA_TXT = os.path.join(PROCESSED_DIR, "eda_summary.txt")

# Public mirrors of the UCI "SMS Spam Collection" (tab-separated: label\ttext).
# We try several so the script keeps working if one mirror goes down.
SMS_MIRRORS = [
    "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv",
    "https://raw.githubusercontent.com/mohitgupta-omg/Kaggle-SMS-Spam-Collection-Dataset-/master/spam.csv",
]

# Target number of synthetic rows PER class (phishing / legitimate) to top up
# the real corpus and guarantee a balanced dataset >= 5000 rows.
SYNTH_PER_CLASS = 2600


# --------------------------------------------------------------------------- #
# 1. Real SMS corpus (best effort, with offline fallback)
# --------------------------------------------------------------------------- #
def download_sms_corpus() -> pd.DataFrame:
    """Try to fetch a public SMS spam corpus. Return empty DF on failure."""
    os.makedirs(RAW_DIR, exist_ok=True)
    for url in SMS_MIRRORS:
        try:
            print(f"[real] trying {url} ...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
            # Persist the raw file for traceability.
            fname = os.path.join(RAW_DIR, os.path.basename(url))
            with open(fname, "wb") as f:
                f.write(raw)

            # Two possible formats across mirrors.
            if url.endswith(".tsv"):
                df = pd.read_csv(io.BytesIO(raw), sep="\t", header=None,
                                 names=["label", "text"])
            else:  # spam.csv style (label in col 0, text in col 1, latin-1)
                df = pd.read_csv(io.BytesIO(raw), encoding="latin-1")
                df = df.iloc[:, :2]
                df.columns = ["label", "text"]

            df = df.dropna()
            df["label"] = (df["label"].astype(str).str.strip().str.lower()
                           .map({"spam": "phishing", "ham": "legitimate"}))
            df = df.dropna(subset=["label"])
            df["type"] = "sms"
            df["source"] = "real"
            print(f"[real] loaded {len(df)} SMS rows.")
            return df[["text", "type", "label", "source"]]
        except Exception as exc:  # network blocked, mirror down, etc.
            print(f"[real] failed ({exc.__class__.__name__}): {exc}")
    print("[real] no corpus reachable -> using synthetic data only.")
    return pd.DataFrame(columns=["text", "type", "label", "source"])


# --------------------------------------------------------------------------- #
# 2. Synthetic generators (templates + randomized slots)
# --------------------------------------------------------------------------- #
BRANDS = ["PayPal", "Amazon", "Netflix", "La Poste", "Orange", "Free", "CIH Bank",
          "Attijariwafa", "BNP", "Microsoft", "Apple", "Google", "DHL", "Chronopost"]
NAMES = ["Sara", "Yassine", "Ali", "Fatima", "Karim", "Léa", "Hugo", "Nadia"]
LEGIT_DOMAINS = ["paypal.com", "amazon.fr", "netflix.com", "laposte.fr", "orange.fr",
                 "google.com", "microsoft.com", "apple.com", "github.com", "wikipedia.org"]
PHISH_HOSTS = [
    "paypa1-secure.com", "amaz0n-verify.net", "netflix-billing.support",
    "laposte-colis.info", "secure-orange-fr.com", "apple-id-locked.co",
    "192.168.43.12", "bit.ly/3xVq9z", "account-update.xyz", "cihbank-login.online",
]
PHISH_PATHS = ["/login/verify", "/secure/update", "/account/confirm",
               "/webscr?cmd=login", "/billing/reactivate", "/unlock?id=8821"]

# Multilingual (FR / EN / AR) phishing SMS/email templates — generic textbook
# smishing examples used to TRAIN a detector.
PHISH_TEMPLATES = [
    "URGENT: votre compte {brand} a ete suspendu. Verifiez ici: {url}",
    "Your {brand} account is locked. Confirm your identity now: {url}",
    "Vous avez gagne un cadeau {brand}! Reclamez-le sous 24h: {url}",
    "Votre colis est bloque. Payez les frais de douane: {url}",
    "Security alert: unusual login on your {brand} account. Reset: {url}",
    "تنبيه: تم تعليق حسابك في {brand}. تحقق من هويتك هنا: {url}",
    "Dernier avertissement: mettez a jour vos infos {brand} ou perte du compte: {url}",
    "Refund of 250 EUR pending from {brand}. Claim within 12h: {url}",
    "Votre carte sera debitee de 89.99 EUR. Annulez ici: {url}",
    "Click to avoid account closure {brand}: {url}",
]
LEGIT_TEMPLATES = [
    "Salut {name}, on se voit a 18h pour le cafe ?",
    "Your {brand} order has shipped and will arrive Tuesday.",
    "Rappel: rendez-vous chez le dentiste demain a 10h.",
    "Merci pour ton message, je te rappelle ce soir.",
    "Your monthly {brand} statement is now available in the app.",
    "Bonjour {name}, la reunion est decalee a 15h.",
    "Happy birthday {name}! Hope you have a great day.",
    "Le livreur passera entre 14h et 16h aujourd'hui.",
    "Code de validation: 728193. Ne le partagez avec personne.",
    "On part en weekend samedi, tu veux venir ?",
]


def _rand_phish_url() -> str:
    host = random.choice(PHISH_HOSTS)
    path = random.choice(PHISH_PATHS) if random.random() < 0.7 else ""
    scheme = "http://" if random.random() < 0.6 else "https://"
    return f"{scheme}{host}{path}"


def _rand_legit_url() -> str:
    host = random.choice(LEGIT_DOMAINS)
    path = random.choice(["", "/", "/help", "/account", "/orders", "/fr"])
    return f"https://{host}{path}"


def gen_text_samples(n: int, label: str) -> list[dict]:
    """Generate n SMS/email-style samples for the given label."""
    rows = []
    templates = PHISH_TEMPLATES if label == "phishing" else LEGIT_TEMPLATES
    for _ in range(n):
        tpl = random.choice(templates)
        url = _rand_phish_url() if label == "phishing" else _rand_legit_url()
        text = tpl.format(brand=random.choice(BRANDS),
                          name=random.choice(NAMES), url=url)
        # Roughly a third are framed as longer "emails".
        kind = "email" if random.random() < 0.33 else "sms"
        if kind == "email":
            greeting = random.choice(["Cher client,", "Dear customer,", "Bonjour,"])
            text = f"{greeting} {text}"
        rows.append({"text": text, "type": kind, "label": label, "source": "synthetic"})
    return rows


def gen_url_samples(n: int, label: str) -> list[dict]:
    """Generate n bare-URL samples for the given label."""
    maker = _rand_phish_url if label == "phishing" else _rand_legit_url
    return [{"text": maker(), "type": "url", "label": label, "source": "synthetic"}
            for _ in range(n)]


# --------------------------------------------------------------------------- #
# 3. Cleaning helpers
# --------------------------------------------------------------------------- #
def normalize(text: str) -> str:
    """Light normalization: collapse whitespace, strip control chars."""
    text = str(text).replace("\r", " ").replace("\n", " ")
    text = " ".join(text.split())
    return text.strip()


def balance(df: pd.DataFrame, tol: float = 0.10) -> pd.DataFrame:
    """Downsample the majority class so classes are within +/- tol of each other."""
    counts = df["label"].value_counts()
    minority = counts.min()
    cap = int(minority * (1 + tol))
    parts = [g.sample(n=min(len(g), cap), random_state=SEED)
             for _, g in df.groupby("label")]
    return pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 4. EDA report
# --------------------------------------------------------------------------- #
def write_eda(df: pd.DataFrame) -> str:
    lines = []
    lines.append("=== EDA SUMMARY — dataset.csv ===")
    lines.append(f"Total rows: {len(df)}")
    lines.append("")
    lines.append("Class distribution:")
    for k, v in df["label"].value_counts().items():
        lines.append(f"  {k:<11}: {v} ({v / len(df):.1%})")
    lines.append("")
    lines.append("Input type distribution:")
    for k, v in df["type"].value_counts().items():
        lines.append(f"  {k:<6}: {v}")
    lines.append("")
    lines.append("Source distribution:")
    for k, v in df["source"].value_counts().items():
        lines.append(f"  {k:<10}: {v}")
    lines.append("")
    df = df.assign(_len=df["text"].str.len())
    lines.append("Average text length (chars):")
    for k, v in df.groupby("label")["_len"].mean().items():
        lines.append(f"  {k:<11}: {v:.1f}")
    lines.append("")
    # Top tokens per class (very rough: split on whitespace, lowercased).
    for label in df["label"].unique():
        tokens = Counter()
        for t in df.loc[df["label"] == label, "text"]:
            tokens.update(w.lower() for w in str(t).split() if len(w) > 3)
        top = ", ".join(f"{w}({c})" for w, c in tokens.most_common(10))
        lines.append(f"Top tokens [{label}]: {top}")
    report = "\n".join(lines)
    with open(EDA_TXT, "w", encoding="utf-8") as f:
        f.write(report)
    return report


# --------------------------------------------------------------------------- #
# 5. Main pipeline
# --------------------------------------------------------------------------- #
def main() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    frames = [download_sms_corpus()]

    # Synthetic top-up: text + URL samples for both classes.
    synth = []
    for label in ("phishing", "legitimate"):
        synth += gen_text_samples(int(SYNTH_PER_CLASS * 0.7), label)
        synth += gen_url_samples(int(SYNTH_PER_CLASS * 0.3), label)
    frames.append(pd.DataFrame(synth))

    df = pd.concat([f for f in frames if not f.empty], ignore_index=True)

    # --- Cleaning ---
    df["text"] = df["text"].map(normalize)
    df = df[df["text"].str.len() > 0]
    df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)

    # --- Balance classes ---
    df = balance(df)

    # --- Save ---
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"\n[done] wrote {len(df)} rows -> {OUTPUT_CSV}")

    print("\n" + write_eda(df))


if __name__ == "__main__":
    main()
