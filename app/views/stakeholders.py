"""Stakeholder-Register + Macht/Interesse-Matrix."""
from __future__ import annotations

from nicegui import ui

from components import frame, stat_tile
from store import STAKEHOLDER_STANCE, Stakeholder, store

STANCE_COLOR = {'befuerworter': 'positive', 'neutral': 'grey-6', 'kritiker': 'negative'}


def _form(existing=None) -> None:
    is_new = existing is None
    with ui.dialog() as d, ui.card().classes('w-[32rem] gap-2'):
        ui.label('Neuer Stakeholder' if is_new else 'Bearbeiten').classes('kontor-title text-lg')
        with ui.row().classes('w-full gap-2'):
            name = ui.input('Name / Rolle', value='' if is_new else existing.name) \
                .props('outlined dense').classes('grow')
            org = ui.input('Bereich / Org', value='' if is_new else existing.org) \
                .props('outlined dense').classes('grow')
        role = ui.input('Funktion im Projekt', value='' if is_new else existing.role) \
            .props('outlined dense').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            influence = ui.number('Macht (1–5)', value=3 if is_new else existing.influence,
                                  min=1, max=5, step=1).props('outlined dense').classes('grow')
            interest = ui.number('Interesse (1–5)', value=3 if is_new else existing.interest,
                                 min=1, max=5, step=1).props('outlined dense').classes('grow')
            stance = ui.select(STAKEHOLDER_STANCE, label='Haltung',
                               value='neutral' if is_new else existing.stance).props('outlined dense').classes('grow')
        strategy = ui.textarea('Einbindungsstrategie', value='' if is_new else existing.strategy) \
            .props('outlined dense autogrow').classes('w-full')
        contact = ui.input('Kontakt', value='' if is_new else existing.contact) \
            .props('outlined dense').classes('w-full')

        def save() -> None:
            if not name.value.strip():
                ui.notify('Name fehlt', type='warning')
                return
            data = dict(name=name.value.strip(), org=org.value or '', role=role.value or '',
                        influence=int(influence.value or 3), interest=int(interest.value or 3),
                        stance=stance.value, strategy=strategy.value or '', contact=contact.value or '')
            if is_new:
                store.add('stakeholders', Stakeholder, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('stakeholders', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


def _grid_option(shs) -> dict:
    colors = {'befuerworter': '#3d7a5d', 'neutral': '#8ba1a8', 'kritiker': '#a63a3a'}
    data = [{'value': [s.interest, s.influence], 'name': s.name,
             'itemStyle': {'color': colors[s.stance]}} for s in shs]
    return {
        'grid': {'left': 90, 'right': 30, 'top': 30, 'bottom': 50},
        'xAxis': {'name': 'Interesse →', 'min': 0.5, 'max': 5.5, 'interval': 1,
                  'splitLine': {'show': True}},
        'yAxis': {'name': 'Macht →', 'min': 0.5, 'max': 5.5, 'interval': 1,
                  'splitLine': {'show': True}},
        'tooltip': {'formatter': '{b}'},
        'series': [{
            'type': 'scatter', 'symbolSize': 22, 'data': data,
            'label': {'show': True, 'formatter': '{b}', 'position': 'right', 'fontSize': 10},
            'markArea': {'silent': True, 'itemStyle': {'color': 'rgba(31,78,95,0.05)'}, 'data': [
                [{'xAxis': 3, 'yAxis': 3}, {'xAxis': 5.5, 'yAxis': 5.5}],
            ]},
        }],
    }


@ui.refreshable
def content() -> None:
    shs = store.p_stakeholders()
    with ui.row().classes('w-full items-center'):
        ui.label('Stakeholder').classes('kontor-title text-lg')
        ui.space()
        ui.button('Neuer Stakeholder', icon='add', on_click=_form).props('no-caps')

    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(shs), 'gesamt')
        stat_tile(len([s for s in shs if s.quadrant == 'Eng einbinden']), 'eng einbinden', 'text-primary')
        stat_tile(len([s for s in shs if s.stance == 'kritiker']), 'kritisch',
                  'text-negative' if any(s.stance == 'kritiker' for s in shs) else 'text-grey-5')

    if shs:
        with ui.card().classes('w-full'):
            ui.label('Macht / Interesse (oben rechts = eng einbinden)').classes('kontor-title text-sm')
            ui.echart(_grid_option(shs)).classes('w-full h-80')

    by_q: dict[str, list] = {}
    for s in shs:
        by_q.setdefault(s.quadrant, []).append(s)
    for quad in ('Eng einbinden', 'Zufrieden halten', 'Informieren', 'Beobachten'):
        group = by_q.get(quad, [])
        with ui.card().classes('w-full gap-1'):
            ui.label(f'{quad} ({len(group)})').classes('kontor-title text-sm')
            if not group:
                ui.label('—').classes('text-xs text-grey-5')
            for s in group:
                with ui.row().classes('w-full items-center gap-2 no-wrap border-t border-grey-2 py-1'):
                    ui.label(s.name).classes('text-sm font-medium w-48 truncate')
                    ui.label(s.org).classes('text-xs text-grey-6 w-28 truncate')
                    ui.badge(STAKEHOLDER_STANCE[s.stance]).props(f'color={STANCE_COLOR[s.stance]}')
                    ui.label(s.strategy).classes('text-xs text-grey-7 grow truncate')
                    ui.button(icon='edit', on_click=lambda s=s: _form(s)).props('flat dense size=sm')


def page() -> None:
    with frame('/stakeholders'):
        ui.label('Stakeholder-Management').classes('kontor-title text-xl')
        content()
