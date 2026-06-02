"""
make_assets.py — Generate real diagrams and simulated app screens (SVG -> PNG).
Outputs to phishing-detector/docs/images/.
"""
import os
import cairosvg

import os as _os
IMG = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "docs", "images")
os.makedirs(IMG, exist_ok=True)

# Palette
NAVY = "#0d3b66"; BLUE = "#1565c0"; LBLUE = "#1e88e5"
GREEN = "#2E7D32"; ORANGE = "#EF6C00"; RED = "#C62828"
BG = "#eef1f5"; CARD = "#ffffff"; INK = "#1a1a1a"; GREY = "#6b7280"
FONT = "font-family='DejaVu Sans, Arial, sans-serif'"


def render(svg: str, name: str, w: int):
    path = os.path.join(IMG, name)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=path, output_width=w)
    print("wrote", path)


# --------------------------------------------------------------------------- #
# Reusable bits
# --------------------------------------------------------------------------- #
def box(x, y, w, h, fill, text, sub="", tcol="#fff", rx=12, fs=15, subfs=11):
    t = f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='{rx}' fill='{fill}'/>"
    cx = x + w / 2
    if sub:
        t += f"<text x='{cx}' y='{y+h/2-4}' text-anchor='middle' {FONT} font-size='{fs}' font-weight='bold' fill='{tcol}'>{text}</text>"
        t += f"<text x='{cx}' y='{y+h/2+15}' text-anchor='middle' {FONT} font-size='{subfs}' fill='{tcol}' opacity='0.9'>{sub}</text>"
    else:
        t += f"<text x='{cx}' y='{y+h/2+5}' text-anchor='middle' {FONT} font-size='{fs}' font-weight='bold' fill='{tcol}'>{text}</text>"
    return t


def arrow(x1, y1, x2, y2, col=NAVY, label=""):
    t = f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{col}' stroke-width='2.5' marker-end='url(#ah)'/>"
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        t += f"<rect x='{mx-26}' y='{my-11}' width='52' height='18' rx='4' fill='#fff' stroke='{col}' stroke-width='1'/>"
        t += f"<text x='{mx}' y='{my+2}' text-anchor='middle' {FONT} font-size='10' fill='{col}'>{label}</text>"
    return t


DEFS = ("<defs><marker id='ah' markerWidth='10' markerHeight='10' refX='8' refY='3' "
        "orient='auto' markerUnits='strokeWidth'><path d='M0,0 L8,3 L0,6 Z' fill='" + NAVY + "'/></marker>"
        "<linearGradient id='hd' x1='0' y1='0' x2='1' y2='1'>"
        f"<stop offset='0' stop-color='{NAVY}'/><stop offset='1' stop-color='{LBLUE}'/></linearGradient></defs>")


# --------------------------------------------------------------------------- #
# 1. Architecture / data-flow (on-device)
# --------------------------------------------------------------------------- #
def diagram_architecture():
    W, H = 760, 560
    s = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}'>", DEFS,
         f"<rect width='{W}' height='{H}' fill='{BG}'/>",
         f"<text x='{W/2}' y='34' text-anchor='middle' {FONT} font-size='18' font-weight='bold' fill='{NAVY}'>Architecture &amp; flux de donnees (traitement 100% local)</text>"]
    # input
    s.append(box(280, 56, 200, 50, NAVY, "Entree utilisateur", "SMS / email / URL"))
    s.append(arrow(380, 106, 380, 134))
    # preprocessing
    s.append(box(250, 136, 260, 46, BLUE, "Pre-traitement", "normalisation + extraction d'URL"))
    # split to two branches
    s.append(arrow(330, 182, 200, 222, label="texte"))
    s.append(arrow(430, 182, 560, 222, label="URL"))
    # two models
    s.append(box(90, 224, 220, 70, "#274690", "DistilBERT", "TFLite int8 — p_text", fs=15))
    s.append(box(450, 224, 220, 70, "#3a6ea5", "Classifieur d'URL", "RandomForest — p_url", fs=15))
    # merge to fusion
    s.append(arrow(200, 294, 330, 340))
    s.append(arrow(560, 294, 430, 340))
    s.append(box(230, 342, 300, 56, ORANGE, "Moteur de fusion (threat_score)",
                 "score 0-100  +  raisons explicables"))
    s.append(arrow(380, 398, 380, 426))
    # UI + Room
    s.append(box(150, 428, 220, 64, GREEN, "Interface d'alerte", "verdict colore + explication"))
    s.append(box(400, 428, 210, 64, "#4b5563", "Historique (Room)", "stockage local chiffrable"))
    s.append(arrow(380, 492, 405, 492))
    # formula
    s.append(f"<rect x='150' y='508' width='460' height='34' rx='8' fill='#fff' stroke='{ORANGE}'/>")
    s.append(f"<text x='{W/2}' y='530' text-anchor='middle' {FONT} font-size='12' fill='{INK}'>score = 100 x (0.6 . p_text + 0.4 . p_url)   |   seuils  0-39 sur . 40-69 suspect . 70-100 dangereux</text>")
    s.append("</svg>")
    render("".join(s), "architecture.png", 1100)


