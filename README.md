# Retouche photo : skill, banc de contrôle et agent critique

Système de retouche et de contrôle qualité pour la photo de mode, de pub et de luxe : peau, lumière, couleur, tissu, bijoux et montres.

## Ce qu'il y a dans ce dépôt

```
.claude/
├── skills/retouche-photo/
│   ├── SKILL.md                    le skill : méthode, ordre des passes, boucle critique
│   ├── references/                 la doctrine par domaine, lue à la demande
│   │   ├── peau.md  lumiere-couleur.md  tissu.md  bijoux-montres.md
│   │   ├── grille-critique.md      les défauts, comment ils se voient, leur gravité
│   │   ├── banc-de-controle.md     lancer et lire le banc, codes d'alerte
│   │   ├── execution.md            quel outil pour quelle passe (connecteur Adobe, Photoshop, IA, ComfyUI)
│   │   ├── automatisation.md       ce qui s'automatise, architecture, éléments à fournir
│   │   ├── livraison-droit.md      export par destination, mentions légales
│   │   └── veille-2026-11.md       faits datés et sources
│   ├── agents/critique-retouche.md l'agent critique (instructions)
│   ├── scripts/
│   │   ├── controle_retouche.py    mesures + vues de contrôle + tuiles à 100 % d'une image
│   │   ├── controle_serie.py       cohérence d'une série
│   │   ├── etalonner.py            repères personnels tirés d'images validées
│   │   ├── relever_rendu.py        relevé chiffré d'un rendu de référence (visuels d'une maison)
│   │   └── installer_agent.py      installe l'agent dans Claude Code
│   ├── assets/                     détecteur de visage YuNet (licence MIT)
│   └── evals/                      trois cas de test
└── agents/critique-retouche.md     l'agent, prêt pour Claude Code dans ce dépôt
dist/retouche-photo.skill           le skill emballé, à installer dans Claude
```

## Installer

**Dans Claude (application ou claude.ai)** : ouvrir `dist/retouche-photo.skill` et l'enregistrer comme skill.

**Dans Claude Code sur le PC** :

```
xcopy /E /I .claude\skills\retouche-photo %USERPROFILE%\.claude\skills\retouche-photo
python %USERPROFILE%\.claude\skills\retouche-photo\scripts\installer_agent.py
pip install -r %USERPROFILE%\.claude\skills\retouche-photo\scripts\requirements.txt
```

## Utiliser le banc sans Claude

```
python scripts\controle_retouche.py final.tif --avant original.tif --genre beaute
python scripts\controle_retouche.py montre.tif --genre montre --symetrie --zoom 2 --masque metal=masque.png
python scripts\controle_serie.py dossier_serie --genre packshot
python scripts\etalonner.py finals_valides --avant originaux --genre beaute --sortie reperes_beaute.json
python scripts\relever_rendu.py visuels_reference --genre montre --masques masques
```

Le rapport (`rapport.md`), les vues de contrôle et les tuiles à 100 % sortent dans `<final>_controle/`. Mode d'emploi complet : `.claude/skills/retouche-photo/references/banc-de-controle.md`.

## État

Le banc a été vérifié sur des défauts fabriqués exprès (peau floutée, fluidité, accentuation, visage rougi seul, postérisation, poussières, fond et métal teintés), et l'agent critique sur une image où quatre défauts avaient été plantés à son insu (les quatre retrouvés). Rien n'a encore tourné sur de vraies retouches. Ses seuils sont des valeurs par défaut : `etalonner.py` les remplace par des bornes tirées d'images validées. Aucun script Photoshop n'est fourni : rien ne peut être testé dans Photoshop depuis l'environnement où ce dépôt a été écrit.
