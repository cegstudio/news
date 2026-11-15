# Voies d'exécution : quel outil pour quelle passe

État des outils au 15/11/2026 (`veille-2026-11.md`). Ces outils bougent vite : avant d'affirmer qu'une fonction existe ou n'existe pas, refaire une recherche.

## Sommaire
1. Choisir la voie
2. Photoshop à la main, guidé
3. Connecteur Adobe pour Claude
4. Photoshop piloté (actions, scripts, MCP)
5. Camera Raw, Lightroom Classic, Capture One
6. Modules IA de retouche
7. ComfyUI en local
8. Python

## 1. Choisir la voie

| Passe | Niveau luxe | Série e-commerce, BtoC |
|---|---|---|
| Développement, base neutre | Camera Raw ou Capture One | idem, par lot |
| Masques (peau, vêtement, produit) | tracés à la plume pour un produit ; masque IA retouché pour une peau | masque IA (connecteur Adobe, Lightroom, SAM) |
| Nettoyage peau | à la main, ou module IA sur calque à opacité réglable puis reprise | module IA par lot |
| Dodge and burn | à la main | module IA, opacité basse |
| Couleur locale | à la main | préréglages, masques IA |
| Plis, peluches | à la main | module IA puis contrôle |
| Métal, pierres, cadran | à la main, dans les tracés | hors sujet |
| Fond, détourage, ombre | tracé, ombre conservée ou refaite | automatique, contrôlé |
| Étalonnage | groupe de calques copié sur la série | préréglage |
| Grain, netteté de sortie, export | action ou script | action ou script |
| Contrôle | banc + agent critique + œil de Charles | banc + agent critique, Charles sur les alertes |

Règle de partage : l'automatique prend ce qui est répétitif et mesurable ; la main garde ce qui demande un jugement de forme ou touche à la vérité du produit.

## 2. Photoshop à la main, guidé

C'est la voie par défaut pour une image de luxe : Charles retouche, le skill prépare et contrôle. La sortie attendue est un plan de retouche (modèle dans `SKILL.md`) : passes dans l'ordre, pour chacune la zone (cellule de la grille), l'outil, le réglage de départ, le calque de contrôle à activer, et le critère d'arrêt. Puis, à chaque export intermédiaire, un passage au banc et à l'agent critique.

Ne pas réexpliquer les outils : donner la décision et la valeur.

## 3. Connecteur Adobe pour Claude

Disponible dans les conversations Claude de Charles. Ce que ses outils font, relevé dans leurs schémas le 15/11/2026 (un seul appel a été tenté, refusé parce que l'image venait d'une URL externe : le premier usage réel sur une image de Charles dira ce qui tient) :

| Outil | Ce qu'il fait | Utile pour |
|---|---|---|
| `image_select_subject`, `image_select_by_prompt` | masque du sujet, d'un objet décrit, ou d'une partie du corps ou du vêtement : cheveux, sourcils, yeux (blanc), pupille (iris), nez, bouche, dents, visage, cou, barbe, oreilles, bras, mains, jambes, chaussures, haut, bas, manteau, robe, chapeau, lunettes, accessoires | masques de travail ; masques nommés pour le banc |
| `image_invert_selection` | inverse un masque | fond |
| `interactive_image_apply_adjustments_app` | réglages par curseurs, sur l'image ou dans un masque : luminosité et contraste, contraste, exposition, noir et blanc, tons clairs et foncés, teinte et saturation, saturation, vibrance, balance des blancs. Cinq réglages par appel. | équilibrage global ou par zone |
| `image_apply_preset` | préréglages Lightroom (une centaine : portraits par carnation, adaptatifs, noir et blanc, grain, netteté…) | rendu rapide sur une série BtoC |
| `image_apply_effects` | grain, bruit, flou gaussien, incrustation de couleur, teinte monochrome (et effets graphiques sans intérêt ici) | grain de finition contre le banding |
| `image_remove_background` | détourage, fond transparent ou couleur unie | packshot simple, fond blanc |
| `image_fill_area` | aplat de couleur dans un masque, opacité et mode de fusion réglables | correction de couleur par calque en mode Couleur ou Teinte |
| `image_apply_lens_blur`, `image_crop_and_resize`, `image_auto_straighten`, `image_generative_expand` | flou de profondeur, recadrage, redressement, extension générative du cadre | finition, formats |

Mode d'emploi :
- Le serveur demande d'appeler `adobe_mandatory_init` une fois avant tout autre outil. S'il n'apparaît pas dans la liste des outils, appeler directement l'outil voulu.
- Les outils travaillent sur des URL d'images, et seulement celles de domaines qu'Adobe accepte : une URL externe est refusée (« URL domain not whitelisted », constaté le 15/11/2026 avec une image hébergée ailleurs). L'image doit donc venir de la conversation, du sélecteur de fichiers (`asset_add_file`) ou du stockage Creative Cloud (`asset_initialize_file_upload` puis `asset_finalize_file_upload`).
- Pour une seule image, les réglages et effets passent par les versions `interactive_…_app` (Charles ajuste les curseurs). Pour plusieurs, par les versions directes.
- Avant de fixer une valeur de réglage, lire les noms et les bornes avec `interactive_image_get_options_for_adjustments_app` ; ne pas les supposer.
- Sorties en PNG pendant le travail.

