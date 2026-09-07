"""Flotte – Portfolio-Sicht ueber alle Projekte."""
from __future__ import annotations

from nicegui import ui

from components import bar, frame, stat_tile
from store import WEATHER, store


def _health_color(h: dict) -> str:
    if h['blocked'] or h['high_risks']:
        return 'text-negative'
    if h['sprint'] and h['progress'] < 0.4 and (h['sprint'].days_left or 9) < 4:
        return 'text-warning'
    return 'text-positive'


@ui.refreshable
def content() -> None:
    projects = store.active_projects
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(projects), 'Projekte')
        stat_tile(len([p for p in projects if store.active_sprint_of(p.id)]), 'im Sprint')
        allblocked = sum(store.project_health(p.id)['blocked'] for p in projects)
        stat_tile(allblocked, 'Blocker gesamt', 'text-negative' if allblocked else 'text-grey-5')
        allrisk = sum(store.project_health(p.id)['high_risks'] for p in projects)
        stat_tile(allrisk, 'hohe Risiken', 'text-negative' if allrisk else 'text-grey-5')

    # -- Auslastung der Crew ueber alle aktiven Sprints ----------------
    active_sprints = [s for p in projects if (s := store.active_sprint_of(p.id))]
    with ui.card().classes('w-full gap-1'):
        ui.label('Crew-Auslastung ueber alle aktiven Sprints').classes('kontor-title text-sm')
        for m in store.active_members:
            load = sum(store.member_load(s.id, m.id) for s in active_sprints)
            cap = sum(store.member_richtwert(s, m) for s in active_sprints) or 1
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.label(m.name).classes('text-xs w-36 truncate')
                with ui.column().classes('grow'):
                    bar(load, cap)

    for p in projects:
        h = store.project_health(p.id)
        sp = h['sprint']
        with ui.card().classes('w-full gap-2').style(f'border-left:4px solid {p.color}'):
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.label(p.key or '·').classes('kontor-title text-xs px-1 rounded').style(
                    f'background:{p.color};color:#fff')
                ui.label(p.name).classes('kontor-title text-lg grow')
                if h['mood']:
                    icon, lbl, col = WEATHER[round(h['mood'])]
                    ui.icon(icon).style(f'color:{col}').tooltip(f'Team-Wetter: {lbl} ({h["mood"]})')
                ui.button('oeffnen', on_click=lambda p=p: (store.set_current_project(p.id),
                                                           ui.navigate.to('/'))) \
                    .props('flat dense no-caps size=sm')
            if p.description:
                ui.label(p.description).classes('text-sm text-grey-7')
            with ui.row().classes('w-full gap-4 flex-wrap text-sm'):
                ui.label(f'Sprint: {sp.name}' if sp else 'kein aktiver Sprint') \
                    .classes('font-medium ' + _health_color(h))
                if sp:
                    ui.label(f'{sp.days_left} Tage übrig' if sp.days_left is not None else '')
                ui.label(f'{h["open_tasks"]} offene Tasks')
                ui.label(f'{h["blocked"]} blockiert').classes('text-negative' if h['blocked'] else 'text-grey-6')
                ui.label(f'{h["open_risks"]} Risiken').classes('text-negative' if h['high_risks'] else 'text-grey-6')
                if h['incidents']:
                    ui.label(f'{h["incidents"]} Incidents').classes('text-negative')
                if h['bugs_critical']:
                    ui.label(f'{h["bugs_critical"]} Bugs krit.').classes('text-negative')
                nm = next((m for m in store.p_milestones(p.id) if m.status == 'offen' and m.due), None)
                if nm:
                    ui.label(f'nächster Meilenstein: {nm.title} ({nm.due})').classes('text-grey-6')
                cost = store.project_cost(p.id)
                if cost['budget']:
                    pctb = cost['eac'] / cost['budget'] * 100
                    ui.label(f'Budget-Prognose: {pctb:.0f}%') \
                        .classes('text-negative' if pctb > 100 else 'text-grey-6')
            if sp and h['committed']:
                bar(h['done'], h['committed'], label='Sprint-Fortschritt (Story-Stunden)')


def page() -> None:
    with frame('/portfolio'):
        ui.label('Flotte').classes('kontor-title text-xl')
        content()
