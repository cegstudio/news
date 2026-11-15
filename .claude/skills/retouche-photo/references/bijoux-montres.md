# Joaillerie et horlogerie

## Sommaire
1. Ce que veut dire « rendu Cartier, Rolex, Tissot »
2. Ce qui se joue à la prise de vue
3. Montre : le flux de retouche
4. Joaillerie : pierres, sertis, perles, chaînes
5. Métaux précieux et déclinaisons
6. Ce qu'un directeur artistique refuse
7. Ce que le banc mesure sur un bijou
8. Temps et niveau de finition

Les passages marqués [analyse] sont des règles de métier non sourcées ; le reste vient de la veille (`veille-2026-11.md`).

## 1. Ce que veut dire « rendu Cartier, Rolex, Tissot »

Ce que la veille établit sur la fabrication des visuels officiels :

- **Rolex** : un studio de CGI (Taylor James) déclare avoir produit douze montres en image de synthèse pour le print, le CGI ayant remplacé la prise de vue. Les planches presse créditent par ailleurs des photographes et un studio. La part de photo et de 3D sur le site n'est documentée nulle part.
- **Cartier** : les films et les dispositifs de salon sont en 3D intégrale (plusieurs crédits de studios). Les visuels fixes sont crédités à des photographes de nature morte sur le site de la maison. L'hybride est attesté de longue date (maquettes photographiées, éléments 3D ajoutés pour les reflets).
- **Tissot** : presque rien de public, hors un film en image de synthèse.
- **Signature visuelle de chaque maison** (traitement des métaux, du cadran, des reflets, des ombres, teinte de l'or) : aucune source, ni professionnelle ni amateur, ne la décrit. Elle se relève sur pièces.

Deux conséquences pratiques.

La référence n'est pas une photo, c'est un objet idéal contrôlé au pixel. Une image photographique qui vise ce niveau se traite comme une illustration sur base photographique : chaque surface est détourée, nettoyée, et son dégradé reconstruit. On ne « corrige » pas une montre, on la redessine avec sa propre lumière.

Le rendu d'une maison se relève, il ne se devine pas. Quand Charles vise une maison précise : réunir dix à vingt visuels officiels du même type (packshot de face, trois quarts, porté), les passer au banc avec des masques métal, cadran et fond, et en tirer un profil chiffré (neutralité et étendue tonale du métal, densité et teinte du fond, nature de l'ombre, marges, inclinaison). `scripts/relever_rendu.py` fait ce relevé sur un dossier, avec un masque par zone et par image. Sans ce relevé, parler du « rendu Cartier » est une impression, pas une cible.

Ce qui est commun au haut de gamme [analyse] :
- Chaque surface métallique porte un dégradé propre, du noir franc au blanc, sans accident. Un photographe joaillier le formule ainsi : un blanc et un noir francs dans chaque image.
- La frontière entre poli et satiné est nette ; le sens du brossage est lisible et constant.
- Aucun reflet ne raconte le studio (trépied, boîte à lumière reconnaissable, photographe, plafond).
- Le cadran est d'une régularité parfaite ; chaque index a le même éclat que son voisin ; les textes sont nets.
- Les métaux blancs sont neutres ; les ors ont une teinte constante d'une vue à l'autre.
- Zéro poussière, zéro rayure, zéro trace de doigt, à 200 %.
- L'ombre et le reflet au sol existent et obéissent à la même lumière que l'objet.

## 2. Ce qui se joue à la prise de vue

La retouche assemble ce que la prise de vue a prévu de séparer. Chiffres relevés chez des photographes de référence :

