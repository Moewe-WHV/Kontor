"""Stundenverbrauchsmeldung: Ist-Aufwand pro Task/Person/Tag buchen."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from nicegui import ui

from components import avatar, bar, frame, stat_tile
from store import store, today_iso

_flt = {'member': None, 'sprint': None}


def _task_options():
    opts = {}
    for t in store.p_tasks():
        if t.status == 'done' and t.sprint_id != (store.active_sprint.id if store.active_sprint else None):
            continue
        sp = store.sprint(t.sprint_id)
        prefix = f'[{sp.name}] ' if sp else '[Backlog] '
        opts[t.id] = prefix + t.title
    return opts


@ui.refreshable
def content() -> None:
    members = store.active_members
    if not members or not store.p_tasks():
        ui.label('Team und Tasks anlegen, dann koennen Stunden gebucht werden.').classes('text-grey-6')
        return

    # -- Buchungsformular ------------------------------------------------
    with ui.card().classes('w-full gap-2'):
        ui.label('Stunden buchen').classes('text-sm font-bold')
        with ui.row().classes('w-full gap-2 items-end flex-wrap'):
            f_member = ui.select({m.id: m.name for m in members}, label='Person',
                                 value=members[0].id).props('outlined dense').classes('w-40')
            f_task = ui.select(_task_options(), label='Task', with_input=True) \
                .props('outlined dense').classes('grow min-w-[16rem]')
            f_date = ui.input('Datum', value=today_iso()).props('outlined dense type=date').classes('w-40')
            f_hours = ui.number('Stunden', value=1.0, min=0.25, step=0.25, format='%.2f') \
                .props('outlined dense').classes('w-28')
            f_note = ui.input('Notiz').props('outlined dense').classes('grow min-w-[10rem]')

            def book() -> None:
                if not f_task.value:
                    ui.notify('Task waehlen', type='warning')
                    return
                store.add_worklog(task_id=f_task.value, member_id=f_member.value,
                                  date=f_date.value or today_iso(), hours=float(f_hours.value or 0),
                                  note=f_note.value or '')
                f_note.value = ''
                ui.notify('Gebucht', type='positive')
                content.refresh()

            ui.button('Buchen', icon='add', on_click=book).props('no-caps')

    # -- Kennzahlen aktueller Sprint -----------------------------------
    sp = store.active_sprint
    if sp:
        logged = store.logged_hours(sp.id)
        cap = store.capacity_hours(sp)
        with ui.row().classes('w-full gap-3 flex-wrap'):
            stat_tile(f'{logged:g} h', f'gebucht · {sp.name.split(" – ")[0]}', 'text-primary')
            stat_tile(f'{store.committed_hours(sp.id):g} h', 'Commitment')
            stat_tile(f'{cap:g} h', 'Kapazitaet')
            week_start = date.today() - timedelta(days=date.today().weekday())
            wk = sum(w.hours for w in store.worklogs if date.fromisoformat(w.date) >= week_start)
            stat_tile(f'{wk:g} h', 'diese Woche (Team)')

    # -- Aufwand je Task (Ist vs. Schaetzung) -------------------------
    with ui.card().classes('w-full gap-1'):
        ui.label('Ist-Aufwand vs. Schaetzung (aktiver Sprint)').classes('text-sm font-bold')
        tasks = [t for t in store.p_tasks() if sp and t.sprint_id == sp.id] if sp else []
        for t in sorted(tasks, key=lambda t: -store.logged_for_task(t.id)):
            lg = store.logged_for_task(t.id)
            if lg == 0 and t.estimate_h == 0:
                continue
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.label(t.title).classes('text-xs w-56 truncate')
                with ui.column().classes('grow'):
                    bar(lg, t.estimate_h or lg or 1)

    # -- Buchungsliste -----------------------------------------------
    with ui.card().classes('w-full gap-1'):
        with ui.row().classes('w-full items-center gap-2'):
            ui.label('Buchungen').classes('text-sm font-bold')
            ui.select({None: 'alle Personen', **{m.id: m.name for m in members}},
                      value=_flt['member'],
                      on_change=lambda e: (_flt.update(member=e.value), content.refresh())) \
                .props('outlined dense').classes('w-44')
        logs = sorted(store.worklogs, key=lambda w: w.date, reverse=True)
        if _flt['member']:
            logs = [w for w in logs if w.member_id == _flt['member']]
        per_member: dict = defaultdict(float)
        for w in logs:
            per_member[w.member_id] += w.hours
        for w in logs[:60]:
            t = store.task(w.task_id)
            m = store.member(w.member_id)
            with ui.row().classes('w-full items-center gap-2 no-wrap border-t border-grey-2 py-1 text-sm'):
                ui.label(w.date).classes('text-xs text-grey-6 w-24')
                avatar(m, '22px')
                ui.label(t.title if t else '—').classes('grow truncate')
                if w.note:
                    ui.label(w.note).classes('text-xs italic text-grey-5 truncate max-w-[12rem]')
                ui.label(f'{w.hours:g} h').classes('w-14 text-right')
                ui.button(icon='delete', on_click=lambda wid=w.id: (store.delete_worklog(wid), content.refresh())) \
                    .props('flat dense size=sm color=grey-6')
        if not logs:
            ui.label('Noch keine Buchungen.').classes('text-xs text-grey-5')

    with ui.card().classes('w-full gap-1'):
        ui.label('Summe je Person (Auswahl)').classes('text-sm font-bold')
        for mid, h in sorted(per_member.items(), key=lambda kv: -kv[1]):
            m = store.member(mid)
            with ui.row().classes('w-full items-center gap-2'):
                avatar(m, '22px')
                ui.label(m.name if m else '—').classes('text-xs w-40')
                ui.label(f'{h:g} h').classes('text-xs text-grey-7')


def page() -> None:
    with frame('/timelog'):
        ui.label('Stundenverbrauch').classes('kontor-title text-xl')
        content()
