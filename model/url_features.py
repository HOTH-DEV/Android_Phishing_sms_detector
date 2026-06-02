"""
url_features.py
===============
Lexical URL feature extraction + a small classifier (Random Forest) for the
URL-risk signal of the threat engine.

Two roles:
  1. `extract_features(url)` -> dict of 15 lexical features. This logic is
     mirrored 1:1 in Kotlin (UrlFeatures.kt) for on-device parity.
  2. `--train` mode: generates a balanced URL dataset, trains a classifier,
     reports ROC-AUC, and saves model/artifacts/url_model.joblib.

Pure-Python parsing only (no tldextract / no network) -> fully reproducible.

Run:
    python model/url_features.py --train      # train + evaluate
    python model/url_features.py "http://paypa1-secure.com/login"   # score one URL

Acceptance criterion (Phase 3): >= 12 features, ROC-AUC >= 0.90.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import re
from collections import Counter
from urllib.parse import urlparse

import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS = os.path.join(HERE, "artifacts")

SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly"}
SUSPICIOUS_TLDS = {"xyz", "top", "info", "online", "support", "click", "country",
                   "co", "tk", "ml", "ga", "cf", "gq", "work", "zip"}
SUSPICIOUS_WORDS = ["login", "verify", "secure", "account", "update", "confirm",
                    "bank", "signin", "password", "billing", "unlock", "webscr",
                    "wp-admin", "paypal", "free", "bonus", "gift"]
IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

# 15 feature names, in fixed order (must match Kotlin).
FEATURE_NAMES = [
    "url_length", "num_dots", "num_hyphens", "num_digits", "num_special",
    "has_ip", "has_at", "num_subdomains", "has_https", "uses_shortener",
    "has_suspicious_word", "suspicious_tld", "digit_ratio", "entropy", "has_port",
]


def _entropy(s: str) -> float:
    """Shannon entropy of the string's character distribution."""
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def extract_features(url: str) -> dict:
    """Return the 15 lexical features for a URL as a name->number dict."""
    url = (url or "").strip()
    # Ensure urlparse sees a scheme so the host is parsed correctly.
    parsed = urlparse(url if "://" in url else "http://" + url)
    host = parsed.hostname or ""
    host_no_port = host
    tld = host.rsplit(".", 1)[-1].lower() if "." in host else ""

    digits = sum(c.isdigit() for c in url)
    specials = sum(c in "@%?=&_~+" for c in url)
    labels = [p for p in host_no_port.split(".") if p]

    feats = {
        "url_length": len(url),
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_digits": digits,
        "num_special": specials,
        "has_ip": int(bool(IP_RE.match(host_no_port))),
        "has_at": int("@" in url),
        # subdomains = host labels beyond domain+TLD (e.g. a.b.example.com -> 2)
        "num_subdomains": max(0, len(labels) - 2),
        "has_https": int(parsed.scheme == "https"),
        "uses_shortener": int(host_no_port in SHORTENERS),
        "has_suspicious_word": int(any(w in url.lower() for w in SUSPICIOUS_WORDS)),
        "suspicious_tld": int(tld in SUSPICIOUS_TLDS),
        "digit_ratio": digits / len(url) if url else 0.0,
        "entropy": round(_entropy(url), 4),
        "has_port": int(parsed.port is not None),
    }
    return feats


def features_vector(url: str) -> list[float]:
    f = extract_features(url)
    return [float(f[name]) for name in FEATURE_NAMES]


