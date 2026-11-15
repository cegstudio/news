#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
controle_serie.py — cohérence d'une série (lookbook, catalogue, collection de bijoux).

Une image juste dans une série fausse est une image fausse : le client voit la planche, pas le fichier. Ce script
mesure chaque image puis compare ce qui doit rester constant d'une vue à l'autre : fond, neutres, exposition,
carnation, cadrage du produit, grain, et signale les images qui s'écartent du reste du lot.

Usage :
    python controle_serie.py dossier --genre packshot
    python controle_serie.py dossier --genre mode --reference image_validee.jpg

Sans --reference, la série est comparée à sa propre médiane. Avec, elle est comparée à l'image de référence.
Sorties : serie.md et serie.json dans <dossier>_serie/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import controle_retouche as cr  # noqa: E402

EXTENSIONS = {".tif", ".tiff", ".jpg", ".jpeg", ".png", ".psd", ".psb"}

# ce qui doit rester constant : (libellé, chemin dans les mesures, écart toléré « mineur », « majeur », unité)
CONSTANTES = [
    ("Fond L*", ("fond", "L"), 1.5, 3.0, ""),
    ("Fond a*", ("fond", "a"), 1.0, 2.0, ""),
    ("Fond b*", ("fond", "b"), 1.0, 2.0, ""),
    ("Neutres moyens a*", ("neutres", "moyens", "a"), 1.5, 3.0, ""),
    ("Neutres moyens b*", ("neutres", "moyens", "b"), 1.5, 3.0, ""),
    ("Luminosité médiane L*", ("tonalite", "L_median"), 4.0, 8.0, ""),
    ("Point blanc L*", ("tonalite", "L_p99_9"), 2.0, 4.0, ""),
    ("Point noir L*", ("tonalite", "L_p0_1"), 2.0, 4.0, ""),
    ("Chroma moyen", ("tonalite", "chroma_moyen"), 3.0, 6.0, ""),
    ("Peau L*", ("peau", "couleur", "L"), 4.0, 8.0, ""),
    ("Peau a*", ("peau", "couleur", "a"), 2.0, 4.0, ""),
    ("Peau b*", ("peau", "couleur", "b"), 2.0, 4.0, ""),
    ("Grain σ", ("grain", "sigma_pixel"), 0.6, 1.2, ""),
    ("Marge gauche", ("symetrie", "marges_pct", "gauche"), 2.0, 4.0, " %"),
    ("Marge droite", ("symetrie", "marges_pct", "droite"), 2.0, 4.0, " %"),
    ("Marge haute", ("symetrie", "marges_pct", "haut"), 2.0, 4.0, " %"),
    ("Marge basse", ("symetrie", "marges_pct", "bas"), 2.0, 4.0, " %"),
    ("Inclinaison", ("symetrie", "inclinaison_axe_deg"), 0.5, 1.2, "°"),
]


def lire(d, chemin):
    for c in chemin:
        if not isinstance(d, dict) or c not in d or d[c] is None:
            return None
        d = d[c]
    return float(d) if isinstance(d, (int, float)) else None


