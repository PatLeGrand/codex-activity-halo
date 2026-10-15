# Utilisation

Ce guide décrit ce que vous voyez et pouvez faire pendant qu'un agent contrôle
votre écran, puis le dépannage. L'installation est dans
[INSTALLATION.md](INSTALLATION.md).

## Une session, du début à la fin

1. **L'agent demande une action** sur le bureau (capture, clic, saisie...).
2. **Annonce.** L'indicateur joue un carillon de début. Le badge, en haut au
   centre de chaque écran, affiche « *Agent* commence dans 2 s » et un bouton
   flottant propose « Annuler le démarrage ». Rien n'est encore envoyé à l'écran.
3. **L'action part** quand le décompte est terminé. Le halo reste visible tant
   que l'agent travaille ; le badge décrit l'opération en cours (« Capture de
   l'écran », « Clic de souris »...).
4. **Les actions s'enchaînent** sans nouveau décompte tant que deux appels
   restent espacés de moins de huit secondes : ce sont une seule session.
5. **Fin de session.** Huit secondes après la dernière réponse, le halo
   s'efface et un carillon de fin retentit.

Si vous annulez pendant le décompte, l'action n'atteint jamais le serveur.

## Ce que vous voyez

| Élément | Signification |
| --- | --- |
| Halo aux quatre coins de chaque écran | L'agent a la main (ou va l'avoir) |
| Badge en haut au centre | Opération en cours, décompte, pause ou attente |
| Anneau qui suit le pointeur | Position réelle du pointeur pendant l'activité |
| Carillons | Début et fin de session (volume modéré) |
| Bouton flottant en haut à droite de l'**écran principal** | Arrêter, annuler ou reprendre |
| Icône dans la zone de notification | Menu de l'indicateur |
| Halo de la couleur « pause » | **Vous avez la main** : l'agent est suspendu |

Les libellés décrivent uniquement le *type* d'opération : capture de l'écran,
repérage des fenêtres, gestion d'une fenêtre, ouverture d'une application,
attente, déplacement, clic, défilement, glisser-déposer, saisie au clavier,
collage, interaction avec un élément ou un champ, presse-papiers. Jamais le
texte saisi, un titre de fenêtre ou le contenu du presse-papiers.

Le libellé dit ce qui a été *demandé*, pas que l'effet a réussi dans
l'application.

### Thèmes

| | Codex | Claude |
| --- | --- | --- |
| Halo et anneau du pointeur | bleu `#24AEFF` | terracotta `#D97757` |
| Badge | fond bleu nuit | fond sombre chaud, texte crème |
| Pause | orange | or `#F4BF43` |
| Icône de notification | disque bleu | étincelle à huit rayons |
| Bouton de contrôle | bleu / orange | terracotta `#C15F3C` / or sombre |

Le thème vient de la variable `HALO_AGENT` du proxy (`claude` ou `codex`). Sans
elle, ou avec une valeur inconnue, c'est Codex. L'indicateur est **partagé** :
le dernier agent qui démarre une action fixe l'apparence. Les thèmes sont
définis dans `theme.py` ; pour en ajouter un, ajoutez une entrée à `THEMES`.

## Reprendre la main : pause et reprise

Vous restez prioritaire. Dès qu'un clavier, une souris ou un pavé tactile
physique est utilisé pendant une session, **l'agent est suspendu** :

- le halo prend la couleur de pause et le badge affiche « Vous avez la main —
  *Agent* suspendu » ;
- l'action en cours est interrompue ; une action non démarrée est refusée avec
  « Control unavailable or paused » ;
- la pause est **verrouillée** : elle ne se lève pas toute seule quand vous
  lâchez la souris, il faut la lever explicitement (ci-dessous).

Pour rendre la main à l'agent :

