# Peau — beauté, portrait, mode

## Sommaire
1. Ce qu'on cherche
2. Diagnostic : trois échelles
3. Les passes, dans l'ordre
4. Séparation de fréquences : quand oui, quand non
5. Détails du visage et du corps
6. Outils IA : où ils aident, où ils cassent
7. Repères chiffrés
8. Signatures d'une peau ratée

## 1. Ce qu'on cherche

Une peau vivante : texture continue d'un bord à l'autre du visage, volume lisible, couleur homogène sans être uniforme. Le test tient en deux regards. À 100 %, il y a des pores partout où l'original en avait, et ils ont la même taille et la même netteté d'une zone à sa voisine. À distance de lecture, on ne voit pas la retouche, on voit quelqu'un qui a bien dormi et qui est bien éclairé.

Tout le reste en découle : on ne lisse pas, on égalise. Le flou détruit l'information au lieu de la corriger, et une fois les pores partis aucun grain ajouté ne les rend.

## 2. Diagnostic : trois échelles

Chaque défaut vit à une échelle, et l'outil doit agir à cette échelle et pas aux autres. C'est la règle qui évite neuf erreurs sur dix. Les tailles ci-dessous sont rapportées à la largeur du visage dans l'image (LV), parce qu'un rayon en pixels ne veut rien dire sans elle.

| Échelle | Taille | Ce qu'on y trouve | Outil |
|---|---|---|---|
| Texture | sous LV/400 | pores, duvet, ridules, grain | correcteur et tampon sur calque vide, greffe de texture |
| Modelé local | de LV/400 à LV/40 | taches, rougeurs diffuses, cernes, veines, creux, peau d'orange, brillances | dodge and burn micro |
| Forme | au-delà de LV/40 | volumes du visage, direction de la lumière, ombres portées | dodge and burn macro, courbes masquées |

Lire l'image dans cet ordre avant de toucher : ce qui dérange vient presque toujours du modelé local, rarement de la texture. Un retoucheur qui s'attaque à la texture pour régler un problème de modelé produit la peau plastique.

## 3. Les passes, dans l'ordre

