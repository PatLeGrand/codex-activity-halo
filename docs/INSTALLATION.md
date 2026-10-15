# Installation

Ce guide installe, sur KDE Plasma sous Wayland, un agent IA capable de voir et
de contrôler l'écran (Claude Code ou Codex), avec un indicateur visuel et des
garde-fous : halo, anneau autour du pointeur, sons, décompte avant l'action,
pause dès que vous touchez le clavier ou la souris, arrêt d'urgence.

Voir aussi : [UTILISATION.md](UTILISATION.md) pour l'usage au quotidien et le
dépannage, [ARCHITECTURE.md](ARCHITECTURE.md) pour le fonctionnement interne.

> **Ce projet n'est affilié ni à Anthropic ni à OpenAI.** « Claude » et
> « Codex » ne désignent ici que les agents qu'il habille ; les couleurs du thème
> Claude s'en inspirent librement.

## Ce que vous installez

| Pièce | Rôle | Obligatoire |
| --- | --- | --- |
| `computer-use-mcp` (serveur MCP, Rust) | Capture d'écran, clic, saisie, lecture des fenêtres, via les portails KDE | oui |
| Ce dépôt : proxy + indicateur (Python, Qt) | Halo, sons, décompte, bouton d'arrêt, reprise humaine | oui |
| Détecteur d'entrées physiques (service systemd, `sudo` une fois) | Détecte que vous touchez clavier ou souris, sans rien enregistrer | **oui** : sans lui, le contrôle refuse de démarrer |
| Raccourci global Ctrl+Alt+Fin | Arrêt d'urgence | recommandé |

L'agent parle au serveur MCP **à travers le proxy** de ce dépôt. Le proxy ne
modifie pas le protocole : il annonce chaque action à l'indicateur, attend le
décompte, puis la transmet.

## Prérequis

**Testé sur** : Fedora 44, KDE Plasma 6.7 sous Wayland, deux écrans
1920×1080, Claude Code 2.1 et l'application Codex. Rien n'a été essayé sur
d'autres distributions ou d'autres bureaux : sur Ubuntu/Debian, les noms de
paquets ci-dessous sont à adapter.