1. cliquez sur **« Reprendre le contrôle *Agent* »** (bouton flottant, ou menu
   de l'icône) ;
2. **lâchez clavier et souris** : une attente de sécurité de 5 secondes
   s'affiche, et toute nouvelle activité physique la relance.

Une touche ou un bouton maintenu bloque aussi le contrôle. Les entrées envoyées
par l'agent lui-même ne déclenchent pas la pause : les périphériques virtuels
sont exclus de la détection.

> Piège fréquent : écrire un message à l'agent *est* une activité physique. Si
> l'agent est en pause, reprenez le contrôle, puis laissez-lui quelques
> secondes sans toucher à rien avant qu'il agisse.

### Arrêt d'urgence

- **Ctrl+Alt+Fin** (Ctrl+Alt+End), de n'importe où : suspend le contrôle et
  le laisse suspendu jusqu'à une reprise manuelle.
- Bouton flottant « Arrêter le contrôle *Agent* », ou menu de l'icône.
- En dernier recours, créez le signal natif du serveur :
  `touch "$XDG_RUNTIME_DIR/computer-use-mcp-takeover"` (supprimé par la reprise).

## Menu de l'icône

| Entrée | Effet |
| --- | --- |
| Afficher l'indicateur | Active ou masque le halo (n'affecte pas les garde-fous) |
| Aperçu pendant 8 secondes | Affiche le halo, étiqueté comme aperçu |
| Reprendre le contrôle *Agent* | Lève la pause (voir ci-dessus) |
| Quitter l'indicateur | Arrête l'indicateur |

Sans indicateur, le proxy **refuse** les appels (« Action not started »), il ne
les laisse pas passer sans garde-fou. Un proxy ne relance l'indicateur qu'à son
propre démarrage : après l'avoir quitté, redémarrez l'agent, ou relancez-le
à la main depuis le dossier du dépôt :

```bash
HALO_AGENT=claude QT_QPA_PLATFORM=xcb setsid python3 overlay.py >/dev/null 2>&1 &
```

Les proxys déjà ouverts se reconnectent ensuite sans redémarrage.

## Variables d'environnement

