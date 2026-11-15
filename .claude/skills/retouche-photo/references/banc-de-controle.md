# Le banc de contrôle : lancer, lire, étalonner

## Sommaire
1. Installation
2. Les trois scripts
3. Ce qui sort
4. Lire les vues
5. Lire les tuiles
6. Codes d'alerte et faux positifs connus
7. Masques nommés
8. Étalonner sur ses propres images
9. Ce qui a été vérifié, ce qui ne l'a pas été

## 1. Installation

```
pip install numpy pillow opencv-python-headless
pip install tifffile psd-tools        # facultatif : TIFF 16 bits compressés, PSD
```

Python 3.10 ou plus récent. Fonctionne sous Windows, macOS, Linux. Le détecteur de visage (`assets/face_detection_yunet_2023mar.onnx`, licence MIT) est fourni ; sans lui, le banc tourne mais le masque de peau devient approximatif.

Formats lus : TIFF et PNG en 8 et 16 bits, JPEG, PSD aplati (avec psd-tools, en 8 bits). Pas de RAW : exporter un TIFF 16 bits.

## 2. Les trois scripts

```
# une image, avec son original quand il existe (même cadrage)
python scripts/controle_retouche.py final.tif --avant original.tif --genre beaute

# une série
python scripts/controle_serie.py dossier --genre packshot --reference vue_validee.jpg

# repères personnels, à partir d'images validées
python scripts/etalonner.py finals_valides --avant originaux --genre beaute --sortie reperes_beaute.json
python scripts/controle_retouche.py final.tif --avant original.tif --reperes reperes_beaute.json
```

Options de `controle_retouche.py` :

| Option | Effet |
|---|---|
| `--avant` | original au même cadrage : active toutes les mesures « conservé par la retouche », la carte des différences et la détection de déformation |
| `--genre` | `beaute`, `portrait`, `mode`, `bijou`, `montre`, `packshot`, `general`, ou `auto` (visage détecté → portrait, fond uni → packshot) |
| `--masque nom=fichier` | zone à mesurer à part (blanc = zone). Répétable. Voir § 7 |
| `--tuiles` | `12` par défaut ; un nombre, `toutes`, ou une liste `C4,D4` |
| `--zoom 2` | tuiles à 200 %, chaque cellule coupée en quatre (a, b, c, d) |
| `--taille-tuile` | côté d'une cellule, 768 px par défaut |
| `--symetrie` | symétrie, inclinaison, centrage et marges du sujet sur fond uni |
| `--largeur-visage` | à donner si le visage n'est pas détecté ou mal mesuré |
| `--reperes` | fichier de repères personnels |
| `--sans-vues` | mesures seules, pour un lot |

Durée mesurée : 6 s pour 9 Mpx, 21 s pour 45 Mpx avec original, 2,4 Go de mémoire.

## 3. Ce qui sort

Dans `<final>_controle/` :
- `rapport.md` : alertes triées par gravité, mesures, liste des vues et des tuiles. À lire en premier.
- `rapport.json` : la même chose, pour un traitement automatique.
- `vues/` : l'image entière sous plusieurs éclairages de contrôle, 1568 px de grand côté.
- `tuiles/` : des morceaux à 100 %, deux fichiers par cellule.

Les cellules sont nommées comme sur un plan : colonne en lettre, ligne en chiffre (`C4`). La vue `00_apercu_grille` montre le quadrillage, en jaune les cellules qui ont une tuile.

## 4. Lire les vues

