"""1:1-Gespräche – Notizen, Gesprächspunkte, Folgeaufgaben pro Crew-Mitglied."""
from __future__ import annotations

from datetime import date

from nicegui import ui

from components import avatar, frame
from store import OneOnOne, store

_sel = {'member': None}


def _form(member_id: str, existing=None) -> None:
    is_new = existing is None
    with ui.dialog() as d, ui.card().classes('w-[34rem] gap-2'):
        ui.label('Neues 1:1' if is_new else '1:1 bearbeiten').classes('kontor-title text-lg')
        dt = ui.input('Datum', value=date.today().isoformat() if is_new else existing.date) \
            .props('outlined dense type=date').classes('w-full')
        points = ui.textarea('Gesprächspunkte', value='' if is_new else existing.talking_points) \
            .props('outlined dense autogrow').classes('w-full')
        notes = ui.textarea('Notizen', value='' if is_new else existing.notes) \
            .props('outlined dense autogrow').classes('w-full')
        actions = ui.textarea('Vereinbarungen / To-dos', value='' if is_new else existing.actions) \
            .props('outlined dense autogrow').classes('w-full')
        nxt = ui.input('Nächster Termin', value='' if is_new else existing.next_date) \
            .props('outlined dense type=date').classes('w-full')

        def save() -> None:
            data = dict(date=dt.value, talking_points=points.value or '', notes=notes.value or '',
                        actions=actions.value or '', next_date=nxt.value or '')
            if is_new:
                store.add('one_on_ones', OneOnOne, member_id=member_id, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('one_on_ones', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    members = store.active_members
    if not members:
        ui.label('Erst Crew anlegen.').classes('text-grey-6')
        return
    mid = _sel['member'] or members[0].id
    with ui.row().classes('w-full items-center gap-2'):
        ui.select({m.id: m.name for m in members}, value=mid,
                  on_change=lambda e: (_sel.update(member=e.value), content.refresh())) \
            .props('outlined dense').classes('w-56')
        ui.space()
        ui.button('Neues 1:1', icon='add', on_click=lambda: _form(mid)).props('no-caps')

    talks = sorted((o for o in store.one_on_ones if o.member_id == mid),
                   key=lambda o: o.date, reverse=True)

    # offene To-dos ueber alle Gespraeche der Person
    upcoming = [o for o in store.one_on_ones if o.member_id == mid and o.next_date >= date.today().isoformat()]
    if upcoming:
        nxt = min(o.next_date for o in upcoming)
        ui.label(f'Nächster Termin: {nxt}').classes('text-sm text-primary')

    if not talks:
        ui.label('Noch keine Gespräche dokumentiert.').classes('text-sm text-grey-5')
    for o in talks:
        with ui.card().classes('w-full gap-1'):
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                avatar(store.member(mid), '22px')
                ui.label(o.date).classes('kontor-title text-sm grow')
                ui.button(icon='edit', on_click=lambda o=o: _form(mid, o)).props('flat dense size=sm')
            for lbl, val in (('Gesprächspunkte', o.talking_points), ('Notizen', o.notes),
                             ('Vereinbarungen', o.actions)):
                if val:
                    ui.label(lbl).classes('text-xs font-bold text-grey-6')
                    ui.label(val).classes('text-sm mb-1 whitespace-pre-line')
            if o.next_date:
                ui.label(f'nächster Termin: {o.next_date}').classes('text-xs text-grey-5')


def page() -> None:
    with frame('/one-on-ones'):
        ui.label('1:1-Gespräche').classes('kontor-title text-xl')
        content()
