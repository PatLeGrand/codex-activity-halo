# Codex Activity Halo

Plugin compagnon pour mirsella/computer-use-mcp sous KDE Plasma Wayland.
Un halo bleu transparent apparaît aux quatre coins de chaque écran pendant
les appels au bureau. Un badge distingue l’observation du contrôle.
Le halo reste visible 2,5 secondes après chaque appel, puis disparaît.

Il surveille uniquement les métadonnées du journal local de mirsella.
Il ne lit pas les captures, les frappes ou le contenu des fenêtres.
Les appels au bureau privé en arrière-plan sont exclus.
Les autres outils Codex, notamment les commandes terminal, ne sont pas suivis.
La détection est échantillonnée toutes les 100 ms ; elle signale un appel
demandé, y compris lorsqu’une action est ensuite refusée.

## Utilisation

Le serveur MCP lance automatiquement le compagnon. Une icône bleue dans la
zone de notification permet de prévisualiser, désactiver ou quitter le halo.
Pour arrêter durablement le lancement automatique, désactiver le plugin
`activity-halo@patou-local` dans Codex.

Le plugin fournit `status` et `preview` (aperçu explicitement étiqueté,
pendant huit secondes). Il ne contrôle pas le PC.

## Installation

Pré-requis : Python 3, PySide6, KDE avec XWayland et composition activée.
L’overlay utilise Qt/XWayland avec entrée transparente et sans prise de focus.
Il est affiché sur tous les écrans, indépendamment des limites multi-écran
de mirsella. Il peut apparaître dans les captures faites pendant son affichage.

Depuis un emplacement permanent contenant ces fichiers :

```bash
codex plugin marketplace add /chemin/vers/codex-activity-plugin
codex plugin add activity-halo@patou-local
```

Pour récupérer le projet depuis GitHub :

```bash
git clone https://github.com/PatLeGrand/codex-activity-halo.git
cd codex-activity-halo
codex plugin marketplace add "$PWD"
codex plugin add activity-halo@patou-local
```

Le serveur utilise `/usr/bin/python3` ; PySide6 doit être disponible pour cet
interpréteur. `requirements.txt` documente la dépendance Python.

Redémarrer Codex pour charger le serveur. Aucun démarrage système ni service
privilégié n’est installé. Les fichiers de fonctionnement sont stockés dans
`$XDG_RUNTIME_DIR/codex-activity-halo`, avec une seule instance par utilisateur.

## Validation

```bash
python3 -m unittest -v test_activity.py
python3 overlay.py
```

Les tests couvrent les appels concurrents, la rotation du journal, les lignes
partiellement écrites, les anciens appels et les processus interrompus.
