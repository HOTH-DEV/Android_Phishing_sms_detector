"""Build a polished PDF dossier from the project Markdown deliverables."""
import os
import markdown
from weasyprint import HTML

import os as _os
ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
OUT = _os.path.join(ROOT, "docs", "PFE_phishing_dossier.pdf")

def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()

rapport = read("docs/rapport.md")
eda = read("data/processed/eda_summary.txt")

# Android source tree (for the app deliverable section).
app_files = []
for dirpath, _, files in os.walk(os.path.join(ROOT, "android-app")):
    for fn in sorted(files):
        rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
        app_files.append(rel)
app_tree = "\n".join("- `" + f + "`" for f in sorted(app_files))

# Cover page (HTML, not markdown, for fine control).
cover = """
<div class="cover">
  <div class="cover-tag">PROJET DE FIN D'ÉTUDES — 4ᵉ ANNÉE SÉCURITÉ INFORMATIQUE</div>
  <h1 class="cover-title">Détection de phishing sur mobile</h1>
  <div class="cover-sub">Application Android &middot; Moteur NLP DistilBERT &middot; Analyse d'URL &middot; Traitement 100 % local</div>
  <div class="cover-deliverables">
    <div class="deliv">📱<br><b>Application mobile</b><br><span>Kotlin + Jetpack Compose</span></div>
    <div class="deliv">🗂️<br><b>Dataset phishing</b><br><span>5 187 entrées FR/EN/AR</span></div>
    <div class="deliv">🧠<br><b>Rapport IA</b><br><span>Méthodo &amp; résultats</span></div>
  </div>
  <div class="cover-foot">Dossier technique &mdash; généré le {date}</div>
</div>
<div class="page-break"></div>
""".format(date="29/05/2026")

# Dataset deliverable section as markdown.
dataset_md = f"""
# Annexe A — Dataset phishing (détails)

Le dataset est produit de façon **reproductible** par `data/build_dataset.py`
(graine fixe, repli hors-ligne) et stocké dans `data/processed/dataset.csv`.
Il combine un corpus SMS public réel et des échantillons synthétiques
multilingues (FR/EN/AR) couvrant SMS, emails et URLs.

**Source du corpus réel — SMS Spam Collection (UCI ML Repository) :**

- https://archive.ics.uci.edu/dataset/228/sms+spam+collection
- Miroir Kaggle : https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset
- Lien brut (build_dataset.py) : https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv

**Schéma des colonnes :** `text`, `type` (sms / email / url),
`label` (phishing / legitimate), `source` (real / synthetic).

```
{eda.strip()}
```

Le dataset est **équilibré** (écart de 4,8 % entre classes), condition
nécessaire pour un entraînement non biaisé. Les tokens les plus fréquents de la
classe *phishing* (« votre », « account », « avertissement », « claim »…)
confirment la présence des marqueurs lexicaux typiques de l'hameçonnage.
"""

# App deliverable section.
app_md = f"""
# Annexe B — Application mobile (structure)

Application **Android native** (Kotlin + Jetpack Compose), package
`com.pfe.phishingdetector`. L'inférence est **entièrement locale** (TensorFlow
Lite) ; l'app ne demande **aucune permission INTERNET**.

## Cœur ML embarqué (Kotlin)

- `ml/WordpieceTokenizer.kt` — tokenisation BERT (lecture de `vocab.txt`).
- `ml/TextClassifier.kt` — inférence DistilBERT via TFLite → P(phishing).
- `ml/UrlFeatures.kt` — 15 features lexicales d'URL (miroir du Python).
- `ml/ThreatEngine.kt` — fusion des signaux + score + raisons.

## Arborescence du projet Android

{app_tree}
"""

# Assemble full markdown body (rapport already embeds diagrams & screenshots).
body_md = "\n\n".join([rapport, dataset_md, app_md])

md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"])
body_html = md.convert(body_md)

css = """
@page { size: A4; margin: 2cm 1.8cm; @bottom-center {
  content: counter(page) " / " counter(pages);
  font-size: 9px; color: #888; } }
@page :first { margin: 0; }
* { box-sizing: border-box; }
body { font-family: 'DejaVu Sans', sans-serif; font-size: 10.5px;
  line-height: 1.55; color: #1a1a1a; }
h1 { font-size: 19px; color: #0d3b66; border-bottom: 2px solid #0d3b66;
  padding-bottom: 4px; margin-top: 26px; page-break-after: avoid; }
h2 { font-size: 14px; color: #1565c0; margin-top: 18px; page-break-after: avoid; }
h3 { font-size: 12px; color: #333; margin-top: 14px; page-break-after: avoid; }
p { margin: 6px 0; text-align: justify; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 9px;
  background: #f1f3f5; padding: 1px 4px; border-radius: 3px; }
pre { background: #0f172a; color: #e2e8f0; padding: 12px; border-radius: 6px;
  font-size: 8.5px; line-height: 1.4; overflow-x: hidden;
  white-space: pre-wrap; word-wrap: break-word; page-break-inside: avoid; }
pre code { background: none; color: inherit; padding: 0; font-size: 8.5px; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.5px;
  page-break-inside: avoid; }
th { background: #0d3b66; color: #fff; padding: 6px 8px; text-align: left; }
td { border: 1px solid #d0d7de; padding: 5px 8px; }
tr:nth-child(even) td { background: #f6f8fa; }
blockquote { border-left: 3px solid #ef6c00; background: #fff7ed;
  margin: 10px 0; padding: 8px 12px; color: #7c3a00; font-size: 10px; }
ul { margin: 6px 0; padding-left: 20px; }
li { margin: 2px 0; }
strong { color: #0d3b66; }
img { max-width: 100%; display: block; margin: 10px auto; }
table img { margin: 4px auto; max-height: 360px; }
.page-break { page-break-after: always; }

/* Cover */
.cover { height: 297mm; padding: 0; margin: 0; color: #fff;
  background: linear-gradient(135deg, #0d3b66 0%, #1565c0 55%, #1e88e5 100%);
  display: flex; flex-direction: column; justify-content: center;
  align-items: center; text-align: center; }
.cover-tag { letter-spacing: 2px; font-size: 11px; opacity: .85;
  border: 1px solid rgba(255,255,255,.5); padding: 6px 14px; border-radius: 20px; }
.cover-title { font-size: 40px; margin: 28px 40px 10px; border: none; color:#fff;
  font-weight: 800; line-height: 1.1; }
.cover-sub { font-size: 13px; opacity: .92; margin: 0 50px; }
.cover-deliverables { display: flex; gap: 18px; margin-top: 50px; }
.deliv { background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.3);
  border-radius: 12px; padding: 18px 16px; width: 150px; font-size: 11px;
  line-height: 1.5; }
.deliv span { opacity: .8; font-size: 9.5px; }
.cover-foot { margin-top: 60px; font-size: 10px; opacity: .8; }
"""

html = f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{cover}{body_html}</body></html>"
HTML(string=html, base_url=os.path.join(ROOT, "docs") + "/").write_pdf(OUT)
size = os.path.getsize(OUT) / 1024
print(f"[pdf] wrote {OUT} ({size:.0f} KB)")
