# Lumière et couleur

## Sommaire
1. Lumière : ce qu'on règle et dans quel ordre
2. Couleur : neutralité, puis intention
3. Étalonnage et cohérence de série
4. Dégradés et banding
5. Netteté
6. Grain
7. Gestion de la couleur, du fichier de travail à la livraison
8. Signatures d'une lumière ou d'une couleur ratée

## 1. Lumière : ce qu'on règle et dans quel ordre

**Les extrémités d'abord.** Point noir et point blanc se décident selon la destination, pas selon l'histogramme. Sur le web, un noir à zéro est acceptable s'il est voulu et sans matière à garder ; en impression, c'est le taux d'encrage qui limite. Un blanc de peau, de tissu ou de métal garde de la matière : on réserve le blanc pur aux spéculaires ponctuels et au fond quand il doit l'être. L'écrêtage se lit canal par canal : une peau dont le rouge sature n'est pas « brûlée » à l'histogramme de luminosité, mais elle a déjà perdu son modelé et vire à l'orangé plat.

**Le contraste global ensuite, puis le local.** Une courbe en S globale durcit tout, y compris ce qui devait rester doux. Le contraste se pose par zones, avec des courbes masquées : c'est du dodge and burn à grande échelle. Clarté et Texture de Camera Raw agissent sur des bandes de fréquence fixes, sans discernement : utiles en masque sur un tissu ou un métal brossé, dangereuses sur une peau.

**La hiérarchie du regard.** Plisser les yeux, ou regarder la vue de luminance contrastée du banc : l'œil doit aller au sujet, puis au produit, et ne s'accrocher à rien d'autre. Ce qui est plus clair ou plus contrasté que le sujet se baisse. Un vignetage se construit par zones, pas par un ovale centré qui se voit.

**Ce que la retouche ne rattrape pas.** La direction et la qualité de la lumière. On peut renforcer un volume, déboucher une ombre, prolonger un dégradé ; on ne peut pas déplacer une source sans que les ombres portées, les reflets et les spéculaires la contredisent. L'outil Relight de Photoshop 28 et le calque de réglage Lumière existent ; ils produisent une lumière plausible, pas la lumière de la prise de vue. À réserver à un rattrapage assumé.

## 2. Couleur : neutralité, puis intention

**Neutraliser avant d'étalonner.** Balance des blancs sur une référence (charte, gris neutre photographié dans la lumière), source par source si l'éclairage est mixte. Un neutre se vérifie à la pipette en Lab : a* et b* proches de zéro dans les ombres, les tons moyens et les hautes lumières séparément. Une dominante qui change de sens entre ombres et hautes lumières se corrige par courbes par canal, pas par la température.

**Le neutre d'un produit n'est pas négociable.** Acier, or blanc, platine, argent, cadran blanc ou noir, chemise blanche : ce sont les étalons du spectateur. Une dominante de 3 unités de chroma sur un métal blanc se voit ; sur un portrait étalonné, c'est un choix. Le banc traite donc la dominante comme une alerte sur un produit et comme une information ailleurs.

**Travailler la couleur par plages.** Teinte, saturation et luminance d'une plage de couleur se règlent séparément, avec un masque quand deux objets partagent la même plage (lèvres et pull rouge). La saturation dépend de la luminosité : une couleur sombre et très saturée paraît sale, une couleur claire très saturée paraît fluo. Vibrance protège les tons de peau, Saturation non.

**Le gamut.** Les rouges, les oranges, les verts et les cyans intenses d'un tissu ou d'une pierre sortent du sRGB. À la conversion ils s'écrêtent : un canal part à 0 ou à 255 et le modelé disparaît. Épreuver en sRGB avant l'export, et ramener ces couleurs dans le gamut à la main (désaturer légèrement, assombrir) plutôt que de laisser la conversion le faire.

## 3. Étalonnage et cohérence de série

L'étalonnage (le « look ») vient après toutes les corrections locales, dans un groupe de calques de réglage au-dessus de tout le reste. Posé avant, il masque les taches qu'on devait corriger et rend chaque retouche locale dépendante de lui.

Sur une série, le groupe d'étalonnage est le même pour toutes les images, copié et non refait. Ce qui varie d'une image à l'autre se corrige en dessous, pour ramener chaque image au même point de départ. `controle_serie.py` mesure ce qui doit rester constant : fond, neutres, point blanc et point noir, luminosité médiane, carnation, grain, cadrage du produit. La série se juge sur une planche, pas image par image.

## 4. Dégradés et banding

