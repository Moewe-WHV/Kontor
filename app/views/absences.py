"""Abwesenheiten (Urlaub, Krank, Fortbildung) – fliessen in die Kapazitaet ein."""
from __future__ import annotations

from datetime import date

from nicegui import ui

from components import avatar, frame, stat_tile
from store import ABSENCE_KINDS, Absence, store, today_iso

KIND_COLOR = {'urlaub': 'primary', 'krank': 'negative', 'fortbildung': 'secondary', 'sonstiges': 'grey-6'}


def _form(existing=None) -> None:
    is_new = existing is None
    with ui.dialog() as d, ui.card().classes('w-96 gap-2'):
        ui.label('Abwesenheit' if is_new else 'Bearbeiten').classes('text-lg font-bold')
        member = ui.select({m.id: m.name for m in store.active_members}, label='Person',
                           value=None if is_new else existing.member_id).props('outlined dense').classes('w-full')
        kind = ui.select(ABSENCE_KINDS, label='Art',
                         value='urlaub' if is_new else existing.kind).props('outlined dense').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            start = ui.input('Von', value=today_iso() if is_new else existing.start) \
                .props('outlined dense type=date').classes('grow')
            end = ui.input('Bis', value=today_iso() if is_new else existing.end) \
                .props('outlined dense type=date').classes('grow')
        note = ui.input('Notiz', value='' if is_new else existing.note).props('outlined dense').classes('w-full')

        def save() -> None:
            if not member.value:
                ui.notify('Person waehlen', type='warning')
                return
            data = dict(member_id=member.value, kind=kind.value, start=start.value,
                        end=end.value, note=note.value or '')
            if is_new:
                store.add('absences', Absence, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('absences', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    with ui.row().classes('w-full items-center'):
        ui.label('Abwesenheiten').classes('text-lg font-bold')
        ui.space()
        ui.button('Eintragen', icon='add', on_click=_form).props('no-caps')

    sp = store.active_sprint
    if sp:
        with ui.row().classes('w-full gap-3 flex-wrap'):
            off = sum(store.absence_hours(m, sp) for m in store.active_members)
            gross = sum(m.weekly_hours * sp.weeks for m in store.active_members)
            stat_tile(f'{gross:g} h', 'Brutto-Kapazitaet', hint=sp.name)
            stat_tile(f'{off:g} h', 'Abwesenheit im Sprint', 'text-warning' if off else 'text-grey-5')
            stat_tile(f'{gross - off:g} h', 'Netto verfuegbar', 'text-positive')

    today = date.today()
    upcoming = sorted((a for a in store.absences if date.fromisoformat(a.end) >= today),
                      key=lambda a: a.start)
    past = sorted((a for a in store.absences if date.fromisoformat(a.end) < today),
                  key=lambda a: a.start, reverse=True)

    for title, items in (('Aktuell & geplant', upcoming), ('Vergangen', past)):
        with ui.card().classes('w-full gap-1'):
            ui.label(title).classes('text-sm font-bold')
            if not items:
                ui.label('—').classes('text-xs text-grey-5')
            for a in items:
                m = store.member(a.member_id)
                with ui.row().classes('w-full items-center gap-2 no-wrap border-t border-grey-2 py-1'):
                    avatar(m, '24px')
                    ui.label(m.name if m else '—').classes('text-sm w-36 truncate')
                    ui.badge(ABSENCE_KINDS.get(a.kind, a.kind)).props(f'color={KIND_COLOR.get(a.kind, "grey")}')
                    ui.label(f'{a.start} → {a.end}').classes('text-xs text-grey-6')
                    ui.label(f'{len(a.workdays())} AT').classes('text-xs text-grey-5')
                    if a.note:
                        ui.label(a.note).classes('text-xs italic text-grey-5 truncate')
                    ui.space()
                    ui.button(icon='edit', on_click=lambda a=a: _form(a)).props('flat dense size=sm')


def page() -> None:
    with frame('/absences'):
        ui.label('Abwesenheitsplanung').classes('kontor-title text-xl')
        content()
