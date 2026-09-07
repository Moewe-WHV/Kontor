"""Sprint-Planung: Sprints anlegen, Backlog -> Sprint ziehen, Commitment vs. Kapazitaet."""
from __future__ import annotations

from datetime import date, timedelta

from nicegui import ui

from components import avatar, bar, frame, priority_dot, resolve_sprint, stat_tile, task_dialog
from store import store

_sel = {'sprint': None}


def _current():
    return resolve_sprint(_sel['sprint'])


def _sprint_form(existing=None) -> None:
    is_new = existing is None
    with ui.dialog() as d, ui.card().classes('w-96 gap-2'):
        ui.label('Neuer Sprint' if is_new else 'Sprint bearbeiten').classes('text-lg font-bold')
        name = ui.input('Name', value='' if is_new else existing.name).props('outlined dense').classes('w-full')
        goal = ui.textarea('Sprint-Ziel', value='' if is_new else existing.goal) \
            .props('outlined dense autogrow').classes('w-full')
        start = date.today() + timedelta(days=(0 - date.today().weekday()) % 7)
        with ui.row().classes('w-full gap-2'):
            s_start = ui.input('Start', value=start.isoformat() if is_new else existing.start) \
                .props('outlined dense type=date').classes('grow')
            s_end = ui.input('Ende', value=(start + timedelta(days=11)).isoformat() if is_new else existing.end) \
                .props('outlined dense type=date').classes('grow')

        def save() -> None:
            if not name.value.strip():
                ui.notify('Name fehlt', type='warning')
                return
            if is_new:
                store.add_sprint(project_id=store.pid, name=name.value.strip(), goal=goal.value or '',
                                 start=s_start.value, end=s_end.value)
            else:
                existing.name, existing.goal = name.value.strip(), goal.value or ''
                existing.start, existing.end = s_start.value, s_end.value
                store.save()
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-end'):
            ui.button('Abbrechen', on_click=d.close).props('flat')
            ui.button('Speichern', on_click=save)
    d.open()


def _row(task, in_sprint: bool, sid: str | None) -> None:
    with ui.row().classes('w-full items-center gap-2 py-1 border-b border-grey-3 no-wrap'):
        priority_dot(task.priority)
        ui.label(task.title).classes('text-sm grow truncate')
        ui.label(f'{task.estimate_h:g} h').classes('text-xs text-grey-6 w-12 text-right')
        avatar(store.member(task.assignee_id), '22px')
        if in_sprint:
            ui.button(icon='arrow_back', on_click=lambda: _move(task, None)) \
                .props('flat dense size=sm').tooltip('zurueck ins Backlog')
        else:
            ui.button(icon='arrow_forward', on_click=lambda: _move(task, sid)) \
                .props('flat dense size=sm color=primary').tooltip('in den Sprint')
        ui.button(icon='edit', on_click=lambda: task_dialog(task, on_saved=content.refresh)) \
            .props('flat dense size=sm')


def _move(task, sid) -> None:
    task.sprint_id = sid
    store.save()
    content.refresh()


@ui.refreshable
def content() -> None:
    sprints = store.p_sprints()
    if not sprints:
        ui.label('Noch kein Sprint. Lege den ersten an.').classes('text-grey-6')
        ui.button('Sprint anlegen', icon='add', on_click=_sprint_form).props('no-caps')
        return

    sp = _current()
    with ui.row().classes('w-full items-center gap-2'):
        ui.select({s.id: s.name for s in sprints}, value=sp.id,
                  on_change=lambda e: (_sel.update(sprint=e.value), content.refresh())) \
            .props('outlined dense').classes('w-64')
        badge = {'active': ('AKTIV', 'positive'), 'planned': ('geplant', 'grey-6'), 'done': ('fertig', 'blue-4')}
        lbl, col = badge.get(sp.status, ('?', 'grey'))
        ui.badge(lbl).props(f'color={col}')
        ui.space()
        if sp.status != 'active':
            ui.button('aktivieren', icon='play_arrow',
                      on_click=lambda: (store.activate_sprint(sp.id), content.refresh())) \
                .props('outline no-caps size=sm')
        ui.button(icon='edit', on_click=lambda: _sprint_form(sp)).props('flat dense')
        ui.button('Neuer Sprint', icon='add', on_click=_sprint_form).props('no-caps size=sm')

    if sp.goal:
        ui.label(f'Ziel: {sp.goal}').classes('text-sm italic text-grey-8')

    committed = store.committed_hours(sp.id)
    capacity = store.capacity_hours(sp)
    sprint_tasks = [t for t in store.p_tasks() if t.sprint_id == sp.id]
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(f'{sp.start} → {sp.end}', 'Zeitraum', hint=f'{len(sp.workdays())} Werktage')
        stat_tile(f'{committed:g} h', 'Commitment', 'text-primary', f'{len(sprint_tasks)} Tasks')
        stat_tile(f'{capacity:g} h', 'Kapazitaet',
                  'text-negative' if committed > capacity else 'text-positive',
                  'ueberbucht' if committed > capacity else 'im Rahmen')
        stat_tile(f'{(committed / capacity * 100) if capacity else 0:.0f}%', 'Auslastung')

    with ui.card().classes('w-full gap-1'):
        ui.label('Auslastung pro Person').classes('text-sm font-bold')
        for m in store.active_members:
            cap = store.capacity_of(sp.id, m.id)
            mcap = cap.hours if cap else round(m.weekly_hours * sp.weeks, 1)
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                avatar(m, '24px')
                ui.label(m.name).classes('text-xs w-32 truncate')
                with ui.column().classes('grow'):
                    bar(store.member_load(sp.id, m.id), mcap or 1)

    with ui.row().classes('w-full gap-3 items-start no-wrap'):
        for title, tasks, in_sprint in [
            (f'Backlog ({len(store.backlog_tasks())})', store.backlog_tasks(), False),
            (f'Im Sprint ({len(sprint_tasks)}) · {committed:g} h', sprint_tasks, True),
        ]:
            with ui.card().classes('grow gap-0 min-w-0'):
                ui.label(title).classes('text-sm font-bold mb-1')
                if not tasks:
                    ui.label('—').classes('text-xs text-grey-5')
                for t in sorted(tasks, key=lambda t: -t.estimate_h):
                    _row(t, in_sprint, sp.id)


def page() -> None:
    with frame('/sprints'):
        ui.label('Sprint-Planung').classes('kontor-title text-xl')
        content()