| Vue | Ce qu'elle montre | Ce qu'on y cherche |
|---|---|---|
| `00_apercu_grille` | l'image et le quadrillage | lecture d'ensemble, localisation |
| `01_ecretage` | rouge : blanc brûlé ; jaune : un canal au maximum ; bleu : noir bouché ; cyan : un canal à zéro | brûlures sur le sujet, couleurs en aplat |
| `02_solarisation` | courbe en dents de scie par canal | poussières, raccords de tampon, dégradés irréguliers, paliers, salissures du fond |
| `03_luminance` | noir et blanc contrasté | hiérarchie de lumière, taches de densité, halos de dodge and burn, dégradés de métal |
| `04_saturation` | blanc = saturé | plaques de saturation, bords de masque, zones éteintes |
| `05_teinte` | teinte seule à saturation maximale, gris = neutre | plaques de teinte sur la peau, métal ou fond qui vire, dominantes locales |
| `05b_masque_peau` | ce que les mesures ont pris pour de la peau | si le masque déborde ou manque, les chiffres de peau sont à relativiser |
| `06_texture` | passe-haut de l'aperçu | continuité de la matière à l'échelle de l'image |
| `07_fond` | fond étiré au maximum | fond sale ou inégal, halo et frange de détourage, ombre coupée |
| `08_paliers` | carte des marches franches | où se trouve le banding |
| `09_poussieres` | candidats cerclés sur la solarisation | poussières, pétouilles, points de capteur |
| `10_avant_apres` | original et final | ce qui a changé, d'un coup d'œil |
| `11_difference` | à gauche l'écart total, à droite l'écart local (étalonnage retiré) | où la retouche a porté, ce qui a été oublié |
| `12_deformation` | déplacement des pixels | fluidité, déformation, ce qu'elle a entraîné |

Les vues 07 à 12 n'apparaissent que si elles ont quelque chose à montrer.

## 5. Lire les tuiles

