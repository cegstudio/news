# Grille de l'agent critique

La grille sert à ne rien oublier, pas à cocher. Un défaut ne compte que s'il est vu sur une vue ou une tuile, ou mesuré par le banc.

## Gravités

| Gravité | Définition | Conséquence |
|---|---|---|
| **Bloquant** | Se voit en lecture normale, trahit le produit (couleur, matière, construction), ou engage une obligation légale non remplie. Un directeur artistique le refuse sans discuter. | Un seul suffit : pas livrable. |
| **Majeur** | Un œil professionnel le voit à 100 %. | À corriger avant livraison au niveau luxe ; tolérable sur une série e-commerce si le brief le dit. |
| **Mineur** | Perfectible, ne se remarque pas sans le chercher. | À corriger si le temps le permet. |
| **Doute** | Ni confirmé ni écarté avec ce qui a été fourni. | À dire tel quel, avec ce qu'il faudrait pour trancher. |

Le niveau de finition demandé déplace les gravités d'un cran, jamais de deux : une poussière sur un fond de lookbook est mineure, la même sur un cadran de montre est bloquante.

## Lecture d'ensemble (avant tout zoom)

| Question | Où regarder |
|---|---|
| Où va l'œil en premier ? Est-ce le bon endroit ? | aperçu, vue de luminance |
| L'image a-t-elle un vrai noir et un vrai blanc, là où il faut ? | rapport (tonalité), vue d'écrêtage |
| La lumière est-elle crédible : une direction, des ombres cohérentes ? | aperçu |
| La couleur d'ensemble sert-elle l'intention du brief ? | aperçu, rapport (neutres) |
| Voit-on la retouche ? | aperçu, à l'instinct, avant d'avoir lu les mesures |

## Peau

| Défaut | Comment il se voit | Gravité usuelle | Correction |
|---|---|---|---|
| Peau plastique, texture perdue | PEAU_TEXTURE_PERDUE ; passe-haut vide sur les tuiles | bloquant en beauté, majeur ailleurs | revenir à l'original, dodge and burn, greffe de texture |
| Plages mortes | PEAU_LISSAGE_LOCAL ; trous dans le passe-haut | majeur | greffe depuis une zone voisine de même lumière |
| Aplat, volume perdu | PEAU_APLAT ; luminance contrastée sans relief | majeur | baisser l'opacité du groupe dodge and burn, rendre les ombres utiles |
| Halos de dodge and burn | auréoles sur la luminance contrastée | majeur | reprendre au pinceau plus petit |
| Taches de saturation ou de teinte | vues de saturation et de teinte ; PEAU_TACHES_AJOUTEES | majeur | calque Teinte/Saturation écrêté sur les courbes |
| Visage non raccordé au corps | PEAU_VISAGE_DESACCORDE ; comparaison cou, mains | majeur | étendre la correction de couleur |
| Brillances brûlées ou crayeuses | PEAU_BRULEE, PEAU_HL_CRAYEUSES | majeur | récupérer au RAW, recolorer, greffer |
| Ombres grises | PEAU_OMBRES_GRISES | mineur | calque couleur dans les ombres |
| Texture répétée ou étirée | motif identique, pores en ovale sur les tuiles | majeur | refaire la zone depuis l'original |
| Grain de peau différent du reste | GRAIN_INCOHERENT | majeur | grain commun en finition |
| Yeux : blanc uni, iris uniforme, reflets faux | tuile des yeux | majeur | rendre le dégradé du globe, la structure de l'iris |
| Dents blanc papier, lèvres lissées | tuile de la bouche | mineur à majeur | baisser, rendre les stries |
| Contour du visage ou des cheveux découpé | bord net artificiel, frange | majeur | masque repris, mèches rendues |
| Permanents effacés (grain de beauté, rousseur) sans demande | avant/après | majeur | les rendre |
| Silhouette modifiée | DEFORMATION ; vue de déformation | selon le brief ; bloquant si la mention légale manque | voir `livraison-droit.md` |
| Décor entraîné par la fluidité | lignes tordues près du corps | bloquant | geler et refaire |

## Lumière et couleur

