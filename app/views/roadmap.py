"""Roadmap – Epics & Meilensteine auf einer Zeitachse (Gantt)."""
from __future__ import annotations

from datetime import date, timedelta

from nicegui import ui

from components import frame, stat_tile
from store import EPIC_STATUS, Epic, store

_sel = {'epic': None}


def _epic_form(existing=None) -> None:
    is_new = existing is None
    palette = ['#1f4e5f', '#5b8ca3', '#3d7a5d', '#b5533a', '#cf8a2e', '#7a5c99']
    with ui.dialog() as d, ui.card().classes('w-[30rem] gap-2'):
        ui.label('Neues Epic' if is_new else 'Epic bearbeiten').classes('kontor-title text-lg')
        title = ui.input('Titel', value='' if is_new else existing.title).props('outlined dense').classes('w-full')
        desc = ui.textarea('Beschreibung', value='' if is_new else existing.description) \
            .props('outlined dense autogrow').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            start = ui.input('Von', value=date.today().isoformat() if is_new else existing.start) \
                .props('outlined dense type=date').classes('grow')
            end = ui.input('Bis', value=(date.today() + timedelta(days=28)).isoformat() if is_new else existing.end) \
                .props('outlined dense type=date').classes('grow')
        with ui.row().classes('w-full gap-2'):
            status = ui.select(EPIC_STATUS, label='Status',
                               value='geplant' if is_new else existing.status).props('outlined dense').classes('grow')
            color = ui.select(palette, label='Farbe',
                              value=palette[len(store.p_epics()) % len(palette)] if is_new else existing.color) \
                .props('outlined dense').classes('grow')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), description=desc.value or '',
                        start=start.value, end=end.value, status=status.value, color=color.value)
            if is_new:
                store.add('epics', Epic, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('epics', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    epics = store.p_epics()
    milestones = [m for m in store.p_milestones() if m.due]
    with ui.row().classes('w-full items-center'):
        ui.label('Roadmap').classes('kontor-title text-lg')
        ui.space()
        ui.button('Neues Epic', icon='add', on_click=_epic_form).props('no-caps')

    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(epics), 'Epics')
        stat_tile(len([e for e in epics if e.status == 'aktiv']), 'aktiv', 'text-positive')
        stat_tile(len(milestones), 'Meilensteine')

    dates = [date.fromisoformat(x) for e in epics for x in (e.start, e.end) if x]
    dates += [date.fromisoformat(m.due) for m in milestones]
    if not dates:
        ui.label('Noch keine Epics mit Zeitraum.').classes('text-sm text-grey-5')
        return
    lo = min(dates + [date.today()]) - timedelta(days=3)
    hi = max(dates + [date.today()]) + timedelta(days=3)
    span = max((hi - lo).days, 1)

    def pct(d: date) -> float:
        return (d - lo).days / span * 100

    # Monatsraster
    with ui.card().classes('w-full overflow-x-auto'):
        with ui.column().classes('min-w-[48rem] w-full gap-1'):
            # Kopfzeile Monate
            months, cur = [], date(lo.year, lo.month, 1)
            while cur <= hi:
                nxt = date(cur.year + (cur.month // 12), (cur.month % 12) + 1, 1)
                months.append((cur, max(cur, lo), min(nxt, hi)))
                cur = nxt
            with ui.row().classes('w-full relative h-5').style('border-bottom:1px solid #dbe2de'):
                for m0, a, b in months:
                    ui.label(m0.strftime('%b %y')).classes('absolute text-[10px] text-grey-6') \
                        .style(f'left:{pct(a):.2f}%')
            # heute-Linie
            with ui.element('div').classes('w-full relative').style('height:0'):
                ui.element('div').style(
                    f'position:absolute;left:{pct(date.today()):.2f}%;top:0;bottom:0;width:2px;'
                    f'background:#a63a3a;opacity:.5;z-index:5')

            for e in epics:
                if not e.start or not e.end:
                    continue
                s, en = date.fromisoformat(e.start), date.fromisoformat(e.end)
                tasks = [t for t in store.p_tasks() if t.epic_id == e.id]
                done = len([t for t in tasks if t.status == 'done'])
                frac = (done / len(tasks)) if tasks else 0.0
                with ui.row().classes('w-full items-center gap-2 no-wrap py-1'):
                    ui.label(e.title).classes('text-xs w-40 truncate shrink-0') \
                        .tooltip(f'{e.start} → {e.end} · {EPIC_STATUS[e.status]}')
                    with ui.element('div').classes('relative grow h-5'):
                        bar = ui.element('div').style(
                            f'position:absolute;left:{pct(s):.2f}%;width:{max(pct(en) - pct(s), 1):.2f}%;'
                            f'top:2px;height:16px;border-radius:4px;background:{e.color}33;'
                            f'border:1px solid {e.color};overflow:hidden')
                        with bar:
                            ui.element('div').style(
                                f'height:100%;width:{frac * 100:.0f}%;background:{e.color}')
                    ui.label(f'{done}/{len(tasks)}' if tasks else '–') \
                        .classes('text-[10px] text-grey-6 w-10 shrink-0')
                    ui.button(icon='edit', on_click=lambda e=e: _epic_form(e)) \
                        .props('flat dense size=sm').classes('shrink-0')

            # Meilensteine als Rauten
            if milestones:
                with ui.row().classes('w-full items-center gap-2 no-wrap py-1'):
                    ui.label('Meilensteine').classes('text-xs w-40 shrink-0 text-grey-6')
                    with ui.element('div').classes('relative grow h-5'):
                        for ms in milestones:
                            col = {'offen': '#1f4e5f', 'erreicht': '#3d7a5d', 'verpasst': '#a63a3a'}[ms.status]
                            ui.label('◆').style(
                                f'position:absolute;left:{pct(date.fromisoformat(ms.due)):.2f}%;'
                                f'transform:translateX(-50%);color:{col};font-size:14px').tooltip(
                                f'{ms.title} · {ms.due}')

    # Epic-Detail: unzugeordnete Tasks
    loose = [t for t in store.p_tasks() if not t.epic_id and t.status != 'done']
    if loose:
        ui.label(f'{len(loose)} offene Tasks ohne Epic-Zuordnung').classes('text-xs text-grey-5')


def page() -> None:
    with frame('/roadmap'):
        ui.label('Roadmap').classes('kontor-title text-xl')
        content()
