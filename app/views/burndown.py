"""Burndown-Chart + Sprint-Fortschritt (ECharts)."""
from __future__ import annotations

from nicegui import ui

from components import chart_opts, frame, resolve_sprint, stat_tile
from store import store

_sel = {'sprint': None}


def _current():
    return resolve_sprint(_sel['sprint'])


def _burndown_option(sp) -> dict:
    bd = store.burndown(sp)
    return {
        'tooltip': {'trigger': 'axis'},
        'legend': {'data': ['Ideal', 'Rest-Aufwand', 'Ist-Aufwand kumuliert']},
        'grid': {'left': 45, 'right': 20, 'top': 40, 'bottom': 30},
        'xAxis': {'type': 'category', 'data': bd['days'], 'boundaryGap': False},
        'yAxis': {'type': 'value', 'name': 'h'},
        'series': [
            {'name': 'Ideal', 'type': 'line', 'data': bd['ideal'],
             'lineStyle': {'type': 'dashed', 'color': '#94a3b8'}, 'itemStyle': {'color': '#94a3b8'},
             'symbol': 'none'},
            {'name': 'Rest-Aufwand', 'type': 'line', 'data': bd['remaining'],
             'smooth': True, 'lineStyle': {'width': 3, 'color': '#6366f1'},
             'itemStyle': {'color': '#6366f1'}, 'areaStyle': {'opacity': 0.08, 'color': '#6366f1'}},
            {'name': 'Ist-Aufwand kumuliert', 'type': 'line', 'data': bd['logged'],
             'lineStyle': {'color': '#10b981'}, 'itemStyle': {'color': '#10b981'}, 'symbol': 'none'},
        ],
    }


def _capacity_option(sp) -> dict:
    names, load, cap = [], [], []
    for m in store.active_members:
        c = store.capacity_of(sp.id, m.id)
        names.append(m.name.split()[0])
        load.append(round(store.member_load(sp.id, m.id), 1))
        cap.append(round(c.hours if c else m.weekly_hours * sp.weeks, 1))
    return {
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'legend': {'data': ['geplante Last', 'Kapazität']},
        'grid': {'left': 45, 'right': 20, 'top': 40, 'bottom': 30},
        'xAxis': {'type': 'category', 'data': names},
        'yAxis': {'type': 'value', 'name': 'h'},
        'series': [
            {'name': 'geplante Last', 'type': 'bar', 'data': load, 'itemStyle': {'color': '#6366f1'}},
            {'name': 'Kapazität', 'type': 'bar', 'data': cap, 'itemStyle': {'color': '#cbd5e1'}},
        ],
    }


@ui.refreshable
def content() -> None:
    if not store.p_sprints():
        ui.label('Kein Sprint vorhanden.').classes('text-grey-6')
        return
    sp = _current()
    with ui.row().classes('w-full items-center gap-2'):
        ui.select({s.id: s.name for s in store.p_sprints()}, value=sp.id,
                  on_change=lambda e: (_sel.update(sprint=e.value), content.refresh())) \
            .props('outlined dense').classes('w-64')
        ui.button(icon='refresh', on_click=content.refresh).props('flat dense')

    committed = store.committed_hours(sp.id)
    done = store.done_hours(sp.id)
    logged = store.logged_hours(sp.id)
    cap = store.capacity_hours(sp)
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(f'{committed:g} h', 'Commitment')
        stat_tile(f'{done:g} h', 'erledigt', 'text-positive', f'{(done / committed * 100) if committed else 0:.0f}%')
        stat_tile(f'{committed - done:g} h', 'Rest-Scope', 'text-primary')
        stat_tile(f'{logged:g} h', 'Ist-Aufwand')
        dl = sp.days_left
        stat_tile('—' if dl is None else dl, 'Tage übrig',
                  'text-negative' if (dl is not None and dl < 0) else 'text-primary')

    if not store.burndown(sp)['days']:
        ui.label('Sprint hat kein gueltiges Start/Ende – bitte in der Sprint-Planung setzen.') \
            .classes('text-warning')
        return

    with ui.card().classes('w-full'):
        ui.label(f'Burndown · {sp.name}').classes('text-sm font-bold')
        ui.echart(chart_opts(_burndown_option(sp))).classes('w-full h-72')

    with ui.card().classes('w-full'):
        ui.label('Kapazitaet vs. geplante Last je Person').classes('text-sm font-bold')
        ui.echart(chart_opts(_capacity_option(sp))).classes('w-full h-64')


def page() -> None:
    with frame('/burndown'):
        ui.label('Burndown & Fortschritt').classes('text-xl font-bold')
        content()
