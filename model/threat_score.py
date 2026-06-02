"""
threat_score.py
===============
Fusion engine: combines the text-classifier probability (DistilBERT) and the
URL-classifier probability into a single Threat Score (0-100), assigns a
verdict, and produces human-readable reasons (explainability).

This logic is mirrored in Kotlin (ThreatEngine.kt) for on-device use.

Thresholds:
    0-39  -> safe       (green)
    40-69 -> suspicious (orange)
    70-100-> dangerous  (red)

Run a demo:
    python model/threat_score.py
"""

from __future__ import annotations

import os
import re

from url_features import extract_features, features_vector  # local import

W_TEXT = 0.6   # weight of the text signal in the fusion
W_URL = 0.4    # weight of the URL signal (only when a URL is present)

URL_RE = re.compile(r"(https?://[^\s]+|www\.[^\s]+|\b[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?)",
                    re.IGNORECASE)

# Multilingual urgency / pressure cues (FR / EN / AR) for explainability.
URGENCY_WORDS = ["urgent", "immédiat", "immediately", "now", "maintenant", "24h",
                 "expire", "suspendu", "suspended", "locked", "bloqué", "dernier",
                 "last warning", "avertissement", "عاجل", "فورا"]
CREDENTIAL_WORDS = ["password", "mot de passe", "login", "identifiant", "verify",
                    "vérifier", "confirm", "confirmer", "code", "pin", "تحقق"]
MONEY_WORDS = ["refund", "remboursement", "gagné", "won", "prize", "cadeau",
               "gift", "eur", "$", "€", "facture", "payer", "pay", "bonus"]

_url_model = None  # lazily loaded joblib model


def _load_url_model():
    global _url_model
    if _url_model is None:
        path = os.path.join(os.path.dirname(__file__), "artifacts", "url_model.joblib")
        if os.path.exists(path):
            import joblib
            _url_model = joblib.load(path)
        else:
            _url_model = False  # mark as unavailable
    return _url_model


def find_urls(text: str) -> list[str]:
    """Extract candidate URLs from free text."""
    return [m.group(0).rstrip(".,);") for m in URL_RE.finditer(text or "")]


def url_risk(url: str) -> float:
    """Return phishing probability for a URL in [0,1]."""
    model = _load_url_model()
    if model:
        import numpy as np
        proba = model["model"].predict_proba(np.array([features_vector(url)]))[0, 1]
        return float(proba)
    # Heuristic fallback if the trained model is absent.
    f = extract_features(url)
    score = (0.30 * f["has_ip"] + 0.20 * f["suspicious_tld"]
             + 0.20 * f["has_suspicious_word"] + 0.15 * (1 - f["has_https"])
             + 0.15 * min(f["num_hyphens"] / 3, 1))
    return min(score, 1.0)


def text_signals(text: str) -> list[str]:
    """Return human-readable reasons found in the text (explainability)."""
    t = (text or "").lower()
    reasons = []
    if any(w in t for w in URGENCY_WORDS):
        reasons.append("Ton d'urgence / pression temporelle détecté")
    if any(w in t for w in CREDENTIAL_WORDS):
        reasons.append("Demande d'identifiants / code de vérification")
    if any(w in t for w in MONEY_WORDS):
        reasons.append("Promesse de gain ou pression financière")
    return reasons


def heuristic_text_prob(text: str) -> float:
    """Lightweight text probability used ONLY when DistilBERT is unavailable
    (e.g. running this demo before training). Production uses the model."""
    n = len(text_signals(text))
    return min(0.25 + 0.25 * n, 0.95)


def verdict(score: int) -> tuple[str, str]:
    if score >= 70:
        return "Dangereux", "red"
    if score >= 40:
        return "Suspect", "orange"
    return "Sûr", "green"


def analyze(text: str, p_text: float | None = None) -> dict:
    """Full analysis: fuse text + URL signals, produce score, verdict, reasons.

    p_text: phishing probability from DistilBERT in [0,1]. If None, a heuristic
            is used so the engine remains runnable without the trained model.
    """
    if p_text is None:
        p_text = heuristic_text_prob(text)

    urls = find_urls(text)
    reasons = text_signals(text)

    if urls:
        # Use the riskiest URL found.
        p_url = max(url_risk(u) for u in urls)
        risky = max(urls, key=url_risk)
        fused = W_TEXT * p_text + W_URL * p_url
        if p_url >= 0.5:
            f = extract_features(risky)
            flags = []
            if f["has_ip"]:
                flags.append("adresse IP brute")
            if f["suspicious_tld"]:
                flags.append("extension de domaine suspecte")
            if f["has_suspicious_word"]:
                flags.append("mot-clé sensible dans l'URL")
            if not f["has_https"]:
                flags.append("absence de HTTPS")
            detail = (" (" + ", ".join(flags) + ")") if flags else ""
            reasons.append(f"URL à risque : {risky}{detail}")
    else:
        p_url = None
        fused = p_text

    score = round(100 * fused)
    label, color = verdict(score)
    if not reasons:
        reasons.append("Aucun signal fort ; contenu jugé probablement légitime"
                       if score < 40 else "Score élevé du modèle de langage")

    return {
        "text": text,
        "threat_score": score,
        "verdict": label,
        "color": color,
        "p_text": round(float(p_text), 3),
        "p_url": round(float(p_url), 3) if p_url is not None else None,
        "urls": urls,
        "reasons": reasons,
    }


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    examples = [
        "Salut, on se voit a 18h pour le cafe ?",
        "URGENT: votre compte PayPal a ete suspendu. Verifiez ici: http://paypa1-secure.xyz/login",
        "Your Amazon order has shipped and will arrive Tuesday.",
        "Vous avez gagne 500 EUR! Reclamez sous 24h: http://192.168.43.12/claim",
        "Connectez-vous a votre espace: https://www.orange.fr/account",
    ]
    for ex in examples:
        r = analyze(ex)
        print(f"\n[{r['threat_score']:>3}/100] {r['verdict']:<10} | {ex[:60]}")
        for reason in r["reasons"]:
            print(f"      - {reason}")