# --------------------------------------------------------------------------- #
# 2. On-device topology (no internet)
# --------------------------------------------------------------------------- #
def diagram_topology():
    W, H = 760, 460
    s = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}'>", DEFS,
         f"<rect width='{W}' height='{H}' fill='{BG}'/>",
         f"<text x='{W/2}' y='34' text-anchor='middle' {FONT} font-size='18' font-weight='bold' fill='{NAVY}'>Topologie : tout reste sur l'appareil</text>"]
    # phone container
    s.append(f"<rect x='150' y='60' width='460' height='320' rx='28' fill='#fff' stroke='{NAVY}' stroke-width='3'/>")
    s.append(f"<text x='380' y='90' text-anchor='middle' {FONT} font-size='13' font-weight='bold' fill='{NAVY}'>Smartphone Android</text>")
    s.append(box(185, 108, 175, 48, "#274690", "Sources", "SMS reception / partage", fs=13))
    s.append(box(400, 108, 175, 48, BLUE, "App PhishGuard", "Kotlin + Compose", fs=13))
    s.append(box(185, 176, 175, 48, "#3a6ea5", "Modeles embarques", "DistilBERT + URL", fs=12))
    s.append(box(400, 176, 175, 48, ORANGE, "Moteur de score", "fusion + raisons", fs=13))
    s.append(box(185, 244, 175, 48, GREEN, "UI d'alerte", "verdict colore", fs=13))
    s.append(box(400, 244, 175, 48, "#4b5563", "Base locale Room", "historique", fs=13))
    s.append(f"<text x='380' y='340' text-anchor='middle' {FONT} font-size='12' fill='{GREY}'>Aucune permission INTERNET — donnees jamais transmises</text>")
    # crossed-out cloud
    s.append(f"<ellipse cx='680' cy='150' rx='52' ry='30' fill='#fde2e2' stroke='{RED}' stroke-width='2'/>")
    s.append(f"<text x='680' y='148' text-anchor='middle' {FONT} font-size='12' fill='{RED}'>Cloud</text>")
    s.append(f"<text x='680' y='164' text-anchor='middle' {FONT} font-size='10' fill='{RED}'>serveur</text>")
    s.append(f"<line x1='642' y1='176' x2='718' y2='124' stroke='{RED}' stroke-width='3'/>")
    s.append(f"<line x1='610' y1='150' x2='628' y2='150' stroke='{RED}' stroke-width='2.5' stroke-dasharray='5,4'/>")
    s.append(f"<text x='620' y='400' text-anchor='middle' {FONT} font-size='12' fill='{GREEN}' font-weight='bold'>Privacy by design</text>")
    s.append("</svg>")
    render("".join(s), "topology.png", 1100)


# --------------------------------------------------------------------------- #
# 3. Offline training pipeline
# --------------------------------------------------------------------------- #
def diagram_training():
    W, H = 880, 260
    s = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}'>", DEFS,
         f"<rect width='{W}' height='{H}' fill='{BG}'/>",
         f"<text x='{W/2}' y='32' text-anchor='middle' {FONT} font-size='17' font-weight='bold' fill='{NAVY}'>Chaine d'entrainement (hors-ligne, sur PC)</text>"]
    xs = [20, 200, 380, 560, 740]
    s.append(box(xs[0], 90, 150, 80, NAVY, "Dataset", "5187 lignes FR/EN/AR", fs=14))
    s.append(box(xs[1], 90, 150, 80, BLUE, "Fine-tuning", "DistilBERT multiling.", fs=14))
    s.append(box(xs[2], 90, 150, 80, "#3a6ea5", "Evaluation", "F1, matrice conf.", fs=14))
    s.append(box(xs[3], 90, 150, 80, ORANGE, "Export TFLite", "quantization int8", fs=13))
    s.append(box(xs[4], 90, 120, 80, GREEN, "Assets app", "model.tflite + vocab", fs=12))
    for i in range(4):
        s.append(arrow(xs[i] + 150, 130, xs[i + 1], 130))
    s.append(f"<text x='{W/2}' y='210' text-anchor='middle' {FONT} font-size='12' fill='{GREY}'>build_dataset.py  ->  train.py  ->  evaluate.py  ->  export_tflite.py  ->  android-app/.../assets/</text>")
    s.append("</svg>")
    render("".join(s), "training_pipeline.png", 1200)


