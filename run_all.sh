#!/usr/bin/env bash
#
# run_all.sh — Installe les dépendances et exécute toute la chaîne du projet :
#   dataset -> classifieur URL -> baseline -> tests -> (DistilBERT) ->
#   évaluation -> export TFLite -> copie des artefacts vers l'app Android.
#
# Usage :
#   ./run_all.sh                 # tout, y compris le fine-tuning DistilBERT
#   SKIP_TRAIN=1 ./run_all.sh    # saute l'entraînement DistilBERT (rapide)
#   NO_VENV=1 ./run_all.sh       # n'utilise pas d'environnement virtuel
#
set -uo pipefail

# ----- jolis logs ----------------------------------------------------------
BLUE='\033[1;34m'; GREEN='\033[1;32m'; YEL='\033[1;33m'; RED='\033[1;31m'; NC='\033[0m'
step() { echo -e "\n${BLUE}==>${NC} ${1}"; }
ok()   { echo -e "${GREEN}[OK]${NC} ${1}"; }
warn() { echo -e "${YEL}[!]${NC} ${1}"; }
err()  { echo -e "${RED}[ERREUR]${NC} ${1}"; }

cd "$(dirname "$0")"
ROOT="$(pwd)"
PY=python3

# ----- 0. Python venv ------------------------------------------------------
if [ "${NO_VENV:-0}" != "1" ]; then
  step "Création de l'environnement virtuel (.venv)"
  $PY -m venv .venv && source .venv/bin/activate
  PY=python
  ok "venv activé"
else
  warn "venv désactivé (NO_VENV=1)"
fi

# ----- 1. Dépendances ------------------------------------------------------
step "Installation des dépendances (requirements.txt)"
$PY -m pip install --upgrade pip >/dev/null
if $PY -m pip install -r requirements.txt; then
  ok "dépendances installées"
else
  err "échec de l'installation des dépendances"; exit 1
fi

# ----- 2. Dataset ----------------------------------------------------------
step "Construction du dataset"
$PY data/build_dataset.py && ok "dataset prêt -> data/processed/dataset.csv"

# ----- 3. Classifieur d'URL ------------------------------------------------
step "Entraînement + évaluation du classifieur d'URL"
$PY model/url_features.py --train && ok "modèle URL -> model/artifacts/url_model.joblib"

# ----- 4. Baseline TF-IDF --------------------------------------------------
step "Baseline TF-IDF + régression logistique (comparatif)"
$PY model/baseline_tfidf.py && ok "baseline -> model/artifacts/baseline_metrics.json"

# ----- 5. Tests unitaires --------------------------------------------------
step "Tests unitaires (pytest)"
$PY -m pytest -q tests/ && ok "tests passants"

# ----- 6. Fine-tuning DistilBERT (lourd) -----------------------------------
if [ "${SKIP_TRAIN:-0}" = "1" ]; then
  warn "Fine-tuning DistilBERT sauté (SKIP_TRAIN=1)"
else
  step "Fine-tuning DistilBERT (peut être long ; nécessite réseau/GPU conseillé)"
  if $PY model/train.py --epochs "${EPOCHS:-3}"; then
    ok "modèle entraîné -> model/artifacts/"
    step "Évaluation (matrice de confusion)"
    $PY model/evaluate.py && ok "rapport -> model/artifacts/"
    step "Export TensorFlow Lite (int8)"
    if $PY model/export_tflite.py; then
      ok "modèle exporté -> model/artifacts/model.tflite"
      step "Copie des artefacts vers l'app Android"
      ASSETS="android-app/app/src/main/assets"
      cp -f model/artifacts/model.tflite "$ASSETS/" 2>/dev/null && \
      cp -f model/artifacts/vocab.txt   "$ASSETS/" 2>/dev/null && \
      ok "model.tflite + vocab.txt copiés dans $ASSETS"
    else
      warn "export TFLite échoué (TensorFlow requis)"
    fi
  else
    warn "fine-tuning échoué/ignoré — l'app fonctionnera en mode heuristique."
  fi
fi

# ----- 7. Build APK (si SDK Android présent) -------------------------------
step "Construction de l'APK Android (optionnelle)"
if [ -n "${ANDROID_HOME:-}" ] || [ -n "${ANDROID_SDK_ROOT:-}" ]; then
  ( cd android-app && chmod +x ./gradlew 2>/dev/null; ./gradlew assembleDebug ) && \
    ok "APK -> android-app/app/build/outputs/apk/debug/app-debug.apk"
else
  warn "SDK Android introuvable (ANDROID_HOME non défini)."
  echo "    Pour compiler l'app : ouvrez android-app/ dans Android Studio,"
  echo "    ou définissez ANDROID_HOME puis lancez :  cd android-app && ./gradlew assembleDebug"
fi

echo -e "\n${GREEN}=== Terminé. ===${NC}"
echo "Artefacts : model/artifacts/  |  Dataset : data/processed/dataset.csv"