Un dégradé lisse (fond de studio, ciel, reflet sur un métal poli, peau très unie) n'a que quelques dizaines de niveaux en 8 bits. Tout réglage fort les écarte et les marches apparaissent.

- Travailler en 16 bits du RAW jusqu'à l'export. Un fichier 8 bits converti en 16 bits n'a rien gagné ; le banc le signale (FAUX_16_BITS).
- Reconstruire un dégradé abîmé plutôt que le flouter : outil dégradé ou gros pinceau sur un calque 16 bits, puis bruit.
- Finir par un grain fin, de l'ordre de 1 à 2 %, monochromatique, avant la conversion 8 bits, et laisser le tramage activé à la conversion. Aucun pourcentage précis n'est établi par les sources ; c'est le plus faible grain qui casse les paliers à 100 %.
- Se méfier de l'après : un dégradé parfaitement propre survit à l'export et se bande à la recompression d'Instagram ou d'une place de marché. Le banc le signale comme risque (DEGRADE_SANS_GRAIN), pas comme défaut.

## 5. Netteté

Trois accentuations distinctes, à ne pas confondre : celle du dérawtisage (compenser le capteur, légère), la créative (locale, par masque : cils, iris, tissu, arêtes d'un bijou), et celle de sortie (selon la taille et le support finaux, appliquée après redimensionnement). Accentuer avant de redimensionner ne sert à rien.

Le halo est le signe d'un rayon trop grand ou d'un gain trop fort : un liseré clair d'un côté du contour, sombre de l'autre. Sur une peau il durcit les pores, sur un métal il double les arêtes, sur un détourage il dessine une frange. Le banc mesure le dépassement aux contours francs ; au-delà de 7 % il se voit à 100 %, au-delà de 14 % il se voit à l'écran.

## 6. Grain

Le grain unifie. Une image composée d'une peau retouchée, d'un fond reconstruit et d'un tissu débruité a trois textures de bruit différentes, et c'est à cela qu'on reconnaît une retouche. Un grain commun, posé en dernier sur un calque gris en mode Incrustation ou Lumière tamisée, à la taille de sortie, les recolle. Il se règle sur le support : ce qui est fin à 100 % d'un fichier de 45 Mpx a disparu sur une vignette de 1500 px.

## 7. Gestion de la couleur, du fichier de travail à la livraison

- **Fichier de travail** : 16 bits, espace large (ProPhoto ou Adobe RGB), profil incorporé, calques conservés.
- **Écran** : calibré, D65 pour le web. Pour juger une épreuve d'impression, l'ICC donne D50 et 160 cd/m².
- **Web** : JPEG sRGB avec profil incorporé, c'est le seul choix sûr partout. Display P3 ne vaut que si le profil survit à la mise en ligne, ce qu'aucune source officielle ne garantit pour Instagram ou les places de marché. Sans profil incorporé, chaque navigateur interprète à sa façon : le banc le classe en défaut majeur.
- **Formats** : AVIF est pris en charge par environ 94 % des navigateurs ; JPEG XL se décode dans Chrome depuis la version 155 (octobre 2026) ; le HDR passe par un JPEG avec gain map. Pour une livraison client, JPEG sRGB reste la référence, le reste se décide avec celui qui intègre les images.
- **Impression** : conversion CMJN par profil, épreuvage écran d'abord. Les profils ECI actuels sont PSO Coated v3 et PSO Uncoated v3 ; ISO Coated v2 est classé ancien mais reste demandé par des titres de presse. Toujours demander la fiche technique du support.

Spécifications par destination dans `livraison-droit.md`.

## 8. Signatures d'une lumière ou d'une couleur ratée

- Blancs sans matière sur le sujet ; noirs bouchés là où il y avait du détail (cheveux, tissu noir, cadran).
- Un canal saturé : couleur vive devenue aplat.
- Contraste global trop fort : ombres dures, peau dure, transitions cassées.
- Faux HDR : ombres trop débouchées, halos larges autour des contours, image grise.
- Dominante sur un neutre ; dominante croisée entre ombres et hautes lumières.
- Neutres différents d'une image à l'autre dans une série.
- Saturation uniforme poussée : peau orange, lèvres fluo, verts électriques.
- Paliers dans un dégradé ; histogramme en peigne.
- Halos d'accentuation ; grain différent d'une zone à l'autre.
- Vignetage visible ; regard attiré par un bord ou un arrière-plan trop clair.
- Profil absent ou mauvais profil : image terne ou saturée selon le navigateur.
