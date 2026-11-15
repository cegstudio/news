#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
controle_retouche.py — banc de contrôle d'une retouche photo.

Reproduit hors Photoshop les calques de contrôle d'un retoucheur (solarisation,
luminance contrastée, saturation, teinte, passe-haut, écrêtage, fond) et y ajoute
des mesures chiffrées (texture de peau conservée, dominante sur les neutres,
banding, halos, poussières, déformation avant/après…). Découpe aussi l'image en
tuiles à 100 % : un relecteur qui ne voit qu'une vignette ne voit rien.

Usage minimal :
    python controle_retouche.py final.tif
Avec l'original, pour mesurer ce que la retouche a changé :
    python controle_retouche.py final.tif --avant original.tif --genre beaute
Avec des masques nommés (blanc = zone), par exemple exportés de Photoshop :
    python controle_retouche.py bague.tif --genre bijou --masque metal=m_metal.png --masque pierre=m_pierre.png

Sorties (dossier <final>_controle/ par défaut) :
    rapport.md, rapport.json, vues/*.jpg, tuiles/*.png

Dépendances : numpy, pillow, opencv-python-headless. Optionnel : tifffile, psd-tools.
Les seuils sont des repères par défaut (dictionnaire REPERES) ; ils se remplacent
par un fichier produit par etalonner.py à partir de tes propres images validées.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageFont, ImageOps

Image.MAX_IMAGE_PIXELS = None  # fichiers de 100 Mpx et plus : pas une attaque, un moyen format
try:  # OpenCV 5 bavarde sur stderr à chaque détection de visage
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
except Exception:
    pass

ICI = Path(__file__).resolve().parent
MODELE_VISAGE = ICI.parent / "assets" / "face_detection_yunet_2023mar.onnx"

VUE_MAX = 1568       # plus grand côté des vues d'ensemble (au-delà, un modèle de vision réduit l'image)
REDUIT_MAX = 1600    # plus grand côté de l'image de travail pour les statistiques de couleur
GENRES = ("auto", "beaute", "portrait", "mode", "bijou", "montre", "packshot", "general")
GENRES_PEAU = ("beaute", "portrait", "mode")
GENRES_PRODUIT = ("bijou", "montre", "packshot")

# --------------------------------------------------------------------------- #
# Repères par défaut. « mineur » = perfectible, « majeur » = visible par un œil pro.
# Ce sont des points de départ raisonnables, pas des vérités : etalonner.py les
# remplace par des bornes tirées de tes propres images validées.
# --------------------------------------------------------------------------- #
REPERES = {
    "sujet_brule_pct": {"mineur": 0.05, "majeur": 0.5},        # tous canaux au maximum, hors fond
    "canal_brule_pct": {"mineur": 1.0, "majeur": 4.0},         # au moins un canal au maximum, hors fond
    "noir_bouche_pct": {"mineur": 1.0, "majeur": 6.0},         # tous canaux à zéro
    "neutres_chroma": {"mineur": 3.0, "majeur": 6.0},          # C*ab moyen des quasi-neutres, par bande
    "fond_chroma": {"mineur": 1.5, "majeur": 3.5},             # fond censé être neutre
    "fond_etendue_L": {"mineur": 4.0, "majeur": 9.0},          # étendue L* p2–p98 d'un fond censé être uni
    "fond_blanc_pur_pct": {"mineur": 99.0, "majeur": 90.0},    # part du fond blanc réellement à 255 (sens inverse)
    "banding_pct": {"mineur": 0.3, "majeur": 2.0},             # surface en marches d'escalier franches (2 niveaux et plus)
    "peigne_pct": {"mineur": 8.0, "majeur": 25.0},             # trous dans l'histogramme
    "halo_ratio": {"mineur": 0.07, "majeur": 0.14},            # dépassement médian aux contours francs
    "blocs_jpeg": {"mineur": 1.15, "majeur": 1.35},            # contraste aux frontières de blocs 8×8
    "peau_retention_pores": {"mineur": 0.80, "majeur": 0.60},  # texture fine conservée (sens inverse)
    "peau_retention_pores_haut": {"mineur": 1.25, "majeur": 1.6},  # texture fine gonflée (accentuation, grain ajouté)
    "peau_modele_ratio": {"mineur": 0.45, "majeur": 0.30},     # modelé conservé (sens inverse) : en dessous, aplat
    "peau_zones_lissees_pct": {"mineur": 6.0, "majeur": 18.0}, # blocs de peau nettement plus lisses que la médiane
    "peau_taches_couleur": {"mineur": 2.6, "majeur": 4.0},     # variation a*b* à l'échelle des plaques, dégradé anatomique retiré
    "peau_chroma": {"mineur": 34.0, "majeur": 42.0},           # C* médian (peau orange au-delà)
    "peau_visage_corps_dE": {"mineur": 5.0, "majeur": 9.0},    # écart de couleur a*b* visage / reste de la peau, à luminosité égale
    "peau_brulee_pct": {"mineur": 0.3, "majeur": 2.0},         # peau avec un canal au maximum
    "grain_ecart": {"mineur": 1.8, "majeur": 3.0},             # peau n fois plus lisse au pixel que le reste de l'image
    "deformation_pct_diag": {"mineur": 0.25, "majeur": 0.8},   # déplacement p99 en % de la diagonale
    "metal_chroma": {"mineur": 3.5, "majeur": 7.0},            # métal blanc censé être neutre
    "metal_etendue_L": {"mineur": 50.0, "majeur": 35.0},       # étendue L* p1–p99 d'un métal (sens inverse) : en dessous, métal plat
    "poussieres_par_mpx": {"mineur": 4.0, "majeur": 20.0},     # candidats par mégapixel de surface lisse
}
SENS_INVERSE = {"fond_blanc_pur_pct", "peau_retention_pores", "peau_modele_ratio", "metal_etendue_L"}
# Repères qui dépendent du goût, de la carnation ou de la lumière : tant qu'ils n'ont pas été étalonnés sur des images
# validées, leur gravité descend d'un cran (majeur → mineur, mineur → info). Les autres tiennent à la physique du fichier.
REPERES_SOUPLES = {"peau_taches_couleur", "peau_visage_corps_dE", "peau_chroma", "peau_zones_lissees_pct",
                   "fond_etendue_L", "metal_etendue_L", "peau_modele_ratio"}


# --------------------------------------------------------------------------- #
# Lecture
# --------------------------------------------------------------------------- #
def _profondeur(im: Image.Image, chemin: Path) -> int:
    """Profondeur par canal telle qu'écrite dans le fichier (Pillow réduit le 16 bits RVB sans le dire)."""
    try:
        if im.format == "TIFF":
            bps = im.tag_v2.get(258)
            if bps:
                return int(max(bps) if isinstance(bps, (tuple, list)) else bps)
        if im.format == "PNG":
            with open(chemin, "rb") as f:
                tete = f.read(26)
            return int(tete[24])
    except Exception:
        pass
    return 16 if im.mode.startswith("I;16") or im.mode == "I" else 8


def _qualite_jpeg(im: Image.Image):
    """Estimation de la qualité JPEG d'après la table de quantification de la luminance."""
    try:
        q = im.quantization[0]
        moy = float(np.mean(list(q)))
        # relation approchée avec la table standard de l'IJG (moyenne ≈ 57,6 à qualité 50)
        s = moy / 57.625 * 100.0
        return int(round(max(1, min(100, (200 - s) / 2 if s <= 100 else 5000 / s))))
    except Exception:
        return None


def _vers_srgb(image, icc: bytes | None):
    """Convertit vers sRGB si un autre profil est incorporé.

    `image` est un tableau RVB 8 bits ou une image Pillow (CMJN compris).
    Retourne (tableau sRGB, nom du profil, converti ?, part des pixels hors gamut sRGB en %).
    """
    pil = image if isinstance(image, Image.Image) else Image.fromarray(image)
    rgb = lambda: np.asarray(pil.convert("RGB")).copy()  # noqa: E731
    if not icc:
        return rgb(), None, False, None
    try:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        nom = (ImageCms.getProfileDescription(src) or "").strip() or "profil sans nom"
        if "srgb" in nom.lower() and pil.mode == "RGB":
            return rgb(), nom, False, None
        dst = ImageCms.createProfile("sRGB")
        intent = ImageCms.Intent.RELATIVE_COLORIMETRIC
        out = ImageCms.profileToProfile(pil, src, dst, renderingIntent=intent, outputMode="RGB")
        hors = None
        if pil.mode == "RGB":
            # aller-retour : une couleur que le sRGB contient revient à sa valeur ; une couleur hors gamut, non
            retour = ImageCms.profileToProfile(out, dst, src, renderingIntent=intent, outputMode="RGB")
            a, b = np.asarray(pil).astype(np.int16), np.asarray(retour).astype(np.int16)
            ecart = np.abs(a - b).max(axis=2)
            hors = round(float(((ecart > 8) & (a.max(axis=2) > 12)).mean()) * 100, 3)
        return np.asarray(out).copy(), nom, True, hors
    except Exception as e:  # profil illisible : on analyse tel quel et on le dit
        return rgb(), f"profil illisible ({e})", False, None


def charger(chemin: str | Path) -> dict:
    """Lit une image. Retourne natif (uint8/uint16 RVB, valeurs du fichier), srgb8 (uint8 sRGB) et infos."""
    chemin = Path(chemin)
    if not chemin.exists():
        raise SystemExit(f"Fichier introuvable : {chemin}")
    ext = chemin.suffix.lower()
    infos = {"chemin": str(chemin), "nom": chemin.name, "octets": chemin.stat().st_size, "remarques": []}

    if ext in (".cr2", ".cr3", ".nef", ".arw", ".raf", ".dng", ".orf", ".rw2", ".iiq", ".3fr"):
        raise SystemExit("RAW non pris en charge : exporte un TIFF 16 bits (ou un JPEG) depuis ton dérawtiseur.")

    if ext in (".psd", ".psb"):
        try:
            from psd_tools import PSDImage
        except ImportError:
            raise SystemExit("PSD/PSB : installe psd-tools (pip install psd-tools) ou exporte un TIFF aplati.")
        psd = PSDImage.open(chemin)
        pil = psd.topil() or psd.composite()
        icc = pil.info.get("icc_profile")
        infos.update(format="PSD", bits=int(psd.depth), mode=pil.mode)
        if psd.depth > 8:
            infos["remarques"].append("PSD 16/32 bits lu en 8 bits : pour le banding, exporte un TIFF 16 bits aplati.")
        rgb8 = np.asarray(pil.convert("RGB"))
        natif = rgb8
    else:
        with Image.open(chemin) as im:
            icc = im.info.get("icc_profile")
            bits = _profondeur(im, chemin)
            dpi = im.info.get("dpi")
            infos.update(format=im.format, bits=bits, mode=im.mode,
                         dpi=[float(dpi[0]), float(dpi[1])] if dpi else None)
            if im.format == "JPEG":
                infos["qualite_jpeg_estimee"] = _qualite_jpeg(im)
                try:
                    from PIL import JpegImagePlugin
                    infos["sous_echantillonnage"] = {0: "4:4:4", 1: "4:2:2", 2: "4:2:0"}.get(JpegImagePlugin.get_sampling(im), "?")
                except Exception:
                    pass
            natif = None
            if bits > 8 and im.mode not in ("CMYK",):
                brut = np.fromfile(str(chemin), dtype=np.uint8)
                arr = cv2.imdecode(brut, cv2.IMREAD_UNCHANGED)
                if arr is None or arr.dtype != np.uint16:
                    try:
                        import tifffile
                        arr = tifffile.imread(str(chemin))
                        if arr.ndim == 3 and arr.shape[2] >= 3:
                            arr = arr[:, :, [2, 1, 0] + list(range(3, arr.shape[2]))]  # RVB → BVR, comme OpenCV
                    except Exception:
                        arr = None
                if arr is not None and arr.dtype == np.uint16:
                    if arr.ndim == 2:
                        arr = np.stack([arr] * 3, axis=-1)
                    if arr.shape[2] == 4:
                        infos["alpha"] = True
                        arr = arr[:, :, :3]
                    natif = np.ascontiguousarray(arr[:, :, ::-1])  # BVR → RVB
                else:
                    infos["remarques"].append("Fichier 16 bits lu en 8 bits (décodeur indisponible) : installe tifffile.")
                    infos["bits_lus"] = 8
            if natif is None:
                im2 = ImageOps.exif_transpose(im)
                if im2.mode in ("RGBA", "LA", "PA") or (im2.mode == "P" and "transparency" in im2.info):
                    infos["alpha"] = True
                    im2 = im2.convert("RGBA")
                    infos["_alpha"] = np.asarray(im2.split()[-1]).copy()
                    blanc = Image.new("RGBA", im2.size, (255, 255, 255, 255))
                    im2 = Image.alpha_composite(blanc, im2).convert("RGB")
                    infos["remarques"].append("Transparence aplatie sur blanc pour l'analyse.")
                if im2.mode == "CMYK":
                    infos["remarques"].append("Fichier CMJN : converti en sRGB pour l'analyse, les mesures d'écrêtage ne valent que pour cette conversion.")
                    encre = np.asarray(im2).astype(np.uint16).sum(axis=2) / 255.0 * 100.0
                    infos["encrage_total_max_pct"] = round(float(encre.max()), 1)
                    infos["encrage_total_p99_9_pct"] = round(float(np.percentile(encre[::2, ::2], 99.9)), 1)
                    rgb8, nom, _, _ = _vers_srgb(im2, icc)
                    infos["profil"] = nom
                    return _finir(chemin, infos, rgb8, rgb8, deja_srgb=True)
                if im2.mode != "RGB":
                    if im2.mode in ("L", "I;16", "I", "F"):
                        infos["niveaux_de_gris"] = True
                    im2 = im2.convert("RGB")
                natif = np.asarray(im2).copy()

    if natif.dtype == np.uint16:
        rgb8 = np.round(natif / 257.0).astype(np.uint8)
    else:
        rgb8 = natif
    return _finir(chemin, infos, natif, rgb8, icc=icc)


def _finir(chemin, infos, natif, rgb8, icc=None, deja_srgb=False):
    if not deja_srgb:
        srgb8, nom, converti, hors = _vers_srgb(rgb8, icc)
        infos["profil"] = nom
        infos["converti_vers_srgb"] = converti
        if hors is not None:
            infos["hors_gamut_srgb_pct"] = hors
    else:
        srgb8 = rgb8
    h, w = srgb8.shape[:2]
    infos.update(largeur=w, hauteur=h, megapixels=round(w * h / 1e6, 2))
    alpha = infos.pop("_alpha", None)
    return {"natif": natif, "srgb8": np.ascontiguousarray(srgb8), "infos": infos, "alpha": alpha}


def charger_masque(chemin: str | Path, forme) -> np.ndarray:
    """Masque binaire à la taille de l'image (blanc = zone)."""
    with Image.open(chemin) as im:
        if im.mode in ("RGBA", "LA"):
            m = np.asarray(im.split()[-1]) if np.asarray(im.split()[-1]).min() < 250 else np.asarray(im.convert("L"))
        else:
            m = np.asarray(im.convert("L"))
    if m.shape[:2] != tuple(forme[:2]):
        m = cv2.resize(m, (forme[1], forme[0]), interpolation=cv2.INTER_LINEAR)
    return m >= 128


# --------------------------------------------------------------------------- #
# Outils
# --------------------------------------------------------------------------- #
def reduire(img: np.ndarray, cote_max: int, interp=cv2.INTER_AREA) -> np.ndarray:
    h, w = img.shape[:2]
    f = cote_max / max(h, w)
    if f >= 1:
        return img
    return cv2.resize(img, (max(1, round(w * f)), max(1, round(h * f))), interpolation=interp)


def luma(rgb8: np.ndarray) -> np.ndarray:
    """Luminance encodée (0–255, float32)."""
    return (rgb8[..., 0] * 0.2126 + rgb8[..., 1] * 0.7152 + rgb8[..., 2] * 0.0722).astype(np.float32)


def vers_lab(rgb8: np.ndarray) -> np.ndarray:
    """CIELAB (L 0–100, a, b en unités réelles) depuis du sRGB 8 bits."""
    return cv2.cvtColor(rgb8.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)


def flou(img: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0.01:
        return img
    return cv2.GaussianBlur(img, (0, 0), sigmaX=float(sigma), sigmaY=float(sigma), borderType=cv2.BORDER_REFLECT)


def mad(v: np.ndarray) -> float:
    """Écart absolu médian, mis à l'échelle d'un écart-type. Insensible aux valeurs aberrantes."""
    if v.size == 0:
        return float("nan")
    med = np.median(v)
    return float(np.median(np.abs(v - med)) * 1.4826)


def teinte_deg(a, b):
    return (np.degrees(np.arctan2(b, a)) + 360.0) % 360.0


def nom_direction(a: float, b: float) -> str:
    """Nomme la direction d'une dominante dans le plan a*b*."""
    if math.hypot(a, b) < 0.8:
        return "neutre"
    h = (math.degrees(math.atan2(b, a)) + 360) % 360
    noms = [(20, "magenta-rouge"), (65, "rouge-orangé"), (110, "jaune"), (160, "jaune-vert"), (200, "vert"),
            (250, "cyan"), (300, "bleu"), (340, "violet-magenta"), (361, "magenta-rouge")]
    for borne, nom in noms:
        if h < borne:
            return nom
    return "?"


class Grille:
    """Quadrillage de l'image en cellules de `taille` px, nommées A1, B1… (colonne lettre, ligne chiffre)."""

    def __init__(self, largeur: int, hauteur: int, taille: int):
        self.w, self.h, self.t = largeur, hauteur, taille
        self.nc = max(1, math.ceil(largeur / taille))
        self.nl = max(1, math.ceil(hauteur / taille))

    @staticmethod
    def _lettres(c: int) -> str:
        s = ""
        while True:
            s = chr(65 + c % 26) + s
            c = c // 26 - 1
            if c < 0:
                return s

    def nom(self, c: int, l: int) -> str:
        return f"{self._lettres(c)}{l + 1}"

    def boite(self, c: int, l: int):
        x0, y0 = c * self.t, l * self.t
        return x0, y0, min(self.w, x0 + self.t), min(self.h, y0 + self.t)

    def depuis_nom(self, nom: str):
        nom = nom.strip().upper()
        i = 0
        while i < len(nom) and nom[i].isalpha():
            i += 1
        if i == 0 or i == len(nom) or not nom[i:].isdigit():
            raise ValueError(f"Nom de cellule invalide : {nom}")
        c = 0
        for ch in nom[:i]:
            c = c * 26 + (ord(ch) - 64)
        c -= 1
        l = int(nom[i:]) - 1
        if not (0 <= c < self.nc and 0 <= l < self.nl):
            raise ValueError(f"Cellule hors image : {nom} (grille {self._lettres(self.nc - 1)}{self.nl})")
        return c, l

    def par_cellule(self, carte: np.ndarray) -> np.ndarray:
        """Moyenne d'une carte (à n'importe quelle échelle) dans chaque cellule → tableau (lignes, colonnes)."""
        hh, ww = carte.shape[:2]
        ys = (np.arange(hh) + 0.5) * (self.h / hh) // self.t
        xs = (np.arange(ww) + 0.5) * (self.w / ww) // self.t
        idx = (np.clip(ys, 0, self.nl - 1)[:, None] * self.nc + np.clip(xs, 0, self.nc - 1)[None, :]).astype(np.int64)
        somme = np.bincount(idx.ravel(), weights=carte.astype(np.float64).ravel(), minlength=self.nl * self.nc)
        compte = np.bincount(idx.ravel(), minlength=self.nl * self.nc)
        return (somme / np.maximum(compte, 1)).reshape(self.nl, self.nc)

    def cellules_fortes(self, carte: np.ndarray, seuil: float, n: int = 6) -> list[str]:
        """Noms des cellules où la moyenne de la carte dépasse `seuil`, les plus fortes d'abord."""
        m = self.par_cellule(carte)
        ordre = np.argsort(m.ravel())[::-1]
        out = []
        for i in ordre[:n]:
            if m.ravel()[i] > seuil:
                out.append(self.nom(int(i % self.nc), int(i // self.nc)))
        return out


class Alertes:
    def __init__(self, reperes: dict, etalonnes: set | None = None):
        self.r = reperes
        self.etalonnes = etalonnes or set()
        self.liste: list[dict] = []

    def ajouter(self, code, gravite, message, zone=None, valeur=None, repere=None):
        self.liste.append({"code": code, "gravite": gravite, "message": message,
                           "zone": zone, "valeur": valeur, "repere": repere})

    def seuil(self, cle, valeur, code, message, zone=None, unite=""):
        """Compare une valeur à son repère et ajoute l'alerte si elle le franchit. Retourne la gravité ou None."""
        if valeur is None or (isinstance(valeur, float) and math.isnan(valeur)):
            return None
        s = self.r.get(cle)
        if not s:
            return None
        inv = cle in SENS_INVERSE
        grav = None
        if (valeur <= s["majeur"]) if inv else (valeur >= s["majeur"]):
            grav = "majeur"
        elif (valeur <= s["mineur"]) if inv else (valeur >= s["mineur"]):
            grav = "mineur"
        if grav:
            signe = "≥" if inv else "≤"
            repere = f"{signe} {s['mineur']}{unite}"
            if cle in REPERES_SOUPLES and cle not in self.etalonnes:
                grav = "mineur" if grav == "majeur" else "info"
                repere += " (repère par défaut, non étalonné)"
            self.ajouter(code, grav, message, zone, round(float(valeur), 3), repere)
        return grav


# --------------------------------------------------------------------------- #
# Mesures générales
# --------------------------------------------------------------------------- #
def mesurer_ecretage(natif: np.ndarray, grille: Grille, fond: np.ndarray | None, al: Alertes, genre: str) -> tuple[dict, dict]:
    maxv = 65535 if natif.dtype == np.uint16 else 255
    haut = maxv - (1 if maxv == 255 else 260)
    bas = 1 if maxv == 255 else 260
    tout_haut = np.all(natif >= haut, axis=2)
    un_haut = np.any(natif >= haut, axis=2)
    tout_bas = np.all(natif <= bas, axis=2)
    un_bas = np.any(natif <= bas, axis=2)
    sujet = np.ones(natif.shape[:2], bool) if fond is None else ~fond
    n_sujet = max(1, int(sujet.sum()))
    brule_sujet = tout_haut & sujet
    canal_sujet = un_haut & sujet & ~tout_haut
    m = {
        "blanc_brule_pct_image": round(float(tout_haut.mean()) * 100, 3),
        "sujet_brule_pct": round(float(brule_sujet.sum()) / n_sujet * 100, 3),
        "canal_brule_pct": round(float(canal_sujet.sum()) / n_sujet * 100, 3),
        "noir_bouche_pct": round(float((tout_bas & sujet).sum()) / n_sujet * 100, 3),
        "canal_bouche_pct": round(float((un_bas & sujet & ~tout_bas).sum()) / n_sujet * 100, 3),
    }
    # plus grande plage brûlée d'un seul tenant, hors fond
    petit = reduire(brule_sujet.astype(np.uint8) * 255, REDUIT_MAX, cv2.INTER_AREA) > 127
    if petit.any():
        n, _, stats, cent = cv2.connectedComponentsWithStats(petit.astype(np.uint8), connectivity=8)
        if n > 1:
            i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            m["plus_grande_plage_brulee_pct"] = round(float(stats[i, cv2.CC_STAT_AREA]) / petit.size * 100, 3)
    zones_b = grille.cellules_fortes(brule_sujet.astype(np.float32), 0.01)
    zones_c = grille.cellules_fortes(canal_sujet.astype(np.float32), 0.03)
    zones_n = grille.cellules_fortes((tout_bas & sujet).astype(np.float32), 0.05)
    produit = genre in GENRES_PRODUIT
    al.seuil("sujet_brule_pct", m["sujet_brule_pct"], "BLANC_BRULE",
             "Hautes lumières brûlées sur le sujet (plus aucune matière)." +
             (" Sur du métal ou une pierre, un spéculaire ponctuel est normal : c'est une plage étendue qui pose problème." if produit else ""),
             ", ".join(zones_b) or None, " %")
    al.seuil("canal_brule_pct", m["canal_brule_pct"], "CANAL_BRULE",
             "Un canal est saturé sur le sujet : couleur qui s'aplatit (peau qui vire, rouge ou jaune sans modelé).",
             ", ".join(zones_c) or None, " %")
    al.seuil("noir_bouche_pct", m["noir_bouche_pct"], "NOIR_BOUCHE",
             "Noirs bouchés sur le sujet : vérifier qu'il n'y avait pas de matière à garder (tissu noir, cheveux, cadran).",
             ", ".join(zones_n) or None, " %")
    cartes = {"tout_haut": tout_haut, "un_haut": un_haut, "tout_bas": tout_bas, "un_bas": un_bas}
    return m, cartes


def mesurer_tonalite(lab: np.ndarray, al: Alertes) -> dict:
    L = lab[..., 0]
    p = np.percentile(L, [0.1, 1, 50, 99, 99.9])
    m = {"L_p0_1": round(float(p[0]), 1), "L_p1": round(float(p[1]), 1), "L_median": round(float(p[2]), 1),
         "L_p99": round(float(p[3]), 1), "L_p99_9": round(float(p[4]), 1),
         "chroma_moyen": round(float(np.hypot(lab[..., 1], lab[..., 2]).mean()), 1)}
    if p[0] > 9:
        al.ajouter("NOIRS_DECOLLES", "info", "Point noir relevé (noirs voilés). Voulu si c'est un parti pris mat ; sinon l'image manque d'assise.",
                   valeur=m["L_p0_1"], repere="L* p0,1 ≤ 9")
    if p[4] < 88:
        al.ajouter("BLANCS_ETEINTS", "info", "Point blanc bas : aucun vrai blanc dans l'image. Voulu en low-key ; sinon image terne.",
                   valeur=m["L_p99_9"], repere="L* p99,9 ≥ 88")
    return m


NOMS_BANDES = {"ombres": "ombres", "moyens": "tons moyens", "hautes_lumieres": "hautes lumières"}


def mesurer_neutres(lab: np.ndarray, al: Alertes, exclure: np.ndarray | None = None, produit: bool = False) -> dict:
    """Dominante portée par les pixels quasi neutres, par bande de luminosité.

    Sur un produit, un neutre doit être neutre : c'est une alerte. Sur un portrait ou une image de mode, un
    étalonnage teinté est un choix : la mesure est donnée pour information.
    """
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.hypot(a, b)
    base = (C < 12) & (L > 3) & (L < 98.5)
    if exclure is not None:
        base &= ~exclure
    bandes = {"ombres": (L < 35), "moyens": (L >= 35) & (L < 70), "hautes_lumieres": (L >= 70)}
    out = {}
    for nom, mb in bandes.items():
        mm = base & mb
        part = float(mm.mean()) * 100
        if part < 0.5:
            out[nom] = {"part_pct": round(part, 2)}
            continue
        am, bm = float(a[mm].mean()), float(b[mm].mean())
        c = math.hypot(am, bm)
        out[nom] = {"part_pct": round(part, 2), "a": round(am, 2), "b": round(bm, 2),
                    "chroma": round(c, 2), "direction": nom_direction(am, bm)}
        texte = (f"Les neutres des {NOMS_BANDES[nom]} tirent vers le {nom_direction(am, bm)} (a* {am:+.1f}, b* {bm:+.1f}). "
                 "À confirmer sur une zone réellement neutre : un décor chaud ou froid donne le même signal.")
        if produit:
            al.seuil("neutres_chroma", c, "DOMINANTE_NEUTRES", texte)
        elif c >= al.r["neutres_chroma"]["mineur"]:
            al.ajouter("DOMINANTE_NEUTRES", "info", texte + " Sans objet si l'étalonnage est voulu.",
                       valeur=round(c, 2), repere=f"≤ {al.r['neutres_chroma']['mineur']}")
    valides = [v for v in out.values() if "chroma" in v]
    if len(valides) >= 2:
        o, h = out["ombres"], out["hautes_lumieres"]
        if "chroma" in o and "chroma" in h:
            ecart = math.hypot(o["a"] - h["a"], o["b"] - h["b"])
            out["ecart_ombres_hautes"] = round(ecart, 2)
            if ecart > 5:
                al.ajouter("DOMINANTE_CROISEE", "info",
                           f"Ombres ({o['direction']}) et hautes lumières ({h['direction']}) ne tirent pas dans le même sens. "
                           "Voulu si c'est un virage partiel ; sinon, courbe par canal à reprendre.",
                           valeur=round(ecart, 2), repere="écart a*b* ≤ 5")
    return out


def detecter_fond(rgb_r: np.ndarray, lab_r: np.ndarray) -> np.ndarray | None:
    """Masque du fond uni ou en dégradé doux, par remplissage depuis les bords. None si le pourtour n'est pas un fond."""
    h, w = rgb_r.shape[:2]
    e = max(2, round(0.025 * min(h, w)))
    bord = np.zeros((h, w), bool)
    bord[:e], bord[-e:], bord[:, :e], bord[:, -e:] = True, True, True, True
    Lb = lab_r[..., 0][bord]
    # le pourtour doit être lisse à petite échelle (un dégradé est permis, une texture non)
    y = luma(rgb_r)
    rugosite = np.abs(y - flou(y, 3))[bord]
    if np.percentile(rugosite, 90) > 2.5:
        return None
    lisse = cv2.GaussianBlur(rgb_r, (0, 0), 1.2)
    masque = np.zeros((h + 2, w + 2), np.uint8)
    pas = max(4, min(h, w) // 60)
    graines = [(x, 0) for x in range(0, w, pas)] + [(x, h - 1) for x in range(0, w, pas)] + \
              [(0, yy) for yy in range(0, h, pas)] + [(w - 1, yy) for yy in range(0, h, pas)]
    tol = (2, 2, 2)
    for gx, gy in graines:
        if masque[gy + 1, gx + 1]:
            continue
        cv2.floodFill(lisse, masque, (gx, gy), 0, tol, tol, flags=4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8))
    fond = masque[1:-1, 1:-1] > 0
    # garde-fou : un produit clair sur fond clair se raccorde au fond par ses ombres douces. On ne garde que ce qui
    # reste dans la plage de couleur du pourtour, puis ce qui touche encore le bord.
    L, a, b = lab_r[..., 0], lab_r[..., 1], lab_r[..., 2]
    lo, hi = np.percentile(Lb, [1, 99])
    am, bm = float(np.median(a[bord])), float(np.median(b[bord]))
    fond &= (L >= lo - 2.5) & (L <= hi + 2.5) & (np.abs(a - am) < 4) & (np.abs(b - bm) < 4)
    n, comp = cv2.connectedComponents(fond.astype(np.uint8), connectivity=4)
    if n > 1:
        touche = np.unique(np.concatenate([comp[0], comp[-1], comp[:, 0], comp[:, -1]]))
        fond = np.isin(comp, touche[touche > 0])
    part = float(fond.mean())
    if part < 0.08 or part > 0.985:
        return None
    # la part du pourtour couverte doit être élevée, sinon ce n'est pas un fond mais un bout de décor
    if float(fond[bord].mean()) < 0.6:
        return None
    return fond


def mesurer_fond(fond_r: np.ndarray, lab_r: np.ndarray, srgb8: np.ndarray, al: Alertes, genre: str) -> dict:
    L, a, b = lab_r[..., 0][fond_r], lab_r[..., 1][fond_r], lab_r[..., 2][fond_r]
    Lm, am, bm = float(np.median(L)), float(np.median(a)), float(np.median(b))
    p2, p98 = np.percentile(L, [2, 98])
    typ = "blanc" if Lm > 93 else "noir" if Lm < 10 else "gris" if math.hypot(am, bm) < 5 else "couleur"
    m = {"part_image_pct": round(float(fond_r.mean()) * 100, 1), "type": typ,
         "L": round(Lm, 1), "a": round(am, 2), "b": round(bm, 2), "chroma": round(math.hypot(am, bm), 2),
         "etendue_L_p2_p98": round(float(p98 - p2), 2)}
    if typ in ("blanc", "noir", "gris"):
        al.seuil("fond_chroma", m["chroma"], "FOND_TEINTE",
                 f"Fond {typ} pas neutre : tire vers le {nom_direction(am, bm)} (a* {am:+.1f}, b* {bm:+.1f}).")
    if typ == "blanc":
        grand = cv2.resize(fond_r.astype(np.uint8), (srgb8.shape[1], srgb8.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
        grand = cv2.erode(grand.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0  # on se tient à l'écart du contour
        if grand.any():
            pur = float(np.all(srgb8[grand] == 255, axis=1).mean()) * 100
            m["blanc_pur_pct"] = round(pur, 2)
            if pur < 99.0:
                texte = (f"Le fond est un blanc à L* {Lm:.1f}, à 255 sur {pur:.0f} % seulement de sa surface. Sans conséquence pour un "
                         "blanc cassé voulu ; bloquant pour une place de marché qui exige du blanc pur, et visible sur une page blanche.")
                if genre in GENRES_PRODUIT:
                    al.seuil("fond_blanc_pur_pct", pur, "FOND_BLANC_PAS_PUR", texte, unite=" %")
                else:
                    al.ajouter("FOND_BLANC_PAS_PUR", "info", texte, valeur=round(pur, 2), repere="≥ 99 %")
    if typ != "couleur" or genre in GENRES_PRODUIT:
        al.seuil("fond_etendue_L", m["etendue_L_p2_p98"], "FOND_INEGAL",
                 "Le fond varie en luminosité. Normal pour un dégradé voulu ; sinon fond sale ou vignetage à égaliser (voir la vue du fond).")
    return m


def _escaliers_lignes(img8: np.ndarray, pas: int, lmin: int = 16):
    """Paliers en marches d'escalier, ligne par ligne.

    Retourne (pixels en marches de 2 niveaux et plus, pixels en marches de 1 niveau, total, carte des marches franches).
    Une marche de 1 niveau est la quantification normale d'un dégradé 8 bits sans grain : invisible sur un bon écran,
    mais fragile. À partir de 2 niveaux, la marche se voit.
    """
    H, W = img8.shape
    total = franc = latent = 0
    carte = np.zeros((H // pas + 1, W), np.uint8)
    for k, r in enumerate(range(0, H, pas)):
        ligne = img8[r].astype(np.int16)
        d = np.flatnonzero(np.diff(ligne))
        total += W
        if d.size == 0 or d.size > W // 3:
            continue  # ligne constante (aplat) ou très texturée : rien à chercher
        debuts = np.concatenate(([0], d + 1))
        fins = np.concatenate((d, [W - 1]))
        longs = fins - debuts + 1
        vals = ligne[debuts]
        base = (longs >= lmin) & (vals > 2) & (vals < 253)
        # on ne regarde que les paliers longs, et on accepte entre deux paliers voisins quelques
        # pixels de transition : un vrai banding passé par un rééchantillonnage ou un JPEG n'a pas des marches nettes
        idx = np.flatnonzero(longs >= lmin)
        m2 = np.zeros(len(vals), bool)
        m1 = np.zeros(len(vals), bool)
        if idx.size >= 2:
            ecart = debuts[idx[1:]] - fins[idx[:-1]] - 1
            saut = np.abs(vals[idx[1:]] - vals[idx[:-1]])
            proche = ecart <= 4
            franc_ = proche & (saut >= 2) & (saut <= 6)
            doux_ = proche & (saut == 1)
            m2[idx[:-1][franc_]] = True
            m2[idx[1:][franc_]] = True
            m1[idx[:-1][doux_]] = True
            m1[idx[1:][doux_]] = True
        m2 &= base
        m1 &= base & ~m2
        if m2.any():
            franc += int(longs[m2].sum())
            for s_, f_ in zip(debuts[m2], fins[m2]):
                carte[k, s_:f_ + 1] = 1
        if m1.any():
            latent += int(longs[m1].sum())
    return franc, latent, total, carte


def mesurer_banding(srgb8: np.ndarray, natif: np.ndarray, grille: Grille, al: Alertes) -> tuple[dict, np.ndarray]:
    """Postérisation : paliers en marches d'escalier dans les dégradés, et histogramme en peigne."""
    # canal par canal : une courbe forte postérise chaque canal à des endroits différents, et la luminance, qui les
    # mélange, ne montre plus que des marches courtes. Un filtre médian 3×3 retire le bruit de ±1 niveau du JPEG
    # sans toucher aux marches.
    pas = max(2, srgb8.shape[0] // 1200)
    pas2 = max(2, srgb8.shape[1] // 1200)
    franc = latent = 0.0
    carte = np.zeros((400, 400), np.float32)
    for c in range(3):
        canal = cv2.medianBlur(np.ascontiguousarray(srgb8[..., c]), 3)
        f1, l1, t1, c1 = _escaliers_lignes(canal, pas)
        f2, l2, t2, c2 = _escaliers_lignes(np.ascontiguousarray(canal.T), pas2)
        franc = max(franc, 100.0 * (f1 + f2) / max(1, t1 + t2))
        latent = max(latent, 100.0 * (l1 + l2) / max(1, t1 + t2))
        carte = np.maximum(carte, np.maximum(cv2.resize(c1, (400, 400), interpolation=cv2.INTER_AREA),
                                             cv2.resize(np.ascontiguousarray(c2.T), (400, 400), interpolation=cv2.INTER_AREA)).astype(np.float32))
    m = {"marches_franches_pct": round(franc, 3), "degrades_sans_grain_pct": round(latent, 2)}
    # histogramme en peigne, par canal, sur la plage occupée
    trous = []
    for c in range(3):
        hist = np.bincount(srgb8[..., c].ravel(), minlength=256).astype(np.float64)
        occ = np.flatnonzero(hist > hist.sum() * 1e-5)
        if occ.size < 20:
            continue
        lo, hi = occ[0] + 2, occ[-1] - 2
        if hi - lo < 16:
            continue
        lis = np.convolve(hist, np.ones(7) / 7.0, mode="same")
        seg = slice(lo, hi + 1)
        trous.append(float(np.mean((hist[seg] < 0.3 * lis[seg]) & (lis[seg] > hist.sum() * 2e-5))) * 100)
    m["histogramme_trous_pct"] = round(max(trous), 2) if trous else 0.0
    if natif.dtype == np.uint16:
        sous = natif[::7, ::7, 1]
        m["niveaux_distincts_canal_vert"] = int(np.unique(sous).size)
        if m["niveaux_distincts_canal_vert"] <= 300:
            al.ajouter("FAUX_16_BITS", "mineur",
                       "Fichier 16 bits qui ne contient que quelques centaines de niveaux : il vient d'un 8 bits. "
                       "Aucune marge pour les dégradés ; repartir du RAW si une reprise de tonalité est prévue.",
                       valeur=m["niveaux_distincts_canal_vert"], repere="> 300 niveaux")
    zones = grille.cellules_fortes(carte, 0.05)
    al.seuil("banding_pct", franc, "BANDING",
             "Dégradés en marches d'escalier visibles (postérisation). Fréquent sur fond de studio, ciel, reflet de métal poli : "
             "retravailler en 16 bits et finir par un grain léger avant l'export 8 bits.",
             ", ".join(zones) or None, " %")
    if latent >= 8.0 and franc < al.r["banding_pct"]["mineur"]:
        al.ajouter("DEGRADE_SANS_GRAIN", "info",
                   f"{latent:.0f} % de l'image est un dégradé parfaitement lisse, sans grain. Rien de visible en l'état, "
                   "mais la moindre recompression (réseau social, place de marché) ou un écran médiocre y fera apparaître des bandes. "
                   "Un grain fin (1 à 2 %) avant l'export 8 bits l'en protège.",
                   valeur=round(latent, 1), repere="< 8 %")
    al.seuil("peigne_pct", m["histogramme_trous_pct"], "HISTOGRAMME_PEIGNE",
             "Histogramme en peigne : la tonalité a été étirée sur trop peu de niveaux (réglage fort appliqué en 8 bits).", unite=" %")
    return m, carte


def mesurer_bruit(y: np.ndarray, lab_L_plein: np.ndarray | None = None) -> tuple[float, np.ndarray, np.ndarray]:
    """Grain au pixel (méthode d'Immerkær). Retourne (sigma, carte |laplacien|, masque des zones sans contour).

    Les zones « calmes » sont choisies sur l'image lissée, donc sur sa structure et non sur son grain, et le grain de
    l'image est la médiane de ce qu'on mesure bloc par bloc : sinon une plage floutée par la retouche passe pour la
    zone de référence et le grain est sous-estimé.
    """
    noyau = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], np.float32)
    lap = np.abs(cv2.filter2D(y, cv2.CV_32F, noyau, borderType=cv2.BORDER_REFLECT))
    yl = flou(y, 3.0)
    mag = np.hypot(cv2.Sobel(yl, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(yl, cv2.CV_32F, 0, 1, ksize=3))
    calme = mag <= np.percentile(mag[::4, ::4], 50)
    sig, _, ok = grain_par_blocs(lap, calme, y)
    return (float(np.median(sig[ok])) if ok.sum() >= 8 else float("nan")), lap, calme


def grain_par_blocs(lap: np.ndarray, masque: np.ndarray, y: np.ndarray, bloc: int = 64):
    """Grain mesuré bloc par bloc dans un masque. Retourne (sigma par bloc, luminance par bloc, blocs valides)."""
    h, w = lap.shape
    taille = (max(1, w // bloc), max(1, h // bloc))
    m = masque.astype(np.float32)
    num = cv2.resize(lap * m, taille, interpolation=cv2.INTER_AREA)
    den = cv2.resize(m, taille, interpolation=cv2.INTER_AREA)
    sig = math.sqrt(math.pi / 2) * num / np.maximum(den, 1e-3) / 6.0
    return sig, cv2.resize(y, taille, interpolation=cv2.INTER_AREA), den > 0.5


def mesurer_halos(y: np.ndarray, al: Alertes, graine: int = 7) -> dict:
    """Dépassement de part et d'autre des contours francs : signature d'une accentuation trop forte ou d'un détourage frangé."""
    yb = flou(y, 0.8)
    gx = cv2.Sobel(yb, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(yb, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.hypot(gx, gy)
    h, w = y.shape
    marge = 16
    zone = mag[marge:-marge, marge:-marge]
    if zone.size == 0:
        return {}
    seuil = max(60.0, float(np.percentile(zone[::3, ::3], 99.5)))
    ys, xs = np.nonzero(zone >= seuil)
    if ys.size < 200:
        return {"contours_mesures": int(ys.size)}
    rng = np.random.default_rng(graine)
    sel = rng.choice(ys.size, size=min(4000, ys.size), replace=False)
    ys, xs = ys[sel] + marge, xs[sel] + marge
    nx, ny = gx[ys, xs] / mag[ys, xs], gy[ys, xs] / mag[ys, xs]
    t = np.arange(-12, 13, dtype=np.float32)
    mx = (xs[:, None] + t[None, :] * nx[:, None]).astype(np.float32)
    my = (ys[:, None] + t[None, :] * ny[:, None]).astype(np.float32)
    # profils pris sur l'image à peine débruitée : le grain ne doit ni fabriquer ni masquer un liseré
    prof = cv2.remap(yb, mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)  # N × 25, du sombre vers le clair
    bas, haut = prof[:, :4], prof[:, -4:]
    pb, ph = np.median(bas, axis=1), np.median(haut, axis=1)
    hauteur = ph - pb
    propre = (hauteur > 40) & (bas.std(axis=1) < 0.10 * hauteur) & (haut.std(axis=1) < 0.10 * hauteur)
    if propre.sum() < 60:
        return {"contours_mesures": int(propre.sum())}
    p, hh, pb, ph = prof[propre], hauteur[propre], pb[propre], ph[propre]
    sur = (p[:, 12:].max(axis=1) - ph) / hh
    sous = (pb - p[:, :13].min(axis=1)) / hh
    ratio = float(np.median((np.clip(sur, 0, None) + np.clip(sous, 0, None)) / 2))
    # largeur de transition 10–90 %
    norm = (p - pb[:, None]) / hh[:, None]
    larg = ((norm > 0.1) & (norm < 0.9)).sum(axis=1)
    m = {"contours_mesures": int(propre.sum()), "depassement_median": round(ratio, 3),
         "largeur_transition_px": round(float(np.median(larg)), 1)}
    al.seuil("halo_ratio", ratio, "HALOS",
             "Liseré clair/sombre le long des contours francs : accentuation trop forte ou à trop grand rayon, "
             "ou frange de détourage. À regarder à 100 % sur les bords du sujet.")
    return m


def mesurer_blocs_jpeg(y: np.ndarray, al: Alertes, qualite: int | None = None) -> dict:
    dh = np.abs(np.diff(y, axis=1))
    dv = np.abs(np.diff(y, axis=0))
    cols = np.arange(dh.shape[1]) % 8 == 7
    ligs = np.arange(dv.shape[0]) % 8 == 7
    rh = float(dh[:, cols].mean() / max(1e-6, dh[:, ~cols].mean()))
    rv = float(dv[ligs].mean() / max(1e-6, dv[~ligs].mean()))
    r = (rh + rv) / 2
    if qualite is None or qualite < 90:   # sur un fichier peu compressé, un dégradé très lisse suffit à fausser le rapport
        al.seuil("blocs_jpeg", r, "BLOCS_JPEG",
                 "Blocs de compression visibles : le fichier a été enregistré en JPEG trop compressé (ou plusieurs fois).")
    return {"contraste_frontieres_blocs": round(r, 3)}


def detecter_poussieres(y: np.ndarray, sigma_bruit: float, exclure: np.ndarray | None, grille: Grille, al: Alertes,
                        genre: str) -> tuple[dict, list]:
    """Candidats poussière / point / pétouille : petites taches isolées sur une surface lisse.

    L'écart de chaque tache est rapporté au grain qui l'entoure : sur une image très grainée, le grain lui-même
    ne doit pas compter pour de la poussière.
    """
    sig = sigma_bruit if sigma_bruit == sigma_bruit else 1.0
    yl = flou(y, 0.8)
    med = cv2.medianBlur(np.clip(yl, 0, 255).astype(np.uint8), 15).astype(np.float32)
    res = yl - med
    local = np.sqrt(np.maximum(cv2.boxFilter(res * res, cv2.CV_32F, (41, 41), borderType=cv2.BORDER_REFLECT), 0))
    # surface lisse : faible rugosité autour du point. La médiane se prend sur une fenêtre assez large (41 px) pour
    # qu'une poussière, qui perturbe l'image sur une dizaine de pixels autour d'elle, ne rende pas « rugueuse » la
    # surface sur laquelle elle est posée, tout en laissant rugueux un tissu à motif ou une chevelure.
    rr = np.clip(np.abs(y - flou(y, 4)) * 8, 0, 255).astype(np.uint8)
    rug = cv2.medianBlur(rr, 41).astype(np.float32) / 8.0
    lisse = rug < max(1.2, 2.5 * sig)
    if exclure is not None:
        lisse &= ~exclure
    cand = (np.abs(res) > np.maximum(4.0, 5.0 * local + 1.0)) & lisse & (y > 6)   # un point blanc sur fond clair compte aussi
    n, lab, stats, cent = cv2.connectedComponentsWithStats(cand.astype(np.uint8), connectivity=8)
    points = []
    for i in range(1, n):
        aire = stats[i, cv2.CC_STAT_AREA]
        ww, hh = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        if 3 <= aire <= 400 and max(ww, hh) <= 40 and aire >= 0.3 * ww * hh:
            points.append((float(cent[i, 0]), float(cent[i, 1]), int(max(ww, hh))))
    mpx_lisse = max(0.05, float(lisse.sum()) / 1e6)
    densite = len(points) / mpx_lisse
    m = {"candidats": len(points), "surface_lisse_mpx": round(mpx_lisse, 2), "candidats_par_mpx_lisse": round(densite, 1)}
    if points:
        carte = np.zeros((grille.nl, grille.nc), np.int32)
        for x, yy, _ in points:
            carte[min(grille.nl - 1, int(yy // grille.t)), min(grille.nc - 1, int(x // grille.t))] += 1
        ordre = np.argsort(carte.ravel())[::-1][:6]
        zones = [f"{grille.nom(int(i % grille.nc), int(i // grille.nc))} ({carte.ravel()[i]})" for i in ordre if carte.ravel()[i] > 0]
        m["cellules"] = zones
        if genre in GENRES_PRODUIT or genre == "general":
            al.seuil("poussieres_par_mpx", densite, "POUSSIERES",
                     f"{len(points)} petites taches isolées sur les surfaces lisses (poussières, pétouilles, points de capteur). "
                     "Ce sont des candidats : un micro-reflet ou un détail gravé y figure aussi. Vérifier sur la vue dédiée.",
                     ", ".join(zones), " /Mpx")
    return m, points


# --------------------------------------------------------------------------- #
# Peau
# --------------------------------------------------------------------------- #
def detecter_visages(srgb8: np.ndarray) -> list[dict]:
    """Visages (boîte en pixels pleine résolution), du plus grand au plus petit. Liste vide si le modèle manque."""
    if not MODELE_VISAGE.exists() or not hasattr(cv2, "FaceDetectorYN"):
        return []
    visages = []
    try:
        for cote in (640, 1280):
            petit = reduire(srgb8, cote)
            f = srgb8.shape[1] / petit.shape[1]
            det = cv2.FaceDetectorYN.create(str(MODELE_VISAGE), "", (petit.shape[1], petit.shape[0]), 0.7, 0.3, 50)
            _, res = det.detect(cv2.cvtColor(petit, cv2.COLOR_RGB2BGR))
            if res is not None and len(res):
                for r in res:
                    x, y, w, h = [float(v) * f for v in r[:4]]
                    visages.append({"x": x, "y": y, "w": w, "h": h, "score": round(float(r[14]), 2)})
                break
    except Exception:
        return []
    visages.sort(key=lambda v: v["w"] * v["h"], reverse=True)
    return visages


def masque_peau(rgb_r: np.ndarray, visages_r: list[dict]) -> tuple[np.ndarray, str]:
    """Masque de peau à l'échelle réduite.

    Avec un visage, le modèle de couleur est appris sur ce visage : il suit la carnation réelle et l'étalonnage de
    l'image. Les cheveux et la barbe, proches en couleur, sont écartés par leur rugosité. Ce qui n'est pas relié au
    visage (mains, bras, mais aussi un décor chaud) n'est gardé que si sa couleur est très proche de celle du visage.
    Cela reste une approximation : la vue du masque permet d'en juger, et --masque peau=… la remplace.
    """
    ycc = cv2.cvtColor(rgb_r, cv2.COLOR_RGB2YCrCb).astype(np.float32)
    yv, cr, cb = ycc[..., 0], ycc[..., 1], ycc[..., 2]
    r, g, b = [rgb_r[..., i].astype(np.int16) for i in range(3)]
    large = (cr >= 133) & (cr <= 185) & (cb >= 75) & (cb <= 135) & (r > g) & (r > b)
    rug = flou(np.abs(yv - flou(yv, 1.5)), 4.0)
    methode = "plage générique (approximatif)"
    proche = large
    tres_proche = None
    coeur = None
    if visages_r:
        v = visages_r[0]
        x0, y0 = max(0, int(v["x"] + 0.2 * v["w"])), max(0, int(v["y"] + 0.15 * v["h"]))
        x1, y1 = int(v["x"] + 0.8 * v["w"]), int(v["y"] + 0.85 * v["h"])
        zone = np.zeros(large.shape, bool)
        zone[y0:y1, x0:x1] = True
        if zone.sum() > 400:
            # échantillon : cœur du visage, tons moyens (on écarte yeux, sourcils, narines, reflets)
            ech = zone & (yv > np.percentile(yv[zone], 25)) & (yv < np.percentile(yv[zone], 97))
            if ech.sum() > 200:
                pts = np.stack([cr[ech], cb[ech]], axis=1)
                centre = np.median(pts, axis=0)
                d0 = np.linalg.norm(pts - centre, axis=1)
                pts = pts[d0 <= np.percentile(d0, 80)]  # on resserre avant d'estimer la dispersion
                inv = np.linalg.inv(np.cov(pts.T) + np.eye(2) * 2.0)
                dx, dy = cr - centre[0], cb - centre[1]
                d2 = inv[0, 0] * dx * dx + 2 * inv[0, 1] * dx * dy + inv[1, 1] * dy * dy
                r0 = float(np.median(rug[ech]))
                lisse = rug < 2.2 * r0 + 1.0
                proche = (d2 < 10.0) & (yv > 12) & lisse
                tres_proche = (d2 < 4.5) & (yv > 12) & lisse
                # second modèle appris sous le menton : si le visage a été corrigé seul, le cou n'a plus sa
                # couleur, et c'est justement ce qu'on veut pouvoir mesurer
                cou = np.zeros(large.shape, bool)
                cou[int(v["y"] + 1.05 * v["h"]):int(v["y"] + 1.6 * v["h"]), int(v["x"] + 0.2 * v["w"]):int(v["x"] + 0.8 * v["w"])] = True
                ech2 = cou & large & lisse
                if ech2.sum() > 300:
                    pts2 = np.stack([cr[ech2], cb[ech2]], axis=1)
                    c2 = np.median(pts2, axis=0)
                if ech2.sum() > 300 and ech2.sum() > 0.08 * cou.sum() and np.linalg.norm(c2 - centre) < 24:
                    e2 = np.linalg.norm(pts2 - c2, axis=1)
                    pts2 = pts2[e2 <= np.percentile(e2, 80)]
                    inv2 = np.linalg.inv(np.cov(pts2.T) + np.eye(2) * 2.0)
                    ex, ey = cr - c2[0], cb - c2[1]
                    d2b = inv2[0, 0] * ex * ex + 2 * inv2[0, 1] * ex * ey + inv2[1, 1] * ey * ey
                    proche |= (d2b < 10.0) & (yv > 12) & lisse
                    tres_proche |= (d2b < 4.5) & (yv > 12) & lisse
                    zone = zone | ech2
                coeur = zone
                methode = "couleur apprise sur le visage"
    if coeur is not None:
        # couronne de cheveux : autour de l'ovale du visage (côtés et dessus), rien n'est de la peau, même si la
        # couleur colle — des cheveux châtains flous ont la couleur et la douceur d'une joue
        hh, ww = large.shape
        gy, gx = np.mgrid[0:hh, 0:ww].astype(np.float32)
        cx, cy = v["x"] + v["w"] / 2, v["y"] + v["h"] / 2
        ovale = ((gx - cx) / (0.54 * v["w"])) ** 2 + ((gy - cy) / (0.60 * v["h"])) ** 2 <= 1.0
        couronne = (gx > v["x"] - 0.7 * v["w"]) & (gx < v["x"] + 1.7 * v["w"]) & \
                   (gy > v["y"] - 0.7 * v["h"]) & (gy < v["y"] + 0.92 * v["h"]) & ~ovale
        proche &= ~couronne
        tres_proche &= ~couronne
        # sous le menton, seule la colonne du cou et du décolleté se propage librement
        colonne = (gx > v["x"] - 0.15 * v["w"]) & (gx < v["x"] + 1.15 * v["w"])
        proche &= ovale | colonne | tres_proche
    proche = cv2.morphologyEx(proche.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(proche, connectivity=8)
    masque = np.zeros(proche.shape, bool)
    if n > 1:
        mini = 0.003 * proche.size
        for i in range(1, n):
            if stats[i, cv2.CC_STAT_AREA] < mini:
                continue
            comp = lab == i
            if coeur is None or (comp & coeur).any():
                masque |= comp                       # relié au visage (ou pas de visage : on garde tout)
            else:
                masque |= comp & tres_proche         # ailleurs : seulement ce qui a vraiment la couleur du visage
    if coeur is not None:
        masque = cv2.morphologyEx(masque.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0
    return masque, methode


def echelles_texture(largeur_visage: float) -> tuple[float, float, float]:
    """Rayons (sigma, px) qui séparent grain, pores et modelé, proportionnels à la taille du visage dans l'image."""
    s1 = float(np.clip(largeur_visage / 1500.0, 0.6, 4.0))
    s2 = float(np.clip(largeur_visage / 400.0, 1.5, 12.0))
    s3 = float(np.clip(largeur_visage / 40.0, 8.0, 120.0))
    return s1, s2, s3


def bandes(y: np.ndarray, s1: float, s2: float, s3: float):
    g1, g2, g3 = flou(y, s1), flou(y, s2), flou(y, s3)
    return y - g1, g1 - g2, g2 - g3  # grain, pores, modelé


def mesurer_peau(ctx: dict, al: Alertes, largeur_visage_forcee: float | None) -> dict | None:
    srgb8, rgb_r, lab_r, grille = ctx["srgb8"], ctx["rgb_r"], ctx["lab_r"], ctx["grille"]
    f = srgb8.shape[1] / rgb_r.shape[1]
    visages = ctx["visages"]
    visages_r = [{k: (v[k] / f if k in "xywh" else v[k]) for k in v} for v in visages]
    if ctx.get("masque_peau_fourni") is not None:
        peau_r = cv2.resize(ctx["masque_peau_fourni"].astype(np.uint8), (rgb_r.shape[1], rgb_r.shape[0]),
                            interpolation=cv2.INTER_AREA) > 0
        methode = "masque fourni"
    else:
        peau_r, methode = masque_peau(rgb_r, visages_r)
    if ctx.get("fond_r") is not None:
        peau_r &= ~ctx["fond_r"]
    part = float(peau_r.mean()) * 100
    if part < 0.4:
        return None
    if largeur_visage_forcee:
        lv, origine = float(largeur_visage_forcee), "forcée"
    elif visages:
        lv, origine = float(visages[0]["w"]), "détectée"
    else:
        # pas de visage entier dans le cadre : gros plan beauté ou détail de corps
        lv, origine = float(max(srgb8.shape[:2])) * (0.9 if ctx["genre"] == "beaute" else 0.15), "supposée"
    s1, s2, s3 = echelles_texture(lv)
    m = {"methode_masque": methode, "part_image_pct": round(part, 1),
         "visages": len(visages), "largeur_visage_px": round(lv), "largeur_visage_origine": origine,
         "rayons_px": {"grain": round(s1, 2), "pores": round(s2, 2), "modele": round(s3, 1)}}
    if lv < 500:
        m["note"] = "Visage petit dans l'image : les pores ne sont pas résolus, la mesure de texture ne vaut que pour le grain."

    # ---- texture, en pleine résolution, dans la boîte englobante de la peau
    ys, xs = np.nonzero(peau_r)
    y0, y1 = int(ys.min() * f), min(srgb8.shape[0], int((ys.max() + 1) * f) + 1)
    x0, x1 = int(xs.min() * f), min(srgb8.shape[1], int((xs.max() + 1) * f) + 1)
    yb = luma(srgb8[y0:y1, x0:x1])
    mp = cv2.resize(peau_r.astype(np.uint8), (srgb8.shape[1], srgb8.shape[0]), interpolation=cv2.INTER_NEAREST)[y0:y1, x0:x1]
    k = max(3, int(round(s2 * 3)) | 1)
    mp = cv2.erode(mp, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0  # on s'écarte des bords et des traits
    if mp.sum() < 2000:
        m["texture"] = None
    else:
        grain, pores, modele = bandes(yb, s1, s2, s3)
        tex = {"grain": round(mad(grain[mp]), 3), "pores": round(mad(pores[mp]), 3), "modele": round(mad(modele[mp]), 3)}
        # uniformité locale de la texture fine : blocs de peau nettement plus lisses que la médiane
        B = int(np.clip(round(lv / 25), 24, 160))
        hh, ww = (yb.shape[0] // B) * B, (yb.shape[1] // B) * B
        zones_lisses, part_lisse, blocs_valides = [], 0.0, 0
        if hh >= B and ww >= B:
            e = np.abs(pores[:hh, :ww]).reshape(hh // B, B, ww // B, B).mean(axis=(1, 3))
            couv = mp[:hh, :ww].reshape(hh // B, B, ww // B, B).mean(axis=(1, 3))
            ok = couv > 0.85
            blocs_valides = int(ok.sum())
            if blocs_valides >= 12:
                ref = float(np.median(e[ok]))
                lisses = ok & (e < 0.45 * ref)
                part_lisse = float(lisses.sum()) / blocs_valides * 100
                carte = np.zeros(srgb8.shape[:2], np.float32)
                sous = cv2.resize(lisses.astype(np.float32), (ww, hh), interpolation=cv2.INTER_NEAREST)
                carte[y0:y0 + hh, x0:x0 + ww] = sous
                zones_lisses = grille.cellules_fortes(reduire(carte, REDUIT_MAX), 0.04)
                ctx["carte_peau_lisse"] = carte
        tex["blocs_analyses"] = blocs_valides
        tex["zones_lissees_pct"] = round(part_lisse, 1)
        m["texture"] = tex
        al.seuil("peau_zones_lissees_pct", part_lisse, "PEAU_LISSAGE_LOCAL",
                 "Des plages de peau sont nettement plus lisses que le reste : trace de flou local, de tampon étalé ou de correcteur. "
                 "La texture doit être continue d'une zone à l'autre.", ", ".join(zones_lisses) or None, " %")
        # grain de la peau contre grain du reste de l'image : blocs hors peau, sans contour, de luminosité comparable.
        # On prend le haut de la distribution (3e quartile) : le grain de l'image est celui des zones que la retouche
        # n'a pas touchées, et une plage floutée ailleurs ne doit pas servir d'étalon.
        peau_pleine = cv2.resize(cv2.dilate(peau_r.astype(np.uint8), np.ones((7, 7), np.uint8)),
                                 (srgb8.shape[1], srgb8.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
        y_plein = luma(srgb8)
        sig_b, lum_b, ok_b = grain_par_blocs(ctx["lap"], ctx["calme"] & ~peau_pleine, y_plein)
        lo, hi = np.percentile(yb[mp], [25, 75])
        comparables = ok_b & (lum_b >= lo - 12) & (lum_b <= hi + 12)
        if comparables.sum() < 12:
            comparables = ok_b
        s_reste = float(np.percentile(sig_b[comparables], 75)) if comparables.sum() >= 8 else float("nan")
        s_peau = float(math.sqrt(math.pi / 2) * ctx["lap"][y0:y1, x0:x1][mp].mean() / 6.0)
        if s_reste == s_reste and s_reste > 0.05:
            ratio = s_peau / s_reste
            tex["grain_peau"] = round(s_peau, 2)
            tex["grain_reste"] = round(s_reste, 2)
            tex["grain_peau_sur_reste"] = round(ratio, 2)
            # seul ce sens est un défaut : une peau a naturellement plus de détail fin qu'un fond flou
            if s_reste > 0.6 and ratio < 1 / al.r["grain_ecart"]["mineur"]:
                al.ajouter("GRAIN_INCOHERENT", "majeur" if ratio < 1 / al.r["grain_ecart"]["majeur"] else "mineur",
                           f"La peau est {1 / ratio:.1f} fois plus lisse au pixel que le reste de l'image (σ {s_peau:.1f} contre {s_reste:.1f}) : "
                           "le grain doit être le même partout, sinon la retouche se voit. Finir par un grain commun.",
                           valeur=round(ratio, 2), repere=f"≥ {1 / al.r['grain_ecart']['mineur']:.2f}")
        # avant / après
        av = ctx.get("avant_srgb8")
        if av is not None:
            ya = luma(av[y0:y1, x0:x1])
            ga, pa, ma_ = bandes(ya, s1, s2, s3)
            ref = {"grain": mad(ga[mp]), "pores": mad(pa[mp]), "modele": mad(ma_[mp])}
            ret = {kx: (round(tex[kx] / ref[kx], 3) if ref[kx] > 1e-4 else None) for kx in ref}
            m["avant_apres"] = {"avant": {kx: round(vx, 3) for kx, vx in ref.items()}, "conserve": ret}
            rp, rm = ret.get("pores"), ret.get("modele")
            if rp is not None:
                g = al.seuil("peau_retention_pores", rp, "PEAU_TEXTURE_PERDUE",
                             f"La retouche n'a gardé que {rp * 100:.0f} % de la texture fine de la peau (pores). "
                             "En dessous de 80 %, la peau commence à se lisser ; en dessous de 60 %, elle est plastique. "
                             "Revenir au dodge and burn plutôt qu'au flou, ou regreffer la texture d'origine.")
                if not g:
                    al.seuil("peau_retention_pores_haut", rp, "PEAU_TEXTURE_GONFLEE",
                             f"La texture fine de la peau a augmenté de {(rp - 1) * 100:.0f} % : accentuation ou grain ajouté trop fort, "
                             "la peau devient rêche.")
            if rm is not None and rp is not None and rp >= al.r["peau_retention_pores"]["mineur"]:
                al.seuil("peau_modele_ratio", rm, "PEAU_APLAT",
                         f"Le modelé local de la peau est tombé à {rm * 100:.0f} % de l'original alors que les pores sont gardés : "
                         "dodge and burn poussé trop loin, le visage perd son volume et prend l'aspect d'un aplat.")

    # ---- couleur
    L, a, b = lab_r[..., 0][peau_r], lab_r[..., 1][peau_r], lab_r[..., 2][peau_r]
    C = np.hypot(a, b)
    moyens = (L > 30) & (L < 85)
    if moyens.sum() > 500:
        h = teinte_deg(a[moyens], b[moyens])
        hp = np.percentile(h, [10, 50, 90])
        coul = {"L": round(float(np.median(L)), 1), "a": round(float(np.median(a[moyens])), 1),
                "b": round(float(np.median(b[moyens])), 1), "chroma": round(float(np.median(C[moyens])), 1),
                "teinte_deg": round(float(hp[1]), 1), "etendue_teinte_p10_p90": round(float(hp[2] - hp[0]), 1)}
        m["couleur"] = coul
        # taches de couleur : ce qui reste de a*b* une fois retiré le dégradé anatomique (joues plus rouges, front plus jaune)
        lv_r = lv / f
        mf = peau_r.astype(np.float32)

        def lisse_dans_masque(canal, sigma):
            return flou(canal * mf, sigma) / np.maximum(flou(mf, sigma), 1e-3)

        def taches(lab_img):
            res = []
            for c in (1, 2):
                fin = lisse_dans_masque(lab_img[..., c], max(1.0, lv_r / 60))
                res.append(mad((fin - lisse_dans_masque(lab_img[..., c], max(6.0, lv_r / 6)))[peau_r]))
            return float(math.hypot(*res))

        coul["taches_couleur"] = round(taches(lab_r), 2)
        if ctx.get("avant_srgb8") is not None:
            av_r = reduire(ctx["avant_srgb8"], REDUIT_MAX)
            if av_r.shape == rgb_r.shape:
                ref = taches(vers_lab(av_r))
                coul["taches_couleur_avant"] = round(ref, 2)
                if ref > 0.2 and coul["taches_couleur"] > 1.25 * ref and coul["taches_couleur"] > 1.5:
                    al.ajouter("PEAU_TACHES_AJOUTEES", "majeur",
                               f"La peau est plus tachée en couleur après retouche qu'avant ({ref:.1f} → {coul['taches_couleur']:.1f}) : "
                               "dodge and burn qui sature ou désature par endroits, ou corrections locales mal fondues. Voir la vue de teinte.",
                               valeur=coul["taches_couleur"], repere=f"≤ {ref:.1f} (valeur d'origine)")
        al.seuil("peau_taches_couleur", coul["taches_couleur"], "PEAU_TEINTE_INEGALE",
                 "Plaques de couleur sur la peau (rougeurs, zones jaunes ou verdâtres) à l'échelle de quelques centimètres. "
                 "Voir la vue de teinte ; uniformiser par un calque de teinte ciblé, pas par une désaturation globale.")
        al.seuil("peau_chroma", coul["chroma"], "PEAU_SATUREE", "Peau très saturée dans les tons moyens (rendu orangé).")
        if coul["teinte_deg"] < 32:
            al.ajouter("PEAU_TROP_ROUGE", "mineur", "Teinte médiane de la peau très rouge/magenta. À confirmer à l'œil : la carnation et l'étalonnage comptent.",
                       valeur=coul["teinte_deg"], repere="repère 35–65°")
        elif coul["teinte_deg"] > 72:
            al.ajouter("PEAU_TROP_JAUNE", "mineur", "Teinte médiane de la peau très jaune/verte. À confirmer à l'œil : la carnation et l'étalonnage comptent.",
                       valeur=coul["teinte_deg"], repere="repère 35–65°")
        hl, om = (L > 86), (L < 28)
        if hl.sum() > 300:
            coul["chroma_hautes_lumieres"] = round(float(np.median(C[hl])), 1)
            if coul["chroma_hautes_lumieres"] < 5 and coul["chroma"] > 14:
                al.ajouter("PEAU_HL_CRAYEUSES", "mineur", "Les hautes lumières de la peau sont presque blanches : brillances crayeuses, sans couleur de peau.",
                           valeur=coul["chroma_hautes_lumieres"], repere="C* ≥ 5")
        if om.sum() > 300:
            coul["chroma_ombres"] = round(float(np.median(C[om])), 1)
            if coul["chroma_ombres"] < 6 and coul["chroma"] > 14:
                al.ajouter("PEAU_OMBRES_GRISES", "mineur", "Les ombres de la peau sont grises : peau terreuse. Leur redonner de la couleur (calque couleur, pas de noir pur en burn).",
                           valeur=coul["chroma_ombres"], repere="C* ≥ 6")
        # visage contre reste de la peau
        if visages_r:
            v = visages_r[0]
            zv = np.zeros(peau_r.shape, bool)
            zv[max(0, int(v["y"])):int(v["y"] + v["h"]), max(0, int(v["x"])):int(v["x"] + v["w"])] = True
            zc = np.zeros(peau_r.shape, bool)
            ex = 0.35
            zc[max(0, int(v["y"] - ex * v["h"])):int(v["y"] + (1 + ex) * v["h"]),
               max(0, int(v["x"] - ex * v["w"])):int(v["x"] + (1 + ex) * v["w"])] = True
            mv, mc = peau_r & zv, peau_r & ~zc

            def ecart_visage_corps(lab_img):
                """Écart de couleur visage / reste de la peau à luminosité égale : l'éclairage change L*, peu la couleur."""
                Lr = lab_img[..., 0]
                lo = max(np.percentile(Lr[mv], 20), np.percentile(Lr[mc], 20))
                hi = min(np.percentile(Lr[mv], 80), np.percentile(Lr[mc], 80))
                bv, bc = mv & (Lr >= lo) & (Lr <= hi), mc & (Lr >= lo) & (Lr <= hi)
                if hi - lo < 5 or bv.sum() < 300 or bc.sum() < 300:
                    return None
                l1, l2 = np.median(lab_img[bv], axis=0), np.median(lab_img[bc], axis=0)
                dh = (float(teinte_deg(l1[1], l1[2]) - teinte_deg(l2[1], l2[2])) + 180) % 360 - 180
                return {"ecart_couleur_ab": round(float(math.hypot(l1[1] - l2[1], l1[2] - l2[2])), 1), "dTeinte_deg": round(dh, 1),
                        "dL_global": round(float(np.median(Lr[mv]) - np.median(Lr[mc])), 1)}

            if mv.sum() > 500 and mc.sum() > max(500, 0.25 * mv.sum()):
                vc = ecart_visage_corps(lab_r)
                if vc:
                    coul["visage_contre_corps"] = vc
                    avant_vc = None
                    if ctx.get("avant_srgb8") is not None:
                        av_r = reduire(ctx["avant_srgb8"], REDUIT_MAX)
                        if av_r.shape == rgb_r.shape:
                            avant_vc = ecart_visage_corps(vers_lab(av_r))
                    if avant_vc:
                        vc["ecart_couleur_ab_avant"] = avant_vc["ecart_couleur_ab"]
                    if avant_vc and vc["ecart_couleur_ab"] > avant_vc["ecart_couleur_ab"] + 3.0:
                        al.ajouter("PEAU_VISAGE_DESACCORDE", "majeur",
                                   f"La retouche a creusé l'écart de couleur entre le visage et le reste de la peau "
                                   f"({avant_vc['ecart_couleur_ab']} → {vc['ecart_couleur_ab']}, teinte {vc['dTeinte_deg']:+.1f}°) : "
                                   "correction faite sur le seul visage. Étendre la correction au cou, au décolleté et aux mains.",
                                   valeur=vc["ecart_couleur_ab"], repere=f"≤ {avant_vc['ecart_couleur_ab'] + 3.0:.1f} (origine + 3)")
                    else:
                        al.seuil("peau_visage_corps_dE", vc["ecart_couleur_ab"], "PEAU_VISAGE_CORPS",
                                 f"À luminosité égale, le visage et le reste de la peau (cou, mains, bras) n'ont pas la même couleur : "
                                 f"écart a*b* {vc['ecart_couleur_ab']}, teinte {vc['dTeinte_deg']:+.1f}°. Maquillage non raccordé, ou correction faite sur le seul visage.")
    # peau brûlée
    haut = np.any(rgb_r >= 254, axis=2)
    pb = float((haut & peau_r).sum()) / max(1, int(peau_r.sum())) * 100
    m["peau_canal_sature_pct"] = round(pb, 2)
    al.seuil("peau_brulee_pct", pb, "PEAU_BRULEE", "Brillances de peau brûlées (un canal au maximum) : plus de couleur ni de texture à cet endroit.",
             ", ".join(grille.cellules_fortes((haut & peau_r).astype(np.float32), 0.02)) or None, " %")
    ctx["peau_r"] = peau_r
    return m


# --------------------------------------------------------------------------- #
# Masques nommés (métal, pierre, tissu, cadran…)
# --------------------------------------------------------------------------- #
METAUX_BLANCS = ("metal", "acier", "argent", "platine", "or_blanc", "orblanc", "titane")


def mesurer_masque(nom: str, masque: np.ndarray, ctx: dict, al: Alertes) -> dict:
    srgb8, lab_r = ctx["srgb8"], ctx["lab_r"]
    mr = cv2.resize(masque.astype(np.uint8), (lab_r.shape[1], lab_r.shape[0]), interpolation=cv2.INTER_AREA) > 0
    if mr.sum() < 200:
        return {"erreur": "masque vide ou trop petit"}
    L, a, b = lab_r[..., 0][mr], lab_r[..., 1][mr], lab_r[..., 2][mr]
    C = np.hypot(a, b)
    p1, p50, p99 = np.percentile(L, [1, 50, 99])
    am, bm = float(np.median(a)), float(np.median(b))
    m = {"part_image_pct": round(float(mr.mean()) * 100, 2), "L_p1": round(float(p1), 1), "L_median": round(float(p50), 1),
         "L_p99": round(float(p99), 1), "etendue_L": round(float(p99 - p1), 1),
         "a": round(am, 2), "b": round(bm, 2), "chroma_median": round(float(np.median(C)), 2),
         "teinte_deg": round(float(teinte_deg(am, bm)), 1) if math.hypot(am, bm) > 2 else None}
    px = srgb8[masque]
    m["canal_sature_pct"] = round(float(np.any(px >= 254, axis=1).mean()) * 100, 2)
    m["blanc_brule_pct"] = round(float(np.all(px >= 254, axis=1).mean()) * 100, 2)
    m["noir_bouche_pct"] = round(float(np.all(px <= 1, axis=1).mean()) * 100, 2)
    # texture fine dans le masque (et ce que la retouche en a gardé)
    ys, xs = np.nonzero(masque)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    yb = luma(srgb8[y0:y1, x0:x1])
    mm = cv2.erode(masque[y0:y1, x0:x1].astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    if mm.sum() > 2000:
        fin = yb - flou(yb, 2.0)
        m["texture_fine"] = round(mad(fin[mm]), 3)
        av = ctx.get("avant_srgb8")
        if av is not None:
            ya = luma(av[y0:y1, x0:x1])
            ref = mad((ya - flou(ya, 2.0))[mm])
            if ref > 1e-3:
                m["texture_fine_conservee"] = round(m["texture_fine"] / ref, 3)
        # motif périodique de couleur (moiré) : pic isolé dans le spectre de la chrominance
        if min(yb.shape) >= 128:
            cote = min(512, min(yb.shape) // 2 * 2)
            cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
            ry0, rx0 = max(0, cy - cote // 2), max(0, cx - cote // 2)
            bloc = srgb8[ry0:ry0 + cote, rx0:rx0 + cote]
            if bloc.shape[0] == cote and bloc.shape[1] == cote and masque[ry0:ry0 + cote, rx0:rx0 + cote].mean() > 0.8:
                lb = vers_lab(bloc)
                chroma = lb[..., 1] - lb[..., 2]
                win = np.outer(np.hanning(cote), np.hanning(cote)).astype(np.float32)
                sp = np.abs(np.fft.fftshift(np.fft.fft2((chroma - chroma.mean()) * win)))
                yy, xx = np.indices(sp.shape)
                rr = np.hypot(yy - cote / 2, xx - cote / 2)
                couronne = (rr > cote / 100) & (rr < cote / 6)
                pic = float(sp[couronne].max() / max(1e-6, np.median(sp[couronne])))
                m["pic_periodique_chroma"] = round(pic, 1)
                if pic > 40:
                    al.ajouter("MOIRE_COULEUR", "mineur",
                               f"Motif périodique de couleur dans la zone « {nom} » : moiré probable si la matière est unie.",
                               valeur=round(pic, 1), repere="pic < 40")
    bas = nom.lower()
    if bas.startswith(METAUX_BLANCS):
        al.seuil("metal_chroma", m["chroma_median"], "METAL_PAS_NEUTRE",
                 f"Le métal blanc « {nom} » n'est pas neutre : il tire vers le {nom_direction(am, bm)} (a* {am:+.1f}, b* {bm:+.1f}). "
                 "Un acier, un or blanc ou un platine de catalogue est neutre, à peine froid.")
    if bas.startswith(METAUX_BLANCS + ("or", "gold")):
        al.seuil("metal_etendue_L", m["etendue_L"], "METAL_PLAT",
                 f"Le métal « {nom} » manque de contraste (étendue L* {m['etendue_L']:.0f}) : un métal poli va du noir profond au blanc. "
                 "Reconstruire les dégradés et poser des noirs francs.")
    if bas.startswith(("tissu", "vetement", "maille", "cuir", "soie", "velours", "denim")):
        r = m.get("texture_fine_conservee")
        if r is not None and r < 0.7:
            al.ajouter("TISSU_MATIERE_PERDUE", "majeur" if r < 0.5 else "mineur",
                       f"La zone « {nom} » a perdu {(1 - r) * 100:.0f} % de sa texture fine : armure lissée par le nettoyage des plis ou le débruitage.",
                       valeur=r, repere="≥ 0.7")
        if m["canal_sature_pct"] > 3:
            al.ajouter("TISSU_COULEUR_BOUCHEE", "mineur",
                       f"Couleur saturée sans modelé dans « {nom} » (un canal au maximum sur {m['canal_sature_pct']:.1f} % de la zone).",
                       valeur=m["canal_sature_pct"], repere="≤ 3 %")
        if p50 < 18 and (p99 - p1) < 9:
            al.ajouter("TISSU_NOIR_SANS_MATIERE", "mineur", f"Le noir de « {nom} » est un aplat : plus de plis ni de matière lisibles.",
                       valeur=m["etendue_L"], repere="étendue L* ≥ 9")
    return m


# --------------------------------------------------------------------------- #
# Avant / après
# --------------------------------------------------------------------------- #
def aligner_avant(avant: np.ndarray, forme) -> tuple[np.ndarray | None, str]:
    h, w = forme[:2]
    ha, wa = avant.shape[:2]
    if (ha, wa) == (h, w):
        return avant, "mêmes dimensions"
    if abs(wa / ha - w / h) < 0.01:
        return cv2.resize(avant, (w, h), interpolation=cv2.INTER_AREA if wa > w else cv2.INTER_LANCZOS4), "redimensionné (même rapport)"
    return None, "cadrage différent : exporter le final et l'original au même cadrage pour les mesures avant/après"


def mesurer_avant_apres(ctx: dict, al: Alertes) -> dict:
    grille = ctx["grille"]
    lab_f = ctx["lab_r"]
    av_r = reduire(ctx["avant_srgb8"], REDUIT_MAX)
    if av_r.shape != ctx["rgb_r"].shape:
        av_r = cv2.resize(av_r, (ctx["rgb_r"].shape[1], ctx["rgb_r"].shape[0]), interpolation=cv2.INTER_AREA)
    lab_a = vers_lab(av_r)
    d = lab_f - lab_a
    dE = np.sqrt((d ** 2).sum(axis=2))
    Ca, Cf = np.hypot(lab_a[..., 1], lab_a[..., 2]), np.hypot(lab_f[..., 1], lab_f[..., 2])
    m = {"dL_moyen": round(float(d[..., 0].mean()), 2), "da_moyen": round(float(d[..., 1].mean()), 2),
         "db_moyen": round(float(d[..., 2].mean()), 2), "dE_moyen": round(float(dE.mean()), 2),
         "dE_p95": round(float(np.percentile(dE, 95)), 2),
         "contraste_ratio": round(float(lab_f[..., 0].std() / max(1e-3, lab_a[..., 0].std())), 3),
         "saturation_ratio": round(float(Cf.mean() / max(1e-3, Ca.mean())), 3),
         "surface_modifiee_pct": round(float((dE > 3).mean()) * 100, 1)}
    # la part locale du changement : on retire le changement global (étalonnage) pour voir où la retouche a porté
    locale = np.sqrt(((d - flou(d, 60)) ** 2).sum(axis=2))
    ctx["carte_dE"] = dE
    ctx["carte_dE_locale"] = locale
    m["cellules_les_plus_modifiees"] = grille.cellules_fortes(locale, 1.2, n=8)

    # ---- déformation géométrique (fluidité, déformation, recadrage interne)
    def norm(img):
        g = cv2.cvtColor(reduire(img, 1024), cv2.COLOR_RGB2GRAY)
        return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(g)

    ga, gf = norm(ctx["avant_srgb8"]), norm(ctx["srgb8"])
    if ga.shape != gf.shape:
        ga = cv2.resize(ga, (gf.shape[1], gf.shape[0]))
    args = dict(pyr_scale=0.5, levels=5, winsize=31, iterations=3, poly_n=7, poly_sigma=1.5, flags=0)
    f_ab = cv2.calcOpticalFlowFarneback(ga, gf, None, **args)
    f_ba = cv2.calcOpticalFlowFarneback(gf, ga, None, **args)
    hh, ww = ga.shape
    xx, yy = np.meshgrid(np.arange(ww, dtype=np.float32), np.arange(hh, dtype=np.float32))
    retour = cv2.remap(f_ba, xx + f_ab[..., 0], yy + f_ab[..., 1], cv2.INTER_LINEAR)
    coherent = np.hypot(f_ab[..., 0] + retour[..., 0], f_ab[..., 1] + retour[..., 1]) < 1.0
    # il faut de la structure pour qu'un déplacement ait un sens
    struct = flou(np.hypot(cv2.Sobel(ga, cv2.CV_32F, 1, 0), cv2.Sobel(ga, cv2.CV_32F, 0, 1)), 6) > 6
    fx = f_ab[..., 0] - np.median(f_ab[..., 0][coherent]) if coherent.any() else f_ab[..., 0]
    fy = f_ab[..., 1] - np.median(f_ab[..., 1][coherent]) if coherent.any() else f_ab[..., 1]
    mag = np.hypot(fx, fy)
    mag[~(coherent & struct)] = 0
    mag = cv2.medianBlur(mag.astype(np.float32), 5)
    diag = math.hypot(hh, ww)
    fiable = coherent & struct
    p99 = float(np.percentile(mag[fiable], 99)) / diag * 100 if fiable.sum() > 500 else 0.0
    seuil_px = al.r["deformation_pct_diag"]["mineur"] / 100 * diag
    deforme = mag > seuil_px
    n, lab, stats, _ = cv2.connectedComponentsWithStats(deforme.astype(np.uint8), connectivity=8)
    grandes = np.zeros(n, bool)
    if n > 1:
        grandes[1:] = stats[1:, cv2.CC_STAT_AREA] >= 0.002 * deforme.size
    deforme = grandes[lab]
    part = float(deforme.mean()) * 100
    m["deformation"] = {"deplacement_p99_pct_diagonale": round(p99, 3),
                        "deplacement_max_px_pleine_resolution": round(float(mag.max()) * ctx["srgb8"].shape[1] / ww, 1),
                        "surface_deformee_pct": round(part, 2)}
    ctx["carte_deformation"] = mag / max(1e-6, seuil_px * 4)
    if part > 0.2:
        zones = grille.cellules_fortes(deforme.astype(np.float32), 0.05, n=8)
        m["deformation"]["cellules"] = zones
        grav = "majeur" if p99 >= al.r["deformation_pct_diag"]["majeur"] else "mineur"
        al.ajouter("DEFORMATION", grav,
                   "La géométrie a changé entre l'original et le final (fluidité, déformation, redressement). "
                   "Normal si c'était demandé. Vérifier les lignes voisines (fond, vêtement, bijou) et, pour une image commerciale "
                   "où la silhouette d'un mannequin est affinée ou épaissie, l'obligation de mention « Photographie retouchée ».",
                   ", ".join(zones) or None, round(p99, 3), f"≤ {al.r['deformation_pct_diag']['mineur']} % de la diagonale")
    return m


# --------------------------------------------------------------------------- #
# Symétrie (packshot de face)
# --------------------------------------------------------------------------- #
def mesurer_symetrie(fond_r: np.ndarray) -> dict | None:
    sujet = (~fond_r).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(sujet, connectivity=8)
    if n < 2:
        return None
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    s = (lab == i)
    x, y, w, h = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
    bloc = s[y:y + h, x:x + w]
    miroir = bloc[:, ::-1]
    iou = float((bloc & miroir).sum() / max(1, (bloc | miroir).sum()))
    ys, xs = np.nonzero(s)
    pts = np.stack([xs - xs.mean(), ys - ys.mean()], axis=1).astype(np.float64)
    vals, vecs = np.linalg.eigh(np.cov(pts.T))
    v = vecs[:, int(np.argmax(vals))]
    ang = math.degrees(math.atan2(v[0], v[1]))  # écart à la verticale
    ang = (ang + 90) % 180 - 90
    if abs(ang) > 45:
        ang = ang - 90 if ang > 0 else ang + 90   # objet plus large que haut : on mesure l'écart à l'horizontale
    H, W = fond_r.shape
    return {"silhouette_symetrie_gauche_droite_pct": round(iou * 100, 1), "inclinaison_axe_deg": round(ang, 2),
            "centrage_horizontal_pct": round(((x + w / 2) / W - 0.5) * 100, 2),
            "centrage_vertical_pct": round(((y + h / 2) / H - 0.5) * 100, 2),
            "marges_pct": {"gauche": round(x / W * 100, 1), "droite": round((W - x - w) / W * 100, 1),
                           "haut": round(y / H * 100, 1), "bas": round((H - y - h) / H * 100, 1)}}


# --------------------------------------------------------------------------- #
# Vues de contrôle
# --------------------------------------------------------------------------- #
_LUT_SOLAIRE = np.round((0.5 - 0.5 * np.cos(2 * np.pi * 3 * np.arange(256) / 255.0)) * 255).astype(np.uint8)


def vue_solarisation(rgb8):
    return _LUT_SOLAIRE[rgb8]


def vue_luminance(rgb8):
    y = luma(rgb8)
    lo, hi = np.percentile(y[::3, ::3], [1, 99])
    x = np.clip((y - lo) / max(1.0, hi - lo), 0, 1)
    x = 1.0 / (1.0 + np.exp(-(x - 0.5) * 7.0))
    g = np.round(np.clip((x - 0.0293) / (0.9707 - 0.0293), 0, 1) * 255).astype(np.uint8)
    return np.stack([g] * 3, axis=-1)


def vue_saturation(rgb8):
    lab = vers_lab(rgb8)
    c = np.clip(np.hypot(lab[..., 1], lab[..., 2]) / 70.0, 0, 1)
    g = np.round(c * 255).astype(np.uint8)
    return np.stack([g] * 3, axis=-1)


def vue_teinte(rgb8):
    lab = vers_lab(rgb8)
    c = np.hypot(lab[..., 1], lab[..., 2])
    hsv = cv2.cvtColor(rgb8, cv2.COLOR_RGB2HSV)
    hsv[..., 1], hsv[..., 2] = 255, 255
    out = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    out[c < 6] = 128
    return out


def vue_texture(rgb8, s_bas=0.0, s_haut=3.0, gain=6.0):
    y = luma(rgb8)
    b = (flou(y, s_bas) if s_bas > 0 else y) - flou(y, s_haut)
    g = np.clip(128 + gain * b, 0, 255).astype(np.uint8)
    return np.stack([g] * 3, axis=-1)


def vue_ecretage(rgb8, cartes):
    g = (luma(rgb8) * 0.45 + 70).astype(np.uint8)
    out = np.stack([g] * 3, axis=-1)
    out[cartes["un_bas"]] = (0, 200, 220)
    out[cartes["tout_bas"]] = (0, 60, 255)
    out[cartes["un_haut"]] = (255, 210, 0)
    out[cartes["tout_haut"]] = (255, 0, 0)
    return out


def vue_fond(rgb8, L_fond_8bits):
    y = luma(rgb8)
    if L_fond_8bits > 200:
        lo, hi = max(0.0, L_fond_8bits - 22), 255.0
    elif L_fond_8bits < 40:
        lo, hi = 0.0, min(255.0, L_fond_8bits + 26)
    else:
        lo, hi = L_fond_8bits - 16, L_fond_8bits + 16
    g = np.clip((y - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)
    return np.stack([g] * 3, axis=-1)


def vue_carte(carte, maxi, taille):
    c = np.clip(carte / maxi, 0, 1)
    c = cv2.resize(c.astype(np.float32), (taille[1], taille[0]), interpolation=cv2.INTER_LINEAR)
    return cv2.cvtColor(cv2.applyColorMap((c * 255).astype(np.uint8), cv2.COLORMAP_INFERNO), cv2.COLOR_BGR2RGB)


def _police(taille: int):
    try:
        return ImageFont.load_default(size=taille)
    except TypeError:
        return ImageFont.load_default()


def dessiner_grille(rgb8: np.ndarray, grille: Grille, marquer: set[str] | None = None) -> np.ndarray:
    im = Image.fromarray(rgb8).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    f = im.width / grille.w
    pol = _police(max(11, min(22, int(grille.t * f * 0.22))))
    for c in range(grille.nc):
        for l in range(grille.nl):
            x0, y0, x1, y1 = [v * f for v in grille.boite(c, l)]
            nom = grille.nom(c, l)
            sel = marquer and nom in marquer
            d.rectangle([x0, y0, x1, y1], outline=(255, 220, 0, 230) if sel else (255, 255, 255, 110), width=2 if sel else 1)
            d.rectangle([x0 + 2, y0 + 2, x0 + 6 + pol.getlength(nom), y0 + 6 + pol.size], fill=(0, 0, 0, 150))
            d.text((x0 + 4, y0 + 3), nom, fill=(255, 220, 0, 255) if sel else (255, 255, 255, 255), font=pol)
    return np.asarray(im)


def _sans_accents(texte: str) -> str:
    """La police intégrée à Pillow n'a pas tous les accents : une étiquette lisible vaut mieux qu'un carré vide."""
    import unicodedata
    texte = texte.replace("Δ", "d").replace("×", "x")
    return "".join(c for c in unicodedata.normalize("NFKD", texte) if not unicodedata.combining(c))


def etiqueter(rgb8: np.ndarray, texte: str) -> np.ndarray:
    texte = _sans_accents(texte)
    im = Image.fromarray(rgb8)
    d = ImageDraw.Draw(im, "RGBA")
    pol = _police(16)
    d.rectangle([0, 0, 10 + pol.getlength(texte), 24], fill=(0, 0, 0, 170))
    d.text((5, 3), texte, fill=(255, 255, 255, 255), font=pol)
    return np.asarray(im)


def cote_a_cote(a: np.ndarray, b: np.ndarray, ta: str, tb: str) -> np.ndarray:
    h = max(a.shape[0], b.shape[0])

    def cale(x):
        if x.shape[0] == h:
            return x
        return np.pad(x, ((0, h - x.shape[0]), (0, 0), (0, 0)), constant_values=40)

    sep = np.full((h, 8, 3), 40, np.uint8)
    return np.concatenate([etiqueter(cale(a), ta), sep, etiqueter(cale(b), tb)], axis=1)


def ecrire(img: np.ndarray, chemin: Path):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    im = Image.fromarray(img)
    if chemin.suffix.lower() == ".png":
        im.save(chemin, optimize=False, compress_level=4)
    else:
        im.save(chemin, quality=95, subsampling=0)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def choisir_tuiles(ctx: dict, demande: str, al: Alertes) -> list[str]:
    g: Grille = ctx["grille"]
    toutes = [g.nom(c, l) for l in range(g.nl) for c in range(g.nc)]
    d = demande.strip().lower()
    if d in ("toutes", "tout", "all"):
        return toutes
    if not d.isdigit():
        noms = []
        for n in demande.replace(";", ",").split(","):
            if n.strip():
                c, l = g.depuis_nom(n)
                noms.append(g.nom(c, l))
        return noms
    n = int(d)
    if n <= 0:
        return []
    rgb_r = ctx["rgb_r"]
    y = luma(rgb_r)
    score = g.par_cellule(np.hypot(cv2.Sobel(y, cv2.CV_32F, 1, 0), cv2.Sobel(y, cv2.CV_32F, 0, 1)))
    score = score / max(1e-6, score.max())
    if ctx.get("fond_r") is not None:
        score *= np.clip(g.par_cellule((~ctx["fond_r"]).astype(np.float32)) * 3, 0.05, 1)  # le sujet avant le fond
    if ctx.get("peau_r") is not None:
        score += 1.5 * g.par_cellule(ctx["peau_r"].astype(np.float32))
    if ctx.get("carte_dE_locale") is not None:
        cl = g.par_cellule(ctx["carte_dE_locale"])
        score += 1.5 * cl / max(1e-6, cl.max())
    for v in ctx.get("visages", [])[:3]:   # les yeux et la bouche se regardent toujours à 100 %
        for (px, py) in ((0.3, 0.4), (0.7, 0.4), (0.5, 0.75), (0.5, 0.2)):
            c = int(min(g.nc - 1, max(0, (v["x"] + px * v["w"]) // g.t)))
            l = int(min(g.nl - 1, max(0, (v["y"] + py * v["h"]) // g.t)))
            score[l, c] += 3
    # les cellules citées par une alerte passent devant
    for a in al.liste:
        if a["zone"]:
            for z in a["zone"].split(","):
                z = z.strip().split(" ")[0]
                try:
                    c, l = g.depuis_nom(z)
                    score[l, c] += 2.5 if a["gravite"] == "majeur" else 1.5
                except ValueError:
                    pass
    ordre = np.argsort(score.ravel())[::-1][:n]
    return sorted((g.nom(int(i % g.nc), int(i // g.nc)) for i in ordre), key=lambda s: (int("".join(ch for ch in s if ch.isdigit())), s))


def sortir_tuiles(srgb8: np.ndarray, avant8: np.ndarray | None, grille: Grille, noms: list[str], zoom: int, dossier: Path,
                  largeur_visage: float | None) -> list[dict]:
    """Écrit les tuiles à 100 % (ou zoomées) des cellules demandées. `largeur_visage` renseignée = image avec peau."""
    peau = largeur_visage is not None
    s2 = echelles_texture(largeur_visage)[1] if peau else 2.5
    sorties = []
    for nom in noms:
        c, l = grille.depuis_nom(nom)
        x0, y0, x1, y1 = grille.boite(c, l)
        sous = [("", x0, y0, x1, y1)]
        if zoom > 1:
            mx, my = (x0 + x1) // 2, (y0 + y1) // 2
            sous = [("a", x0, y0, mx, my), ("b", mx, y0, x1, my), ("c", x0, my, mx, y1), ("d", mx, my, x1, y1)]
        for suf, a0, b0, a1, b1 in sous:
            if a1 - a0 < 8 or b1 - b0 < 8:
                continue
            bloc = srgb8[b0:b1, a0:a1]

            def z(x):
                return x if zoom == 1 else cv2.resize(x, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_CUBIC)

            if avant8 is not None:
                image = cote_a_cote(z(avant8[b0:b1, a0:a1]), z(bloc), f"{nom}{suf} avant", f"{nom}{suf} après")
            else:
                image = etiqueter(z(bloc), f"{nom}{suf}  {zoom * 100} %")
            ecrire(image, dossier / f"{nom}{suf}.png")
            if peau:   # sur la peau, c'est la densité qu'on lit ; sur un produit, les poussières et les dégradés
                gauche, titre = vue_luminance(bloc), "luminance contrastée"
            else:
                gauche, titre = vue_solarisation(bloc), "solarisation"
            ctrl = cote_a_cote(z(gauche), z(vue_texture(bloc, 0.0, s2, 5.0)), f"{nom}{suf} {titre}", f"{nom}{suf} passe-haut")
            ecrire(ctrl, dossier / f"{nom}{suf}_controle.png")
            sorties.append({"cellule": f"{nom}{suf}", "fichier": f"tuiles/{nom}{suf}.png", "controle": f"tuiles/{nom}{suf}_controle.png",
                            "boite_px": [int(a0), int(b0), int(a1), int(b1)], "zoom": zoom})
    return sorties


def tuiles_seules(final: str | Path, avant: str | Path | None, sortie: str | Path | None, tuiles: str, taille_tuile: int,
                  zoom: int, peau: bool, largeur_visage: float | None) -> list[dict]:
    """Complément : écrit seulement des tuiles dans le dossier de contrôle, sans refaire les mesures ni toucher au rapport."""
    final = Path(final)
    img = charger(final)
    srgb8 = img["srgb8"]
    grille = Grille(srgb8.shape[1], srgb8.shape[0], taille_tuile)
    avant8 = None
    if avant:
        avant8, _ = aligner_avant(charger(avant)["srgb8"], srgb8.shape)
    if tuiles.strip().lower() in ("toutes", "tout", "all"):
        noms = [grille.nom(c, l) for l in range(grille.nl) for c in range(grille.nc)]
    else:
        noms = [grille.nom(*grille.depuis_nom(n)) for n in tuiles.replace(";", ",").split(",") if n.strip()]
    sortie = Path(sortie) if sortie else final.with_name(final.stem + "_controle")
    lv = None
    if peau:
        vis = detecter_visages(srgb8)
        lv = largeur_visage or (vis[0]["w"] if vis else max(srgb8.shape[:2]) * 0.15)
    return sortir_tuiles(srgb8, avant8, grille, noms, zoom, sortie / "tuiles", lv)


def analyser(final: str | Path, avant: str | Path | None = None, genre: str = "auto", masques: dict | None = None,
             sortie: str | Path | None = None, tuiles: str = "12", taille_tuile: int = 768, zoom: int = 1,
             largeur_visage: float | None = None, reperes: dict | None = None, symetrie: bool = False,
             sans_vues: bool = False) -> dict:
    """Analyse complète. Retourne le rapport (dict) et écrit rapport.json, rapport.md, vues et tuiles."""
    final = Path(final)
    rep = dict(REPERES)
    etalonnes = set()
    if reperes:
        for k, v in reperes.items():
            if k in rep and isinstance(v, dict):
                rep[k] = {**rep[k], **v}
                etalonnes.add(k)
    al = Alertes(rep, etalonnes)
    img = charger(final)
    natif, srgb8, infos = img["natif"], img["srgb8"], img["infos"]
    H, W = srgb8.shape[:2]
    grille = Grille(W, H, taille_tuile)
    rgb_r = reduire(srgb8, REDUIT_MAX)
    lab_r = vers_lab(rgb_r)
    ctx = {"srgb8": srgb8, "natif": natif, "rgb_r": rgb_r, "lab_r": lab_r, "grille": grille, "genre": genre}
    mes: dict = {}

    if not infos.get("profil"):
        al.ajouter("PROFIL_ABSENT", "majeur",
                   "Aucun profil colorimétrique incorporé : chaque logiciel et chaque navigateur affichera des couleurs différentes. "
                   "Incorporer le profil à l'export (sRGB pour le web).")
    elif infos.get("converti_vers_srgb") and infos.get("hors_gamut_srgb_pct", 0) > 1.0:
        al.ajouter("HORS_GAMUT_SRGB", "info",
                   f"{infos['hors_gamut_srgb_pct']} % des pixels sortent du sRGB (profil {infos['profil']}) : "
                   "ces couleurs seront écrêtées sur le web. Épreuver en sRGB avant l'export.",
                   valeur=infos["hors_gamut_srgb_pct"], repere="≤ 1 %")
    if infos.get("encrage_total_p99_9_pct") is not None:
        enc = infos["encrage_total_p99_9_pct"]
        al.ajouter("ENCRAGE", "mineur" if enc > 300 else "info",
                   f"Fichier CMJN : taux d'encrage total de {enc:.0f} % dans les zones les plus chargées (maximum {infos['encrage_total_max_pct']:.0f} %). "
                   "À comparer à la limite de la fiche technique du support (300 % est courant en presse magazine).",
                   valeur=enc, repere="limite du support")
    if infos.get("format") == "JPEG" and infos.get("qualite_jpeg_estimee") and infos["qualite_jpeg_estimee"] < 85:
        al.ajouter("JPEG_QUALITE_BASSE", "mineur", f"JPEG enregistré vers la qualité {infos['qualite_jpeg_estimee']} : trop bas pour une livraison.",
                   valeur=infos["qualite_jpeg_estimee"], repere="≥ 90")

    # ---- fond, visages, genre
    fond_r = detecter_fond(rgb_r, lab_r)
    visages = detecter_visages(srgb8)
    ctx["visages"] = visages
    if genre == "auto":
        if visages and visages[0]["w"] > 0.04 * W:
            lv = visages[0]["w"] / W
            genre = "beaute" if lv > 0.38 else "portrait" if lv > 0.12 else "mode"
        elif fond_r is not None:
            genre = "packshot"
        else:
            genre = "general"
    ctx["genre"] = genre
    ctx["fond_r"] = fond_r
    fond_plein = None
    if fond_r is not None:
        fond_plein = cv2.resize(fond_r.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
        k = int(2 * W / rgb_r.shape[1]) + 3   # on déborde un peu sur le contour : un liseré de fond n'est pas du sujet brûlé
        fond_plein = cv2.dilate(fond_plein, np.ones((k, k), np.uint8)) > 0
        mes["fond"] = mesurer_fond(fond_r, lab_r, srgb8, al, genre)

    if img.get("alpha") is not None and img["alpha"].shape == (H, W) and (img["alpha"] < 128).mean() > 0.02:
        # image détourée : la transparence dit où est le fond, mieux que toute détection
        transparent = cv2.dilate((img["alpha"] < 250).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        fond_plein = transparent if fond_plein is None else (fond_plein | transparent)

    # ---- avant
    if avant:
        av = charger(avant)
        av8, note = aligner_avant(av["srgb8"], srgb8.shape)
        infos["avant"] = {"nom": Path(avant).name, "alignement": note,
                          "largeur": av["infos"]["largeur"], "hauteur": av["infos"]["hauteur"]}
        if av8 is not None:
            ctx["avant_srgb8"] = av8
        else:
            al.ajouter("AVANT_NON_ALIGNE", "info", "Original et final n'ont pas le même cadrage : mesures avant/après ignorées.")

    # ---- mesures générales
    mes["ecretage"], cartes_ecr = mesurer_ecretage(natif, grille, fond_plein, al, genre)
    mes["tonalite"] = mesurer_tonalite(lab_r, al)
    y = luma(srgb8)
    sigma, lap, calme = mesurer_bruit(y)
    ctx["sigma_bruit"], ctx["lap"], ctx["calme"] = sigma, lap, calme
    mes["grain"] = {"sigma_pixel": round(sigma, 3) if sigma == sigma else None}
    mes["banding"], carte_band = mesurer_banding(srgb8, natif, grille, al)
    mes["contours"] = mesurer_halos(y, al)
    if infos.get("format") == "JPEG":
        mes["jpeg"] = mesurer_blocs_jpeg(y, al, infos.get("qualite_jpeg_estimee"))

    # ---- peau
    masques = masques or {}
    masques_charges = {n: charger_masque(p, srgb8.shape) for n, p in masques.items()}
    if "peau" in masques_charges:
        ctx["masque_peau_fourni"] = masques_charges["peau"]
    if genre in GENRES_PEAU or "peau" in masques_charges or (visages and genre == "general"):
        mp = mesurer_peau(ctx, al, largeur_visage)
        if mp:
            mes["peau"] = mp

    # ---- neutres (hors peau : la peau n'est pas un neutre)
    mes["neutres"] = mesurer_neutres(lab_r, al, exclure=ctx.get("peau_r"), produit=genre in GENRES_PRODUIT)

    # ---- masques nommés
    if masques_charges:
        mes["masques"] = {n: mesurer_masque(n, m, ctx, al) for n, m in masques_charges.items() if n != "peau"}

    # ---- poussières
    excl = None
    if ctx.get("peau_r") is not None:
        excl = cv2.resize(cv2.dilate(ctx["peau_r"].astype(np.uint8), np.ones((9, 9), np.uint8)), (W, H),
                          interpolation=cv2.INTER_NEAREST) > 0
    mes["poussieres"], points = detecter_poussieres(y, sigma, excl, grille, al, genre)

    # ---- avant / après
    if ctx.get("avant_srgb8") is not None:
        mes["avant_apres"] = mesurer_avant_apres(ctx, al)

    # ---- symétrie
    if symetrie and fond_r is not None:
        mes["symetrie"] = mesurer_symetrie(fond_r)

    ordre_g = {"bloquant": 0, "majeur": 1, "mineur": 2, "info": 3}
    al.liste.sort(key=lambda a: ordre_g.get(a["gravite"], 9))
    rapport = {"fichier": infos, "genre": genre, "grille": {"colonnes": grille.nc, "lignes": grille.nl, "cellule_px": grille.t},
               "mesures": mes, "alertes": al.liste, "vues": [], "tuiles": []}

    if sortie is None:
        sortie = final.with_name(final.stem + "_controle")
    sortie = Path(sortie)
    sortie.mkdir(parents=True, exist_ok=True)

    if not sans_vues:
        choisies = choisir_tuiles(ctx, tuiles, al)
        vue = reduire(srgb8, VUE_MAX)
        dv = sortie / "vues"

        def sauver(nom, image, legende):
            ecrire(image, dv / nom)
            rapport["vues"].append({"fichier": f"vues/{nom}", "legende": legende})

        sauver("00_apercu_grille.jpg", dessiner_grille(vue, grille, set(choisies)),
               "Image entière et quadrillage. Les cellules en jaune ont une tuile à 100 %.")
        sauver("01_ecretage.jpg", vue_ecretage(vue, {k: reduire(v.astype(np.uint8) * 255, VUE_MAX) > 100 for k, v in cartes_ecr.items()}),
               "Écrêtage. Rouge : blanc brûlé. Jaune : un canal au maximum. Bleu : noir bouché. Cyan : un canal à zéro.")
        sauver("02_solarisation.jpg", vue_solarisation(vue),
               "Courbe solarisée : fait ressortir poussières, taches, raccords de tampon, dégradés irréguliers et paliers.")
        sauver("03_luminance.jpg", vue_luminance(vue),
               "Noir et blanc contrasté : répartition de la lumière, taches de densité, dodge and burn irrégulier, dégradés de métal.")
        sauver("04_saturation.jpg", vue_saturation(vue),
               "Saturation (blanc = saturé) : plaques de saturation, zones éteintes, bords de masque.")
        sauver("05_teinte.jpg", vue_teinte(vue),
               "Teinte seule, à saturation maximale (gris = neutre) : plaques de teinte sur la peau, dominantes locales, métal qui vire.")
        fv = W / vue.shape[1]
        sauver("06_texture.jpg", vue_texture(vue, 0.0, max(1.0, 3.0 / max(1.0, fv) * 2), 7.0),
               "Passe-haut de l'aperçu : continuité de la matière à l'échelle de l'image. La texture fine se juge sur les tuiles.")
        if ctx.get("peau_r") is not None:
            mq = cv2.resize(ctx["peau_r"].astype(np.uint8), (vue.shape[1], vue.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
            ov = (vue * 0.35).astype(np.uint8)
            ov[mq] = vue[mq]
            sauver("05b_masque_peau.jpg", ov,
                   "Ce que les mesures ont pris pour de la peau (le reste est assombri). Si le masque déborde ou manque, "
                   "les chiffres de peau sont à relativiser : fournir --masque peau=fichier.")
        if fond_r is not None:
            Lf8 = float(np.median(luma(rgb_r)[fond_r]))
            sauver("07_fond.jpg", vue_fond(vue, Lf8),
                   "Fond étiré au maximum : salissures, fond inégal, halo ou frange de détourage, ombre coupée.")
        if carte_band.max() > 0.05:
            sauver("08_paliers.jpg", cote_a_cote(vue_carte(carte_band, 1.0, vue.shape[:2]), vue_luminance(vue), "paliers détectés", "luminance"),
                   "Où se trouvent les dégradés en marches d'escalier.")
        if points:
            im = Image.fromarray(vue_solarisation(vue))
            d = ImageDraw.Draw(im)
            for x, yy, t in points[:1500]:
                r = max(5, t / fv + 4)
                d.ellipse([x / fv - r, yy / fv - r, x / fv + r, yy / fv + r], outline=(255, 255, 0), width=1)
            sauver("09_poussieres.jpg", np.asarray(im), f"{len(points)} candidats poussière ou point, cerclés sur la vue solarisée. À confirmer à 100 %.")
        if ctx.get("carte_dE") is not None:
            av_vue = reduire(ctx["avant_srgb8"], VUE_MAX)
            sauver("10_avant_apres.jpg", cote_a_cote(reduire(av_vue, VUE_MAX // 2), reduire(vue, VUE_MAX // 2), "avant", "après"),
                   "Original et final côte à côte.")
            sauver("11_difference.jpg", cote_a_cote(reduire(vue_carte(ctx["carte_dE"], 25.0, vue.shape[:2]), VUE_MAX // 2),
                                                   reduire(vue_carte(ctx["carte_dE_locale"], 10.0, vue.shape[:2]), VUE_MAX // 2),
                                                   "écart total (ΔE)", "écart local, étalonnage global retiré"),
                   "Ce que la retouche a changé. À droite : seulement les interventions locales.")
            if mes["avant_apres"]["deformation"]["surface_deformee_pct"] > 0.2:
                sauver("12_deformation.jpg", cote_a_cote(reduire(vue_carte(ctx["carte_deformation"], 1.0, vue.shape[:2]), VUE_MAX // 2),
                                                        reduire(vue, VUE_MAX // 2), "déplacement des pixels", "après"),
                       "Où la géométrie a bougé (fluidité, déformation).")

        # ---- tuiles à 100 %
        lv = mes.get("peau", {}).get("largeur_visage_px") if "peau" in mes else None
        rapport["tuiles"] = sortir_tuiles(srgb8, ctx.get("avant_srgb8"), grille, choisies, zoom, sortie / "tuiles", lv)

    (sortie / "rapport.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=2, default=_json), encoding="utf-8")
    (sortie / "rapport.md").write_text(rediger(rapport, sortie), encoding="utf-8")
    rapport["dossier"] = str(sortie)
    return rapport


def _json(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


# --------------------------------------------------------------------------- #
# Rapport lisible
# --------------------------------------------------------------------------- #
def rediger(r: dict, sortie: Path) -> str:
    f, m = r["fichier"], r["mesures"]
    L = [f"# Contrôle — {f['nom']}", ""]
    L.append(f"- Fichier : {f['largeur']} × {f['hauteur']} px ({f['megapixels']} Mpx), {f.get('format')} {f.get('bits')} bits, "
             f"profil : {f.get('profil') or 'AUCUN'}" + (f", JPEG qualité ≈ {f['qualite_jpeg_estimee']}" if f.get("qualite_jpeg_estimee") else ""))
    if f.get("avant"):
        L.append(f"- Original : {f['avant']['nom']} ({f['avant']['alignement']})")
    L.append(f"- Genre retenu : {r['genre']} — grille {r['grille']['colonnes']} × {r['grille']['lignes']} cellules de {r['grille']['cellule_px']} px")
    if f.get("encrage_total_p99_9_pct") is not None:
        L.append(f"- Encrage total (CMJN) : {f['encrage_total_p99_9_pct']} % dans les zones les plus chargées, maximum {f['encrage_total_max_pct']} %")
    for rq in f.get("remarques", []):
        L.append(f"- Remarque : {rq}")
    L += ["", "## Alertes", ""]
    if not r["alertes"]:
        L.append("Aucune alerte des mesures. Cela ne vaut pas validation : les mesures ne voient ni le goût, ni la justesse d'un regard, ni la fidélité au produit.")
    else:
        L.append("| Gravité | Code | Zone | Valeur | Repère | Constat |")
        L.append("|---|---|---|---|---|---|")
        for a in r["alertes"]:
            L.append(f"| {a['gravite']} | {a['code']} | {a['zone'] or '—'} | {a['valeur'] if a['valeur'] is not None else '—'} | "
                     f"{a['repere'] or '—'} | {a['message']} |")
    L += ["", "## Mesures", ""]
    e, t = m["ecretage"], m["tonalite"]
    L.append(f"- Écrêtage (hors fond) : blanc brûlé {e['sujet_brule_pct']} %, un canal saturé {e['canal_brule_pct']} %, noir bouché {e['noir_bouche_pct']} %")
    L.append(f"- Tonalité : L* p0,1 {t['L_p0_1']} · médiane {t['L_median']} · p99,9 {t['L_p99_9']} ; chroma moyen {t['chroma_moyen']}")
    for nom, v in m["neutres"].items():
        if isinstance(v, dict) and "chroma" in v:
            L.append(f"- Neutres, {NOMS_BANDES.get(nom, nom)} : a* {v['a']:+} b* {v['b']:+} → {v['direction']} (chroma {v['chroma']}, {v['part_pct']} % de l'image)")
    if "fond" in m:
        fd = m["fond"]
        L.append(f"- Fond {fd['type']} ({fd['part_image_pct']} % de l'image) : L* {fd['L']}, a* {fd['a']:+}, b* {fd['b']:+}, étendue L* {fd['etendue_L_p2_p98']}"
                 + (f", blanc pur sur {fd['blanc_pur_pct']} %" if "blanc_pur_pct" in fd else ""))
    b = m["banding"]
    L.append(f"- Dégradés : marches franches sur {b['marches_franches_pct']} % de la surface ; dégradé lisse sans grain sur "
             f"{b['degrades_sans_grain_pct']} % ; trous d'histogramme {b['histogramme_trous_pct']} %"
             + (f" ; {b['niveaux_distincts_canal_vert']} niveaux distincts (16 bits)" if "niveaux_distincts_canal_vert" in b else ""))
    L.append(f"- Grain au pixel : σ {m['grain']['sigma_pixel']} niveaux")
    c = m.get("contours") or {}
    if "depassement_median" in c:
        L.append(f"- Contours francs ({c['contours_mesures']} mesurés) : dépassement {c['depassement_median'] * 100:.1f} %, transition {c['largeur_transition_px']} px")
    if "jpeg" in m:
        L.append(f"- Blocs JPEG : contraste aux frontières {m['jpeg']['contraste_frontieres_blocs']}")
    p = m.get("poussieres")
    if p:
        L.append(f"- Poussières et points : {p['candidats']} candidats ({p['candidats_par_mpx_lisse']} par Mpx de surface lisse)"
                 + (f" — {', '.join(p['cellules'])}" if p.get("cellules") else ""))
    if "peau" in m:
        pe = m["peau"]
        L += ["", "### Peau", ""]
        L.append(f"- Masque : {pe['methode_masque']}, {pe['part_image_pct']} % de l'image ; visage {pe['largeur_visage_px']} px ({pe['largeur_visage_origine']})")
        if pe.get("note"):
            L.append(f"- {pe['note']}")
        if pe.get("texture"):
            tx = pe["texture"]
            L.append(f"- Texture (écart robuste, niveaux) : grain {tx['grain']} · pores {tx['pores']} · modelé {tx['modele']} ; "
                     f"plages lissées {tx['zones_lissees_pct']} % des {tx['blocs_analyses']} blocs"
                     + (f" ; grain peau / reste {tx['grain_peau_sur_reste']}" if "grain_peau_sur_reste" in tx else ""))
        if pe.get("avant_apres"):
            cs = pe["avant_apres"]["conserve"]
            L.append("- Conservé par la retouche : " + " · ".join(f"{k} {v * 100:.0f} %" for k, v in cs.items() if v is not None))
        if pe.get("couleur"):
            co = pe["couleur"]
            L.append(f"- Couleur : L* {co['L']}, a* {co['a']}, b* {co['b']}, chroma {co['chroma']}, teinte {co['teinte_deg']}° "
                     f"(étendue p10–p90 {co['etendue_teinte_p10_p90']}°) ; taches de couleur {co.get('taches_couleur')}"
                     + (f" (avant : {co['taches_couleur_avant']})" if "taches_couleur_avant" in co else ""))
            if "visage_contre_corps" in co:
                vc = co["visage_contre_corps"]
                L.append(f"- Visage contre reste de la peau, à luminosité égale : écart a*b* {vc['ecart_couleur_ab']}, teinte {vc['dTeinte_deg']:+}° "
                         f"(écart de luminosité global {vc['dL_global']:+} L*)"
                         + (f" ; avant retouche : {vc['ecart_couleur_ab_avant']}" if "ecart_couleur_ab_avant" in vc else ""))
    if "masques" in m:
        L += ["", "### Zones masquées", ""]
        for nom, v in m["masques"].items():
            if "erreur" in v:
                L.append(f"- {nom} : {v['erreur']}")
                continue
            L.append(f"- {nom} : L* {v['L_p1']}–{v['L_p99']} (médiane {v['L_median']}), a* {v['a']:+} b* {v['b']:+}, chroma {v['chroma_median']}"
                     + (f", teinte {v['teinte_deg']}°" if v.get("teinte_deg") is not None else "")
                     + f", brûlé {v['blanc_brule_pct']} %, canal saturé {v['canal_sature_pct']} %"
                     + (f", texture fine conservée {v['texture_fine_conservee'] * 100:.0f} %" if "texture_fine_conservee" in v else ""))
    if "avant_apres" in m:
        aa = m["avant_apres"]
        L += ["", "### Avant / après", ""]
        L.append(f"- Global : ΔL* {aa['dL_moyen']:+}, Δa* {aa['da_moyen']:+}, Δb* {aa['db_moyen']:+} ; contraste × {aa['contraste_ratio']} ; saturation × {aa['saturation_ratio']}")
        L.append(f"- Surface modifiée (ΔE > 3) : {aa['surface_modifiee_pct']} % ; interventions locales les plus fortes : "
                 f"{', '.join(aa['cellules_les_plus_modifiees']) or '—'}")
        dfm = aa["deformation"]
        L.append(f"- Géométrie : déplacement p99 {dfm['deplacement_p99_pct_diagonale']} % de la diagonale, "
                 f"jusqu'à {dfm['deplacement_max_px_pleine_resolution']} px ; surface déformée {dfm['surface_deformee_pct']} %"
                 + (f" ({', '.join(dfm['cellules'])})" if dfm.get("cellules") else ""))
    if m.get("symetrie"):
        s = m["symetrie"]
        L += ["", "### Symétrie et cadrage du sujet", ""]
        L.append(f"- Silhouette symétrique à {s['silhouette_symetrie_gauche_droite_pct']} %, axe incliné de {s['inclinaison_axe_deg']}°, "
                 f"centrage horizontal {s['centrage_horizontal_pct']:+} %, vertical {s['centrage_vertical_pct']:+} %")
        L.append(f"- Marges : gauche {s['marges_pct']['gauche']} %, droite {s['marges_pct']['droite']} %, haut {s['marges_pct']['haut']} %, bas {s['marges_pct']['bas']} %")
    if r["vues"]:
        L += ["", "## Vues de contrôle", ""]
        for v in r["vues"]:
            L.append(f"- `{v['fichier']}` — {v['legende']}")
    if r["tuiles"]:
        L += ["", "## Tuiles", ""]
        L.append("Chaque tuile existe en deux fichiers : l'image (avec l'original à gauche s'il a été fourni) et `_controle` "
                 "(luminance contrastée ou solarisation, à gauche ; passe-haut, à droite).")
        L.append("")
        L.append(", ".join(f"`{t['fichier']}`" for t in r["tuiles"]))
    L += ["", "## Ce que ces mesures ne voient pas", "",
          "Le goût, la justesse d'une expression, la fidélité au produit réel, la cohérence avec le reste de la série, "
          "le rendu à l'impression. Une image sans alerte n'est pas une image validée ; une alerte n'est pas un défaut tant "
          "qu'elle n'est pas confirmée à l'œil sur la vue ou la tuile correspondante.", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------- #
def main(argv=None):
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    p = argparse.ArgumentParser(description="Banc de contrôle d'une retouche photo : mesures, vues de contrôle, tuiles à 100 %.")
    p.add_argument("final", help="image retouchée (TIFF, PNG, JPEG ; PSD avec psd-tools)")
    p.add_argument("--avant", help="original, au même cadrage, pour mesurer ce que la retouche a changé")
    p.add_argument("--genre", default="auto", choices=GENRES)
    p.add_argument("--masque", action="append", default=[], metavar="NOM=FICHIER",
                   help="masque nommé, blanc = zone (peau, metal, or_jaune, pierre, cadran, tissu…). Répétable.")
    p.add_argument("--sortie", help="dossier de sortie (défaut : <final>_controle)")
    p.add_argument("--tuiles", default="12", help="nombre de tuiles choisies d'office, « toutes », ou liste : C4,D4")
    p.add_argument("--taille-tuile", type=int, default=768, help="côté d'une cellule en pixels (défaut 768)")
    p.add_argument("--zoom", type=int, default=1, choices=(1, 2, 3), help="agrandissement des tuiles (2 = 200 %%, chaque cellule en 4 quarts)")
    p.add_argument("--largeur-visage", type=float, help="largeur du visage en pixels si la détection se trompe")
    p.add_argument("--reperes", help="fichier JSON de repères personnels (sortie de etalonner.py)")
    p.add_argument("--symetrie", action="store_true", help="mesurer symétrie, inclinaison et centrage du sujet (packshot de face)")
    p.add_argument("--sans-vues", action="store_true", help="mesures seules, sans images (traitement par lot)")
    p.add_argument("--tuiles-seules", action="store_true",
                   help="complément : écrit seulement les tuiles demandées par --tuiles dans le dossier de sortie, "
                        "sans refaire les mesures ni toucher au rapport")
    p.add_argument("--discret", action="store_true", help="n'affiche que le chemin du rapport, pas les alertes")
    a = p.parse_args(argv)
    if a.tuiles_seules:
        if a.tuiles.strip().isdigit():
            p.error("--tuiles-seules attend une liste de cellules (--tuiles C4,D4) ou « toutes »")
        avec_peau = a.genre in GENRES_PEAU or (a.genre == "auto" and bool(detecter_visages(charger(a.final)["srgb8"])))
        t = tuiles_seules(a.final, a.avant, a.sortie, a.tuiles, a.taille_tuile, a.zoom, avec_peau, a.largeur_visage)
        dossier = Path(a.sortie) if a.sortie else Path(a.final).with_name(Path(a.final).stem + "_controle")
        print(f"{len(t)} tuiles écrites dans {dossier / 'tuiles'} : " + ", ".join(x["cellule"] for x in t))
        return 0
    masques = {}
    for mq in a.masque:
        if "=" not in mq:
            p.error(f"--masque attend NOM=FICHIER, reçu : {mq}")
        n, ch = mq.split("=", 1)
        masques[n.strip()] = ch.strip()
    rep = None
    if a.reperes:
        rep = json.loads(Path(a.reperes).read_text(encoding="utf-8")).get("reperes")
    r = analyser(a.final, a.avant, a.genre, masques, a.sortie, a.tuiles, a.taille_tuile, a.zoom, a.largeur_visage, rep,
                 a.symetrie, a.sans_vues)
    if a.discret:
        print(f"Rapport : {Path(r['dossier']) / 'rapport.md'}")
        return 0
    n = {g: sum(1 for x in r["alertes"] if x["gravite"] == g) for g in ("majeur", "mineur", "info")}
    print(f"{r['fichier']['nom']} — genre {r['genre']} — alertes : {n['majeur']} majeures, {n['mineur']} mineures, {n['info']} infos")
    for x in r["alertes"]:
        print(f"  [{x['gravite']}] {x['code']}" + (f" ({x['zone']})" if x["zone"] else "") + f" : {x['message']}")
    print(f"Rapport : {Path(r['dossier']) / 'rapport.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