Ce qu'il ne fait pas : ni correcteur ni tampon, ni courbes, ni dodge and burn, ni séparation de fréquences, ni tracés, ni calques d'un PSD. Les descriptions de ses outils de sélection indiquent que l'édition générative n'est pas disponible par cette voie. Un test tiers de mai 2026 le situe au niveau d'Adobe Express. Conclusion : bon pour des masques, un équilibrage, un fond, une série BtoC ; pas pour la retouche au pixel d'une image de luxe.

Usage le plus rentable ici : lui demander les masques (visage, cou, mains, vêtement, objet), les télécharger, et les donner au banc avec `--masque`, ce qui rend les mesures de peau et de matière fiables.

## 4. Photoshop piloté (actions, scripts, MCP)

- **Actions et droplets** : la voie la plus solide pour un lot. Tout ce qui est fixe (mise en place des calques de contrôle et des groupes de dodge and burn, grain de finition, netteté de sortie, conversions, exports) devient une action. Les modules IA s'y enchaînent.
- **Scripts** : ExtendScript (`.jsx`) n'a pas de date de retrait publiée ; seuls les panneaux CEP en ont une (désactivés en décembre 2027). UXP (`.psjs`, batchPlay) est la voie d'avenir, avec des manques signalés par les développeurs (API d'imagerie incomplète en CMJN et alpha, erreurs batchPlay depuis la 27.9). Tout script écrit par Claude pour Photoshop doit être testé sur la machine de Charles avant d'être déclaré bon : rien dans ce skill n'a été exécuté dans Photoshop.
- **MCP tiers** : `photoshop-mcp-imt` (135 outils, pilote Photoshop par ExtendScript et un pont UXP, vérifié par son auteur sur les versions 27.9 et 27.10) et `adb-mcp` (preuve de concept). Projets individuels, maturité faible. À essayer sur des copies.
- **MCP officiel Adobe** : annoncé le 10/11/2026 (Photoshop, Illustrator, Premiere, After Effects), bêta privée début 2027, rien d'installable aujourd'hui.
- **API Adobe côté serveur** : l'API Photoshop v1 est arrêtée depuis le 31/07/2026 ; la v2 passe par un contrat Firefly Services d'entreprise, sans tarif public. Pas une voie pour un indépendant à ce jour.

Toute proposition d'outil nouveau se justifie face au stack existant (`ceg-stack`).

## 5. Camera Raw, Lightroom Classic, Capture One

- Lightroom Classic 16.0 (10/11/2026) : suppression IA des imperfections visage par visage, masques de profondeur, étalonnage dans les masques.
- Capture One 16.9 (29/10/2026) : Skin Tone et Body Skin Retouching en local avec accélération GPU sous Windows, retouche des cheveux rebelles ; Match Look et masques de personnes depuis 2025.
- Ces outils sont à leur place au développement et sur les séries. Pour un maître de luxe, s'en tenir à une base neutre et faire le travail local dans Photoshop, où il reste réversible calque par calque.

## 6. Modules IA de retouche

- **Retouch4me** : quinze modules (Heal, Dodge&Burn, Portrait Volumes, Skin Tone, Skin Mask, Mattifier, Eyes, White Teeth, Stray Hairs, Color Match, Fabric, Dust, Clean Backdrop…), licence perpétuelle locale à partir de 94,25 $. S'enchaîne par actions Photoshop sur TIFF 16 bits (environ 20 s pour 45 Mpx) ou par l'application Arams sur un dossier. Pas de ligne de commande trouvée. L'API en ligne ne prend que du PNG ou du JPEG et ne rend pas de TIFF 16 bits.
- **Evoto** (en ligne, à crédits), **Aftershoot Retouch** (local), **Imagen**, **Neurapix** : orientés volume, pas d'API ni de ligne de commande publiques trouvées.
- Règle d'emploi : toujours sur un calque séparé, opacité réglée à l'œil, puis banc avec l'original. Les échecs documentés portent sur la dentelle, les tatouages et les taches de rousseur.

## 7. ComfyUI en local

Voir `ceg-stack` et `comfyui-pilotage` pour l'accès et les workflows de Charles.

- **Masques** : SAM 3.1 (natif dans ComfyUI, sélection par texte), Sapiens2-seg (corps), face-parsing SegFormer (peau, cheveux, lèvres, yeux). C'est la voie locale pour remplacer le masque de peau approximatif du banc.
- **Édition par instruction** (Qwen-Image-2.1, FLUX) et **agrandissement** (SeedVR2, SUPIR) : ils régénèrent des pixels. Trois règles :
  1. Jamais sur les pixels du produit vendu (bijou, montre, vêtement) ni sur un visage livré, sauf commande explicite.
  2. Toujours dans un masque, puis recomposition sur l'original : hors du masque, l'image doit rester identique au pixel près. Le banc le vérifie avec `--avant`.
  3. Les conséquences de transparence sont dans `livraison-droit.md`.
- Usages sains : extension de fond, nettoyage de décor, suppression d'un accessoire de plateau.

## 8. Python

Les scripts de `scripts/` ne retouchent pas : ils mesurent. Tout traitement déterministe d'un lot (recadrage normalisé, fond, conversion de profil, grain, export par destination, renommage) s'écrit volontiers en Python ; le livrer complet, prêt à lancer, et le faire suivre du banc.
