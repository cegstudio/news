#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
installer_agent.py — installe l'agent critique dans Claude Code.

Copie agents/critique-retouche.md vers un dossier d'agents de Claude Code en lui ajoutant l'en-tête attendu et le
chemin réel du skill, pour que l'agent retrouve le banc et les références d'où qu'il soit lancé.

    python installer_agent.py              → ~/.claude/agents/ (tous les projets)
    python installer_agent.py --projet .   → <projet>/.claude/agents/ (ce projet seulement)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SOURCE = SKILL / "agents" / "critique-retouche.md"

ENTETE = """---
name: critique-retouche
description: "Contre-expertise d'une retouche photo avant livraison : mesure le fichier (banc de contrôle), le regarde à 100 %, liste ce qui cloche avec preuve, gravité et correction, et rend un verdict livrable / à reprendre / à refaire. À utiliser dès qu'une image retouchée doit être relue, validée ou comparée à son original — peau, lumière, couleur, tissu, bijou, montre, packshot. Lui donner les chemins des fichiers et le brief, jamais son propre avis sur l'image."
tools: Read, Bash, Glob, Grep
---

Dossier du skill `retouche-photo` : `{skill}`
Tous les chemins `scripts/…` et `references/…` ci-dessous partent de ce dossier.

"""


def main(argv=None):
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    p = argparse.ArgumentParser(description="Installe l'agent critique-retouche dans Claude Code.")
    p.add_argument("--projet", help="dossier d'un projet : installe dans <projet>/.claude/agents/ au lieu de ~/.claude/agents/")
    p.add_argument("--chemin-skill", help="chemin du skill à écrire dans l'agent (défaut : là où se trouve ce script)")
    a = p.parse_args(argv)
    cible = (Path(a.projet).resolve() / ".claude" / "agents") if a.projet else (Path.home() / ".claude" / "agents")
    cible.mkdir(parents=True, exist_ok=True)
    skill = a.chemin_skill or str(SKILL)
    corps = SOURCE.read_text(encoding="utf-8")
    fichier = cible / "critique-retouche.md"
    fichier.write_text(ENTETE.replace("{skill}", skill) + corps, encoding="utf-8")
    print(f"Agent installé : {fichier}")
    print(f"Il utilisera le skill situé dans : {skill}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
