# Partager une version communautaire

## Ce qui est portable

Le bouton utilise l’écran principal par défaut. Les manifestes distribués
n’imposent ni nom d’utilisateur, ni chemin personnel, ni connecteur HDMI.
L’exemple d’intégration comporte des chemins explicitement à remplacer.
Le service et le raccourci génèrent leurs chemins et UID sur la machine cible.
Ne pas partager ces fichiers générés depuis son propre poste.

Le nom de marketplace distribué est **activity-halo**, avec l’identifiant
`activity-halo@activity-halo`. Les versions locales antérieures utilisaient
`activity-halo@patou-local` : ne pas activer les deux identifiants en parallèle.
Conserver l’installation locale existante pendant la migration, puis la désactiver
quand la nouvelle a été vérifiée. Un seul halo tourne par utilisateur.

Les noms dans `LICENSE`, l’auteur du manifeste et l’URL du dépôt sont des
attributions. La licence MIT doit accompagner les copies. Partager le source
ne nécessite pas de retirer ces mentions ; distribuer les dépendances ou le
binaire du moteur demande de conserver aussi leurs notices respectives.

## Avant de diffuser

1. Utiliser une révision identifiée du compagnon et un moteur compatible.
2. Conserver `LICENSE`, `README.md`, `docs/` et `examples/`.
3. Faire installer les dépendances et le détecteur sur la machine cible.
4. Tester une capture, un déplacement, la reprise humaine, l’arrêt global et
   les cinq secondes de reprise, avec les moniteurs réellement présents.
5. Ne pas inclure captures privées, journaux, jetons du portail, configuration
   du client ou fichiers de session de sa propre machine dans l’archive.

La documentation n’a pas pour effet de rendre un dépôt privé public. Le choix
de visibilité GitHub et la publication d’une release sont des actions distinctes.
Cette version est communautaire et validée sur un poste Fedora/KDE ; aucune
compatibilité Windows ou multi-distribution n’est revendiquée.

## Désinstaller

Désactiver d’abord le serveur Computer Use configuré avec le proxy, ou restaurer
sa configuration précédente, puis désactiver le plugin compagnon dans le client.
Quitter le halo depuis son menu. Ne pas enlever ses fichiers pendant un contrôle.

Dans les paramètres KDE, retirer le raccourci **Arrêter le contrôle Codex**, puis
supprimer `$XDG_DATA_HOME/kglobalaccel/codex-stop.desktop` (par défaut sous
`~/.local/share/kglobalaccel`).

Pour le détecteur, depuis le compte ayant effectué l’installation :

```bash
sudo systemctl disable --now "codex-input-activity-$(id -u).service"
sudo rm "/etc/systemd/system/codex-input-activity-$(id -u).service"
sudo systemctl daemon-reload
```

Le helper `/usr/local/libexec/codex-input-activity/monitor_helper.py` est commun
aux utilisateurs : ne le supprimer que si aucun autre service utilisateur ne
l’utilise. Retirer enfin le dossier permanent du projet. Les fichiers temporaires
sous `$XDG_RUNTIME_DIR` disparaissent à la fin de la session.