Du proxy (donc de l'agent) :

| Variable | Rôle |
| --- | --- |
| `HALO_AGENT` | `claude` ou `codex` : thème et nom affichés |
| `XDG_STATE_HOME` | Dossier d'état du serveur : **jeton du portail** et historique des appels. À séparer entre agents |
| `XDG_RUNTIME_DIR` | Emplacement des sockets et de `status.json` |

Du serveur `computer-use-mcp` (voir son [MCP.md](https://github.com/mirsella/computer-use-mcp/blob/main/MCP.md)) :

| Variable | Rôle |
| --- | --- |
| `COMPUTER_USE_MCP_MONITOR` | Écran contrôlé (fork), p. ex. `HDMI-A-1` |
| `COMPUTER_USE_MCP_SMOOTH_POINTER=1` | Pointeur animé (fork). L'indicateur doit tourner et son anneau fournit la position |
| `COMPUTER_USE_MCP_TAKEOVER=1` | Force le signal de reprise humaine |
| `COMPUTER_USE_MCP_PERSIST_PORTAL=0` | Ne lit ni n'écrit le jeton du portail |
| `COMPUTER_USE_MCP_KDE_WINDOW_MANAGEMENT=1` | Géométrie des fenêtres via KWin (voir limites) |

## Conseils pour l'agent

Avec `--compact-tools`, le serveur n'expose que `help` et `dispatch`. Les
consignes à donner à l'agent tiennent en quelques règles :

- appeler `list_desktop` d'abord et **recopier tels quels** les identifiants
  (`app-…`, `win-…`, `obs-…`, `frame-…`, `e-…`) : ils sont liés à un worker
  et deviennent invalides s'il est remplacé ;
- les coordonnées sont celles de l'**image** reçue, pas celles de l'écran. Une
  capture de 1920×1080 est renvoyée en 1280×720 ; le serveur reconvertit
  exactement ;
- préférer les actions sémantiques (`element_id`, arbre d'accessibilité) aux
  clics par coordonnées pour les petites cibles ;
- après une pause humaine, les observations antérieures sont périmées :
  attendre `human_idle`, puis observer de nouveau.

## Dépannage

| Symptôme | Cause probable | Que faire |
| --- | --- | --- |
| « Control unavailable or paused » | Vous avez touché clavier ou souris : pause verrouillée, ou attente de sécurité en cours | Reprendre le contrôle, lâcher les périphériques (5 s) |
| `stale_session` sur chaque `observe`, juste après `list_desktop` | Le worker de bureau est retiré : portail refusé ou jeton invalide pour l'identité de l'application | Dossier d'état propre à l'agent, puis `computer-use-mcp init`. Vérifiez qu'aucun autre agent n'utilise le même `XDG_STATE_HOME` |
| `stale_session` après une longue pause ou un redémarrage du worker | Les identifiants sont périmés | Rappeler `list_desktop` et recopier les nouveaux |
| Contrôle refusé dès le premier appel, sans que vous ayez touché à rien (« Control unavailable or paused » ou « Desktop call blocked ») | Le détecteur d'entrées ne tourne pas ou sa couverture est incomplète | `systemctl status codex-input-activity-$(id -u)`, `python3 monitor_helper.py --check` |
| `"human_monitor_ready": false` dans `status.json` | Même cause | Idem ; après un branchement de périphérique, le service redémarre seul |
| Aucune icône, aucun halo, appels refusés (« Action not started ») | Indicateur non lancé (PySide6 absent, pas de XWayland) ou quitté | Lire `$XDG_RUNTIME_DIR/codex-activity-halo/overlay.log`, puis relancer l'indicateur |
| Le halo garde l'ancien aspect | L'ancien indicateur tourne toujours | Menu → « Quitter l'indicateur », puis relancer l'agent |
| Mauvais thème (Codex au lieu de Claude) | `HALO_AGENT` absent du serveur MCP | `claude mcp get computer_use` : la variable doit apparaître |
| « Cursor is outside known screens » ou refus du déplacement | Pointeur lissé : la souris est sur un autre écran que celui contrôlé | Replacer la souris sur l'écran contrôlé |
| Le halo apparaît dans les captures | Normal : l'indicateur est une fenêtre | — |
| Une fenêtre KDE d'approbation s'ouvre à chaque session | Jeton perdu (session tuée de force, autre agent sur le même dossier) | `computer-use-mcp init` |

Logs utiles : `computer-use-mcp history --errors --last 20` (appels du
serveur) et `overlay.log` (indicateur).

## Limites connues

- **Recadrage de fenêtre.** `crop: "target_window"` exige l'interface KWin
  `org_kde_plasma_window_management`, que KWin réserve aux programmes déclarés
  par `X-KDE-Wayland-Interfaces` dans un fichier `.desktop`. Avec le mode
  activé, `list_desktop` renvoyait des identifiants refusés (`stale_session`)
  sur la version testée : il n'est pas recommandé. Sans lui, le serveur renvoie
  l'écran entier avec la raison du repli.
- **Un indicateur, un utilisateur.** Une seule instance tourne par session
  utilisateur, partagée par tous les agents ; deux agents actifs en même temps
  se partagent l'affichage.
- **KDE Plasma sous Wayland uniquement.** Le serveur et l'indicateur reposent
  sur les portails KDE, KWin et XWayland.
- **Pas un bac à sable.** Les garde-fous empêchent surtout une action contre
  votre gré ; ils ne limitent pas ce que l'agent peut faire une fois autorisé.

## Confidentialité et sécurité

- **Ce que l'indicateur lit** : les métadonnées du journal d'appels du serveur
  (type d'action, identifiants d'appel, moment), jamais les captures, les
  frappes ni le contenu des fenêtres. Il ne capture aucune entrée clavier.
- **Le détecteur** (root, puis utilisateur normal) ne transmet que des
  booléens et des compteurs. Son code est court et se lit :
  [`monitor_helper.py`](../monitor_helper.py).
- **Le serveur** voit tout l'écran sélectionné (fenêtres, notifications
  comprises) et peut lire l'arbre d'accessibilité. N'accordez le portail qu'à un
  agent et un utilisateur de confiance. Voir
  [SECURITY.md](https://github.com/mirsella/computer-use-mcp/blob/main/SECURITY.md).
- **Réseau** : ni l'indicateur ni le détecteur n'ouvrent de connexion ; seuls
  des sockets Unix locaux (`AF_UNIX`) sont utilisés.
