"""Kanban-Board mit Drag & Drop (SortableJS ueber ui.column().make_sortable)."""
from __future__ import annotations

from nicegui import ui

from components import avatar, frame, priority_dot, stat_tile, task_dialog
from store import STATUS_LABELS, STATUSES, store

_filter = {'sprint': None}  # None => aktiver Sprint; '' => Backlog; sonst sprint-id; '*' => alle


def _scope_tasks():
    sel = _filter['sprint']
    ptasks = store.p_tasks()
    if sel is None:
        sp = store.active_sprint
        return [t for t in ptasks if sp and t.sprint_id == sp.id], (sp.name if sp else '—')
    if sel == '*':
        return list(ptasks), 'alle Tasks'
    if sel == '':
        return store.backlog_tasks(), 'Backlog'
    sp = store.sprint(sel)
    return [t for t in ptasks if t.sprint_id == sel], (sp.name if sp else '?')


def _column_id_map() -> dict:
    return _COLS  # gefuellt in render()


_COLS: dict = {}


def _on_drop(e) -> None:
    target_status = _COLS.get(e.target.id)
    if not target_status:
        return
    # Reihenfolge + Status aus der neuen DOM-Anordnung der Zielspalte uebernehmen
    for index, child in enumerate(e.target.default_slot.children):
        tid = getattr(child, '_task_id', None)
        if not tid:
            continue
        t = store.task(tid)
        if t:
            t.order = index
            if t.status != target_status:
                t.status = target_status
                t.done_at = None
            if target_status == 'done' and not t.done_at:
                from store import today_iso
                t.done_at = today_iso()
    store.save()
    stats.refresh()


def _card(task) -> None:
    m = store.member(task.assignee_id)
    logged = store.logged_for_task(task.id)
    card = ui.card().classes('w-full p-2 gap-1 cursor-grab').style('border-left:3px solid transparent')
    card._task_id = task.id  # type: ignore[attr-defined]
    with card:
        with ui.row().classes('w-full items-center no-wrap gap-1'):
            priority_dot(task.priority)
            ui.label(task.title).classes('text-sm font-medium grow leading-tight') \
                .style('word-break:break-word')
            if task.depends_on:
                unmet = any((d := store.task(x)) and d.status != 'done' for x in task.depends_on)
                ui.icon('link' if not unmet else 'link_off', size='15px') \
                    .classes('text-grey-5' if not unmet else 'text-warning') \
                    .tooltip('Abhaengigkeit ' + ('erfuellt' if not unmet else 'noch offen'))
            if task.github_url:
                with ui.link(target=task.github_url, new_tab=True).classes('text-grey-6'):
                    ui.icon('open_in_new', size='16px').tooltip('Link oeffnen')
        with ui.row().classes('w-full items-center gap-1 text-xs text-grey-6'):
            avatar(m, '22px')
            ui.space()
            if task.estimate_h:
                ui.label(f'{logged:g}/{task.estimate_h:g} h')
            for lb in task.labels[:2]:
                ui.badge(lb).props('outline color=primary').classes('text-[10px]')
        if task.blocked:
            with ui.row().classes('items-center gap-1 text-xs text-negative'):
                ui.icon('block', size='14px')
                ui.label(task.blocked_reason or 'blockiert').classes('truncate')
    card.on('click', lambda: task_dialog(task, on_saved=lambda: (board.refresh(), stats.refresh())))


@ui.refreshable
def stats() -> None:
    tasks, scope = _scope_tasks()
    done = [t for t in tasks if t.status == 'done']
    est = sum(t.estimate_h for t in tasks)
    est_done = sum(t.estimate_h for t in done)
    blocked = [t for t in tasks if t.blocked]
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(tasks), f'Tasks · {scope}')
        stat_tile(f'{est_done:g}/{est:g}', 'Story-Stunden', 'text-primary',
                  f'{(est_done / est * 100) if est else 0:.0f}% erledigt')
        stat_tile(len(blocked), 'blockiert', 'text-negative' if blocked else 'text-grey-5')
        stat_tile(len(done), 'fertig', 'text-positive')


@ui.refreshable
def board() -> None:
    _COLS.clear()
    tasks, _ = _scope_tasks()
    by_status = {s: [] for s in STATUSES}
    for t in sorted(tasks, key=lambda t: t.order):
        by_status.setdefault(t.status, []).append(t)

    with ui.row().classes('w-full gap-3 no-wrap overflow-x-auto items-start'):
        for s in STATUSES:
            col_tasks = by_status.get(s, [])
            with ui.card().classes('bg-grey-2 p-2 gap-2 min-w-[15rem] w-64 shrink-0'):
                with ui.row().classes('w-full items-center px-1'):
                    ui.label(STATUS_LABELS[s]).classes('text-sm font-bold uppercase text-grey-7')
                    ui.badge(str(len(col_tasks))).props('color=grey-5')
                    ui.space()
                    ui.label(f'{sum(t.estimate_h for t in col_tasks):g} h').classes('text-xs text-grey-6')
                container = ui.column().classes('w-full gap-2 min-h-[3rem]')
                _COLS[container.id] = s
                with container:
                    for t in col_tasks:
                        _card(t)
                container.make_sortable(group='kanban', animation=0.15, on_end=_on_drop)
                ui.button('+ Task', on_click=lambda s=s: task_dialog(
                    default_status=s,
                    default_sprint=(_filter['sprint'] if isinstance(_filter['sprint'], str)
                                    and _filter['sprint'] not in ('', '*') else
                                    (store.active_sprint.id if store.active_sprint else None)),
                    on_saved=lambda: (board.refresh(), stats.refresh()),
                )).props('flat dense no-caps size=sm').classes('w-full')


def page() -> None:
    with frame('/board'):
        options = {None: 'Aktiver Sprint', '': 'Backlog', '*': 'Alle'}
        options.update({s.id: s.name for s in store.p_sprints()})
        with ui.row().classes('w-full items-center gap-3'):
            ui.label('Kanban-Board').classes('kontor-title text-xl')
            ui.select(options, value=_filter['sprint'],
                      on_change=lambda e: (_filter.update(sprint=e.value), board.refresh(), stats.refresh())) \
                .props('outlined dense').classes('w-56')
            ui.space()
            ui.button('Neuer Task', icon='add',
                      on_click=lambda: task_dialog(
                          on_saved=lambda: (board.refresh(), stats.refresh()))).props('no-caps')
        stats()
        board()
        ui.label('Tipp: Karten per Drag & Drop zwischen den Spalten ziehen · Klick = bearbeiten') \
            .classes('text-xs text-grey-5')