Chaque cellule choisie donne `C4.png` (l'image à 100 %, avec l'original à gauche s'il a été fourni) et `C4_controle.png` (à gauche la luminance contrastée pour une image avec peau, la solarisation pour un produit ; à droite le passe-haut).

Le passe-haut est la vue la plus parlante : un gris uni à l'endroit où le reste est granuleux, c'est une texture perdue ; un motif qui se répète, c'est un tampon ; des traits orientés tous pareil, c'est une fluidité ou un flou directionnel.

Les tuiles sont choisies d'office sur les cellules citées par une alerte, puis sur les yeux et la bouche, la peau, le sujet, et là où la retouche a le plus porté. Douze ne couvrent pas une image de 45 Mpx : demander celles qui manquent avec `--tuiles`, et `--zoom 2` pour un bijou.

## 6. Codes d'alerte et faux positifs connus

Une alerte est une piste. Elle ne devient un défaut qu'une fois vue.

| Code | Signifie | Faux positifs connus |
|---|---|---|
| PROFIL_ABSENT | pas de profil incorporé | aucun |
| HORS_GAMUT_SRGB | des couleurs sortent du sRGB | normal sur un maître en espace large |
| BLANC_BRULE, CANAL_BRULE | hautes lumières ou canal au maximum, hors fond | spéculaires de métal et de pierre ; fond clair mal détecté |
| NOIR_BOUCHE | noirs à zéro sur le sujet | fond noir mal détecté, parti pris graphique |
| NOIRS_DECOLLES, BLANCS_ETEINTS | pas de vrai noir, pas de vrai blanc | rendu mat, low-key : simple information |
| DOMINANTE_NEUTRES | les quasi-neutres ont une couleur | décor chaud ou froid ; étalonnage voulu (information hors produit) |
| DOMINANTE_CROISEE | ombres et hautes lumières tirent en sens opposés | virage partiel voulu |
| FOND_TEINTE, FOND_INEGAL, FOND_BLANC_PAS_PUR | fond pas neutre, pas uni, pas à 255 | dégradé de fond voulu, blanc cassé voulu |
| BANDING | marches de 2 niveaux et plus | aplats graphiques voisins |
| DEGRADE_SANS_GRAIN | dégradé lisse, marches de 1 niveau : risque, pas défaut | image de synthèse, fond numérique |
| HISTOGRAMME_PEIGNE | tonalité étirée en 8 bits | image très peu nuancée |
| FAUX_16_BITS | 16 bits issu d'un 8 bits | aucun |
| HALOS | dépassement aux contours francs | contours naturellement liserés (contre-jour, rim light) |
| BLOCS_JPEG, JPEG_QUALITE_BASSE | compression visible | aucun en dessous de la qualité 90 |
| POUSSIERES | petites taches isolées sur surface lisse | micro-reflets, gravures, grains de beauté, étoiles, paillettes |
| PEAU_TEXTURE_PERDUE, PEAU_TEXTURE_GONFLEE | pores conservés hors plage (avec original) | recadrage ou réduction entre original et final |
| PEAU_APLAT | modelé écrasé, pores gardés | changement d'éclairage voulu |
| PEAU_LISSAGE_LOCAL | plages plus lisses que le reste | zones hors mise au point, maquillage couvrant |
| GRAIN_INCOHERENT | peau plus lisse au pixel que le reste | fond très texturé |
| PEAU_TEINTE_INEGALE, PEAU_TACHES_AJOUTEES | plaques de couleur ; plus qu'avant | lumière mixte, maquillage coloré |
| PEAU_VISAGE_CORPS, PEAU_VISAGE_DESACCORDE | visage et corps de couleurs différentes ; écart creusé par la retouche | éclairage coloré différent sur le corps |
| PEAU_BRULEE, PEAU_HL_CRAYEUSES, PEAU_OMBRES_GRISES | brillances et ombres sans couleur | maquillage nacré, contre-jour |
| PEAU_SATUREE, PEAU_TROP_ROUGE, PEAU_TROP_JAUNE | couleur de peau hors plage usuelle | étalonnage voulu, lumière colorée |
| DEFORMATION | la géométrie a bougé | recadrage, redressement d'objectif entre les deux fichiers |
| METAL_PAS_NEUTRE, METAL_PLAT | métal blanc teinté ; métal sans contraste | masque qui déborde sur autre chose |
| TISSU_MATIERE_PERDUE, TISSU_COULEUR_BOUCHEE, TISSU_NOIR_SANS_MATIERE | matière, couleur ou noir en aplat | tissu réellement lisse |
| MOIRE_COULEUR | motif périodique de couleur | motif tissé ou imprimé régulier |

Les repères qui dépendent du goût, de la carnation ou de la lumière (taches de couleur, visage contre corps, saturation de peau, plages lissées, aplat, fond inégal, métal plat) descendent d'un cran tant qu'ils n'ont pas été étalonnés, et le rapport l'écrit. Ceux qui tiennent au fichier (écrêtage, banding, halos, profil, texture conservée, déformation) gardent leur gravité.

## 7. Masques nommés

Un masque est une image en niveaux de gris à la taille du fichier, blanc sur la zone. Sources possibles : une couche alpha ou un tracé exportés de Photoshop, une sélection du connecteur Adobe (`image_select_subject` ou `image_select_by_prompt`, téléchargée), un modèle de segmentation local.

Le nom décide du contrôle appliqué :
- `peau` : remplace la détection automatique de la peau.
- `metal`, `acier`, `argent`, `platine`, `or_blanc`, `titane` : neutralité et étendue tonale.
- `or…`, `gold…` : étendue tonale, teinte relevée.
- `tissu…`, `vetement…`, `maille…`, `cuir…`, `soie…`, `velours…`, `denim…` : matière conservée, couleur bouchée, noir sans matière, moiré.
- tout autre nom (`pierre`, `cadran`, `fond`…) : statistiques seules (L*, a*, b*, teinte, écrêtage, texture).

## 8. Étalonner sur ses propres images

Les repères par défaut sont raisonnables, pas justes. `etalonner.py` mesure un dossier d'images que Charles a validées, avec leurs originaux quand ils existent, et fixe chaque borne à la limite de ce qu'il valide d'habitude. Un fichier par type d'image. Il en faut au moins huit, vingt à trente pour des bornes stables.

Le même relevé sert à chiffrer un rendu de référence : un dossier de visuels officiels d'une maison donne ses valeurs de fond, de neutralité, de marges, d'inclinaison.

## 9. Ce qui a été vérifié, ce qui ne l'a pas été

Vérifié le 15/11/2026, sur des photos libres de droits et des défauts fabriqués exprès à partir d'un portrait : peau floutée (détectée, 5 % de texture conservée), fluidité de 25 px (détectée et localisée), accentuation excessive (détectée), visage rougi seul (détecté), ciel postérisé (détecté), image grainée (4 487 fausses poussières ramenées à 5 après correction). Lecture des TIFF 16 bits, d'un PNG détouré, d'un fichier de 45 Mpx ; cohérence de série sur quatre vues dont deux dérivées.

Pas vérifié : aucune vraie retouche de Charles, aucun vrai fichier de bijou ou de montre en haute définition, aucun fichier en Adobe RGB ou ProPhoto, aucun PSD. Les seuils n'ont été confrontés à aucune image validée par lui. Tant que l'étalonnage n'est pas fait, lire les chiffres comme des ordres de grandeur.
