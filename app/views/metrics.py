"""Team-Metriken: Velocity, Forecast, Lead-/Cycle-Time, Durchsatz."""
from __future__ import annotations

from statistics import mean, median

from nicegui import ui

from components import frame, stat_tile
from store import store


def _velocity_option() -> dict:
    hist = store.velocity_history()
    names = [s.name.split(' – ')[0].replace('Sprint ', 'S') for s, _, _ in hist]
    committed = [round(c, 1) for _, c, _ in hist]
    done = [round(d, 1) for _, _, d in hist]
    return {
        'tooltip': {'trigger': 'axis'},
        'legend': {'data': ['Commitment', 'erledigt']},
        'grid': {'left': 45, 'right': 15, 'top': 35, 'bottom': 25},
        'xAxis': {'type': 'category', 'data': names},
        'yAxis': {'type': 'value', 'name': 'h'},
        'series': [
            {'name': 'Commitment', 'type': 'bar', 'data': committed, 'itemStyle': {'color': '#cdd8d3'}},
            {'name': 'erledigt', 'type': 'bar', 'data': done, 'itemStyle': {'color': '#1f4e5f'}},
        ],
    }


def _throughput_option() -> dict:
    tp = store.throughput_by_week()
    return {
        'tooltip': {'trigger': 'axis'},
        'grid': {'left': 35, 'right': 15, 'top': 20, 'bottom': 25},
        'xAxis': {'type': 'category', 'data': list(tp)},
        'yAxis': {'type': 'value', 'name': 'Tasks'},
        'series': [{'type': 'bar', 'data': list(tp.values()), 'itemStyle': {'color': '#3d7a5d'}}],
    }


def _hist_option(values: list[int], color: str) -> dict:
    values = [v for v in values if v >= 0]
    if not values:
        return {}
    hi = max(values)
    buckets = [0] * (hi + 1)
    for v in values:
        buckets[v] += 1
    return {
        'tooltip': {'trigger': 'axis'},
        'grid': {'left': 35, 'right': 15, 'top': 20, 'bottom': 25},
        'xAxis': {'type': 'category', 'data': [str(i) for i in range(hi + 1)], 'name': 'Tage'},
        'yAxis': {'type': 'value', 'name': 'Tasks'},
        'series': [{'type': 'bar', 'data': buckets, 'itemStyle': {'color': color}}],
    }


@ui.refreshable
def content() -> None:
    lead = store.lead_times()
    cycle = store.cycle_times()
    backlog_h, vel, needed = store.forecast_sprints()

    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(f'{vel:g} h', 'Ø Velocity', hint='letzte 3 Sprints')
        stat_tile(f'{median(cycle):g} d' if cycle else '–', 'Median Cycle-Time', hint='In Arbeit → Fertig')
        stat_tile(f'{median(lead):g} d' if lead else '–', 'Median Lead-Time', hint='Erstellt → Fertig')
        stat_tile(f'{needed:g}', 'Sprints fuer Backlog',
                  hint=f'{backlog_h:g} h offen / {vel:g} h')

    sp = store.active_sprint
    if sp and vel:
        committed = store.committed_hours(sp.id)
        with ui.card().classes('w-full'):
            over = committed > vel * 1.15
            ui.label(
                f'Aktueller Sprint: {committed:g} h committed vs. {vel:g} h Ø Velocity — '
                + ('⚠ ambitioniert, ggf. Scope pruefen' if over else '✓ im historischen Rahmen')
            ).classes('text-sm ' + ('text-warning' if over else 'text-positive'))

    with ui.card().classes('w-full'):
        ui.label('Velocity – Commitment vs. tatsaechlich erledigt').classes('text-sm font-bold')
        ui.echart(_velocity_option()).classes('w-full h-64')

    with ui.row().classes('w-full gap-3 no-wrap flex-wrap'):
        with ui.card().classes('grow min-w-[20rem]'):
            ui.label('Cycle-Time-Verteilung').classes('text-sm font-bold')
            if cycle:
                ui.echart(_hist_option(cycle, '#1f4e5f')).classes('w-full h-56')
                ui.label(f'Ø {mean(cycle):.1f} d · Median {median(cycle):g} d · max {max(cycle)} d') \
                    .classes('text-xs text-grey-6')
            else:
                ui.label('noch keine abgeschlossenen Tasks mit Startzeitpunkt').classes('text-xs text-grey-5')
        with ui.card().classes('grow min-w-[20rem]'):
            ui.label('Lead-Time-Verteilung').classes('text-sm font-bold')
            if lead:
                ui.echart(_hist_option(lead, '#5b8ca3')).classes('w-full h-56')
                ui.label(f'Ø {mean(lead):.1f} d · Median {median(lead):g} d · max {max(lead)} d') \
                    .classes('text-xs text-grey-6')
            else:
                ui.label('noch keine Daten').classes('text-xs text-grey-5')

    with ui.card().classes('w-full'):
        ui.label('Durchsatz – erledigte Tasks pro Woche').classes('text-sm font-bold')
        ui.echart(_throughput_option()).classes('w-full h-52')


def page() -> None:
    with frame('/metrics'):
        ui.label('Team-Metriken').classes('kontor-title text-xl')
        content()
