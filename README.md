# Codex Activity Halo

Plugin compagnon pour mirsella/computer-use-mcp sous KDE Plasma Wayland.
Un halo bleu transparent apparaît aux quatre coins de chaque écran pendant
les appels au bureau. Un badge distingue l’observation du contrôle.
Avec le proxy de contrôle, le halo reste visible pendant la session et disparaît
après huit secondes sans action. La surveillance simple du journal conserve
une indication de 2,5 secondes après chaque appel.

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

## Feedback de contrôle (v0.2)

Un anneau bleu suit le pointeur réel pendant l’activité ; le thème du pointeur
système reste inchangé. Deux courts carillons WAV locaux annoncent le début et
la fin. Le premier appel au bureau attend deux secondes après le son de début.
Les appels espacés de moins de huit secondes forment une session ; le son de
fin joue huit secondes après la dernière réponse. Une annulation pendant le
compte à rebours empêche l’appel d’atteindre le contrôleur.

Le proxy `feedback_proxy.py` s’intercale entre Codex et le binaire mirsella.
Il démarre le compagnon et relaie le protocole MCP. Configurez le serveur
Computer Use avec `/usr/bin/python3` comme commande et les arguments
`/chemin/feedback_proxy.py /chemin/computer-use-mcp mcp --compact-tools`.
Cette intégration est prévue pour notre profil de contrôle de l’écran principal.

Pour les mouvements réels animés, le fork Computer Use doit être compilé avec
le correctif de `codex/desktop-feedback` et démarré avec
`COMPUTER_USE_MCP_SMOOTH_POINTER=1`. Il demande la position actuelle au compagnon
par socket local et vérifie le nom et la géométrie de l’écran contre la région
EIS autorisée. Si la souris est sur l’autre écran, il refuse le déplacement :
replacez-la sur l’écran principal. Il refuse aussi si le compagnon ne répond
pas ; il ne revient pas à un déplacement instantané.

Les déplacements utilisent une interpolation à environ 60 événements par
seconde. Les clics attendent la fin du trajet. Le rendu de l’anneau est mis à
jour à environ 30 images par seconde. Les images capturées peuvent contenir
cet anneau. Le compagnon ne masque jamais le curseur natif et ne capture aucune
entrée clavier.

Tests additionnels : `python3 -m unittest -v test_feedback.py test_proxy.py`.
