"""Projekt-Steckbrief – Charter: Vision, Scope, Erfolgskriterien, Rahmen, DoR/DoD."""
from __future__ import annotations

from nicegui import ui

from components import frame, stat_tile
from store import store


def _list_field(label: str, obj, attr: str) -> None:
    ta = ui.textarea(label, value='\n'.join(getattr(obj, attr))) \
        .props('outlined dense autogrow').classes('w-full')
    ta.on('blur', lambda: store.update(
        obj, **{attr: [x.strip() for x in (ta.value or '').splitlines() if x.strip()]}))


@ui.refreshable
def content() -> None:
    p = store.project
    if not p:
        return
    ui.label('Änderungen werden beim Verlassen eines Feldes gespeichert.').classes('text-xs text-grey-5')

    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(p.scope_in), 'im Scope')
        stat_tile(len(p.scope_out), 'außerhalb')
        stat_tile(len(p.success_criteria), 'Erfolgskriterien')
        crit = [r for r in store.p_requirements(p.id) if r.moscow == 'muss']
        stat_tile(f'{len([r for r in crit if r.status == "abgenommen"])}/{len(crit)}', 'Muss-Anf. abgenommen')

    with ui.card().classes('w-full gap-2'):
        ui.label('Eckdaten').classes('kontor-title text-sm')
        with ui.row().classes('w-full gap-2'):
            for lbl, attr in (('Start', 'start_date'), ('Zieltermin', 'target_date')):
                w = ui.input(lbl, value=getattr(p, attr)).props('outlined dense type=date').classes('grow')
                w.on('blur', lambda w=w, a=attr: store.update(p, **{a: w.value or ''}))
            sp = ui.input('Sponsor / Auftraggeber', value=p.sponsor).props('outlined dense').classes('grow')
            sp.on('blur', lambda: store.update(p, sponsor=sp.value or ''))
        vis = ui.textarea('Vision / Zielbild', value=p.vision).props('outlined dense autogrow').classes('w-full')
        vis.on('blur', lambda: store.update(p, vision=vis.value or ''))

    with ui.row().classes('w-full gap-3 no-wrap flex-wrap'):
        with ui.card().classes('grow min-w-[18rem] gap-2'):
            ui.label('In Scope').classes('kontor-title text-sm text-positive')
            _list_field('', p, 'scope_in')
        with ui.card().classes('grow min-w-[18rem] gap-2'):
            ui.label('Out of Scope').classes('kontor-title text-sm text-negative')
            _list_field('', p, 'scope_out')

    with ui.card().classes('w-full gap-2'):
        ui.label('Erfolgskriterien').classes('kontor-title text-sm')
        _list_field('', p, 'success_criteria')
    with ui.row().classes('w-full gap-3 no-wrap flex-wrap'):
        with ui.card().classes('grow min-w-[18rem] gap-2'):
            ui.label('Randbedingungen').classes('kontor-title text-sm')
            _list_field('', p, 'constraints')
        with ui.card().classes('grow min-w-[18rem] gap-2'):
            ui.label('Annahmen').classes('kontor-title text-sm')
            _list_field('', p, 'assumptions')

    with ui.row().classes('w-full gap-3 no-wrap flex-wrap'):
        with ui.card().classes('grow min-w-[18rem] gap-2'):
            ui.label('Definition of Ready').classes('kontor-title text-sm')
            _list_field('', p, 'dor')
        with ui.card().classes('grow min-w-[18rem] gap-2'):
            ui.label('Definition of Done').classes('kontor-title text-sm')
            _list_field('', p, 'dod')


def page() -> None:
    with frame('/charter'):
        ui.label('Projekt-Steckbrief').classes('kontor-title text-xl')
        content()
