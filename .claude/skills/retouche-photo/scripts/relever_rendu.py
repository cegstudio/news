#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
relever_rendu.py — chiffre le rendu d'un lot d'images de référence (les visuels d'une maison, une campagne validée).

« Rendu Cartier » ou « comme la dernière campagne » ne sont des cibles qu'une fois mesurés. Ce script passe un dossier
de visuels de référence au banc et en tire un relevé : fond, points noir et blanc, neutres, grain, cadrage du sujet,
et, si des masques sont fournis, neutralité et étendue tonale du métal, teinte de l'or, densité du cadran…

Usage :
    python relever_rendu.py dossier_references --genre montre --sortie releve_maison
    python relever_rendu.py dossier_references --genre bijou --masques dossier_masques

Masques (facultatifs) : dans le dossier donné, un fichier par zone nommé <image>.<zone>.png, blanc sur la zone.
Exemple : pour bague01.jpg → bague01.or_blanc.png, bague01.pierre.png. Les noms de zone sont ceux du banc.

Sorties : releve.md (à lire) et releve.json (valeurs médianes, étendues, détail par image).
Dix à vingt images du même type (même angle, même usage) donnent un relevé exploitable ; mélanger packshots et
visuels de campagne ne donne qu'une moyenne sans signification.
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

# (libellé, chemin dans les mesures, unité)
MESURES = [
    ("Fond : L*", ("fond", "L"), ""),
    ("Fond : a*", ("fond", "a"), ""),
    ("Fond : b*", ("fond", "b"), ""),
    ("Fond : étendue de L* (uni ou dégradé)", ("fond", "etendue_L_p2_p98"), ""),
    ("Fond : part réellement à 255", ("fond", "blanc_pur_pct"), " %"),
    ("Fond : part de l'image", ("fond", "part_image_pct"), " %"),
    ("Point noir, L* p0,1", ("tonalite", "L_p0_1"), ""),
    ("Luminosité médiane, L*", ("tonalite", "L_median"), ""),
    ("Point blanc, L* p99,9", ("tonalite", "L_p99_9"), ""),
    ("Chroma moyen de l'image", ("tonalite", "chroma_moyen"), ""),
    ("Neutres des ombres : a*", ("neutres", "ombres", "a"), ""),
    ("Neutres des ombres : b*", ("neutres", "ombres", "b"), ""),
    ("Neutres des tons moyens : a*", ("neutres", "moyens", "a"), ""),
    ("Neutres des tons moyens : b*", ("neutres", "moyens", "b"), ""),
    ("Neutres des hautes lumières : a*", ("neutres", "hautes_lumieres", "a"), ""),
    ("Neutres des hautes lumières : b*", ("neutres", "hautes_lumieres", "b"), ""),
    ("Blanc brûlé sur le sujet", ("ecretage", "sujet_brule_pct"), " %"),
    ("Noir bouché sur le sujet", ("ecretage", "noir_bouche_pct"), " %"),
    ("Grain au pixel, σ", ("grain", "sigma_pixel"), ""),
    ("Dégradé lisse sans grain", ("banding", "degrades_sans_grain_pct"), " %"),
    ("Transition des contours francs", ("contours", "largeur_transition_px"), " px"),
    ("Sujet : symétrie gauche-droite de la silhouette", ("symetrie", "silhouette_symetrie_gauche_droite_pct"), " %"),
    ("Sujet : inclinaison de l'axe", ("symetrie", "inclinaison_axe_deg"), "°"),
    ("Sujet : centrage horizontal", ("symetrie", "centrage_horizontal_pct"), " %"),
    ("Sujet : centrage vertical", ("symetrie", "centrage_vertical_pct"), " %"),
    ("Marge gauche", ("symetrie", "marges_pct", "gauche"), " %"),
    ("Marge droite", ("symetrie", "marges_pct", "droite"), " %"),
    ("Marge haute", ("symetrie", "marges_pct", "haut"), " %"),
    ("Marge basse", ("symetrie", "marges_pct", "bas"), " %"),
    ("Peau : L*", ("peau", "couleur", "L"), ""),
    ("Peau : a*", ("peau", "couleur", "a"), ""),
    ("Peau : b*", ("peau", "couleur", "b"), ""),
    ("Peau : teinte", ("peau", "couleur", "teinte_deg"), "°"),
]
MESURES_MASQUE = [
    ("L* le plus sombre (p1)", "L_p1", ""),
    ("L* médian", "L_median", ""),
    ("L* le plus clair (p99)", "L_p99", ""),
    ("étendue de L*", "etendue_L", ""),
    ("a*", "a", ""),
    ("b*", "b", ""),
    ("chroma", "chroma_median", ""),
    ("teinte", "teinte_deg", "°"),
    ("blanc brûlé", "blanc_brule_pct", " %"),
]


def lire(d, chemin):
    for c in chemin:
        if not isinstance(d, dict) or c not in d or d[c] is None:
            return None
        d = d[c]
    return float(d) if isinstance(d, (int, float)) else None


def resume(vals: list[float]) -> dict:
    v = np.array(vals, dtype=float)
    return {"n": int(v.size), "mediane": round(float(np.median(v)), 2), "min": round(float(v.min()), 2), "max": round(float(v.max()), 2)}


def main(argv=None):
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    p = argparse.ArgumentParser(description="Chiffre le rendu d'un lot d'images de référence.")
    p.add_argument("dossier", help="dossier des images de référence, toutes du même type")
    p.add_argument("--genre", default="auto", choices=cr.GENRES)
    p.add_argument("--masques", help="dossier de masques nommés <image>.<zone>.png")
    p.add_argument("--sortie", help="dossier de sortie (défaut : <dossier>_releve)")
    a = p.parse_args(argv)

    dossier = Path(a.dossier)
    images = sorted(f for f in dossier.iterdir() if f.suffix.lower() in EXTENSIONS and f.stem.count(".") == 0)
    if not images:
        raise SystemExit(f"Aucune image dans {dossier}")
    sortie = Path(a.sortie) if a.sortie else dossier.with_name(dossier.name + "_releve")
    sortie.mkdir(parents=True, exist_ok=True)
    dm = Path(a.masques) if a.masques else None

    rapports = {}
    for f in images:
        masques = {}
        if dm:
            for m in sorted(dm.glob(f"{f.stem}.*.png")):
                masques[m.stem[len(f.stem) + 1:]] = str(m)
        try:
            rapports[f.name] = cr.analyser(f, genre=a.genre, masques=masques, symetrie=True, sans_vues=True,
                                           sortie=sortie / "mesures" / f.stem)
            print(f"  mesuré : {f.name}" + (f"  (masques : {', '.join(masques)})" if masques else ""))
        except SystemExit as e:
            print(f"  ignoré : {f.name} ({e})")
    if not rapports:
        raise SystemExit("Aucune image lisible.")

    lignes = []
    for libelle, chemin, unite in MESURES:
        vals = [v for v in (lire(r["mesures"], chemin) for r in rapports.values()) if v is not None]
        if len(vals) >= max(1, len(rapports) // 3):
            lignes.append({"mesure": libelle, "unite": unite, **resume(vals)})
    zones = sorted({z for r in rapports.values() for z in r["mesures"].get("masques", {})})
    lignes_zones = {}
    for z in zones:
        lignes_zones[z] = []
        for libelle, cle, unite in MESURES_MASQUE:
            vals = [v for v in (lire(r["mesures"], ("masques", z, cle)) for r in rapports.values()) if v is not None]
            if vals:
                lignes_zones[z].append({"mesure": libelle, "unite": unite, **resume(vals)})
    types_fond = sorted({r["mesures"]["fond"]["type"] for r in rapports.values() if "fond" in r["mesures"]})
    formats = sorted({f"{r['fichier']['largeur']}×{r['fichier']['hauteur']}" for r in rapports.values()})
    profils = sorted({r["fichier"].get("profil") or "aucun" for r in rapports.values()})

    L = [f"# Relevé de rendu — {dossier.name}", "",
         f"{len(rapports)} images, genre {a.genre}. Fond : {', '.join(types_fond) or 'non détecté'}. "
         f"Profils : {', '.join(profils)}. Dimensions : {', '.join(formats[:6])}{'…' if len(formats) > 6 else ''}.", "",
         "Une étendue étroite (minimum et maximum proches) signale une constante de la maison : c'est une cible. "
         "Une étendue large signale une variable, qu'il ne faut pas copier à la médiane.", "",
         "## Image entière", "", "| Mesure | Médiane | Minimum | Maximum | Images |", "|---|---|---|---|---|"]
    for x in lignes:
        L.append(f"| {x['mesure']} | {x['mediane']}{x['unite']} | {x['min']}{x['unite']} | {x['max']}{x['unite']} | {x['n']} |")
    for z, ls in lignes_zones.items():
        L += ["", f"## Zone « {z} »", "", "| Mesure | Médiane | Minimum | Maximum | Images |", "|---|---|---|---|---|"]
        for x in ls:
            L.append(f"| {x['mesure']} | {x['mediane']}{x['unite']} | {x['min']}{x['unite']} | {x['max']}{x['unite']} | {x['n']} |")
    if not zones:
        L += ["", "Aucun masque fourni : la neutralité et l'étendue tonale du métal, la teinte de l'or ou la densité du cadran "
              "ne sont pas relevées. Fournir des masques avec --masques pour les obtenir."]
    L += ["", "## Ce que ce relevé ne dit pas", "",
          "La forme des dégradés, le dessin des reflets, la nature de l'ombre, le traitement des arêtes : cela se lit sur les "
          "images, pas dans un tableau. Le relevé donne les valeurs à atteindre, pas la manière.", ""]
    (sortie / "releve.md").write_text("\n".join(L), encoding="utf-8")
    (sortie / "releve.json").write_text(json.dumps({
        "dossier": str(dossier), "genre": a.genre, "images": list(rapports),
        "image_entiere": lignes, "zones": lignes_zones,
        "detail": {n: r["mesures"] for n, r in rapports.items()}}, ensure_ascii=False, indent=2, default=cr._json), encoding="utf-8")
    print(f"\n{len(rapports)} images. Relevé : {sortie / 'releve.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
