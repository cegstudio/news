#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
etalonner.py — tire des repères personnels d'un lot d'images que tu as validées.

Les seuils par défaut de controle_retouche.py sont des points de départ. Ton goût, ta lumière et tes clients
fixent les vrais : ce script mesure un dossier de finals validés (avec leurs originaux si tu les as) et en
déduit les bornes au-delà desquelles une image sort de TA pratique.

Usage :
    python etalonner.py dossier_finals --avant dossier_originaux --genre beaute --sortie reperes_beaute.json
    python controle_retouche.py nouvelle_image.tif --avant original.tif --reperes reperes_beaute.json

Les originaux sont appariés par nom de fichier (sans l'extension, sans les suffixes courants : _final, _retouche,
-edit, _v2…). Un fichier de repères par type d'image : la beauté, le packshot bijou et le lookbook n'ont pas les mêmes.
Il faut au moins 8 images pour que les bornes aient un sens ; 20 à 30, c'est bien.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import controle_retouche as cr  # noqa: E402

EXTENSIONS = {".tif", ".tiff", ".jpg", ".jpeg", ".png", ".psd", ".psb"}
SUFFIXES = re.compile(r"([_\- ](final|finale|retouche|retouch|retouched|edit|web|hd|bd|v\d+|\d{1,2}))+$", re.I)


def cle(nom: str) -> str:
    return SUFFIXES.sub("", Path(nom).stem).lower()


def lire(d, *chemin):
    for c in chemin:
        if not isinstance(d, dict) or c not in d or d[c] is None:
            return None
        d = d[c]
    return d if isinstance(d, (int, float)) else None


# repère → où lire la valeur dans les mesures
EXTRACTEURS = {
    "sujet_brule_pct": lambda m: lire(m, "ecretage", "sujet_brule_pct"),
    "canal_brule_pct": lambda m: lire(m, "ecretage", "canal_brule_pct"),
    "noir_bouche_pct": lambda m: lire(m, "ecretage", "noir_bouche_pct"),
    "fond_chroma": lambda m: lire(m, "fond", "chroma"),
    "fond_etendue_L": lambda m: lire(m, "fond", "etendue_L_p2_p98"),
    "banding_pct": lambda m: lire(m, "banding", "marches_franches_pct"),
    "halo_ratio": lambda m: lire(m, "contours", "depassement_median"),
    "peau_retention_pores": lambda m: lire(m, "peau", "avant_apres", "conserve", "pores"),
    "peau_retention_pores_haut": lambda m: lire(m, "peau", "avant_apres", "conserve", "pores"),
    "peau_modele_ratio": lambda m: lire(m, "peau", "avant_apres", "conserve", "modele"),
    "peau_zones_lissees_pct": lambda m: lire(m, "peau", "texture", "zones_lissees_pct"),
    "peau_taches_couleur": lambda m: lire(m, "peau", "couleur", "taches_couleur"),
    "peau_chroma": lambda m: lire(m, "peau", "couleur", "chroma"),
    "peau_visage_corps_dE": lambda m: lire(m, "peau", "couleur", "visage_contre_corps", "ecart_couleur_ab"),
    "peau_brulee_pct": lambda m: lire(m, "peau", "peau_canal_sature_pct"),
    "deformation_pct_diag": lambda m: lire(m, "avant_apres", "deformation", "deplacement_p99_pct_diagonale"),
    "poussieres_par_mpx": lambda m: lire(m, "poussieres", "candidats_par_mpx_lisse"),
}
# repères qu'on ne déduit pas d'un lot : ils tiennent au fichier, pas au goût
FIXES = {"fond_blanc_pur_pct", "peigne_pct", "blocs_jpeg", "grain_ecart", "neutres_chroma", "metal_chroma", "metal_etendue_L"}


