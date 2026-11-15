# Automatiser la retouche : ce qui est possible, ce qu'il faut pour le construire

## 1. Ce qui s'automatise aujourd'hui

État de novembre 2026, sources dans `veille-2026-11.md`.

| Tâche | De bout en bout, sans personne | Avec contrôle | À la main |
|---|---|---|---|
| Contrôle technique (ce skill) | oui | | |
| Masques peau, cheveux, vêtement, produit | oui (ébauche) | reprise pour le luxe | tracés produit |
| Détourage, fond, recadrage normalisé, export | oui | | |
| Nettoyage peau et cheveux par lot | | oui | finition beauté |
| Dodge and burn | | premier passage | sculpture |
| Plis, peluches | | oui | matières fragiles |
| Cohérence de série | mesure : oui | correction : oui | |
| Métal, pierres, cadran | | repérage des poussières | reconstruction |
| Validation finale | | | Charles |

Aucune source ne décrit une retouche beauté ou joaillerie haut de gamme fiable sans retoucheur. L'objectif réaliste est donc : zéro intervention sur le BtoC et l'e-commerce simple quand le banc ne lève aucune alerte, et sur le luxe, une préparation et un contrôle qui retirent tout sauf le geste.

## 2. Architecture cible

```
dossier d'entrée (ou e-mail client, ou export Capture One)
   │
   ▼
1. Tri : genre, destination, niveau de finition          → règle par dossier ou par nom, sinon Claude
2. Masques : peau, cheveux, vêtement, produit, fond      → segmentation locale (SAM 3.1, Sapiens2, face-parsing)
3. Passes automatiques selon le genre                    → actions Photoshop + modules IA, ou Python
4. Banc de contrôle                                      → controle_retouche.py (+ --avant, + masques, + repères perso)
5. Agent critique                                        → verdict, défauts localisés, corrections
6. Boucle : corriger ce qui est automatisable, relancer  → trois tours au plus
7. File « à valider » : image, rapport, tuiles           → Charles tranche
8. Export par destination + cohérence de série           → controle_serie.py
```

Principes :
- Le banc et l'agent critique sont le cœur, pas la retouche automatique : une chaîne qui produit sans se relire livre ses erreurs.
- Rien ne part chez un client sans Charles pour le niveau luxe. Pour le BtoC, la règle d'envoi sans relecture se fixe avec lui, sur des critères du rapport (zéro alerte majeure, par exemple).
- Tout traitement est non destructif et rejouable : l'original n'est jamais écrasé, chaque étape écrit un nouveau fichier.
- L'orchestration s'insère dans l'existant : n8n en local pour le déclenchement et le suivi, scripts Python pour le banc, Photoshop sur le PC pour les actions. Voir `ceg-stack` avant de proposer un outil nouveau.

## 3. Ce qu'il faut pour le construire

À demander à Charles, dans cet ordre d'utilité. Sans les trois premiers, l'automatisation reste générique.

**Indispensable**
1. **Des paires avant/après validées**, par type d'image : 20 à 30 en beauté, autant en mode ou lookbook, 10 à 20 en bijou et en montre. Original au même cadrage que le final (TIFF ou JPEG pleine définition). Elles servent à étalonner les repères du banc sur son goût (`etalonner.py`) et à juger tout outil automatique sur pièces.
2. **Des visuels de référence du rendu visé**, par maison ou par client : dix à vingt images officielles du même type. Le relevé chiffré de `bijoux-montres.md` § 1 en dépend.
3. **La chaîne logicielle exacte** : versions de Photoshop, de Camera Raw ou Capture One ; modules déjà achetés (Retouch4me, autres) ; actions et préréglages qu'il utilise ; ce que fait aujourd'hui le service local de retouche BtoC cité dans `ceg-stack` (outil, entrées, sorties).
4. **Les cahiers des charges de livraison** de ses clients et canaux : dimensions, rapport, fond, profil, poids, nommage. Un par destination.

**Très utile**
5. Trois à cinq retouches refusées ou reprises, avec la raison : ce sont les meilleurs cas d'essai pour l'agent critique.
6. Ses calques de contrôle et son montage de dodge and burn, pour que les plans de retouche parlent sa langue.
7. Les conditions de prise de vue type (boîtier, optique, schéma de lumière, charte de couleur ou non) : elles décident de ce qui est rattrapable.
8. Le volume par type d'image et le temps passé aujourd'hui : c'est ce qui dit où l'automatisation rapporte.

**Accès**
9. Une session sur son PC (Claude Code, ou un dossier partagé par Remote Control) pour tester les scripts Photoshop sur la vraie machine. Aucun script Photoshop ne doit être tenu pour bon avant ce test.
10. Un dossier d'échange (entrée, sortie, à valider) sur le PC ou sur Drive.

## 4. Étapes proposées

1. **Fait** : doctrine, banc de contrôle, agent critique, cohérence de série, étalonnage.
2. **Étalonner** sur ses paires validées ; relever le rendu des maisons visées.
3. **Masques fiables** : segmentation locale branchée sur le banc à la place du masque de peau par couleur.
4. **Pont Photoshop** : actions de mise en place et d'export, enchaînement des modules IA, testés sur le PC.
5. **Chaîne BtoC et e-commerce** dans n8n : dossier d'entrée, passes, banc, agent, file de validation.
6. **Assistance luxe** : préparation (assemblage, masques, repérage des poussières) et contrôle, la main restant à Charles.

Chaque étape se juge sur les paires validées : un outil qui fait moins bien que la retouche de référence au banc ne rentre pas dans la chaîne.