**Nettoyage ponctuel.** Correcteur et tampon sur un calque vide, échantillon « actif et inférieurs », dureté élevée pour ne pas baver. On enlève le passager (bouton, peluche, poil isolé, pellicule, marque de vêtement, rougeur du jour). On garde le permanent (grain de beauté, cicatrice, taches de rousseur, ride d'expression) sauf demande contraire : c'est l'identité de la personne, et un visage sans aucun repère ne ressemble plus à personne. Une ride se détend, elle ne s'efface pas.

**Dodge and burn micro.** Deux calques de courbes, une claire et une sombre, masques noirs, pinceau doux en blanc. Les sources de référence convergent : opacité de 3 à 5 % ou flux de 1 à 2 %, zoom entre 60 et 200 %, et un pinceau de la taille de la tache à corriger, pas plus. Au-delà de 1 à 2 % de flux on ne contrôle plus l'accumulation. On travaille sous un calque de contrôle noir et blanc contrasté, qu'on coupe régulièrement pour revenir à la couleur. Le geste : éclaircir ce qui est trop sombre par rapport à son entourage immédiat, assombrir ce qui est trop clair, jamais l'inverse, et s'arrêter quand la transition est régulière, pas quand elle est plate. Les pores ne se remplissent pas : un pore est une ombre, l'éclaircir c'est l'effacer.

**Dodge and burn macro.** Même montage, pinceau large, pour renforcer les volumes que la lumière a déjà posés : arête du nez, pommettes, front, menton, creux des joues, clavicules. On suit la lumière existante. Inventer une direction de lumière que la prise de vue n'a pas donnée se voit tout de suite, parce que les ombres portées et les reflets dans les yeux racontent autre chose.

**Couleur.** Le dodge and burn dérègle la saturation : ce qu'on assombrit se sature, ce qu'on éclaircit se délave. La correction se fait par un calque Teinte/Saturation écrêté sur chaque courbe (désaturer légèrement le burn, resaturer le dodge), sous contrôle d'un calque de saturation. Puis, dans cet ordre : rougeurs (plage des rouges de Teinte/Saturation décalée vers le jaune, masque peint, jamais de désaturation globale qui grise la peau), zones jaunes ou verdâtres, raccord visage / cou / décolleté / mains, hautes lumières qui doivent garder une couleur de peau, ombres qui ne doivent pas virer au gris.

**Texture.** Là où il n'y en a plus (brillance brûlée, zone trop corrigée), on greffe : tampon sur la couche haute d'une séparation de fréquences, depuis une zone voisine qui a la même taille de pore et la même direction de lumière. Une greffe prise ailleurs se trahit par l'échelle (pores du front sur une joue) ou par l'éclairage (relief éclairé à contresens).

**Fluidité.** En dernier parmi les passes de forme, légère, avec un gel des zones voisines. Tout déplacement entraîne ce qui est derrière : une ligne de décor, un col, une bretelle, une chaîne. Voir `livraison-droit.md` pour la mention obligatoire quand la silhouette d'un mannequin est affinée ou épaissie dans une image commerciale.

## 4. Séparation de fréquences : quand oui, quand non

Oui pour trois usages : corriger une transition de couleur ou de densité sous une texture intacte, nettoyer des poils ou des cheveux sur la peau sans toucher à la couleur dessous, greffer de la texture. Non comme méthode de lissage : peindre la couche basse au pinceau doux ou au pinceau mélangeur donne la peau cireuse, puis la « peau d'orange » quand la texture d'origine flotte sur un fond devenu trop lisse.

Réglages d'Appliquer une image sur la couche haute :
- 8 bits : fusion Soustraction, échelle 2, décalage 128, puis mode Lumière linéaire.
- 16 bits : fusion Addition, case Inverser cochée, échelle 2, décalage 0, puis mode Lumière linéaire.

Se tromper de recette entre 8 et 16 bits donne une image grise ou un décalage de densité, c'est l'erreur la plus courante.

Rayon : le plus petit qui fait disparaître la texture de la couche basse. Aucun barème par résolution n'est publié ; un exemple documenté donne 3,5 px correct et 7,8 px excessif sur le même fichier. Repère de travail [non sourcé, cohérent avec le banc de contrôle] : entre LV/500 et LV/300. Trop grand, la couche haute emporte du modelé et toute correction sur la couche basse crée des halos.

La « bande médiane » (passe-haut inversé) atténue le modelé local d'un bloc, sans discernement. Acceptable à faible dose sur un lot BtoC, pas sur une image de beauté : elle aplatit ce que le dodge and burn devait sculpter.

## 5. Détails du visage et du corps

- **Yeux.** Le blanc de l'œil est une sphère : il a un dégradé, des veinules, une ombre portée de la paupière. Le blanchir à plat est un échec classique, que les retoucheurs citent nommément. On atténue les veines, on ne les supprime pas toutes. L'iris garde sa structure rayonnante et son cerne sombre ; l'éclaircir uniformément donne un regard de poupée. Les reflets doivent correspondre à l'éclairage réel, et être cohérents entre les deux yeux.
- **Sourcils et cils.** Combler les trous poil par poil, dans le sens de la pousse. Pas de contour dessiné.
- **Lèvres.** Garder les stries verticales et le relief ; nettoyer le contour sans le redessiner ; le brillant est un reflet, il a une forme.
- **Dents.** Désaturer le jaune, éclaircir peu. Des dents blanc papier, plus claires que le blanc de l'œil, sonnent faux. Garder les différences de teinte d'une dent à l'autre.
- **Cheveux.** Enlever les mèches qui traversent le visage et les cheveux isolés qui accrochent l'œil, pas tous les cheveux fous : une chevelure au contour parfaitement net a l'air découpée. Combler les trous de la raie et les transparences.
- **Cou, mains, corps.** Plis du cou adoucis, pas effacés. Mains : rougeur des jointures, veines atténuées, cuticules, ongles. Coudes, genoux, aisselles : densité et couleur ramenées vers la peau voisine. Les mains et le cou trahissent une retouche qui s'est arrêtée au visage.

## 6. Outils IA : où ils aident, où ils cassent

État de novembre 2026, détail et sources dans `veille-2026-11.md`.

- Les comparatifs de 2026 s'accordent sur une répartition : l'IA traite les 80 % répétitifs (nettoyage, premier dodge and burn), la finition beauté reste manuelle.
- Retouch4me (Heal, Dodge&Burn, Skin Tone…) : traitement local, par actions Photoshop sur TIFF 16 bits. Heal est réputé garder pores et ridules. Échecs connus : dentelle, tatouages, taches de rousseur (qu'il efface). Toujours sur un calque à part, à opacité réglable.
- Lightroom Classic 16 (suppression IA des imperfections, visage par visage) et Capture One 16.9 (Skin Tone, Body Skin Retouching, en local) : bons pour une série, à contrôler.
- Evoto : rendu « plastique » par défaut, à baisser fortement. Le filtre Neural de lissage de peau de Photoshop : à éviter, et de toute façon en panne sur les versions 27.
- Édition générative (Firefly, Qwen, FLUX) sur un visage : elle régénère la peau au lieu de la corriger. Jamais sur un visage livré, sauf demande explicite, et alors avec les obligations de `livraison-droit.md`.

Quel que soit l'outil : passer le résultat au banc de contrôle avec l'original. Une IA qui « garde la texture » en garde parfois 60 %.

## 7. Repères chiffrés

Ce sont les repères par défaut du banc (`banc-de-controle.md`), à remplacer par ceux tirés de tes images validées avec `etalonner.py`.

| Mesure | Bon | À regarder | Raté |
|---|---|---|---|
| Texture fine conservée (pores, avec original) | ≥ 80 % | 60 à 80 % | < 60 % |
| Texture fine augmentée | ≤ 125 % | 125 à 160 % | > 160 % |
| Modelé local conservé, pores gardés | ≥ 45 % | 30 à 45 % | < 30 % : aplat |
| Blocs de peau plus lisses que le reste | < 6 % | 6 à 18 % | > 18 % |
| Peau n fois plus lisse au pixel que le reste | < 1,8 | 1,8 à 3 | > 3 |
| Peau avec un canal saturé | < 0,3 % | 0,3 à 2 % | > 2 % |

Lecture croisée, plus parlante que chaque chiffre : pores perdus et modelé perdu ensemble, c'est du flou ; pores gardés et modelé écrasé, c'est du dodge and burn poussé jusqu'à l'aplat ; pores gonflés, c'est de l'accentuation ou du grain rajouté pour masquer un lissage.

## 8. Signatures d'une peau ratée

- Peau plastique ou cireuse : plus de pores, brillances en aplat.
- Peau d'orange : texture nette posée sur un modelé trop lisse.
- Plages mortes : une zone sans texture (sous les yeux, front, menton) au milieu d'une peau texturée.
- Halos de dodge and burn : auréoles claires ou sombres plus grandes que le défaut corrigé, visibles sur le calque noir et blanc.
- Taches de saturation : plaques orangées là où on a assombri, grises là où on a éclairci.
- Visage en masque : teinte et densité du visage qui ne raccordent ni au cou ni aux mains.
- Texture répétée : même motif de pores deux fois (tampon), ou pores étirés dans une direction (fluidité).
- Arêtes perdues : nez sans arête, mâchoire floue, lèvre supérieure sans bord.
- Yeux de poupée : blanc uni, iris uniformément clair, reflets rajoutés.
- Grain incohérent : peau lisse au pixel dans une image grainée.
- Volume perdu : visage plat parce que les ombres utiles ont été éclaircies avec les défauts.
