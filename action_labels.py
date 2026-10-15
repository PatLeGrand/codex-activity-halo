"""Describe operation kinds without displaying content, titles or coordinates."""


def action_label(message):
    params = message.get('params', {})
    name = params.get('name')
    outer = params.get('arguments', {})
    action = outer.get('action') if name == 'dispatch' else name
    args = outer.get('arguments', {}) if name == 'dispatch' else outer
    labels = {'observe': 'Capture de l’écran', 'list_desktop': 'Repérage des fenêtres',
              'activate_window': 'Gestion d’une fenêtre', 'launch_application': 'Ouverture d’une application',
              'wait_for': 'Attente d’un changement'}
    if action != 'act':
        return labels.get(action, 'Action sur le PC')
    operation = args.get('operation', {})
    kind = operation.get('type')
    if kind == 'pointer':
        pointer = operation.get('action', {}).get('type')
        return {'move': 'Déplacement de la souris', 'click': 'Clic de souris',
                'scroll': 'Défilement', 'drag': 'Glisser-déposer'}.get(pointer, 'Action de souris')
    if kind == 'semantic' and operation.get('action', {}).get('type') == 'set_value':
        return 'Saisie dans un champ'
    return {'paste': 'Collage de texte', 'semantic': 'Interaction avec un élément', 'keyboard': 'Saisie au clavier', 'element': 'Interaction avec un élément',
            'clipboard': 'Action sur le presse-papiers'}.get(kind, 'Interaction avec le PC')
