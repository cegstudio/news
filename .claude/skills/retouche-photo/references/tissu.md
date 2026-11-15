# Tissu et vêtement

## Sommaire
1. Le vêtement est le produit
2. Plis : lesquels garder
3. Rendu par matière
4. Couleur fidèle
5. Moiré
6. Forme, symétrie, ghost mannequin
7. Série
8. Défauts rédhibitoires
9. Ce qui s'automatise

## 1. Le vêtement est le produit

En mode et en e-commerce, le client achète ce qu'il voit : la couleur, la matière, la coupe. Trois fidélités passent avant l'esthétique.

- **Couleur** : celle du vêtement réel, pas celle qui rend le mieux.
- **Matière** : l'armure, la maille, le grain du cuir doivent rester lisibles à 100 %.
- **Construction** : coutures, surpiqûres, boutons, longueurs, étiquettes, usures voulues. La règle des studios de retouche e-commerce est de ne pas modifier les caractéristiques permanentes du produit.

On nettoie ce qui vient de la prise de vue, pas ce qui appartient au vêtement.

## 2. Plis : lesquels garder

| Type | Exemple | Traitement |
|---|---|---|
| Plis de construction et de tombé | drapé, fronces, plis creux, cassure d'un pantalon, poids d'une jupe | Garder. Ils disent la matière et la coupe. |
| Plis de port | coude, aine, taille, tension d'un bouton | Adoucir sans effacer : un vêtement porté sans aucun pli a l'air peint. |
| Plis de manipulation | marques de pliage, de cintre, de transport, froissage | Enlever. |
| Accidents | peluches, fils tirés, poils, poussières, bouloches, épingles, pinces | Enlever. |

Un pli est un dégradé de lumière, pas un objet. On le traite donc par dodge and burn (éclaircir son ombre, assombrir sa crête) ou sur la couche basse d'une séparation de fréquences, ce qui laisse l'armure intacte. Le tampon et le correcteur recopient de la texture : ils servent pour les peluches et les fils, pas pour les plis, sous peine de casser la continuité du tissage ou de répéter un motif. Sur un tissu à motif ou à rayures, tout déplacement se voit : corriger la densité, jamais la géométrie du motif.

Le défaut majeur cité par les spécialistes est la texture lissée : une maille qui a perdu ses boucles, un lin qui a perdu ses irrégularités, un denim qui a perdu son armure. Passer la zone au banc avec `--masque tissu=…` et l'original : en dessous de 70 % de texture fine conservée, la matière est partie.

## 3. Rendu par matière

Ces repères sont de pratique de studio ; aucune source d'autorité ne les chiffre.

- **Velours** : la profondeur vient du contraste entre un noir dense et un reflet doux qui suit le sens du poil. Ne pas déboucher les noirs, ne pas accentuer : le velours accentué devient de la feutrine.
- **Satin, soie** : grands dégradés spéculaires. Ce sont eux qui disent la matière ; ils se nettoient, ne se lissent pas en aplat, et sont les premiers à faire du banding.
- **Cuir** : garder le grain et les nuances. Nettoyer les éraflures accidentelles, pas la patine.
- **Denim** : la diagonale du sergé et les délavages sont le produit. Attention au moiré à la réduction.
- **Maille** : boucles lisibles ; bouloches et fils tirés enlevés un par un. Premier candidat au moiré.
- **Dentelle, tulle, transparences** : les vides sont du dessin. Les outils IA de nettoyage y échouent (ils bouchent les jours).
- **Laine, fourrure, mohair** : le contour est fait de poils. Un détourage dur le rase ; garder un bord en demi-teinte.
- **Noir** : il doit rester du détail entre L* 5 et 20, et le vêtement doit se détacher du fond. Un noir à étendue de luminosité inférieure à 9 L* est un aplat.
- **Blanc** : entre L* 92 et 97 avec du modelé, neutre, jamais à 255 sur le vêtement.
- **Lurex, paillettes, métallisés** : les éclats sont des spéculaires, ils ont le droit d'être blancs, pas les zones autour.

## 4. Couleur fidèle

