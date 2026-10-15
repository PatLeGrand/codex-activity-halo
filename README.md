# Activity Halo — indicateur et garde-fous pour le contrôle d'écran par une IA

Compagnon de [mirsella/computer-use-mcp](https://github.com/mirsella/computer-use-mcp)
sous KDE Plasma Wayland, pour **Claude Code** et **Codex**. Un halo transparent
apparaît aux quatre coins de chaque écran pendant les appels au bureau, un
badge distingue l'observation du contrôle, un anneau suit le pointeur, des
carillons annoncent le début et la fin, et un décompte laisse deux secondes
pour annuler. Dès que vous touchez le clavier ou la souris, l'agent est
suspendu. Chaque agent a sa couleur : bleu pour Codex, terracotta pour Claude.

| Guide | Contenu |
| --- | --- |
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Prérequis, installation pas à pas, brancher Claude Code ou Codex, mise à jour, désinstallation |
| [docs/UTILISATION.md](docs/UTILISATION.md) | Déroulé d'une session, pause et reprise, arrêt d'urgence, variables, dépannage, limites, confidentialité |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Processus, protocole, signal de reprise, ajouter un agent |

Projet non affilié à Anthropic ni à OpenAI. Licence MIT.

Il surveille uniquement les métadonnées du journal local de mirsella.
Il ne lit pas les captures, les frappes ou le contenu des fenêtres.
Les appels au bureau privé en arrière-plan sont exclus.
Les autres outils Codex, notamment les commandes terminal, ne sont pas suivis.
La détection est échantillonnée toutes les 100 ms ; elle signale un appel
demandé, y compris lorsqu’une action est ensuite refusée.

## Utilisation

Le serveur MCP lance automatiquement le compagnon. Une icône dans la
zone de notification permet de prévisualiser, désactiver ou quitter le halo.
Pour arrêter durablement le lancement automatique, désactiver le plugin
`activity-halo@patou-local` dans Codex.

Le plugin fournit `status` et `preview` (aperçu explicitement étiqueté,
pendant huit secondes). Il ne contrôle pas le PC.

## Installation du plugin Codex (résumé)

Le guide complet est dans [docs/INSTALLATION.md](docs/INSTALLATION.md).

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

## Reprise humaine (v0.3 — installation système requise)

Le détecteur lit les événements physiques des claviers, souris et pavés tactiles,
puis ne transmet que des booléens d’activité et de touche/bouton maintenu. Aucun
code de touche, texte ou mouvement détaillé n’est envoyé ou enregistré. Les
périphériques virtuels sans bus physique sont exclus, afin que les entrées EIS
de Codex ne provoquent pas elles-mêmes une pause.

Une unité système ouvre les périphériques en lecture seule, puis abandonne
ses privilèges avant de traiter les événements. Son script installé appartient
à root ; l’utilisateur n’est pas ajouté au groupe `input`. Le service est lié
au gestionnaire de session de l’utilisateur. Si un périphérique est ajouté ou
retiré, il redémarre pour actualiser sa couverture.

Installation, depuis le dossier contenant ces scripts :

```bash
sudo /usr/bin/python3 -I /chemin/install_input_monitor.py
```

L’installation requiert une authentification administrateur locale. Le script
installe uniquement `/usr/local/libexec/codex-input-activity/monitor_helper.py`
et `/etc/systemd/system/codex-input-activity-UID.service`.

La nouvelle version du compagnon doit ensuite être activée et le contrôle
redémarré. L’ancienne version est conservée pendant cette préparation. Le
contrôle de v0.3 refuse de démarrer si aucun signal récent du détecteur n’est
reçu ou si la couverture clavier/souris est incomplète.

Pendant une session, une activité physique crée immédiatement le signal
coopératif natif `computer-use-mcp-takeover` et affiche une indication orange.
Une seconde vérification a lieu à la fin du compte à rebours, avant d’envoyer
l’appel au contrôleur. La pause reste verrouillée jusqu’à « Reprendre le
contrôle Codex » dans le menu de l’icône. Mir­sella conserve aussi son délai de
sécurité natif de 5 secondes après suppression du signal ; la reprise n’est
pas une remise en mouvement immédiate.

Arrêter le détecteur :

```bash
sudo systemctl disable --now codex-input-activity-UID.service
```

Le test de bout en bout avec des entrées physiques réelles doit être effectué
après l’installation. Les tests automatisés utilisent des événements simulés. Le test Qt peut être
relancé avec `python3 verify_takeover_ipc.py`, hors d’un sandbox interdisant les
sockets Unix locaux.

### Arrêt global KDE

`python3 install_stop_shortcut.py` enregistre **Ctrl+Alt+Fin** sans sudo.
Le raccourci laisse le contrôle suspendu jusqu’à une reprise manuelle.
Il crée aussi le signal natif si le compagnon est indisponible.
La combinaison occupée par une autre application est refusée.

### Action en cours

Le proxy annonce uniquement le type d’opération (capture, clic, déplacement,
saisie, collage ou attente). Aucun texte saisi, titre de fenêtre ou contenu
du presse-papiers n’est affiché. Le libellé décrit la commande en cours,
pas la réussite de son effet dans l’application.

## Claude Code

Le même compagnon sert Codex et Claude : chaque proxy annonce son agent
(`HALO_AGENT=claude`) et l'indicateur adopte son nom et ses couleurs, définis
dans `theme.py`. Sans cette variable, l'aspect reste celui de Codex. Le jeton
du portail KDE est lié à l'identité de l'application : Claude doit avoir son
propre `XDG_STATE_HOME`. Commande d'enregistrement, thèmes et comportements
observés : voir [INSTALLATION.md](docs/INSTALLATION.md#claude-code) et
[UTILISATION.md](docs/UTILISATION.md).

Tests : `python3 -m unittest -v test_theme.py`.
