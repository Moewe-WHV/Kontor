"""RACI – Verantwortlichkeiten je Arbeitsbereich × Crew-Mitglied."""
from __future__ import annotations

from nicegui import ui

from components import frame, stat_tile
from store import RACI_LETTERS, RaciArea, store

LETTER_COLOR = {'R': '#1f4e5f', 'A': '#a63a3a', 'C': '#cf8a2e', 'I': '#8ba1a8'}
CYCLE = ['', 'R', 'A', 'C', 'I']


def _add_area() -> None:
    with ui.dialog() as d, ui.card().classes('w-80 gap-2'):
        ui.label('Neuer Arbeitsbereich').classes('kontor-title')
        name = ui.input('Bezeichnung').props('outlined dense').classes('w-full')

        def save() -> None:
            if name.value.strip():
                store.add('raci_areas', RaciArea, project_id=store.pid, name=name.value.strip(),
                          roles={}, order=len(store.p_raci()))
            d.close()
            content.refresh()
        with ui.row().classes('w-full justify-end'):
            ui.button('Abbrechen', on_click=d.close).props('flat')
            ui.button('Anlegen', on_click=save)
    d.open()


def _cycle(area, member_id: str) -> None:
    cur = area.roles.get(member_id, '')
    nxt = CYCLE[(CYCLE.index(cur) + 1) % len(CYCLE)]
    roles = dict(area.roles)
    if nxt:
        roles[member_id] = nxt
    else:
        roles.pop(member_id, None)
    store.update(area, roles=roles)
    content.refresh()


@ui.refreshable
def content() -> None:
    areas = store.p_raci()
    members = store.active_members
    with ui.row().classes('w-full items-center'):
        ui.label('RACI-Matrix').classes('kontor-title text-lg')
        ui.space()
        ui.button('Arbeitsbereich', icon='add', on_click=_add_area).props('no-caps')

    # Konsistenz-Checks
    no_a = [a for a in areas if 'A' not in a.roles.values()]
    multi_a = [a for a in areas if list(a.roles.values()).count('A') > 1]
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(areas), 'Arbeitsbereiche')
        stat_tile(len(no_a), 'ohne Accountable', 'text-negative' if no_a else 'text-positive')
        stat_tile(len(multi_a), 'mehrfach Accountable', 'text-negative' if multi_a else 'text-positive')

    if not areas or not members:
        ui.label('Arbeitsbereiche und Crew anlegen.').classes('text-sm text-grey-5')
        return

    with ui.card().classes('w-full overflow-x-auto'):
        with ui.element('table').classes('w-full text-sm').style('border-collapse:collapse'):
            with ui.element('tr'):
                ui.element('th').classes('text-left p-1').style('min-width:12rem')
                for m in members:
                    with ui.element('th').classes('p-1 text-xs text-grey-7').style('writing-mode:vertical-rl'):
                        ui.label(m.name)
            for a in areas:
                with ui.element('tr').classes('border-t border-grey-2'):
                    with ui.element('td').classes('p-1'):
                        with ui.row().classes('items-center gap-1 no-wrap'):
                            ui.label(a.name).classes('text-sm grow')
                            ui.button(icon='close', on_click=lambda a=a: (store.remove('raci_areas', a.id),
                                                                          content.refresh())) \
                                .props('flat dense size=xs color=grey-5')
                    for m in members:
                        letter = a.roles.get(m.id, '')
                        with ui.element('td').classes('p-1 text-center'):
                            ui.button(letter or '·', on_click=lambda a=a, mid=m.id: _cycle(a, mid)) \
                                .props('flat dense').style(
                                'width:32px;height:28px;font-weight:700;border-radius:6px;'
                                + (f'background:{LETTER_COLOR[letter]};color:#fff' if letter
                                   else 'color:#bbb'))
    with ui.row().classes('gap-3 text-xs text-grey-6'):
        for k, v in RACI_LETTERS.items():
            ui.label(f'{k} = {v}').style(f'color:{LETTER_COLOR[k]}')
        ui.label('· Zelle klicken schaltet R→A→C→I→leer')


def page() -> None:
    with frame('/raci'):
        ui.label('RACI – Verantwortlichkeiten').classes('kontor-title text-xl')
        content()