- KDE Plasma 6 en session **Wayland** (`echo $XDG_SESSION_TYPE` → `wayland`).
- **XWayland** et composition activée (l'indicateur est une fenêtre Qt/X11).
- Portails `xdg-desktop-portal` et `xdg-desktop-portal-kde` : `RemoteDesktop`
  version 2 minimum, `ScreenCast` version 3 minimum.
- PipeWire 1.0 ou plus récent, AT-SPI (`at-spi2-registryd`).
- `systemd` (le détecteur est un service), `busctl`, `python3`.
- Python 3 avec **PySide6** 6.6 à 6.x (Qt Widgets, Network, Multimedia).
- Un compte administrateur, pour une seule commande `sudo` (détecteur d'entrées).

Deux emplacements sont codés en dur : le proxy et le détecteur utilisent
`/usr/bin/python3`, et le socket de l'indicateur se trouve dans
`$XDG_RUNTIME_DIR/codex-activity-halo/` (le nom date de la première version).
PySide6 doit donc être importable avec `/usr/bin/python3` :

```bash
/usr/bin/python3 -c "import PySide6; print(PySide6.__version__)"
```

Si la commande échoue, installez-le pour cet interpréteur, avec le paquet de
votre distribution (`python3-pyside6` sous Fedora) ou avec
`pip install --user -r requirements.txt`.

## 1. Récupérer ce dépôt

```bash
git clone https://github.com/PatLeGrand/codex-activity-halo.git
cd codex-activity-halo
python3 -m unittest -v test_theme.py test_feedback.py test_activity.py \
  test_action_labels.py test_proxy.py test_takeover.py
```

Gardez ce dossier à un emplacement **permanent** : l'agent y lancera le proxy,
et le service système y copie un script à l'installation. Le reste de ce guide
suppose que vous êtes dans ce dossier.

## 2. Installer le serveur `computer-use-mcp`

Le serveur est le projet de mirsella,
[mirsella/computer-use-mcp](https://github.com/mirsella/computer-use-mcp).
Ce dépôt s'intègre à une variante, le fork
[PatLeGrand/computer-use-mcp](https://github.com/PatLeGrand/computer-use-mcp),
qui ajoute trois choses :

- `COMPUTER_USE_MCP_MONITOR` : limiter capture et pointeur à **un seul écran** ;
- `COMPUTER_USE_MCP_SMOOTH_POINTER=1` : pointeur animé que l'anneau suit ;
- une reprise humaine avec 5 secondes de calme.

**Option A, recommandée : le fork.** Il se compile avec Rust 1.97 ou plus
récent et les bibliothèques de développement (clang, D-Bus, GLib, PipeWire,
xkbcommon). Liste Ubuntu 24.04 donnée par le projet :

```bash
sudo apt-get install build-essential clang libclang-dev libdbus-1-dev \
  libglib2.0-dev libpipewire-0.3-dev libspa-0.2-dev libxkbcommon-dev pkg-config
```

Sous Fedora, les paquets équivalents sont `clang`, `clang-devel`,
`dbus-devel`, `glib2-devel`, `pipewire-devel`, `libxkbcommon-devel` et
`pkgconf` (noms habituels, non vérifiés ici). Puis :

```bash
cargo install --locked \
  --git https://github.com/PatLeGrand/computer-use-mcp \
  --branch codex/desktop-feedback computer-use-mcp
```

Le binaire est installé dans `~/.cargo/bin/computer-use-mcp`. La branche
`codex/desktop-feedback` contient aussi la sélection d'écran
(`codex/primary-monitor`).

**Option B : la version de mirsella.** Pas d'écran unique, ni de pointeur
animé, ni d'attente de 5 secondes, mais l'indicateur fonctionne (il lit le
journal des appels). Binaire précompilé (Node.js 22 ou plus, glibc 2.39 ou plus) :

```bash
npx -y @mirsella/opencode-computer-use-mcp version
```

ou compilation : `cargo install --locked --git https://github.com/mirsella/computer-use-mcp computer-use-mcp`.

**Vérifier** (aucune demande d'autorisation) :

```bash
computer-use-mcp doctor
```

Les sections `Wayland session`, `Accessibility (AT-SPI)`, `XDG desktop portal`,
`PipeWire` doivent afficher `READY`. La ligne `Portal approval and EIS input :
NOT TESTED` est normale à ce stade.

## 3. Installer le détecteur d'entrées physiques (sudo, une fois)

Le détecteur lit les événements bruts du clavier, de la souris et du pavé
tactile, pour savoir *que* vous avez la main. Il n'envoie à l'indicateur que
des booléens (activité, touche maintenue, nombre de périphériques) : ni code de
touche, ni texte, ni coordonnées. Il s'exécute dans un service systemd durci,
ouvre les périphériques en lecture seule, **abandonne ses droits root avant de
traiter le moindre événement** et ne vous ajoute pas au groupe `input`. Les
périphériques virtuels, dont ceux que l'agent utilise, sont ignorés.

Regardez d'abord ce qui sera installé :

```bash
python3 install_input_monitor.py --dry-run
```

Puis installez-le, depuis votre compte normal :

```bash
sudo /usr/bin/python3 -I install_input_monitor.py
systemctl status "codex-input-activity-$(id -u).service"
```

Le script copie `monitor_helper.py` dans `/usr/local/libexec/codex-input-activity/`
et crée `/etc/systemd/system/codex-input-activity-<UID>.service`. Pour vérifier
la couverture des périphériques sans rien installer :

```bash
python3 monitor_helper.py --check
```

Il doit annoncer au moins un clavier et un pointeur. Si vous branchez ou
débranchez un périphérique, le service redémarre seul pour actualiser sa
couverture. Sans couverture complète, le contrôle refuse de démarrer, par
sécurité.

## 4. Installer l'arrêt d'urgence Ctrl+Alt+Fin

```bash
python3 install_stop_shortcut.py
```

Le raccourci s'enregistre dans KDE sans `sudo`. S'il est déjà pris par une autre
application, le script le refuse sans rien modifier. Il suspend le contrôle
jusqu'à ce que vous le repreniez à la main.

## 5. Approuver l'écran auprès de KDE

Le portail KDE demande votre accord pour partager **un** écran et autoriser
clavier et pointeur. L'accord se mémorise dans un jeton de reprise. Ce jeton est
**lié à l'identité de l'application** (le scope systemd) : Claude Code et Codex
ne peuvent pas partager le même. Donnez à chaque agent son dossier d'état :

```bash
# pour Claude ; pour Codex, utilisez par exemple ~/.local/state/codex-computer-use
export XDG_STATE_HOME="$HOME/.local/state/claude-computer-use"
mkdir -p "$XDG_STATE_HOME"
COMPUTER_USE_MCP_MONITOR=<ÉCRAN> computer-use-mcp init
```

`<ÉCRAN>` est le nom de l'écran à contrôler, par exemple `HDMI-A-1` ou `eDP-1`
(`kscreen-doctor -o` les liste). Une fenêtre KDE s'ouvre : choisissez cet écran
et validez. Le jeton est enregistré dans
`$XDG_STATE_HOME/computer-use-mcp/portal-restore-token`. Il est à usage unique
et se renouvelle à chaque session propre ; si une session est tuée de force, il
peut manquer, et il suffit de relancer `init`.

## 6. Brancher l'agent

Dans tous les cas, la commande lancée par l'agent est le **proxy**, qui reçoit
en arguments le binaire à envelopper :

```text
/usr/bin/python3 <ce dossier>/feedback_proxy.py <chemin de computer-use-mcp> mcp --compact-tools
```

`--compact-tools` n'expose que deux outils (`help` et `dispatch`), plus
économiques en contexte. Les variables d'environnement utiles sont décrites
dans [UTILISATION.md](UTILISATION.md#variables-denvironnement).

### Claude Code

Lancez la commande **depuis le projet** où vous utiliserez Claude Code (la
portée par défaut est locale à ce projet ; ajoutez `-s user` pour tous vos
projets) :

```bash
claude mcp add computer_use \
  -e COMPUTER_USE_MCP_MONITOR=<ÉCRAN> \
  -e COMPUTER_USE_MCP_SMOOTH_POINTER=1 \
  -e XDG_STATE_HOME="$HOME/.local/state/claude-computer-use" \
  -e HALO_AGENT=claude \
  -- /usr/bin/python3 "$PWD/feedback_proxy.py" \
     "$HOME/.cargo/bin/computer-use-mcp" mcp --compact-tools
```

(Adaptez `$PWD/feedback_proxy.py` si vous lancez la commande ailleurs que dans
le dossier de ce dépôt.) Vérifiez avec `claude mcp list` : l'état doit être
`Connected`. Les outils n'apparaissent qu'au démarrage d'une **nouvelle
session** dans ce projet.

### Codex

Le dépôt est aussi un plugin Codex (`.codex-plugin/`, `.agents/plugins/`), qui
ajoute au besoin les outils `status` et `preview` de l'indicateur :

```bash
codex plugin marketplace add "$PWD"
codex plugin add activity-halo@patou-local
```

Le serveur Computer Use de Codex doit lui aussi passer par le proxy. Voici le
principe, tel qu'utilisé avec le plugin de mirsella (`.mcp.json`) ; remplacez
les chemins et l'écran par les vôtres :

```json
{
  "mcpServers": {
    "computer_use": {
      "command": "/usr/bin/python3",
      "args": [
        "/chemin/vers/codex-activity-halo/feedback_proxy.py",
        "/chemin/vers/computer-use-mcp", "mcp", "--compact-tools"
      ],
      "startup_timeout_sec": 40,
      "tool_timeout_sec": 150,
      "env_vars": ["DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS",
                   "XDG_RUNTIME_DIR", "XDG_SESSION_TYPE", "XDG_CURRENT_DESKTOP"],
      "env": {
        "COMPUTER_USE_MCP_MONITOR": "<ÉCRAN>",
        "COMPUTER_USE_MCP_SMOOTH_POINTER": "1"
      }
    }
  }
}
```

Redémarrez Codex pour charger le serveur. Sans `HALO_AGENT`, l'indicateur garde
l'aspect Codex (bleu).

## 7. Vérifier

1. Une icône apparaît dans la zone de notification au démarrage de l'agent
   (bleue pour Codex, étincelle terracotta pour Claude). Menu → « Aperçu
   pendant 8 secondes » : le halo doit s'afficher aux quatre coins de chaque
   écran.
2. L'état de l'indicateur :

   ```bash
   cat "$XDG_RUNTIME_DIR/codex-activity-halo/status.json"
   ```

   Vérifiez `"human_monitor_ready": true` et `"human_paused": false`. Le champ
   `agent` indique le thème actif.
3. Demandez à l'agent de lister les fenêtres, puis de faire une capture. Au
   premier appel, vous entendez un carillon, le badge compte deux secondes,
   puis l'action part.

Si l'indicateur affiche « Vous avez la main », la pause est active : voir
[UTILISATION.md](UTILISATION.md#reprendre-la-main--pause-et-reprise).

## Mise à jour

```bash
git pull
sudo /usr/bin/python3 -I install_input_monitor.py   # seulement si monitor_helper.py a changé
```

Pour appliquer la nouvelle version de l'indicateur : icône → « Quitter
l'indicateur », puis redémarrez l'agent (son proxy relance l'indicateur au
démarrage) ou relancez-le à la main, voir
[UTILISATION.md](UTILISATION.md#menu-de-licône). Tant qu'il est arrêté, les
appels de l'agent sont refusés.

## Désinstallation

```bash
# détecteur d'entrées
sudo systemctl disable --now "codex-input-activity-$(id -u).service"
sudo rm "/etc/systemd/system/codex-input-activity-$(id -u).service"
sudo rm -r /usr/local/libexec/codex-input-activity
sudo systemctl daemon-reload

# raccourci d'arrêt
rm ~/.local/share/kglobalaccel/codex-stop.desktop   # puis retirez l'entrée dans Raccourcis, si elle reste

# agent
claude mcp remove computer_use                      # Claude Code
# Codex : désactivez le plugin activity-halo@patou-local dans l'application

# jeton du portail et historique des appels de l'agent
rm -r ~/.local/state/claude-computer-use
```

Vous pouvez aussi révoquer l'autorisation dans les paramètres KDE (Confidentialité
→ Partage d'écran / Contrôle à distance), et supprimer le dossier du dépôt.
