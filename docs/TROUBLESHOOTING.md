# Diagnostic

## Le halo ne démarre pas

Lancer `python3 overlay.py` dans un terminal de la session graphique et vérifier
`$XDG_RUNTIME_DIR/codex-activity-halo/overlay.log`. Avec Qt/XWayland, `DISPLAY`
et `XAUTHORITY` doivent appartenir à la session actuelle. Après reconnexion,
relancer le client plutôt que de recopier un ancien chemin `xauth_*`.
`WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR` et le bus D-Bus doivent aussi être ceux de
la même session. Ne pas lancer le halo avec sudo.

## L’agent annonce « Action not started »

Lire `status.json` dans le même dossier de fonctionnement :

- `human_monitor_ready=false` : vérifier le service avec
  `systemctl status "codex-input-activity-$(id -u).service"` et son journal.
- `human_paused=true` : cliquer sur **Reprendre**, pas sur une commande terminal
  supprimant le signal d’arrêt.
- `human_input_held=true` : relâcher touches et boutons.
- `safety_wait_seconds>0` : attendre cinq secondes sans entrée physique.

Un échec avant envoi peut être retenté après résolution. Une action envoyée
ne doit pas être rejouée à l’aveugle : observer d’abord son effet.

## « stale_session » ou approbation portail absente

Une session du moteur peut avoir été révoquée ou retirée. Refaire l’initialisation
avec le binaire installé, accepter soi-même la demande de partage KDE, puis
redécouvrir les fenêtres et reprendre une nouvelle observation. Ne jamais
réutiliser les IDs d’une ancienne session ou ceux d’un autre client.
Comparer le binaire, ses variables de session et ses permissions entre clients ;
une capture réussie dans Codex ne garantit pas la même session dans un autre agent.

L’absence d’accès direct du moteur à `/dev/input` n’est pas, à elle seule, la
preuve d’un échec de capture : le détecteur externe utilise ses descripteurs
ouverts avant abandon des privilèges. Ne pas ajouter le client au groupe `input`
pour résoudre une erreur de portail.

## AT-SPI désactivé

Activer l’infrastructure d’accessibilité de la session et relancer les applications
qui ne sont pas découvertes. Le lecteur vocal Orca n’est pas nécessaire ;
« Activer le lecteur d’écran » peut provoquer une lecture à voix haute.

## Mouvement refusé sur le deuxième écran

Le mode fluide du fork vérifie que le pointeur est sur la région autorisée.
Replacer physiquement la souris sur l’écran contrôlé. Le réglage du bouton du
halo ne change pas les permissions du portail.

## Pas de bouton, ou raccourci inactif

Vérifier l’écran principal KDE et les variables de sélection. Le bouton apparaît
pendant le contrôle, la pause et le délai de reprise ; il est masqué au repos.
Réinstaller le raccourci après déplacement du dossier du projet. Dans les
raccourcis KDE, rechercher **Arrêter le contrôle Codex**. Une application ou un
jeu peut inhiber les raccourcis globaux : confirmer physiquement le résultat.
