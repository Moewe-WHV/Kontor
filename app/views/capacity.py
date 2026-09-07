"""Kapazitaetsmeldungen: verfuegbare Stunden pro Person und Sprint."""
from __future__ import annotations

from nicegui import ui

from components import avatar, bar, frame, resolve_sprint, stat_tile
from store import store

_sel = {'sprint': None}


def _current():
    return resolve_sprint(_sel['sprint'])


@ui.refreshable
def content() -> None:
    if not store.p_sprints():
        ui.label('Erst einen Sprint anlegen (Sprint-Planung).').classes('text-grey-6')
        return
    sp = _current()
    with ui.row().classes('w-full items-center gap-2'):
        ui.select({s.id: s.name for s in store.p_sprints()}, value=sp.id,
                  on_change=lambda e: (_sel.update(sprint=e.value), content.refresh())) \
            .props('outlined dense').classes('w-64')
        ui.label(f'{len(sp.workdays())} Werktage · {sp.weeks:g} Personen-Wochen').classes('text-sm text-grey-6')

    committed = store.committed_hours(sp.id)
    total_cap = 0.0
    rows = []

    with ui.card().classes('w-full gap-1'):
        with ui.row().classes('w-full text-xs font-bold text-grey-7 px-1'):
            ui.label('Person').classes('w-48')
            ui.label('Richtwert').classes('w-24 text-right')
            ui.label('gemeldet (h)').classes('w-40')
            ui.label('Notiz').classes('grow')
        for m in store.active_members:
            cap = store.capacity_of(sp.id, m.id)
            richtwert = round(m.weekly_hours * sp.weeks, 1)
            value = cap.hours if cap else richtwert
            total_cap += value
            with ui.row().classes('w-full items-center gap-2 no-wrap border-t border-grey-2 py-1'):
                with ui.row().classes('w-48 items-center gap-2 no-wrap'):
                    avatar(m, '26px')
                    ui.label(m.name).classes('text-sm truncate')
                ui.label(f'{richtwert:g} h').classes('w-24 text-right text-xs text-grey-6')
                num = ui.number(value=value, min=0, step=1, format='%.1f') \
                    .props('outlined dense').classes('w-40')
                note = ui.input(value=cap.note if cap else '').props('outlined dense').classes('grow')

                def mk_save(mid, num=num, note=note):
                    return lambda: (store.set_capacity(sp.id, mid, float(num.value or 0), note.value or ''),
                                    ui.notify(f'{store.member(mid).name}: gespeichert', type='positive'),
                                    content.refresh())
                num.on('blur', mk_save(m.id))
                note.on('blur', mk_save(m.id))
            rows.append((m, value, richtwert))

    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(f'{total_cap:g} h', 'Team-Kapazitaet')
        stat_tile(f'{committed:g} h', 'Commitment', 'text-primary')
        free = total_cap - committed
        stat_tile(f'{free:g} h', 'frei' if free >= 0 else 'Ueberbuchung',
                  'text-positive' if free >= 0 else 'text-negative')
        stat_tile(f'{(committed / total_cap * 100) if total_cap else 0:.0f}%', 'geplante Auslastung')

    with ui.card().classes('w-full gap-2'):
        ui.label('Gemeldet vs. Richtwert').classes('text-sm font-bold')
        for m, value, richtwert in rows:
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.label(m.name).classes('text-xs w-40 truncate')
                with ui.column().classes('grow'):
                    bar(value, max(richtwert, value, 1), color='primary')


def page() -> None:
    with frame('/capacity'):
        ui.label('Kapazitaetsmeldung').classes('text-xl font-bold')
        ui.label('Jede Person meldet ihre real verfuegbaren Stunden fuer den Sprint '
                 '(Urlaub, Meetings, Support schon abgezogen). Feld verlassen speichert.') \
            .classes('text-xs text-grey-5')
        content()
