# Architecture

Vue d'ensemble du fonctionnement interne. Utile pour dépanner, auditer ou
ajouter un agent.

## Les processus

```text
 Agent (Claude Code / Codex)
        │  MCP, JSON-RPC sur stdin/stdout
        ▼
 feedback_proxy.py ──────────────┐        un proxy par agent et par session
        │ transmet tel quel      │ socket Unix : feedback.sock
        ▼                        ▼
 computer-use-mcp          overlay.py (indicateur)      un seul par utilisateur
  (portails KDE : capture,   halo, badge, anneau, sons, bouton,
   EIS : clic et saisie,     icône, état de pause
   AT-SPI : fenêtres)               ▲
                                    │ socket Unix datagramme : activity.sock
                          monitor_helper.py (service systemd)
                          lit /dev/input, n'émet que des booléens
```

Les sockets, `status.json`, `overlay.log` et le verrou `daemon.lock` se
trouvent dans `$XDG_RUNTIME_DIR/codex-activity-halo/` (le nom date de la
première version, centrée sur Codex).

## Rôle de chaque fichier

| Fichier | Rôle |
| --- | --- |
| `feedback_proxy.py` | Relaie le protocole MCP. Pour chaque appel de bureau au premier plan, dialogue avec l'indicateur (`begin`, `ready`, `end`) avant d'envoyer l'appel au serveur |
| `action_labels.py` | Transforme une requête en libellé neutre (« Clic de souris »), sans contenu |
| `overlay.py` | Indicateur Qt : fenêtres transparentes par écran, serveur de socket, sons, icône, bouton, état de pause |
| `feedback.py` | Chronologie d'une session (décompte de 2 s, fin à 8 s) et libellés du bouton |
| `takeover_state.py` | Machine d'état de la reprise humaine (battement du détecteur, pause verrouillée, attente de 5 s) |
| `theme.py` | Identité visuelle par agent |
| `activity.py` | Lecture du journal d'appels du serveur (indication de repli) et chemin du dossier d'exécution |
| `monitor_helper.py`, `install_input_monitor.py` | Détecteur d'entrées physiques et son installation |
| `stop_control.py`, `install_stop_shortcut.py` | Arrêt global Ctrl+Alt+Fin |
| `server.py` | Petit serveur MCP du plugin Codex : outils `status` et `preview`, lance l'indicateur |

## Protocole du proxy vers l'indicateur

Une ligne JSON par requête sur `feedback.sock`, une ligne JSON de réponse.

| `op` | Effet |
| --- | --- |
| `begin` | Ouvre ou prolonge une session. Champs : `call`, `label`, `agent` (optionnel : `claude`, `codex`). Répond `wait_ms` (reste du décompte) ou une erreur si le contrôle est suspendu |
| `ready` | Seconde vérification, juste avant l'envoi : refuse si une pause est survenue pendant le décompte |
| `end` | Clôt un appel ; la session se termine 8 s après le dernier |
| `cursor` | Position réelle du pointeur et de son écran, pour le pointeur animé du serveur |
| `stop` | Pause immédiate (raccourci d'arrêt) |
| `quit` | Arrête l'indicateur |

Un client sans champ `agent` est traité comme Codex : l'indicateur reste
compatible avec les proxys d'avant l'ajout des thèmes.

## Pause et signal natif

Une activité physique pendant une session fait trois choses : l'indicateur
verrouille la pause, crée le fichier `$XDG_RUNTIME_DIR/computer-use-mcp-takeover`
(signal coopératif lu par le serveur, qui interrompt alors l'action), et
affiche la pause. La reprise supprime ce fichier et lance une attente de
sécurité de 5 secondes, relancée par toute nouvelle activité. Le serveur
conserve de son côté sa propre attente de 5 secondes.

Le contrôle est refusé tant que le détecteur n'a pas envoyé de battement
récent (moins de 2 s) avec au moins un clavier et un pointeur.

## Identité du portail et jeton

Le portail KDE (`xdg-desktop-portal`) identifie l'application d'après son
scope systemd (`app-<identité>-<n>.scope`) et y rattache les autorisations
mémorisées. Le jeton de reprise du serveur
(`$XDG_STATE_HOME/computer-use-mcp/portal-restore-token`) n'est valable que pour
l'identité qui l'a obtenu, et il est consommé à chaque démarrage. D'où la règle :
**un dossier d'état par agent**.

## Ajouter un agent

1. Ajouter un `Theme` à `THEMES` dans `theme.py` (nom, couleurs, icône).
2. Lancer son proxy avec `HALO_AGENT=<clé>`.
3. Ajouter un test dans `test_theme.py` et lancer
   `python3 -m unittest -v test_theme.py test_feedback.py`.
