"""Wetterlage – Team-Stimmung pro Sprint als Wetter (1 Sturm .. 5 Sonnenschein)."""
from __future__ import annotations

from nicegui import ui

from components import avatar, frame, resolve_sprint, stat_tile
from store import WEATHER, store

_sel = {'sprint': None}


@ui.refreshable
def content() -> None:
    if not store.p_sprints():
        ui.label('Kein Sprint vorhanden.').classes('text-grey-6')
        return
    sp = resolve_sprint(_sel['sprint'])
    with ui.row().classes('w-full items-center gap-2'):
        ui.select({s.id: s.name for s in store.p_sprints()}, value=sp.id,
                  on_change=lambda e: (_sel.update(sprint=e.value), content.refresh())) \
            .props('outlined dense').classes('w-64')

    moods = {m.member_id: m for m in store.moods if m.sprint_id == sp.id}
    scores = [m.score for m in moods.values()]
    avg = round(sum(scores) / len(scores), 1) if scores else None

    with ui.row().classes('w-full gap-3 flex-wrap items-stretch'):
        if avg:
            icon, lbl, col = WEATHER[max(1, min(5, round(avg)))]
            with ui.card().classes('items-center p-4 grow min-w-40'):
                ui.icon(icon, size='48px').style(f'color:{col}')
                ui.label(lbl).classes('kontor-title text-lg')
                ui.label(f'Ø {avg} · {len(scores)}/{len(store.active_members)} abgegeben') \
                    .classes('text-xs text-grey-6')
        stat_tile(len([s for s in scores if s <= 2]), 'in Sturm/Regen',
                  'text-negative' if any(s <= 2 for s in scores) else 'text-grey-5')
        stat_tile(len([s for s in scores if s >= 4]), 'bei Sonnenschein', 'text-positive')

    with ui.card().classes('w-full gap-2'):
        ui.label('Stimmung erfassen').classes('kontor-title text-sm')
        for m in store.active_members:
            cur = moods.get(m.id)
            with ui.row().classes('w-full items-center gap-3 no-wrap border-t border-grey-2 py-1'):
                avatar(m, '26px')
                ui.label(m.name).classes('text-sm w-36 truncate')
                with ui.row().classes('gap-1'):
                    for score in (5, 4, 3, 2, 1):
                        icon, lbl, col = WEATHER[score]
                        active = cur and cur.score == score
                        ui.button(icon=icon, on_click=lambda mid=m.id, sc=score: (
                            store.set_mood(store.pid, sp.id, mid, sc,
                                           moods[mid].comment if mid in moods else ''),
                            content.refresh())) \
                            .props(f'flat dense {"unelevated" if active else ""}') \
                            .style(f'color:{col};' + (f'background:{col}22' if active else '')) \
                            .tooltip(lbl)
                note = ui.input(value=cur.comment if cur else '', placeholder='optional …') \
                    .props('outlined dense').classes('grow')
                note.on('blur', lambda mid=m.id, w=note: store.set_mood(
                    store.pid, sp.id, mid,
                    moods[mid].score if mid in moods else 3, w.value or ''))

    # -- Verlauf ueber die Sprints ------------------------------------
    hist = []
    for s in store.p_sprints():
        sc = [x.score for x in store.moods if x.sprint_id == s.id]
        if sc:
            hist.append((s.name, round(sum(sc) / len(sc), 1)))
    if len(hist) > 1:
        with ui.card().classes('w-full'):
            ui.label('Stimmungsverlauf').classes('kontor-title text-sm')
            ui.echart({
                'grid': {'left': 30, 'right': 15, 'top': 20, 'bottom': 25},
                'xAxis': {'type': 'category', 'data': [h[0] for h in hist]},
                'yAxis': {'type': 'value', 'min': 1, 'max': 5},
                'tooltip': {'trigger': 'axis'},
                'series': [{'type': 'line', 'data': [h[1] for h in hist], 'smooth': True,
                            'lineStyle': {'width': 3, 'color': '#1f4e5f'},
                            'areaStyle': {'opacity': 0.1, 'color': '#1f4e5f'}}],
            }).classes('w-full h-52')


def page() -> None:
    with frame('/wetter'):
        ui.label('Wetterlage – Team-Stimmung').classes('kontor-title text-xl')
        content()