def bornes(valeurs: np.ndarray, inverse: bool, defaut: dict) -> dict:
    """mineur = limite de ce que tu valides d'habitude ; majeur = nettement au-delà."""
    if inverse:
        p10, p50 = np.percentile(valeurs, [10, 50])
        mineur = float(p10)
        majeur = float(p10 - max(0.6 * (p50 - p10), 0.08 * abs(p10)))
    else:
        p50, p90 = np.percentile(valeurs, [50, 90])
        # plancher : un lot très propre ne doit pas rendre le contrôle hystérique (quart du repère par défaut au minimum)
        mineur = max(float(p90), 0.25 * defaut["mineur"])
        majeur = max(float(mineur + max(0.8 * (p90 - p50), 0.25 * abs(mineur))), 0.25 * defaut["majeur"])
    if abs(mineur - majeur) < 1e-9:   # lot sans dispersion : on garde l'écart relatif du repère par défaut
        ratio = defaut["majeur"] / defaut["mineur"] if defaut["mineur"] else 2.0
        majeur = mineur * ratio if mineur else defaut["majeur"]
    return {"mineur": round(mineur, 4), "majeur": round(majeur, 4)}


def main(argv=None):
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    p = argparse.ArgumentParser(description="Déduit des repères personnels d'un lot d'images validées.")
    p.add_argument("finals", help="dossier des images validées")
    p.add_argument("--avant", help="dossier des originaux (appariés par nom)")
    p.add_argument("--genre", default="auto", choices=cr.GENRES)
    p.add_argument("--sortie", default="reperes_perso.json")
    a = p.parse_args(argv)

    finals = sorted(f for f in Path(a.finals).iterdir() if f.suffix.lower() in EXTENSIONS)
    if not finals:
        raise SystemExit(f"Aucune image dans {a.finals}")
    originaux = {}
    if a.avant:
        originaux = {cle(f.name): f for f in Path(a.avant).iterdir() if f.suffix.lower() in EXTENSIONS}

    lignes, apparies = [], 0
    for f in finals:
        av = originaux.get(cle(f.name))
        apparies += av is not None
        try:
            r = cr.analyser(f, av, a.genre, sans_vues=True, sortie=Path(a.sortie).with_suffix("") / f.stem)
        except SystemExit as e:
            print(f"  ignoré : {f.name} ({e})")
            continue
        lignes.append(r["mesures"])
        print(f"  mesuré : {f.name}" + (f"  (original : {av.name})" if av else ""))

    n = len(lignes)
    if n < 8:
        print(f"Attention : {n} images seulement. En dessous de 8, les bornes ne veulent pas dire grand-chose.")
    reperes, detail = {}, {}
    for k, ext in EXTRACTEURS.items():
        vals = np.array([v for v in (ext(m) for m in lignes) if v is not None], dtype=float)
        if vals.size < max(4, min(8, n)):
            continue
        inv = k in cr.SENS_INVERSE
        reperes[k] = bornes(vals, inv, cr.REPERES[k])
        detail[k] = {"n": int(vals.size), "min": round(float(vals.min()), 4), "mediane": round(float(np.median(vals)), 4),
                     "max": round(float(vals.max()), 4), "defaut": cr.REPERES[k], "sens": "plancher" if inv else "plafond"}
    sortie = {
        "date": datetime.date.today().isoformat(),
        "genre": a.genre,
        "images": n,
        "images_avec_original": apparies,
        "note": "Repères tirés d'images validées. À refaire quand le style ou le type de commande change.",
        "reperes": reperes,
        "detail": detail,
        "non_etalonnes": sorted(set(cr.REPERES) - set(reperes)),
    }
    Path(a.sortie).write_text(json.dumps(sortie, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{n} images mesurées ({apparies} avec original). Repères personnels : {a.sortie}")
    print(f"{'repère':<28}{'défaut':>16}{'toi':>16}   médiane du lot")
    for k, v in reperes.items():
        d = cr.REPERES[k]
        print(f"{k:<28}{str(d['mineur']) + ' / ' + str(d['majeur']):>16}{str(v['mineur']) + ' / ' + str(v['majeur']):>16}   {detail[k]['mediane']}")
    if sortie["non_etalonnes"]:
        print("Restent sur leur valeur par défaut : " + ", ".join(sortie["non_etalonnes"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
