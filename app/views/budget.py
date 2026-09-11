"""Budget & Kosten – Plan vs. Ist vs. Prognose (auf Basis Tagessätze & Stunden)."""
from __future__ import annotations

from nicegui import ui

from components import bar, frame, stat_tile
from store import store


def _eur(x: float) -> str:
    return f'{x:,.0f} {store.setting("currency")}'.replace(',', '.')


@ui.refreshable
def content() -> None:
    p = store.project
    if not p:
        return
    c = store.project_cost(p.id)
    ui.label(f'Projekt: {p.name}').classes('kontor-title text-lg')

    with ui.card().classes('w-full gap-2'):
        with ui.row().classes('w-full items-center gap-2'):
            ui.label('Budget (EUR)').classes('text-sm')
            num = ui.number(value=p.budget_eur, min=0, step=1000, format='%.0f') \
                .props('outlined dense').classes('w-40')
            num.on('blur', lambda: (store.update(p, budget_eur=float(num.value or 0)), content.refresh()))
        if not any(m.day_rate for m in store.active_members):
            ui.label('Hinweis: keine Tagessätze in der Crew hinterlegt – Kosten = 0.') \
                .classes('text-xs text-warning')

    ext = store.vendor_cost_yearly(p.id)
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(_eur(c['budget']), 'Budget')
        stat_tile(_eur(c['planned']), 'geplant (Personalkosten)')
        stat_tile(_eur(c['actual']), 'Ist (gebuchte Stunden)', 'text-primary')
        if ext:
            stat_tile(_eur(ext), 'externe Kosten / Jahr', hint='aus Lieferanten')
        over = c['eac'] > c['budget'] and c['budget'] > 0
        stat_tile(_eur(c['eac']), 'Prognose (EAC)',
                  'text-negative' if over else 'text-positive',
                  'über Budget' if over else 'im Rahmen')

    with ui.card().classes('w-full gap-2'):
        ui.label('Verbrauch').classes('kontor-title text-sm')
        budget = c['budget'] or max(c['eac'], 1)
        bar(c['actual'], budget, label='Ist vs. Budget')
        bar(c['eac'], budget, color='secondary', label='Prognose (Ist + Restaufwand) vs. Budget')
        if c['budget']:
            left = c['budget'] - c['eac']
            ui.label(('Voraussichtlicher Puffer: ' if left >= 0 else 'Voraussichtliche Überschreitung: ')
                     + _eur(abs(left))).classes('text-sm ' + ('text-positive' if left >= 0 else 'text-negative'))

    # Kosten je Person
    with ui.card().classes('w-full gap-1'):
        ui.label('Ist-Kosten je Person (dieses Projekt)').classes('kontor-title text-sm')
        task_ids = {t.id for t in store.p_tasks(p.id)}
        per: dict[str, float] = {}
        hrs: dict[str, float] = {}
        for w in store.worklogs:
            if w.task_id in task_ids:
                per[w.member_id] = per.get(w.member_id, 0) + w.hours * store._rate_per_hour(w.member_id)
                hrs[w.member_id] = hrs.get(w.member_id, 0) + w.hours
        if not per:
            ui.label('Noch keine gebuchten Stunden.').classes('text-xs text-grey-5')
        for mid, cost in sorted(per.items(), key=lambda kv: -kv[1]):
            m = store.member(mid)
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.label(m.name if m else '—').classes('text-sm w-40 truncate')
                ui.label(f'{hrs[mid]:g} h').classes('text-xs text-grey-6 w-16 text-right')
                ui.label(_eur(cost)).classes('text-sm w-24 text-right')

    # Kosten je Epic
    epics = store.p_epics(p.id)
    if epics:
        with ui.card().classes('w-full gap-1'):
            ui.label('Ist-Kosten je Epic').classes('kontor-title text-sm')
            for e in epics:
                etasks = [t for t in store.p_tasks(p.id) if t.epic_id == e.id]
                eids = {t.id for t in etasks}
                cost = sum(w.hours * store._rate_per_hour(w.member_id)
                           for w in store.worklogs if w.task_id in eids)
                plan = sum(t.estimate_h * store._rate_per_hour(t.assignee_id) for t in etasks)
                with ui.row().classes('w-full items-center gap-2 no-wrap'):
                    ui.label(e.title).classes('text-sm w-48 truncate')
                    with ui.column().classes('grow'):
                        bar(cost, plan or cost or 1, color='primary')
                    ui.label(f'{_eur(cost)} / {_eur(plan)}').classes('text-xs text-grey-6 w-40 text-right')


def page() -> None:
    with frame('/budget'):
        ui.label('Budget & Kosten').classes('kontor-title text-xl')
        content()