# --------------------------------------------------------------------------- #
# Phone mockup frame
# --------------------------------------------------------------------------- #
def phone(content_svg, title):
    W, H = 360, 720
    s = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}'>",
         f"<rect width='{W}' height='{H}' rx='34' fill='#0b1220'/>",
         f"<rect x='8' y='8' width='{W-16}' height='{H-16}' rx='28' fill='{BG}'/>",
         # notch
         f"<rect x='{W/2-45}' y='16' width='90' height='18' rx='9' fill='#0b1220'/>",
         # app bar
         f"<rect x='8' y='34' width='{W-16}' height='56' fill='url(#hd)'/>",
         DEFS,
         f"<text x='28' y='68' {FONT} font-size='17' font-weight='bold' fill='#fff'>{title}</text>",
         content_svg,
         # bottom nav
         f"<rect x='8' y='{H-66}' width='{W-16}' height='58' fill='#fff'/>",
         f"<line x1='8' y1='{H-66}' x2='{W-8}' y2='{H-66}' stroke='#e5e7eb'/>"]
    nav = [("Analyser", BLUE), ("SMS", GREY), ("Demo", GREY), ("Histo.", GREY)]
    for i, (lbl, col) in enumerate(nav):
        cx = 8 + (W - 16) * (i + 0.5) / 4
        s.append(f"<circle cx='{cx}' cy='{H-46}' r='5' fill='{col}'/>")
        s.append(f"<text x='{cx}' y='{H-26}' text-anchor='middle' {FONT} font-size='10' fill='{col}'>{lbl}</text>")
    s.append("</svg>")
    return "".join(s)


def gauge(cx, cy, r, score, col):
    import math
    # 270deg arc from 135 to 405
    def pt(angle):
        a = math.radians(angle)
        return cx + r * math.cos(a), cy + r * math.sin(a)
    x0, y0 = pt(135); x1, y1 = pt(135 + 270)
    xs, ys = pt(135); xe, ye = pt(135 + 270 * score / 100)
    large_bg = 1
    large_fg = 1 if (270 * score / 100) > 180 else 0
    t = f"<path d='M{x0:.1f},{y0:.1f} A{r},{r} 0 {large_bg} 1 {x1:.1f},{y1:.1f}' fill='none' stroke='#dfe3e8' stroke-width='12' stroke-linecap='round'/>"
    t += f"<path d='M{xs:.1f},{ys:.1f} A{r},{r} 0 {large_fg} 1 {xe:.1f},{ye:.1f}' fill='none' stroke='{col}' stroke-width='12' stroke-linecap='round'/>"
    t += f"<text x='{cx}' y='{cy+8}' text-anchor='middle' {FONT} font-size='34' font-weight='bold' fill='{col}'>{score}</text>"
    t += f"<text x='{cx}' y='{cy+26}' text-anchor='middle' {FONT} font-size='10' fill='{GREY}'>/ 100</text>"
    return t


def card(x, y, w, h, fill="#fff", stroke="#e5e7eb"):
    return f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='12' fill='{fill}' stroke='{stroke}'/>"


def screen_analyze():
    c = []
    c.append(f"<text x='24' y='118' {FONT} font-size='12' fill='{GREY}'>Contenu analyse :</text>")
    c.append(card(20, 126, 320, 70))
    c.append(f"<text x='32' y='150' {FONT} font-size='11' fill='{INK}'>URGENT: votre compte PayPal a ete</text>")
    c.append(f"<text x='32' y='166' {FONT} font-size='11' fill='{INK}'>suspendu. Verifiez ici:</text>")
    c.append(f"<text x='32' y='182' {FONT} font-size='11' fill='{BLUE}'>http://paypa1-secure.xyz/login</text>")
    c.append(card(20, 208, 320, 380, "#fdecec", "#f3c0c0"))
    c.append(gauge(180, 300, 62, 97, RED))
    c.append(f"<text x='180' y='392' text-anchor='middle' {FONT} font-size='20' font-weight='bold' fill='{RED}'>Dangereux</text>")
    c.append(f"<text x='40' y='424' {FONT} font-size='12' font-weight='bold' fill='{INK}'>Pourquoi ce verdict :</text>")
    reasons = ["Ton d'urgence / pression temporelle",
               "Demande d'identifiants",
               "URL a risque : extension suspecte (.xyz),",
               "mot-cle sensible, absence de HTTPS"]
    yy = 446
    for r in reasons:
        c.append(f"<text x='40' y='{yy}' {FONT} font-size='11' fill='{INK}'>&#8226; {r}</text>")
        yy += 22
    c.append(card(20, 548, 320, 40, BLUE, BLUE))
    c.append(f"<text x='180' y='573' text-anchor='middle' {FONT} font-size='13' font-weight='bold' fill='#fff'>Analyser</text>")
    return phone("".join(c), "Analyse manuelle")


