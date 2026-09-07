"""Besprechungen – Agenda, Notizen, Beschlüsse & Aufgaben (Steering, Reviews, …)."""
from __future__ import annotations

from nicegui import ui

from components import avatar, frame, stat_tile
from store import MEETING_KINDS, Meeting, store, today_iso

KIND_COLOR = {'steering': 'primary', 'planung': 'secondary', 'review': 'positive',
              'sync': 'grey-6', 'workshop': 'warning', 'sonstiges': 'grey-5'}


def _form(existing=None) -> None:
    is_new = existing is None
    members = {m.id: m.name for m in store.active_members}
    with ui.dialog() as d, ui.card().classes('w-[36rem] gap-2'):
        ui.label('Neue Besprechung' if is_new else 'Besprechung bearbeiten').classes('kontor-title text-lg')
        with ui.row().classes('w-full gap-2'):
            title = ui.input('Titel', value='' if is_new else existing.title) \
                .props('outlined dense').classes('grow')
            kind = ui.select(MEETING_KINDS, label='Art', value='sync' if is_new else existing.kind) \
                .props('outlined dense').classes('w-40')
            dt = ui.input('Datum', value=today_iso() if is_new else existing.date) \
                .props('outlined dense type=date').classes('w-40')
        attend = ui.select(members, label='Teilnehmende', multiple=True,
                           value=[] if is_new else list(existing.attendees)) \
            .props('outlined dense use-chips').classes('w-full')
        agenda = ui.textarea('Agenda', value='' if is_new else existing.agenda) \
            .props('outlined dense autogrow').classes('w-full')
        notes = ui.textarea('Notizen', value='' if is_new else existing.notes) \
            .props('outlined dense autogrow').classes('w-full')
        decisions = ui.textarea('Beschlüsse', value='' if is_new else existing.decisions) \
            .props('outlined dense autogrow').classes('w-full')
        actions = ui.textarea('Aufgaben (wer / was / bis)', value='' if is_new else existing.actions) \
            .props('outlined dense autogrow').classes('w-full')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), kind=kind.value, date=dt.value,
                        attendees=list(attend.value or []), agenda=agenda.value or '',
                        notes=notes.value or '', decisions=decisions.value or '', actions=actions.value or '')
            if is_new:
                store.add('meetings', Meeting, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('meetings', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    ms = store.p_meetings()
    with ui.row().classes('w-full items-center'):
        ui.label('Besprechungen').classes('kontor-title text-lg')
        ui.space()
        ui.button('Neue Besprechung', icon='add', on_click=_form).props('no-caps')

    open_actions = [m for m in ms if m.actions.strip()]
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(ms), 'protokolliert')
        stat_tile(len([m for m in ms if m.date >= today_iso()]), 'anstehend', 'text-primary')
        stat_tile(len(open_actions), 'mit offenen Aufgaben', 'text-warning' if open_actions else 'text-grey-5')

    for m in ms:
        with ui.expansion().classes('w-full q-card') as exp:
            with exp.add_slot('header'):
                with ui.row().classes('w-full items-center gap-2 no-wrap'):
                    ui.label(m.date).classes('text-xs text-grey-5 w-24')
                    ui.badge(MEETING_KINDS[m.kind]).props(f'color={KIND_COLOR[m.kind]}')
                    ui.label(m.title).classes('text-sm font-medium grow truncate')
                    for mid in m.attendees[:5]:
                        avatar(store.member(mid), '18px')
            with ui.column().classes('gap-1 p-2'):
                for lbl, val in (('Agenda', m.agenda), ('Notizen', m.notes),
                                 ('Beschlüsse', m.decisions), ('Aufgaben', m.actions)):
                    if val:
                        ui.label(lbl).classes('text-xs font-bold text-grey-6')
                        ui.label(val).classes('text-sm mb-1 whitespace-pre-line')
                ui.button('Bearbeiten', icon='edit', on_click=lambda m=m: _form(m)) \
                    .props('flat dense size=sm no-caps')


def page() -> None:
    with frame('/meetings'):
        ui.label('Besprechungen').classes('kontor-title text-xl')
        content()
