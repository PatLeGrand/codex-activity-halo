"""Per-agent visual identity for the shared activity overlay.

One overlay serves every agent. The MCP proxy names its agent in the `begin`
request (HALO_AGENT); anything unknown falls back to Codex, so existing
clients keep their look.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    accent: tuple          # corner glow and pointer ring
    paused: tuple          # glow while the human holds control
    dot: tuple             # status dot in the badge
    badge_fill: tuple
    badge_edge: tuple
    badge_text: tuple
    ring_fill: tuple
    ring_outer: tuple
    button: str            # control button while the agent may act
    button_paused: str     # control button while the human holds control
    tray: tuple
    starburst: bool        # draw the tray icon as a spark instead of a disc


THEMES = {
    "codex": Theme(
        name="Codex",
        accent=(36, 174, 255), paused=(255, 172, 47), dot=(62, 173, 255),
        badge_fill=(13, 27, 47, 235), badge_edge=(67, 156, 255, 190), badge_text=(233, 244, 255),
        ring_fill=(26, 108, 235, 35), ring_outer=(227, 247, 255, 235),
        button="#176bc2", button_paused="#c77816", tray=(45, 148, 255), starburst=False),
    # Claude: terracotta accent on warm dark, cream text. The pause colour is a
    # gold that stays clearly apart from the terracotta glow.
    "claude": Theme(
        name="Claude",
        accent=(217, 119, 87), paused=(244, 191, 67), dot=(232, 140, 104),
        badge_fill=(38, 38, 36, 235), badge_edge=(217, 119, 87, 190), badge_text=(250, 249, 245),
        ring_fill=(217, 119, 87, 45), ring_outer=(240, 238, 230, 235),
        button="#c15f3c", button_paused="#a67c00", tray=(217, 119, 87), starburst=True),
}


def theme_for(agent):
    return THEMES.get(agent, THEMES["codex"])