# --------------------------------------------------------------------------- #
# Synthetic URL dataset (rich enough to avoid trivial separability)
# --------------------------------------------------------------------------- #
def _build_url_dataset(n_per_class: int = 1500):
    legit_domains = ["paypal.com", "amazon.fr", "netflix.com", "google.com",
                     "microsoft.com", "apple.com", "github.com", "wikipedia.org",
                     "laposte.fr", "orange.fr", "bnpparibas.fr", "cih.ma"]
    legit_paths = ["", "/", "/help", "/account", "/orders", "/fr", "/login",
                   "/support", "/contact", "/products/item"]
    phish_hosts = ["paypa1-secure.com", "amaz0n-verify.net", "secure-orange-fr.xyz",
                   "apple-id-locked.co", "netflix-billing.support", "cihbank-login.online",
                   "account-update.tk", "192.168.43.12", "172.16.0.9",
                   "free-gift-claim.top", "bnp-confirm.info", "verify-laposte.click"]
    phish_paths = ["/login/verify", "/secure/update", "/account/confirm",
                   "/webscr?cmd=login", "/billing/reactivate", "/unlock?id=8821",
                   "/signin?session=expired", "/password/reset"]

    # A few legitimate brands legitimately use hyphens / login paths -> overlap.
    legit_hyphen_domains = ["my-account.orange.fr", "secure-login.bnpparibas.fr",
                            "sign-in.microsoft.com", "e-commerce.amazon.fr"]

    urls, labels = [], []
    for _ in range(n_per_class):  # legitimate
        # ~15% of legit URLs look "risky-ish" (hyphens, login paths, http) to
        # force the model to learn real signal rather than a single cue.
        if random.random() < 0.15:
            host = random.choice(legit_hyphen_domains)
            scheme = "https://" if random.random() < 0.8 else "http://"
            path = random.choice(["/login", "/account/verify", "/secure"])
        else:
            host = random.choice(["", "www.", "m.", "shop."][:]) + random.choice(legit_domains)
            scheme = "https://"
            path = random.choice(legit_paths)
        urls.append(f"{scheme}{host}{path}")
        labels.append(0)

    for _ in range(n_per_class):  # phishing
        # ~25% of phishing URLs are genuinely clean-looking hard cases:
        # no hyphen, common .com TLD, https, no obvious keyword.
        if random.random() < 0.25:
            host = random.choice(["paypalsecure.com", "amazonbilling.com",
                                  "verifyapple.com", "netflixhelp.com",
                                  "orangeclient.com", "laposteinfo.com"])
            urls.append(f"https://{host}/")
        else:
            host = random.choice(phish_hosts)
            scheme = "http://" if random.random() < 0.6 else "https://"
            sub = random.choice(["", "secure.", "login.", "account.", "verify-"])
            path = random.choice(phish_paths) if random.random() < 0.85 else ""
            urls.append(f"{scheme}{sub}{host}{path}")
        labels.append(1)
    return urls, labels


def train() -> None:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_auc_score, classification_report
    from sklearn.model_selection import train_test_split
    import joblib

    os.makedirs(ARTIFACTS, exist_ok=True)
    urls, labels = _build_url_dataset()
    X = np.array([features_vector(u) for u in urls])
    y = np.array(labels)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25,
                                              stratify=y, random_state=SEED)
    clf = RandomForestClassifier(n_estimators=200, random_state=SEED)
    clf.fit(X_tr, y_tr)

    proba = clf.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, proba)
    print(classification_report(y_te, (proba >= 0.5).astype(int),
                                target_names=["legitimate", "phishing"], digits=4))
    print(f"[result] URL ROC-AUC = {auc:.4f}  "
          f"({'PASS' if auc >= 0.90 else 'BELOW TARGET'} vs target 0.90)")

    # Feature importances (useful for the report).
    importances = sorted(zip(FEATURE_NAMES, clf.feature_importances_),
                         key=lambda t: t[1], reverse=True)
    print("\nTop features:")
    for name, imp in importances[:8]:
        print(f"  {name:<20} {imp:.3f}")

    joblib.dump({"model": clf, "features": FEATURE_NAMES},
                os.path.join(ARTIFACTS, "url_model.joblib"))
    print(f"\n[saved] -> {os.path.join(ARTIFACTS, 'url_model.joblib')}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--train", action="store_true", help="train + evaluate URL model")
    p.add_argument("url", nargs="?", help="a URL to score (prints its features)")
    args = p.parse_args()

    if args.train:
        train()
    elif args.url:
        from pprint import pprint
        pprint(extract_features(args.url))
    else:
        p.print_help()


if __name__ == "__main__":
    main()
