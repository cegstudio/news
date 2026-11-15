# Livraison et obligations légales

Relevé au 15/11/2026 (`veille-2026-11.md`). Les spécifications changent : demander la fiche technique du support ou du client, elle prime. La partie droit rapporte des textes ; ce n'est pas un avis juridique, et tout cas limite se tranche avec un juriste.

## 1. Spécifications par destination

| Destination | Fichier | Remarques |
|---|---|---|
| Web, site client | JPEG sRGB, profil incorporé, 8 bits | seul choix sûr partout ; netteté et grain réglés à la taille livrée |
| Zalando, bijoux et montres | JPEG sRGB, 1801 × 2600 px (rapport 1:1,44), 20 Mo au plus, fond blanc, ombres légères | guide partenaire |
| Google Merchant | 1500 px conseillés, 64 Mpx et 16 Mo au plus, produit sur 75 à 90 % du cadre | aide officielle |
| Amazon | fond blanc pur 255/255/255, produit sur 85 % du cadre, 1000 px au moins | d'après un guide tiers, page officielle non lue |
| Instagram | JPEG sRGB ; le HDR passe par un JPEG avec gain map envoyé depuis un ordinateur | recompression forte : grain fin contre le banding |
| Presse magazine | CMJN, 300 ppp, profil et taux d'encrage de la fiche du titre, fonds perdus | exemple (IDEAT, 2017) : ISO Coated v2 300 %, 5 mm de fonds perdus, 16 bits refusé, épreuve avec bande de contrôle |
| Affichage | PDF, profil de la régie | exemple (JCDecaux Finlande) : Coated FOGRA39, pas de JPEG ; échelle et résolution selon le format |
| Archive, maître | TIFF ou PSD 16 bits, espace large, calques | jamais livré tel quel |

Aucune exigence publiée par Cartier, Rolex ou Tissot n'a été trouvée : elles figurent dans le brief de la maison ou de son agence.

Avant tout envoi, passer le fichier livré (pas le maître) au banc : dimensions, profil, fond, compression, paliers.

## 2. Mention « Photographie retouchée »

**Article L2133-2 du Code de la santé publique** : « Les photographies à usage commercial de mannequins, définis à l'article L. 7123-2 du code du travail, dont l'apparence corporelle a été modifiée par un logiciel de traitement d'image afin d'affiner ou d'épaissir la silhouette du mannequin doivent être accompagnées de la mention : " Photographie retouchée ". »
Sanction : « 37 500 € d'amende, le montant de cette amende pouvant être porté à 30 % des dépenses consacrées à la publicité ».
https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032411563

**Décret n° 2017-738 du 4 mai 2017** (en vigueur depuis le 1er octobre 2017) : la mention vaut pour les messages publicitaires « diffusés notamment par voie d'affichage, par voie de communication au public en ligne […], dans les publications de presse […], dans la correspondance publicitaire destinée aux particuliers et dans les imprimés publicitaires destinés au public ». Elle est « apposée de façon accessible, aisément lisible et clairement différenciée du message publicitaire ou promotionnel ». « L'annonceur veille au respect des obligations ». Aucune taille n'est fixée.
https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000034580217

Ce que cela veut dire pour une retouche :
- Seule la silhouette est visée : affiner ou épaissir un corps. Nettoyer une peau, étalonner, retoucher un vêtement n'entre pas dans le texte.
- L'obligation pèse sur l'annonceur, mais c'est le retoucheur qui sait ce qui a été fait. Dès qu'une fluidité a touché la silhouette d'un mannequin dans une image commerciale, le dire par écrit au client à la livraison.
- Le banc signale toute déformation géométrique entre original et final (DEFORMATION) : c'est le moment de se poser la question.

## 3. Influence commerciale

**Loi n° 2023-451 du 9 juin 2023, article 5** (modifié par l'ordonnance n° 2024-978). Pour les contenus des personnes exerçant l'activité d'influence commerciale, les images ayant fait l'objet :
« 1° D'une modification par tout procédé de traitement d'image visant à affiner ou à épaissir la silhouette ou à modifier l'apparence du visage sont accompagnés de la mention : " Images retouchées " ;
2° D'une production par tout procédé d'intelligence artificielle visant à représenter un visage ou une silhouette sont accompagnés de la mention : " Images virtuelles ". »
Une mention équivalente est admise. Sanction : « un an d'emprisonnement et de 4 500 euros d'amende ».
https://www.legifrance.gouv.fr/loda/id/JORFTEXT000047663185

Ici le visage est visé, pas seulement la silhouette. Quand des images sont destinées à être publiées par un influenceur dans un cadre commercial, le signaler au client. Le décret d'application de ces mentions n'a pas été trouvé ; une réponse ministérielle du 30 avril 2026 renvoie, pour le reste, au règlement européen.

## 4. Règlement européen sur l'IA, article 50

Applicable depuis le 2 août 2026. Un texte de simplification publié le 24 juillet 2026 reporte au 2 décembre 2026 l'obligation de marquage technique (paragraphe 2) pour les systèmes déjà sur le marché.

- **Paragraphe 2, fournisseurs de systèmes** : marquage lisible par machine des contenus générés, sauf si le système remplit « une fonction d'assistance pour la mise en forme standard ».
- **Paragraphe 4, déployeurs** : ceux dont le système « génère ou manipule des images […] constituant un hypertrucage indiquent que les contenus ont été générés ou manipulés par une IA ».
https://artificialintelligenceact.eu/fr/article/50/

Lignes directrices de la Commission (document daté du 5 novembre 2026) :
- Exemptés : « minor colour adjustments or corrections ».
- À marquer : « altering the body shape or the skin colour of a person ».
- Pas un hypertrucage : « colour correction, […] cosmetic adjustments and enhancements ».
- Hypertrucage : une image IA d'un produit pouvant « mislead as to the actual product appearance ».
- L'annonceur qui « merely commissions » le contenu n'est pas le déployeur.
https://digital-strategy.ec.europa.eu/en/library/guidelines-transparency-obligations-providers-and-deployers-ai-systems

Lecture prudente pour l'activité de Charles :
- Une photo réelle retouchée (nettoyage, couleur, dodge and burn), même avec des outils IA d'assistance, relève des ajustements cosmétiques.
- Changer la forme d'un corps ou la couleur de peau d'une personne par IA entre dans ce qui doit être marqué.
- Une image de produit générée ou régénérée par IA (ghost mannequin généré à partir d'une photo portée, vue e-shop générée, déclinaison de coloris ou de métal générée) tombe dans le cas cité par les lignes directrices dès qu'elle peut tromper sur l'apparence réelle du produit. Deux garde-fous : vérifier la fidélité au produit réel avant livraison, et informer le client par écrit de la part de génération. Puisque l'annonceur qui se contente de commander n'est pas le déployeur, celui qui produit l'image avec le système d'IA l'est vraisemblablement : c'est une déduction, pas une citation. Ce point mérite l'avis d'un juriste avant d'en faire une offre.

## 5. Content Credentials

D'après l'aide d'Adobe, depuis août 2026 Adobe attache automatiquement des Content Credentials (C2PA) aux contenus créés ou modifiés avec ses outils d'IA générative. Une retouche qui passe par le remplissage génératif laisse donc une trace dans le fichier. À savoir avant de livrer à un client qui ne veut aucune mention d'IA.

## 6. À la livraison, par écrit

Trois lignes dans le message de livraison quand elles s'appliquent : silhouette modifiée ou non ; part d'image générée par IA, et où ; déclinaisons de coloris ou de métal faites en retouche. C'est ce qui permet au client de remplir ses propres obligations, et c'est ce qui protège Charles.