def screen_sms():
    c = []
    rows = [
        (RED, "Votre colis est bloque, payez 1,99e:", "Dangereux  91/100"),
        (RED, "URGENT compte suspendu verifiez ici", "Dangereux  88/100"),
        (ORANGE, "Vous avez un nouveau message vocal", "Suspect  52/100"),
        (GREEN, "Rdv confirme demain 14h cabinet", "Sur  12/100"),
        (GREEN, "Code 4821 - votre livraison arrive", "Sur  21/100"),
        (ORANGE, "Promo -50% cliquez maintenant", "Suspect  61/100"),
    ]
    y = 110
    for col, body, verdict in rows:
        c.append(card(20, y, 320, 70))
        c.append(f"<circle cx='40' cy='{y+24}' r='7' fill='{col}'/>")
        c.append(f"<text x='58' y='{y+28}' {FONT} font-size='11.5' fill='{INK}'>{body}</text>")
        c.append(f"<text x='58' y='{y+50}' {FONT} font-size='11' font-weight='bold' fill='{col}'>{verdict}</text>")
        y += 82
    return phone("".join(c), "SMS recents")


def screen_demo():
    c = []
    c.append(f"<text x='24' y='116' {FONT} font-size='11.5' fill='{GREY}'>Touchez un exemple pour le tester :</text>")
    ex = [
        ("Compte bancaire suspendu, confirmez vos", "identifiants : cihbank-login.online/verify"),
        ("You won a 500 EUR gift card! Claim within", "24h : http://192.168.43.12/claim"),
        ("(AR) Compte suspendu, verifiez votre", "identite : secure-verify.xyz/login"),
        ("Salut, tu es dispo pour dejeuner demain", "a midi ?"),
        ("Colis La Poste en attente, reglez 1,99e :", "laposte-colis.info/pay"),
    ]
    y = 130
    for a, b in ex:
        c.append(card(20, y, 320, 64))
        c.append(f"<text x='34' y='{y+26}' {FONT} font-size='11' fill='{INK}'>{a}</text>")
        c.append(f"<text x='34' y='{y+46}' {FONT} font-size='11' fill='{BLUE}'>{b}</text>")
        y += 76
    return phone("".join(c), "Mode demo (attaque)")


def screen_history():
    c = []
    c.append(card(20, 110, 154, 84))
    c.append(f"<text x='38' y='150' {FONT} font-size='30' font-weight='bold' fill='{NAVY}'>147</text>")
    c.append(f"<text x='38' y='174' {FONT} font-size='12' fill='{GREY}'>Analyses</text>")
    c.append(card(186, 110, 154, 84))
    c.append(f"<text x='204' y='150' {FONT} font-size='30' font-weight='bold' fill='{RED}'>23</text>")
    c.append(f"<text x='204' y='174' {FONT} font-size='12' fill='{GREY}'>Menaces</text>")
    rows = [
        (RED, "Dangereux", "91/100", "paypa1-secure.xyz...", "29/05 21:14"),
        (GREEN, "Sur", "12/100", "Rdv confirme demain...", "29/05 19:02"),
        (ORANGE, "Suspect", "58/100", "Promo -50% cliquez...", "29/05 17:47"),
        (RED, "Dangereux", "84/100", "192.168.43.12/claim", "28/05 12:30"),
        (GREEN, "Sur", "19/100", "Code 4821 livraison", "28/05 09:15"),
    ]
    y = 208
    for col, v, sc, body, date in rows:
        c.append(card(20, y, 320, 72))
        c.append(f"<text x='34' y='{y+26}' {FONT} font-size='12.5' font-weight='bold' fill='{col}'>{v}</text>")
        c.append(f"<text x='306' y='{y+26}' text-anchor='end' {FONT} font-size='12' font-weight='bold' fill='{INK}'>{sc}</text>")
        c.append(f"<text x='34' y='{y+46}' {FONT} font-size='11' fill='{INK}'>{body}</text>")
        c.append(f"<text x='34' y='{y+62}' {FONT} font-size='10' fill='{GREY}'>{date}</text>")
        y += 84
    return phone("".join(c), "Historique &amp; stats")


diagram_architecture()
diagram_topology()
diagram_training()
render(screen_analyze(), "screen_analyze.png", 420)
render(screen_sms(), "screen_sms.png", 420)
render(screen_demo(), "screen_demo.png", 420)
render(screen_history(), "screen_history.png", 420)
print("done")