- Empilement de mise au point : 13 plans à f/22 pour une image, 16 plans à f/13 pour une autre ; ailleurs 22 plans de mise au point combinés à 10 à 15 expositions.
- Une exposition par élément : le fond sans les caches, les index, le cadran avec une source dédiée. Les papiers noirs qui tuent les reflets parasites sont dans le champ et retirés en retouche.
- Couronne tirée pour arrêter les aiguilles, puis repoussée en retouche.
- Aiguilles : autour de 10 h 10, trotteuse vers 30 à 33 secondes pour dégager le logo. Les réglages par maison que citent les sources se contredisent (pour Rolex : 10 h 10 min 31 s et date au 28 selon l'une, vers 10 h 08 selon une autre). Règle : relever l'heure, la trotteuse, le jour et la date sur les visuels de la maison visée, et s'y tenir sur toute la série.
- Selon un auteur spécialisé, des montres sont confiées sans leur verre. Quand le verre est là, son reflet se gère par l'éclairage, pas après.
- Ordre de grandeur : trois jours pour trois images chez un photographe d'une grande marque d'éclairage ; trois à quatre heures de prise de vue par image dans un studio de packshot.

Ce que la retouche ne rattrape pas : un métal éclairé sans dégradé (il n'y a rien à nettoyer, tout est à peindre), une pierre sans contraste interne, une profondeur de champ trop courte sans plans d'empilement.

## 3. Montre : le flux de retouche

**0. Assemblage.** Empilement dans un logiciel dédié (Helicon est jugé plus précis que Photoshop par un formateur de référence), recouvrements corrigés à la main depuis le plan source. Dans Helicon, la méthode B (carte de profondeur) convient aux surfaces lisses ; la méthode C (pyramide) passe mieux les recouvrements et les arêtes croisées, au prix d'un contraste et de brillances accentués : la réserver, par masque, aux zones où B échoue. Puis composition des expositions séparées, une par calque. L'empilement redimensionne les plans (la mise au point change le grandissement) : toute exposition séparée se recale sur l'image empilée, en mode Différence, avant d'être masquée, sinon arêtes et griffes se dédoublent. Synchroniser le nettoyage des poussières de capteur sur tous les plans avant l'empilement, qui les étire en traînées. La copie aplatie de l'assemblage sert d'« avant » au banc.

**1. Tracés.** Plume, pièce par pièce : boîte, lunette, cornes, couronne, poussoirs, verre, cadran, chaque index, chaque aiguille, bracelet. Les commentateurs d'un time-lapse de retouche d'une Rolex y comptent au moins une centaine de tracés. Les tracés sont enregistrés ; tout le reste se fait à l'intérieur d'eux. C'est ce qui garantit des arêtes nettes sans halo et des corrections qui ne débordent pas. Une sélection automatique sert d'ébauche, jamais de contour final sur un produit de luxe. [analyse]

**2. Nettoyage.** Poussières, fibres, micro-rayures, traces de doigt, sous la courbe solarisée, à 200 %. Sur un poli, correcteur ; sur un brossé, tampon aligné sur le sens du brossage, sinon la trace se voit. La vue `09_poussieres` du banc cercle les candidats.

**3. Métal.** [analyse]
- Poli miroir : ce qu'on voit est le reflet de l'environnement. On reconstruit un dégradé propre dans le tracé (outil dégradé ou pinceau large sur calque masqué), avec des transitions franches là où deux facettes se rencontrent et des noirs posés. Un métal poli sans noir est gris ; le banc signale une étendue tonale insuffisante (METAL_PLAT). Repères de départ, faute de relevé sur des visuels de référence : noirs vers L* 8 à 15, clairs vers L* 92 à 96, blanc pur réservé aux spéculaires.
- Brossé, satiné : la texture directionnelle est le fini. On refait le dégradé de fond sous la texture (couche basse d'une séparation de fréquences), on garde ou on régénère la texture au-dessus (bruit étiré dans le sens du brossage : droit sur un maillon, circulaire sur une lunette).
- Chanfreins et arêtes : un filet clair continu, de largeur constante.
- Bracelet : chaque maillon reçoit le même traitement. Régularité, sans copier-coller identique qui se repère.
- Symétrie : cornes, poussoirs, flancs de boîte.

**4. Cadran.** [analyse] Fond parfaitement régulier. Sur un soleillé, le dégradé est rayonnant et centré sur l'axe des aiguilles, et les rayons restent. Index identiques en éclat et en netteté. Textes et logo nets, repris si besoin sans changer la typographie réelle. Guichet de date centré, chiffre net. Matière luminescente régulière. Compteurs : sillons concentriques conservés. Aiguilles : arêtes propres, ombre portée douce sur le cadran, de même sens partout.

**5. Verre.** [analyse] Reflets parasites supprimés. Selon les visuels de la maison : verre invisible, ou un seul reflet doux et dessiné. Loupe de date : bords propres, grossissement cohérent.

**6. Couronne, poussoirs.** Couronne repoussée. Logo de couronne lisible.

**7. Ombre, reflet, fond.** Ombre de contact dense et courte, ombre portée cohérente avec la lumière de l'objet, reflet au sol avec son atténuation. Fond en 16 bits avec un grain fin : c'est là que le banding apparaît en premier.

**8. Couleur.** Métaux blancs neutres, à peine froids. Un prestataire spécialisé signale la dérive bleue du platine comme piège courant.

**9. Finition.** Les formateurs décrivent la même fin de chaîne : tampon, dodge and burn, lissage des transitions du chrome, dégradé, accentuation, avec un niveau de finition réglé sur la taille finale. Accentuation par pièce, jamais globale : un halo sur une arête de métal ruine le travail des tracés.

## 4. Joaillerie : pierres, sertis, perles, chaînes

**Flux d'une bague ou d'un bijou**, calqué sur celui de la montre [analyse] :
1. Assemblage : empilement, expositions de pierre recalées, copie aplatie pour le banc.
2. Tracés : corps du bijou pan par pan, chaton, chaque griffe, chaque pierre, ombre, fond. Pierres et métal dans des tracés distincts.
3. Nettoyage sous courbe solarisée, à 200 %. Ce qui est posé sur une pierre part ; ses inclusions restent, sauf demande écrite.
4. Forme : griffes égales et rondes, anneau régularisé sur une ellipse, pierre droite dans son serti, sans toucher aux proportions.
5. Métal : dégradé reconstruit surface par surface, noirs posés, filet clair constant sur les arêtes.
6. Pierres : contraste des facettes dans le tracé, à partir de la meilleure exposition ; jamais de lissage.
7. Couleur : métal blanc neutre, or constant ; correction masquée au métal pour ne pas éteindre le feu des pierres.
8. Ombre, reflet, fond ; puis étalonnage, grain, netteté par pièce, contrôle, export.

- **Tracés séparés** pour les diamants, les pierres de couleur et le corps du bijou (pratique décrite par un photographe joaillier). Ils ne reçoivent pas les mêmes réglages.
- **Une prise par reflet**, puis empilement : une photographe citée compte six heures de prise de vue et huit heures de retouche pour une bague.
- **Pierres.** [analyse] La vie d'une pierre taillée est un damier de facettes noires et blanches. On augmente ce contraste, on ne le lisse jamais. La table reste lisible, le dessin des facettes symétrique. Le feu est fait de petits éclats de couleur dans les facettes, pas d'étoiles ajoutées. Une pierre de couleur saturée perd son modelé dès qu'un canal sature : contrôler au banc avec `--masque pierre=…`.
- **Remplacement de pierre.** Des prestataires masquent une pierre mal éclairée par une « pierre maîtresse » bien éclairée. Le risque est décrit par des bijoutiers eux-mêmes : le même diamant répété à l'identique. Si on y recourt : pivoter, changer d'échelle, respecter la perspective et le serti de chaque pierre, et ne jamais remplacer une pierre de centre.
- **Pavage.** [analyse] Chaque pierre distincte, chaque griffe ronde, égale, avec son point de lumière.
- **Perles.** Garder l'orient : le reflet doux de l'environnement et la nuance de couleur dans l'ombre. Une perle lissée devient une bille de plastique.
- **Chaînes.** [analyse] Maillons réguliers, courbe tendue et continue, nœuds défaits ; régularisation par tracé et déformation, pas par tampon.
- **Gravures, poinçons, soudures.** Ils appartiennent à l'objet. Des bijoutiers citent comme défaut des soudures blanches repeintes en or jaune : c'est montrer un bijou qui n'existe pas. On ne masque une vérité de fabrication qu'à la demande écrite du client.

## 5. Métaux précieux et déclinaisons

- Or blanc, platine, argent, acier : neutres. Le banc alerte au-delà de 3,5 de chroma sur une zone masquée `metal`, `acier`, `platine`, `or_blanc`.
- Or jaune : ni cuivré ni verdâtre ; la dérive vers le cuivre est un défaut cité. Or rose : pas orangé.
- Cohérence : la teinte d'un or se relève en Lab sur une plage moyenne et se reporte sur toute la série. Un prestataire décrit un masque par plage de teinte pour isoler chaque or.
- Déclinaison d'un métal à l'autre (jaune vers blanc ou rose) [analyse] : désaturation et courbe pour le blanc, décalage de teinte et de saturation pour le rose, reflets des pierres de couleur préservés à part. Aucune valeur cible n'est publiée : comparer à une pièce réelle dans le métal visé. Le client doit savoir que la déclinaison est faite en retouche.

## 6. Ce qu'un directeur artistique refuse

Aucune liste publiée par un directeur artistique n'a été trouvée. Celle-ci réunit ce que citent des bijoutiers, un studio spécialisé et des prestataires, complétée par la pratique.

Cités par les sources :
- le même diamant répété ;
- des soudures ou des détails de fabrication repeints ;
- des ombres disparues, ou incohérentes d'une image à l'autre ;
- une sur-retouche qui efface les reflets et les détails réels ;
- un métal lissé d'aspect plastique ;
- des halos d'accentuation ;
- des étincelles ajoutées en surimpression ;
- un or jaune qui vire au cuivre.

De pratique [analyse] :
- une poussière ou une rayure restée, même une ;
- un reflet qui montre le studio ;
- un métal blanc qui n'est pas neutre ;
- des index ou des maillons inégaux ; un cadran taché ou en dégradé irrégulier ;
- une arête molle, un contour frangé ;
- des aiguilles mal placées, une date incohérente, une couronne tirée ;
- un objet penché ou décentré sans intention ;
- du banding dans le fond ou dans un reflet.

## 7. Ce que le banc mesure sur un bijou

```
python scripts/controle_retouche.py montre.tif --avant assemblage.tif --genre montre --symetrie --zoom 2 \
    --masque metal=m_boite.png --masque cadran=m_cadran.png
python scripts/controle_retouche.py bague.tif --avant assemblage.tif --genre bijou --zoom 2 \
    --masque or_blanc=m_metal.png --masque pierre=m_pierre.png --masque fond=m_fond.png
python scripts/controle_retouche.py bague.tif --avant assemblage.tif --tuiles-seules --tuiles C3,C4,D3,D4 --zoom 2
```

Le nom du masque décide du contrôle : `metal`, `acier`, `platine`, `or_blanc` pour un métal blanc (neutralité exigée), `or_jaune`, `or_rose` pour un or (teinte relevée). `--symetrie` n'a de sens que pour un objet vu de face ; de trois quarts, seuls le centrage et les marges restent lisibles.

- Poussières : candidats cerclés, par cellule.
- Neutralité du métal et du fond ; étendue tonale du métal ; spéculaires brûlés par zone.
- Paliers dans le fond et les reflets ; halos sur les arêtes.
- Fond blanc réellement à 255, ou non.
- Symétrie de la silhouette, inclinaison de l'axe, centrage et marges (packshot de face).
- `--zoom 2` : tuiles à 200 %, la taille à laquelle une poussière de trois pixels se voit.

Ce qu'il ne mesure pas : la justesse d'un dégradé de métal, la vie d'une pierre, la fidélité à l'objet réel. C'est le travail de l'œil, et de l'agent critique sur les tuiles.

## 8. Temps et niveau de finition

Les chiffres des sources (huit heures de retouche pour une bague, trois jours pour trois images de montre) donnent l'échelle : ce niveau ne s'obtient pas par un traitement automatique. L'automatisation utile ici est en amont et en aval : assemblage, masques d'ébauche, repérage des poussières, contrôle, cohérence de série, export. La reconstruction des métaux et le travail des pierres restent à la main. Voir `automatisation.md`.
