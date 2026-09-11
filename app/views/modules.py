"""Module – Bereiche des Leitstands je Projekt ein- oder ausblenden (v2).

Kleine Projekte brauchen selten Incidents, RACI oder OKRs. Hier lässt sich pro
Projekt festlegen, was im Menü erscheint. Kernbereiche (Leitstand, Fahrplan,
Projekte, Crew, Einstellungen …) bleiben immer sichtbar.

Gespeichert wird die Auswahl als ``Project.disabled_modules`` in pm.json –
leere Liste heißt „alles an", neu hinzukommende Module erscheinen automatisch.
"""
from __future__ import annotations

from nicegui import ui

from components import NAV_GROUPS, frame, help_hint, viewer_is_leader
from store import CORE_MODULES, store

# Ein paar sinnvolle Startpakete für neue Projekte.
PRESETS: dict[str, set[str]] = {
    'Alles': set(),
    'Schlank (kleines Team)': {
        '/charter', '/requirements', '/roadmap', '/milestones', '/okrs', '/raci',
        '/capacity', '/burndown', '/quality', '/environments', '/incidents',
        '/stakeholders', '/meetings', '/changes', '/raid', '/documents', '/vendors',
        '/lessons', '/one-on-ones', '/status', '/metrics', '/budget',
    },
    'Nur Delivery': {
        '/portfolio', '/status', '/metrics', '/budget', '/charter', '/requirements',
        '/roadmap', '/milestones', '/okrs', '/raci', '/stakeholders', '/meetings',
        '/changes', '/raid', '/documents', '/vendors', '/wetter', '/retro',
        '/lessons', '/one-on-ones', '/ideas', '/environments', '/incidents',
    },
    # Nur Bereiche aus, die zwingend mehrere Personen voraussetzen (Kapazitaet,
    # Abwesenheiten, Standup, Retro, Team-Wetter, 1:1s, RACI). Alles, was auch
    # eine Einzelperson braucht – Stakeholder, Budget, Releases, Qualitaet,
    # Steckbrief usw. – bleibt an.
    'Solo (Einzelkämpfer)': {
        '/capacity', '/absences', '/standup', '/retro', '/wetter',
        '/one-on-ones', '/raci',
    },
}


def _all_module_paths() -> list[str]:
    return [path for _, items in NAV_GROUPS for _, _, path in items if path not in CORE_MODULES]


def _apply_preset(name: str) -> None:
    disabled = sorted(PRESETS.get(name, set()) & set(_all_module_paths()))
    store.set_project_modules(disabled)
    ui.notify(f'Vorlage „{name}" übernommen', type='positive')
    content.refresh()


@ui.refreshable
def content() -> None:
    p = store.project
    if not p:
        ui.label('Kein Projekt ausgewählt – lege in der Werft eines an.').classes('text-grey-6')
        return

    disabled = set(getattr(p, 'disabled_modules', None) or [])
    all_paths = _all_module_paths()
    active_n = len(all_paths) - len([x for x in disabled if x in all_paths])
    can_edit = p.mode == 'solo' or viewer_is_leader(p.id)

    help_hint('Schalter aus = der Bereich verschwindet aus dem Menü dieses Projekts. '
              'Die Daten bleiben erhalten und sind nach dem Wiedereinschalten sofort '
              'wieder da. Andere Projekte sind nicht betroffen.',
              title='Wie das funktioniert')

    if not can_edit:
        help_hint('Nur die Teamleitung dieses Projekts kann die Modul-Auswahl ändern. '
                   'Du siehst hier den aktuellen Stand.', title='Nur lesend')

    with ui.card().classes('w-full gap-2'):
        with ui.row().classes('w-full items-center gap-2 flex-wrap'):
            ui.label(f'Projekt: {p.name}').classes('kontor-title text-md')
            ui.badge(f'{active_n} von {len(all_paths)} Zusatz-Modulen aktiv') \
                .props('color=primary')
            ui.space()
            if can_edit:
                ui.label('Vorlage:').classes('text-xs text-grey-6')
                for name in PRESETS:
                    ui.button(name, on_click=lambda n=name: _apply_preset(n)) \
                        .props('flat dense no-caps size=sm')

    for group, items in NAV_GROUPS:
        extra = [(label, icon, path) for label, icon, path in items if path not in CORE_MODULES]
        core = [(label, icon, path) for label, icon, path in items if path in CORE_MODULES]
        if not extra and not core:
            continue
        with ui.card().classes('w-full gap-1'):
            ui.label(group).classes('kontor-title text-sm text-grey-7 uppercase tracking-widest')
            for label, icon, path in core:
                with ui.row().classes('w-full items-center gap-2 no-wrap opacity-60'):
                    ui.icon(icon).classes('text-lg')
                    ui.label(label).classes('text-sm grow')
                    ui.icon('lock', size='16px').classes('text-grey-5').tooltip('Kernbereich – immer sichtbar')
            for label, icon, path in extra:
                on = path not in disabled
                with ui.row().classes('w-full items-center gap-2 no-wrap'):
                    ui.icon(icon).classes('text-lg ' + ('' if on else 'text-grey-5'))
                    ui.label(label).classes('text-sm grow ' + ('' if on else 'text-grey-5'))
                    sw = ui.switch(value=on,
                                   on_change=lambda e, pth=path: _toggle(pth, bool(e.value)))
                    sw.set_enabled(can_edit)


def _toggle(path: str, enabled: bool) -> None:
    store.set_module(path, enabled)
    content.refresh()


def page() -> None:
    with frame('/modules'):
        ui.label('Module').classes('kontor-title text-xl')
        content()
