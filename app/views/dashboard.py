"""Leitstand: Sprint-Lage + GitHub-PRs auf einen Blick."""
from __future__ import annotations

import asyncio
import os
from datetime import date

from nicegui import ui

from components import avatar, bar, chart_opts, frame, stat_tile
from github_client import GitHubClient, human_age
from store import RAG, store

DEFAULT_REPO = os.getenv('GITHUB_REPO', 'zauberzeug/nicegui')
_gh: dict = {'snap': None, 'loading': False, 'repo': DEFAULT_REPO}


def _configured_repo() -> str:
    return (store.setting('github_repo') or '').strip() or DEFAULT_REPO


def _configured_token() -> str | None:
    return (store.setting('github_token') or '').strip() or None


async def _load_gh() -> None:
    _gh['loading'] = True
    gh_panel.refresh()
    try:
        _gh['snap'] = await GitHubClient(_gh['repo'], token=_configured_token()).fetch()
    except Exception as exc:  # noqa: BLE001
        _gh['snap'] = None
        ui.notify(f'GitHub-Fehler: {exc}', type='negative')
    finally:
        _gh['loading'] = False
        gh_panel.refresh()


def _sprint_burndown_option(sp) -> dict:
    bd = store.burndown(sp)
    return {
        'grid': {'left': 35, 'right': 10, 'top': 10, 'bottom': 20},
        'xAxis': {'type': 'category', 'data': bd['days'], 'show': False},
        'yAxis': {'type': 'value', 'show': False},
        'tooltip': {'trigger': 'axis'},
        'series': [
            {'type': 'line', 'data': bd['ideal'], 'symbol': 'none',
             'lineStyle': {'type': 'dashed', 'color': '#94a3b8'}},
            {'type': 'line', 'data': bd['remaining'], 'smooth': True, 'symbol': 'none',
             'lineStyle': {'width': 3, 'color': '#4d9fb4'},
             'areaStyle': {'opacity': 0.15, 'color': '#4d9fb4'}},
        ],
    }


@ui.refreshable
def sprint_panel() -> None:
    sp = store.active_sprint
    if not sp:
        with ui.card().classes('w-full'):
            ui.label('Kein aktiver Sprint – in der Sprint-Planung einen aktivieren.').classes('text-grey-6')
        return
    committed = store.committed_hours(sp.id)
    done = store.done_hours(sp.id)
    cap = store.capacity_hours(sp)
    logged = store.logged_hours(sp.id)
    tasks = [t for t in store.p_tasks() if t.sprint_id == sp.id]

    with ui.card().classes('w-full gap-2'):
        with ui.row().classes('w-full items-center'):
            ui.label(sp.name).classes('text-lg font-bold')
            ui.space()
            dl = sp.days_left
            ui.badge(f'{dl} Tage übrig' if dl is not None and dl >= 0 else 'Sprint-Ende erreicht') \
                .props('color=primary' if (dl or 0) >= 0 else 'color=negative')
        if sp.goal:
            ui.label(sp.goal).classes('text-sm italic text-grey-8')
        with ui.row().classes('w-full gap-3 flex-wrap'):
            stat_tile(f'{done:g}/{committed:g}', 'Story-Stunden', 'text-primary',
                      f'{(done / committed * 100) if committed else 0:.0f}% fertig')
            stat_tile(f'{len([t for t in tasks if t.status == "done"])}/{len(tasks)}', 'Tasks fertig')
            stat_tile(f'{logged:g} h', 'Ist-Aufwand')
            stat_tile(f'{cap:g} h', 'Kapazitaet',
                      'text-negative' if committed > cap else 'text-positive')
        with ui.row().classes('w-full gap-4 no-wrap items-center'):
            with ui.column().classes('grow gap-1'):
                bar(committed, cap, label='Commitment vs. Kapazitaet')
                bar(logged, committed or 1, color='positive', label='Ist-Aufwand vs. Commitment')
            if store.burndown(sp)['days']:
                ui.echart(chart_opts(_sprint_burndown_option(sp))).classes('w-64 h-28')