| Défaut | Comment il se voit | Gravité usuelle | Correction |
|---|---|---|---|
| Blanc brûlé sur le sujet | BLANC_BRULE ; rouge sur la vue d'écrêtage | majeur à bloquant | récupérer au RAW |
| Canal saturé | CANAL_BRULE ; jaune sur la vue d'écrêtage | majeur | ramener dans le gamut, désaturer localement |
| Noirs bouchés avec matière perdue | NOIR_BOUCHE | majeur | déboucher par courbe masquée |
| Dominante sur un neutre | DOMINANTE_NEUTRES, FOND_TEINTE, METAL_PAS_NEUTRE | bloquant sur un produit | courbes par canal |
| Banding | BANDING ; vue des paliers, solarisation | majeur ; bloquant sur un fond de packshot de luxe | 16 bits, dégradé refait, grain |
| Halos d'accentuation | HALOS ; liseré sur les tuiles | majeur | accentuation refaite, rayon plus petit, par masque |
| Faux HDR, contraste local excessif | auréoles larges, image grise | majeur | revenir en arrière |
| Vignetage visible, bord qui attire l'œil | aperçu, luminance | mineur | assombrir par zones |
| Grain incohérent entre zones | passe-haut des tuiles | majeur | grain commun |
| Profil absent, JPEG trop compressé | PROFIL_ABSENT, BLOCS_JPEG | bloquant à la livraison | réexporter |

## Tissu

| Défaut | Comment il se voit | Gravité usuelle | Correction |
|---|---|---|---|
| Matière lissée | TISSU_MATIERE_PERDUE ; passe-haut | bloquant en e-commerce et en luxe | refaire les plis en dodge and burn |
| Couleur infidèle ou variable dans la série | `controle_serie.py` ; comparaison à l'échantillon | bloquant | recaler sur la charte |
| Plis de manipulation, peluches, fils, épingles | tuiles | majeur | nettoyer |
| Vêtement sans aucun pli | aperçu | majeur | rendre les plis de tombé |
| Motif cassé, répété, déformé | tuiles | bloquant | refaire depuis l'original |
| Moiré | MOIRE_COULEUR ; tuiles, et à la taille de livraison | majeur | canaux a et b, ou reprise de vue |
| Noir sans matière, blanc brûlé, couleur en aplat | TISSU_NOIR_SANS_MATIERE, TISSU_COULEUR_BOUCHEE | majeur | courbes masquées |
| Contour rasé, frange de détourage | vue du fond | majeur | masque repris |
| Asymétrie, raccord de ghost mannequin, étiquette | aperçu, tuiles | majeur | reprise |

## Bijou, montre, packshot

| Défaut | Comment il se voit | Gravité usuelle | Correction |
|---|---|---|---|
| Poussière, rayure, trace de doigt | POUSSIERES ; vue des poussières, tuiles à 200 % | bloquant sur l'objet, majeur sur le fond | nettoyer |
| Reflet du studio | tuiles, solarisation | bloquant | reconstruire la surface |
| Métal blanc pas neutre | METAL_PAS_NEUTRE ; vue de teinte | bloquant | neutraliser dans le tracé |
| Métal plat ou plastique | METAL_PLAT ; luminance contrastée | bloquant | redessiner le dégradé, poser les noirs |
| Dégradé de métal sale ou cassé | solarisation | majeur | reconstruire |
| Brossage effacé ou à contresens | passe-haut des tuiles | majeur | régénérer dans le bon sens |
| Arête molle, contour frangé, halo | HALOS ; tuiles, vue du fond | majeur | tracé repris |
| Index, maillons, griffes inégaux | tuiles | majeur | égaliser |
| Cadran taché ou irrégulier ; texte flou | tuiles, solarisation | bloquant | refaire |
| Pierre éteinte, lissée, facettes floues | tuiles | bloquant | recontraster dans le tracé |
| Même pierre répétée ; étincelles ajoutées | tuiles | bloquant | refaire pierre par pierre |
| Or qui vire (cuivre, vert) ou qui change dans la série | vue de teinte, `controle_serie.py` | bloquant | recaler la teinte |
| Aiguilles, date, couronne incohérentes | aperçu | bloquant | recomposer |
| Ombre absente, flottante, incohérente | aperçu, vue du fond | majeur | refaire l'ombre |
| Fond sale, inégal, pas à 255 quand il doit l'être | FOND_INEGAL, FOND_BLANC_PAS_PUR ; vue du fond | majeur à bloquant | nettoyer, niveler |
| Objet penché, décentré, marges inégales dans la série | symétrie du rapport | majeur | redresser, recadrer |
| Détail de fabrication repeint, poinçon effacé | avant/après | bloquant sans accord écrit du client | rendre |

## Livraison

| Point | Vérification |
|---|---|
| Dimensions, rapport, poids, format demandés | rapport (fichier) contre le brief |
| Profil incorporé, bon espace | rapport |
| Fond conforme à la destination | rapport (fond) |
| Netteté et grain réglés à la taille livrée | tuiles du fichier livré, pas du maître |
| Mentions légales si elles s'appliquent | `livraison-droit.md` |
