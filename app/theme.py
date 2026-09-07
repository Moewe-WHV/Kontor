"""Darstellung / Dark-Mode fuer das Kontor.

Die Auswahl (``auto`` | ``hell`` | ``dunkel``) liegt im Browser-Storage des
Nutzers (``app.storage.user['theme']``) – also pro Gerät, ohne Server-Zustand.
``auto`` folgt der Systemeinstellung des Betriebssystems.

Verwendung in jeder Seite ueber ``components.frame`` – dort wird zu Beginn
``apply()`` aufgerufen, das die Farben setzt, das Stylesheet einbindet und den
NiceGUI-Dark-Mode-Schalter passend stellt.
"""
from __future__ import annotations

from nicegui import app, ui

MODES = ('auto', 'hell', 'dunkel')
_NEXT = {'auto': 'hell', 'hell': 'dunkel', 'dunkel': 'auto'}
_ICON = {'auto': 'brightness_auto', 'hell': 'light_mode', 'dunkel': 'dark_mode'}
_LABEL = {'auto': 'System', 'hell': 'Hell', 'dunkel': 'Dunkel'}
_DARK_VALUE = {'auto': None, 'hell': False, 'dunkel': True}

_HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Semi+Condensed:wght@600;700&display=swap" rel="stylesheet">
<style>
  /* -------- Hell (Standard) -------- */
  body { background:#e7ece9; font-family:'Barlow','Segoe UI',system-ui,sans-serif; color:#22303a; }
  .kontor-title { font-family:'Barlow Semi Condensed','Barlow',sans-serif; letter-spacing:.015em; }
  .q-header { border-bottom:3px solid #e6b422; }
  .q-drawer { background:#f4f6f4 !important; }
  .q-card { border:1px solid #dbe2de; border-radius:10px; box-shadow:0 1px 2px rgba(18,48,58,.05); }
  .nav-item:hover { background:#e3e9e4; }
  .nav-active { background:#1f4e5f; color:#fff; }

  /* -------- Dunkel -------- */
  /* Drei Ebenen fuer klare Tiefe: Seite < Spalte/Panel < Karte */
  body.body--dark { background:#0e1a20; color:#ccd8dc; }
  .body--dark .q-header { border-bottom-color:#e6b422; }
  .body--dark .q-drawer { background:#12212a !important; }
  .body--dark .q-card { background:#1e3038; border:1px solid #384c55; color:#ccd8dc;
                        box-shadow:0 1px 3px rgba(0,0,0,.45); }
  .body--dark .nav-item:hover { background:#1e333c; }
  .body--dark .nav-active { background:#2f6d80; color:#fff; }

  /* Textfarben – auf dunklem Grund aufgehellt, Farbton bleibt */
  .body--dark .text-primary   { color:#63a9be !important; }
  .body--dark .text-secondary { color:#d98a70 !important; }
  .body--dark .text-positive  { color:#5cbd8f !important; }
  .body--dark .text-negative  { color:#e0736f !important; }
  .body--dark .text-warning   { color:#e0a44e !important; }
  .body--dark .text-info      { color:#7fb8cc !important; }
  .body--dark .text-dark      { color:#ccd8dc !important; }

  /* Quasar-Grau-Hilfsklassen fuer den dunklen Grund lesbar halten */
  .body--dark .text-grey-9, .body--dark .text-grey-8 { color:#bcc9cd !important; }
  .body--dark .text-grey-7 { color:#a7b5ba !important; }
  .body--dark .text-grey-6 { color:#97a5aa !important; }
  .body--dark .text-grey-5, .body--dark .text-grey-4 { color:#84939a !important; }

  /* getoente Flaechen + Rahmen */
  .body--dark .bg-blue-1  { background:#14303a !important; }
  .body--dark .bg-red-1   { background:#3a2022 !important; }
  .body--dark .bg-green-1 { background:#173026 !important; }
  .body--dark .bg-amber-1 { background:#332a15 !important; }
  .body--dark .bg-grey-1, .body--dark .bg-grey-2, .body--dark .bg-grey-3 { background:#17272e !important; }
  .body--dark .border-blue-2  { border-color:#1f4a5a !important; }
  .body--dark .border-red-2   { border-color:#5a2f31 !important; }
  .body--dark .border-green-2 { border-color:#2a5045 !important; }
  .body--dark .border-amber-3 { border-color:#5a4a20 !important; }
  .body--dark .border-grey-2, .body--dark .border-grey-3 { border-color:#384c55 !important; }

  /* Fortschrittsbalken-Spur nicht zu hell */
  .body--dark .q-linear-progress__track { opacity:.18 !important; }
</style>
"""


def current() -> str:
    """Aktuell gewaehlter Modus (faellt auf ``auto`` zurueck)."""
    try:
        mode = app.storage.user.get('theme', 'auto')
    except Exception:  # noqa: BLE001 – kein Storage-Kontext
        return 'auto'
    return mode if mode in MODES else 'auto'


def set_mode(mode: str) -> None:
    try:
        app.storage.user['theme'] = mode if mode in MODES else 'auto'
    except Exception:  # noqa: BLE001
        pass


def icon(mode: str | None = None) -> str:
    return _ICON.get(mode or current(), 'brightness_auto')


def label(mode: str | None = None) -> str:
    return _LABEL.get(mode or current(), 'System')


def apply() -> ui.dark_mode:
    """Farben + Stylesheet setzen und den Dark-Mode-Schalter zurueckgeben."""
    _colors = dict(primary='#1f4e5f', secondary='#b5533a', accent='#e6b422',
                   positive='#3d7a5d', negative='#a63a3a', warning='#cf8a2e',
                   info='#5b8ca3', dark='#12303a')
    try:
        ui.colors(dark_page='#0f1b20', **_colors)
    except TypeError:  # aeltere NiceGUI ohne dark_page
        ui.colors(**_colors)
    ui.add_head_html(_HEAD)
    dark = ui.dark_mode(_DARK_VALUE[current()])
    return dark


def toggle_button(dark: ui.dark_mode) -> ui.button:
    """Schalter fuer die Kopfzeile – wechselt auto -> hell -> dunkel -> auto (ohne Reload)."""
    btn = ui.button(icon=icon()).props('flat round color=white')
    btn.tooltip(f'Darstellung: {label()}')

    def _cycle() -> None:
        new = _NEXT[current()]
        set_mode(new)
        dark.value = _DARK_VALUE[new]
        btn.props(f'icon={_ICON[new]}')
        btn.tooltip(f'Darstellung: {_LABEL[new]}')

    btn.on('click', _cycle)
    return btn