@ui.refreshable
def focus_panel() -> None:
    blocked = [t for t in store.p_tasks() if t.blocked and t.status != 'done']
    review = [t for t in store.p_tasks() if t.status == 'review']
    with ui.row().classes('w-full gap-3 items-start no-wrap flex-wrap'):
        with ui.card().classes('grow min-w-[18rem] gap-1'):
            ui.label(f'Blockiert ({len(blocked)})').classes('text-sm font-bold text-negative')
            if not blocked:
                ui.label('nichts blockiert 🎉').classes('text-xs text-grey-5')
            for t in blocked:
                with ui.row().classes('w-full items-center gap-2 no-wrap'):
                    ui.icon('block', size='16px').classes('text-negative')
                    ui.label(t.title).classes('text-sm truncate')
                    ui.space()
                    ui.label(t.blocked_reason).classes('text-xs italic text-grey-5 truncate max-w-[10rem]')
        with ui.card().classes('grow min-w-[18rem] gap-1'):
            ui.label(f'Wartet auf Review ({len(review)})').classes('text-sm font-bold text-warning')
            if not review:
                ui.label('Review-Spalte leer').classes('text-xs text-grey-5')
            for t in review:
                with ui.row().classes('w-full items-center gap-2 no-wrap'):
                    avatar(store.member(t.assignee_id), '20px')
                    ui.label(t.title).classes('text-sm truncate')
                    ui.space()
                    ui.label(f'{t.estimate_h:g} h').classes('text-xs text-grey-6')
        incs = store.open_incidents()
        q = store.quality_stats()
        with ui.card().classes('grow min-w-[18rem] gap-1'):
            ui.label('Betrieb & Qualität').classes('text-sm font-bold')
            for i in incs:
                with ui.row().classes('w-full items-center gap-2 no-wrap'):
                    ui.icon('report', size='16px').classes('text-negative')
                    ui.label(f'{i.title} ({i.severity.upper()})').classes('text-sm truncate')
            if not incs:
                ui.label('keine offenen Incidents').classes('text-xs text-grey-5')
            ui.label(f'{q["open"]} offene Bugs · {q["critical_open"]} kritisch/hoch · '
                     f'{q["escaped"]} in Prod') \
                .classes('text-xs ' + ('text-negative' if q['critical_open'] else 'text-grey-6'))


@ui.refreshable
def lead_panel() -> None:
    today = date.today().isoformat()
    su_blockers = [s for s in store.standups if s.date == today and s.blocker.strip()]
    risks = sorted((r for r in store.p_risks() if r.status not in ('geschlossen',)),
                   key=lambda r: -r.score)[:3]
    actions = [a for a in store.p_action_items() if not a.done]
    next_rel = next((r for r in sorted(store.p_releases(), key=lambda r: r.date)
                     if r.status != 'live'), None)

    with ui.row().classes('w-full gap-3 items-start no-wrap flex-wrap'):
        with ui.card().classes('grow min-w-[16rem] gap-1'):
            ui.label(f'Standup-Blocker heute ({len(su_blockers)})').classes('text-sm font-bold text-negative')
            if not su_blockers:
                ui.label('keine gemeldet').classes('text-xs text-grey-5')
            for s in su_blockers:
                m = store.member(s.member_id)
                with ui.row().classes('w-full items-center gap-2 no-wrap'):
                    avatar(m, '18px')
                    ui.label(s.blocker).classes('text-xs truncate')
        with ui.card().classes('grow min-w-[16rem] gap-1'):
            ui.label('Top-Risiken').classes('text-sm font-bold')
            if not risks:
                ui.label('keine offenen Risiken').classes('text-xs text-grey-5')
            for r in risks:
                col = '#a63a3a' if r.score >= 6 else '#cf8a2e' if r.score >= 3 else '#3d7a5d'
                with ui.row().classes('w-full items-center gap-2 no-wrap'):
                    ui.label(str(r.score)).style(
                        f'width:20px;height:20px;border-radius:5px;color:#fff;font-size:11px;font-weight:700;'
                        f'display:flex;align-items:center;justify-content:center;background:{col}')
                    ui.label(r.title).classes('text-xs truncate')
        with ui.card().classes('grow min-w-[16rem] gap-1'):
            ui.label(f'Offene Action-Items ({len(actions)})').classes('text-sm font-bold')
            for a in actions[:3]:
                with ui.row().classes('w-full items-center gap-2 no-wrap'):
                    ui.icon('task_alt', size='14px').classes('text-grey-5')
                    ui.label(a.text).classes('text-xs truncate')
            ms = [m for m in store.p_milestones() if m.status == 'offen' and m.due]
            for m in ms[:3]:
                d = (date.fromisoformat(m.due) - date.today()).days
                with ui.row().classes('w-full items-center gap-2 no-wrap'):
                    ui.icon('outlined_flag', size='14px') \
                        .classes('text-negative' if d < 0 else 'text-grey-5')
                    ui.label(f'{m.title} · {"überfällig" if d < 0 else f"in {d} T"}').classes('text-xs truncate')
            if next_rel:
                ui.separator()
                ui.label(f'Nächster Release: {next_rel.version} ({next_rel.date})').classes('text-xs text-grey-7')