def main(argv=None):
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    p = argparse.ArgumentParser(description="Cohérence d'une série d'images.")
    p.add_argument("dossier")
    p.add_argument("--genre", default="auto", choices=cr.GENRES)
    p.add_argument("--reference", help="image validée à laquelle comparer toute la série")
    p.add_argument("--reperes", help="repères personnels (sortie de etalonner.py)")
    p.add_argument("--sortie")
    a = p.parse_args(argv)

    dossier = Path(a.dossier)
    fichiers = sorted(f for f in dossier.iterdir() if f.suffix.lower() in EXTENSIONS)
    if len(fichiers) < 2:
        raise SystemExit("Il faut au moins deux images pour parler de série.")
    sortie = Path(a.sortie) if a.sortie else dossier.with_name(dossier.name + "_serie")
    sortie.mkdir(parents=True, exist_ok=True)
    rep = json.loads(Path(a.reperes).read_text(encoding="utf-8")).get("reperes") if a.reperes else None

    def mesurer(f):
        return cr.analyser(f, genre=a.genre, reperes=rep, symetrie=True, sans_vues=True, sortie=sortie / "mesures" / f.stem)

    rapports = {}
    for f in fichiers:
        try:
            rapports[f.name] = mesurer(f)
            print(f"  mesuré : {f.name}")
        except SystemExit as e:
            print(f"  ignoré : {f.name} ({e})")
    ref = mesurer(Path(a.reference))["mesures"] if a.reference else None

    lignes, ecarts = [], []
    for libelle, chemin, mineur, majeur, unite in CONSTANTES:
        vals = {n: lire(r["mesures"], chemin) for n, r in rapports.items()}
        presents = {n: v for n, v in vals.items() if v is not None}
        if len(presents) < max(2, len(rapports) // 2):
            continue
        cible = lire(ref, chemin) if ref else None
        if cible is None:
            cible = float(np.median(list(presents.values())))
        etendue = max(presents.values()) - min(presents.values())
        lignes.append((libelle, cible, etendue, unite, presents))
        for n, v in presents.items():
            d = v - cible
            if abs(d) >= mineur:
                ecarts.append({"image": n, "constante": libelle, "valeur": round(v, 2), "cible": round(cible, 2),
                               "ecart": round(d, 2), "gravite": "majeur" if abs(d) >= majeur else "mineur", "unite": unite})

    # fond : l'écart de couleur complet compte plus que chaque axe
    fonds = {n: r["mesures"].get("fond") for n, r in rapports.items()}
    types = {n: f["type"] for n, f in fonds.items() if f}
    if types and len(set(types.values())) > 1:
        ecarts.append({"image": "série", "constante": "Type de fond", "valeur": None, "cible": None, "ecart": None,
                       "gravite": "majeur", "unite": "", "detail": ", ".join(f"{n} : {t}" for n, t in types.items())})
    profils = {n: (r["fichier"].get("profil") or "aucun") for n, r in rapports.items()}
    if len(set(profils.values())) > 1:
        ecarts.append({"image": "série", "constante": "Profil colorimétrique", "valeur": None, "cible": None, "ecart": None,
                       "gravite": "majeur", "unite": "", "detail": ", ".join(f"{n} : {t}" for n, t in profils.items())})
    tailles = {n: (r["fichier"]["largeur"], r["fichier"]["hauteur"]) for n, r in rapports.items()}
    if len(set(tailles.values())) > 1:
        ecarts.append({"image": "série", "constante": "Dimensions", "valeur": None, "cible": None, "ecart": None,
                       "gravite": "mineur", "unite": "", "detail": ", ".join(f"{n} : {t[0]}×{t[1]}" for n, t in tailles.items())})

    ecarts.sort(key=lambda e: (e["gravite"] != "majeur", e["image"]))
    L = [f"# Cohérence de la série — {dossier.name}", "",
         f"{len(rapports)} images, genre {a.genre}. Comparées à " + (f"la référence `{Path(a.reference).name}`." if ref else "la médiane de la série."), "",
         "## Images qui s'écartent", ""]
    if not ecarts:
        L.append("Aucun écart au-delà des tolérances. Reste à juger à l'œil, planche-contact à l'appui : la cohérence d'un regard ou d'un pli ne se mesure pas.")
    else:
        L += ["| Gravité | Image | Constante | Valeur | Cible | Écart |", "|---|---|---|---|---|---|"]
        for e in ecarts:
            if e.get("detail"):
                L.append(f"| {e['gravite']} | {e['image']} | {e['constante']} | {e['detail']} | — | — |")
            else:
                L.append(f"| {e['gravite']} | {e['image']} | {e['constante']} | {e['valeur']}{e['unite']} | {e['cible']}{e['unite']} | {e['ecart']:+}{e['unite']} |")
    L += ["", "## Constantes de la série", "", "| Constante | Cible | Étendue dans la série |", "|---|---|---|"]
    for libelle, cible, etendue, unite, _ in lignes:
        L.append(f"| {libelle} | {cible:.2f}{unite} | {etendue:.2f}{unite} |")
    L += ["", "## Alertes par image", ""]
    for n, r in rapports.items():
        graves = [x for x in r["alertes"] if x["gravite"] in ("majeur", "mineur")]
        L.append(f"- `{n}` : " + (", ".join(f"{x['code']} ({x['gravite']})" for x in graves) if graves else "rien à signaler"))
    L.append("")
    (sortie / "serie.md").write_text("\n".join(L), encoding="utf-8")
    (sortie / "serie.json").write_text(json.dumps({"ecarts": ecarts, "constantes": [
        {"constante": l, "cible": c, "etendue": e, "valeurs": v} for l, c, e, _, v in lignes]}, ensure_ascii=False, indent=2), encoding="utf-8")
    nb = sum(1 for e in ecarts if e["gravite"] == "majeur")
    print(f"\n{len(rapports)} images — {nb} écarts majeurs, {len(ecarts) - nb} mineurs. Rapport : {sortie / 'serie.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
