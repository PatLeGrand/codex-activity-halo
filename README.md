# Activity Halo

Compagnon communautaire pour **KDE Plasma sous Linux/Wayland**, conçu pour
[computer-use-mcp](https://github.com/PatLeGrand/computer-use-mcp/tree/codex/desktop-feedback).
Il affiche quand un agent observe ou contrôle le bureau, et permet de reprendre
la main. Ce projet n’est affilié ni à OpenAI ni à Anthropic. Ce n’est pas une fonctionnalité officielle de Windows.

## Guides complémentaires

- [Installation détaillée pour Codex et Claude Code](docs/INSTALLATION.md)
- [Utilisation et dépannage](docs/UTILISATION.md)
- [Architecture et protocole](docs/ARCHITECTURE.md)

Le proxy accepte `HALO_AGENT=codex` (défaut) ou `HALO_AGENT=claude`.
Un même halo affiche l’identité du dernier agent actif : bleu pour Codex,
terre cuite pour Claude. La reprise humaine reste distincte. Chaque client
conserve son propre `XDG_STATE_HOME` et son autorisation de portail.

## Fonctionnement

- Halo bleu aux coins des écrans, anneau autour du pointeur et libellé de la
  commande : capture, déplacement, clic, saisie, collage ou attente.
- Son de début et avertissement de deux secondes, avec bouton d’annulation.
  Le son de fin joue après huit secondes sans appel en cours.
- Une activité physique pendant le contrôle déclenche une pause orange.
  La perte du détecteur ou une couverture clavier/souris incomplète bloque les appels.
- Bouton visible pour arrêter ou reprendre. Après reprise explicite : cinq
  secondes sans entrée physique ; une nouvelle entrée réinitialise l’attente.
- Raccourci KDE **Ctrl+Alt+Fin** pour demander l’arrêt même hors de la fenêtre de l’agent.

Le libellé décrit une commande en cours, pas la réussite de son effet dans
l’application. Les actions interrompues ne sont pas rejouées automatiquement.
Les commandes terminal et les autres outils de l’agent ne sont pas suivis.
Le compagnon ne modifie pas le thème du curseur : il dessine un anneau.

## Compatibilité et dépendances

Validé sur Fedora 44, KDE Plasma/Wayland, XWayland, Python 3 et PySide6.
Les autres bureaux, Windows et macOS ne sont pas validés. Le détecteur nécessite
Linux evdev et systemd ; l’arrêt global utilise KGlobalAccel de KDE.

```bash
python3 -c 'import PySide6; print(PySide6.__version__)'
```

Installer les dépendances de [requirements.txt](requirements.txt) pour
l’interpréteur qui lance le plugin. Le manifeste utilise `/usr/bin/python3` :
un environnement virtuel n’est pas utilisé automatiquement. Installer les
paquets via le gestionnaire de sa distribution, ou adapter la commande du
manifeste à son environnement Python.

Pour le contrôle complet, il faut également un binaire du fork lié ci-dessus
qui inclut le signal d’arrêt coopératif, le mouvement fluide et le délai natif
de cinq secondes. La version amont peut avoir un autre délai : modifier le
compteur du halo ne modifie pas le moteur. Le halo seul n’accorde aucune
permission de capture ou de contrôle ; l’utilisateur autorise le portail KDE.

## Installation

Conserver le dépôt dans un emplacement permanent accessible à l’utilisateur :

```bash
git clone https://github.com/PatLeGrand/codex-activity-halo.git
cd codex-activity-halo
# Tant que la PR communautaire n’est pas fusionnée :
git switch codex/human-takeover
codex plugin marketplace add "$PWD"
codex plugin add activity-halo@activity-halo
```

Le dépôt GitHub peut nécessiter un accès s’il est encore privé. Ces commandes
n’accordent ni accès au dépôt ni visibilité publique au projet.

Le manifeste MCP démarre `server.py`, qui lance le halo. Les outils disponibles
sont `status` et `preview` (aperçu étiqueté de huit secondes).

### Détecteur d’activité physique

**Le contrôle via le proxy refuse de démarrer sans ce détecteur.** Examiner
les scripts et l’unité avant l’installation administrateur :

```bash
python3 monitor_helper.py --check
python3 install_input_monitor.py --dry-run
sudo /usr/bin/python3 -I "$PWD/install_input_monitor.py"
```

Le service ouvre les périphériques physiques en lecture seule, puis abandonne
les privilèges root avant de traiter les événements. Il n’ajoute pas l’utilisateur
au groupe `input`. Les seuls fichiers système installés sont
`/usr/local/libexec/codex-input-activity/monitor_helper.py` et
`/etc/systemd/system/codex-input-activity-UID.service`, où UID est celui de
l’utilisateur ayant lancé sudo. Le service ne lit pas les événements avant
l’abandon des privilèges ; il garde les descripteurs déjà ouverts.

### Relier le moteur au proxy

Adapter les trois chemins absolus de
[examples/computer-use.mcp.json](examples/computer-use.mcp.json), puis intégrer
la définition du serveur Computer Use à la configuration du client MCP.
Ne pas ajouter un second serveur pilotant le même bureau. Les formats de
configuration varient selon les clients ; cet exemple suit le format du plugin Codex.

Le lancement attendu est :

```text
/usr/bin/python3 /CHEMIN/activity-halo/feedback_proxy.py /CHEMIN/computer-use-mcp mcp --compact-tools
```

Le proxy lance le halo, attend le compte à rebours, revérifie la pause et relaie
les appels MCP. Il ne contourne pas les permissions du portail.

### Installer l’arrêt global

Depuis le même dossier permanent :

```bash
python3 install_stop_shortcut.py
```

Le raccourci est enregistré dans KDE, sans sudo. Si la combinaison appartient
à une autre application, l’installation refuse de la remplacer. Le fichier
`$XDG_DATA_HOME/kglobalaccel/codex-stop.desktop` contient le chemin local du
script d’arrêt, généré sur la machine de l’utilisateur. Ce fichier généré ne
doit pas être distribué à la place de l’installateur.

Redémarrer le client MCP après un changement de proxy ou de manifeste.

## Choisir l’écran

**Aucun nom de connecteur n’est imposé.** Le bouton utilise, dans l’ordre :

1. `ACTIVITY_HALO_MONITOR`, si un écran porte ce nom ;
2. sinon `COMPUTER_USE_MCP_MONITOR`, lorsque la première variable est absente ;
3. l’écran principal KDE si aucune sélection ne correspond.

Les halos restent visibles sur tous les écrans. Le bouton suit les changements
d’écran principal et les branchements/débranchements. Pour connaître les noms :

```bash
QT_QPA_PLATFORM=xcb python3 -c 'from PySide6.QtWidgets import QApplication; a=QApplication([]); print([s.name() for s in a.screens()])'
```

Transmettre les variables au processus MCP ou les définir dans son champ `env`.
`ACTIVITY_HALO_MONITOR` déplace uniquement le bouton ; il ne sélectionne pas le
flux de capture du moteur. `COMPUTER_USE_MCP_MONITOR` sélectionne le flux dans
le fork compatible et ne doit pas être copié depuis une autre machine.

## Confidentialité, limites et diagnostic

Le détecteur traite localement les événements evdev, mais transmet uniquement
activité, touche/bouton maintenu et nombres de périphériques. Aucun code de
touche, texte, coordonnée ou événement brut n’est transmis ou journalisé par
ce détecteur. Les libellés du halo sont une liste fixe ; ils n’affichent pas le
texte saisi, les titres ou le presse-papiers. Le moteur de contrôle possède ses
propres captures et journaux, distincts du compagnon.

Le halo et son bouton peuvent apparaître dans les captures. Quitter le halo
pendant le contrôle peut empêcher une nouvelle commande ; le raccourci écrit
le signal natif même si le halo ne répond pas. Ce mécanisme est un arrêt
coopératif, pas un dispositif de sécurité matérielle.

Voir [le diagnostic](docs/TROUBLESHOOTING.md) et
[le guide de partage et de désinstallation](docs/SHARING.md).

## Validation

```bash
python3 -m unittest discover -v
python3 verify_takeover_ipc.py
```

Le second test utilise Qt hors écran, des événements simulés et des sockets
locaux. Il ne remplace pas un essai physique après installation. Les tests
réels sur Fedora ont confirmé les captures, le déplacement et ses libellés,
la pause par mouvement physique et le bouton de reprise. Le raccourci a été
déclenché par KDE ; sa combinaison physique dans Unreal en plein écran reste
à confirmer. Aucun test réel sur une autre machine n’a encore été effectué.

## Licence

Le code de ce dépôt est sous [licence MIT](LICENSE), qui autorise notamment
la modification et la redistribution en conservant la notice de copyright et
la licence. Les noms d’auteur et liens GitHub sont des attributions publiques,
pas des identifiants requis à l’exécution. Les dépendances et le moteur séparé
conservent leurs propres licences ; inclure leurs notices si on les redistribue.