- À la prise de vue : une charte de couleur ou au moins un gris neutre dans la lumière, pour chaque installation.
- En retouche : neutraliser sur la charte, puis comparer au vêtement réel ou à l'échantillon, sous un éclairage normalisé. Mesurer en Lab sur une plage unie plutôt que juger à l'œil un écran contre un tissu.
- Tolérance : aucune n'est publiée pour l'e-commerce. Les seuils de ΔE 3 ou 5 qu'on lit partout n'ont pas de source. Le seul référentiel public solide est patrimonial (FADGI 2023, mesuré sur charte) : ΔE2000 moyen sous 5, 3,5 ou 2 selon le niveau d'exigence. S'y référer comme ordre de grandeur, et fixer la tolérance avec le client.
- Couleurs hors sRGB : voir `lumiere-couleur.md`. Un rouge ou un orange vif livré en sRGB perd du modelé si on laisse la conversion décider.
- Déclinaison de coloris (recoloration) : changer teinte et saturation, reconstruire la luminance à part pour garder la matière ; un tissu foncé recoloré en clair n'a pas les mêmes ombres. Le client doit savoir que le coloris est décliné et non photographié.

## 5. Moiré

Il se règle d'abord à la prise de vue : changer la distance, le diaphragme ou l'angle suffit souvent. En retouche, le moiré de couleur se traite (pinceau Moiré de Camera Raw, ou flou des seuls canaux a et b en Lab dans la zone) ; le moiré de luminance est une interférence dans le détail lui-même et se rattrape mal.

Le piège est en aval : un tissu propre à 100 % peut moirer une fois réduit à la taille de la fiche produit. Contrôler à la taille de livraison, pas seulement sur le fichier maître. Le banc signale un motif périodique de couleur dans une zone masquée (MOIRE_COULEUR) : c'est un indice, à confirmer à l'œil, parce qu'un motif tissé régulier donne le même signal.

## 6. Forme, symétrie, ghost mannequin

- **Symétrie** sur un axe vertical : cols, épaules, emmanchures, ourlets, ligne de boutonnage. On redresse ce que le stylisme a mal posé, pas la coupe.
- **Fluidité** : pour reprendre un tombé ou une épaule. Les rayures, carreaux et motifs interdisent presque tout déplacement.
- **Ghost mannequin** : assemblage de la vue portée et de l'intérieur du col ou du dos, étiquette restaurée, ombre intérieure cohérente avec la lumière, raccord invisible à l'encolure. Vérifier la continuité des coutures au raccord.
- **Pinces, épingles, bretelles de maintien, cintres** : tout ce qui tenait le vêtement disparaît, avec la tension qu'il créait.

## 7. Série

Un même vêtement photographié sous trois angles doit avoir la même couleur trois fois, le même fond, la même densité, la même échelle de cadrage. `controle_serie.py` le mesure. Les ombres au sol doivent être de même nature d'une vue à l'autre : c'est un des défauts de série les plus cités.

## 8. Défauts rédhibitoires

- Matière lissée : armure, maille ou grain disparus.
- Couleur infidèle au produit, ou différente d'une vue à l'autre.
- Plis de manipulation restés ; ou tous les plis effacés, vêtement en carton.
- Motif cassé, répété ou déformé par un tampon ou une fluidité.
- Peluches, poils, fils, épingles oubliés.
- Moiré, y compris à la taille de livraison.
- Noir bouché, blanc brûlé, couleur vive en aplat.
- Contour rasé (laine, fourrure), frange de détourage, ombre absente ou incohérente.
- Asymétrie non voulue ; raccord de ghost mannequin visible ; étiquette manquante.
- Caractéristique permanente modifiée (longueur, bouton, couture, coloris).

## 9. Ce qui s'automatise

- Détourage, fond, ombre, recadrage normalisé, cohérence de série : oui, avec contrôle.
- Peluches et poussières : oui par outil dédié (Retouch4me Dust, Fabric), à vérifier sur la dentelle et les motifs.
- Plis : en partie (Retouch4me Fabric), sur calque à opacité réglable, puis contrôle de la texture conservée.
- Ghost mannequin et vue « e-shop » générés à partir d'une photo portée : c'est de la génération d'image du produit, pas de la retouche. La fidélité (couleur, matière, détails de construction) doit être vérifiée contre le vêtement, et l'usage a des conséquences de transparence décrites dans `livraison-droit.md`.
- Couleur fidèle à l'échantillon : non sans charte à la prise de vue.
