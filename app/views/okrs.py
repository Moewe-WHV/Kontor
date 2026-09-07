"""OKRs – Objectives & Key Results mit Fortschritts-Rollup."""
from __future__ import annotations

from nicegui import ui

from components import avatar, frame, stat_tile
from store import KeyResult, Objective, store


def _obj_form(existing=None) -> None:
    is_new = existing is None
    members = {'': '– niemand –', **{m.id: m.name for m in store.active_members}}
    with ui.dialog() as d, ui.card().classes('w-96 gap-2'):
        ui.label('Neues Objective' if is_new else 'Objective bearbeiten').classes('kontor-title text-lg')
        title = ui.input('Objective', value='' if is_new else existing.title).props('outlined dense').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            period = ui.input('Zeitraum', value='' if is_new else existing.period,
                              placeholder='z. B. Q3').props('outlined dense').classes('grow')
            owner = ui.select(members, label='Owner',
                              value='' if is_new or not existing.owner_id else existing.owner_id) \
                .props('outlined dense').classes('grow')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), period=period.value or '', owner_id=owner.value or None)
            if is_new:
                store.add('objectives', Objective, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (_delete_obj(existing), d.close(), content.refresh())).props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


def _delete_obj(obj) -> None:
    store.key_results = [k for k in store.key_results if k.objective_id != obj.id]
    store.remove('objectives', obj.id)


def _kr_form(objective_id: str, existing=None) -> None:
    is_new = existing is None
    with ui.dialog() as d, ui.card().classes('w-[26rem] gap-2'):
        ui.label('Neues Key Result' if is_new else 'Key Result bearbeiten').classes('kontor-title text-lg')
        title = ui.input('Key Result', value='' if is_new else existing.title).props('outlined dense').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            sv = ui.number('Start', value=0 if is_new else existing.start_value, format='%g') \
                .props('outlined dense').classes('grow')
            cv = ui.number('Aktuell', value=0 if is_new else existing.current_value, format='%g') \
                .props('outlined dense').classes('grow')
            tv = ui.number('Ziel', value=100 if is_new else existing.target_value, format='%g') \
                .props('outlined dense').classes('grow')
            unit = ui.input('Einheit', value='%' if is_new else existing.unit).props('outlined dense').classes('w-20')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), start_value=float(sv.value or 0),
                        current_value=float(cv.value or 0), target_value=float(tv.value or 0),
                        unit=unit.value or '')
            if is_new:
                store.add('key_results', KeyResult, objective_id=objective_id, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('key_results', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


def _prog_color(p: float) -> str:
    return '#a63a3a' if p < 0.4 else '#cf8a2e' if p < 0.7 else '#3d7a5d'


@ui.refreshable
def content() -> None:
    objs = store.p_objectives()
    with ui.row().classes('w-full items-center'):
        ui.label('OKRs').classes('kontor-title text-lg')
        ui.space()
        ui.button('Neues Objective', icon='add', on_click=_obj_form).props('no-caps')

    if objs:
        avg = sum(store.objective_progress(o.id) for o in objs) / len(objs)
        with ui.row().classes('w-full gap-3 flex-wrap'):
            stat_tile(f'{avg:.0%}', 'Ø Zielerreichung',
                      'text-positive' if avg >= 0.7 else 'text-warning' if avg >= 0.4 else 'text-negative')
            stat_tile(len(objs), 'Objectives')
            stat_tile(sum(len(store.krs_of(o.id)) for o in objs), 'Key Results')

    for o in objs:
        prog = store.objective_progress(o.id)
        with ui.card().classes('w-full gap-2'):
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.circular_progress(prog, min=0, max=1, show_value=False, size='40px') \
                    .props('color=primary track-color=grey-3')
                with ui.column().classes('gap-0 grow'):
                    ui.label(o.title).classes('font-medium')
                    ui.label(f'{o.period or "—"} · {int(prog * 100)}% erreicht').classes('text-xs text-grey-6')
                avatar(store.member(o.owner_id), '22px')
                ui.button(icon='add', on_click=lambda o=o: _kr_form(o.id)).props('flat dense').tooltip('Key Result')
                ui.button(icon='edit', on_click=lambda o=o: _obj_form(o)).props('flat dense size=sm')
            for kr in store.krs_of(o.id):
                with ui.row().classes('w-full items-center gap-2 no-wrap border-t border-grey-2 py-1'):
                    ui.label(kr.title).classes('text-sm grow truncate')
                    ui.label(f'{kr.current_value:g} / {kr.target_value:g} {kr.unit}') \
                        .classes('text-xs text-grey-6 w-28 text-right')
                    ui.linear_progress(kr.progress, show_value=False, size='8px',
                                       color='primary').classes('w-28')
                    ui.button(icon='edit', on_click=lambda kr=kr: _kr_form(o.id, kr)).props('flat dense size=sm')
            if not store.krs_of(o.id):
                ui.label('Noch keine Key Results.').classes('text-xs text-grey-5')


def page() -> None:
    with frame('/okrs'):
        ui.label('OKRs / Ziele').classes('kontor-title text-xl')
        content()