@ui.refreshable
def gh_panel() -> None:
    with ui.card().classes('w-full gap-2'):
        with ui.row().classes('w-full items-center gap-2'):
            ui.label('GitHub – offene Pull Requests').classes('text-sm font-bold')
            repo_in = ui.input(value=_gh['repo']).props('dense outlined').classes('w-56')
            repo_in.on('keydown.enter',
                       lambda: (_gh.update(repo=repo_in.value.strip()), asyncio.create_task(_load_gh())))
            ui.button(icon='refresh', on_click=lambda: asyncio.create_task(_load_gh())).props('flat dense')
            if _gh['loading']:
                ui.spinner()
        snap = _gh['snap']
        if snap is None:
            ui.label('Noch nicht geladen – Repo eingeben und Enter druecken.').classes('text-xs text-grey-5')
            return
        if snap.error:
            ui.label(f'Fehler: {snap.error}').classes('text-negative text-sm')
            if not os.getenv('GITHUB_TOKEN'):
                ui.label('Tipp: GITHUB_TOKEN setzen fuer hoeheres Rate-Limit / private Repos.') \
                    .classes('text-xs text-grey-6')
            return
        conflicts = [p for p in snap.pulls if p.has_conflict]
        ready = [p for p in snap.pulls if p.ready_to_merge]
        with ui.row().classes('w-full gap-3 flex-wrap'):
            stat_tile(len(snap.pulls), 'offene PRs')
            stat_tile(len(conflicts), 'Merge-Konflikte', 'text-negative' if conflicts else 'text-grey-5')
            stat_tile(len(ready), 'merge-bereit', 'text-positive' if ready else 'text-grey-5')
        for p in snap.pulls:
            color = ('border-negative' if p.has_conflict else
                     'border-positive' if p.ready_to_merge else 'border-grey-4')
            with ui.row().classes(f'w-full items-center gap-2 no-wrap border-l-4 {color} pl-2 py-1'):
                ui.link(f'#{p.number} {p.title}', p.url, new_tab=True).classes('text-sm truncate grow')
                if p.is_draft:
                    ui.badge('Entwurf').props('color=grey-6')
                if p.has_conflict:
                    ui.icon('merge_type', size='18px').classes('text-negative').tooltip('Merge-Konflikt')
                ci = {'success': ('done', 'text-positive'), 'failure': ('error', 'text-negative'),
                      'pending': ('hourglass_empty', 'text-warning')}.get(p.ci_state)
                if ci:
                    ui.icon(ci[0], size='16px').classes(ci[1])
                ui.label(f'{p.author} · {human_age(p.created_at)}').classes('text-xs text-grey-6')
        if snap.rate:
            ui.label(f'{snap.repo} · Stand {snap.fetched_at:%H:%M} · API {snap.rate.remaining}/{snap.rate.limit}') \
                .classes('text-xs text-grey-5')


def page() -> None:
    if _gh['snap'] is None and not _gh['loading']:
        _gh['repo'] = _configured_repo()
    with frame('/'):
        with ui.row().classes('w-full items-center'):
            ui.label('Leitstand').classes('kontor-title text-xl')
            ui.label(f'· {store.project.name}' if store.project else '').classes('text-grey-6')
            if store.project:
                lbl, col = RAG.get(store.project.rag, ('?', '#888'))
                ui.badge(lbl).style(f'background:{col}').tooltip('Projekt-Ampel (Statusbericht)')
            ui.space()
            ui.label(f'Moin! {date.today():%d.%m.%Y}').classes('text-sm text-grey-6')
        sprint_panel()
        focus_panel()
        lead_panel()
        gh_panel()
        if _gh['snap'] is None and not _gh['loading']:
            asyncio.create_task(_load_gh())
