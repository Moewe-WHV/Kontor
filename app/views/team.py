"""Team-Verwaltung + Datenpflege."""
from __future__ import annotations

from nicegui import ui

from components import avatar, frame, viewer_is_leader
from store import DATA_FILE, store

_PALETTE = ['#1f4e5f', '#5b8ca3', '#3d7a5d', '#b5533a', '#cf8a2e', '#7a5c99', '#a63a3a', '#2f6f6f']


def _member_form(existing=None) -> None:
    is_new = existing is None
    can_edit_role = not store.project or store.project.mode == 'solo' or viewer_is_leader(store.pid)
    with ui.dialog() as d, ui.card().classes('w-96 gap-2'):
        ui.label('Neues Teammitglied' if is_new else 'Bearbeiten').classes('text-lg font-bold')
        name = ui.input('Name', value='' if is_new else existing.name).props('outlined dense').classes('w-full')
        role = ui.input('Rolle', value='' if is_new else existing.role).props('outlined dense').classes('w-full')
        role.set_enabled(can_edit_role)
        if not can_edit_role:
            ui.label('Nur die Teamleitung dieses Projekts kann die Rolle ändern.') \
                .classes('text-xs text-grey-5')
        with ui.row().classes('w-full gap-2'):
            hours = ui.number('Wochenstunden',
                              value=store.setting('default_weekly_hours') if is_new else existing.weekly_hours,
                              min=0, step=1, format='%.1f').props('outlined dense').classes('grow')
            rate = ui.number('Tagessatz (EUR)', value=0 if is_new else existing.day_rate,
                             min=0, step=10, format='%.0f').props('outlined dense').classes('grow')
        color = ui.select(_PALETTE, label='Farbe',
                          value=_PALETTE[len(store.members) % len(_PALETTE)] if is_new else existing.color) \
            .props('outlined dense').classes('w-full')
        active = ui.checkbox('aktiv', value=True if is_new else existing.active)

        def save() -> None:
            if not name.value.strip():
                ui.notify('Name fehlt', type='warning')
                return
            if is_new:
                store.add_member(name=name.value.strip(), role=role.value or '',
                                 weekly_hours=float(hours.value or 0), day_rate=float(rate.value or 0),
                                 color=color.value, active=active.value)
            else:
                existing.name = name.value.strip()
                existing.role = role.value or ''
                existing.weekly_hours = float(hours.value or 0)
                existing.day_rate = float(rate.value or 0)
                existing.color = color.value
                existing.active = active.value
                store.save()
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-end'):
            ui.button('Abbrechen', on_click=d.close).props('flat')
            ui.button('Speichern', on_click=save)
    d.open()


def _set_leader(mid: str) -> None:
    store.update(store.project, leader_member_id=mid or '')
    ui.notify('Teamleitung aktualisiert', type='positive')
    content.refresh()


def _leader_section() -> None:
    p = store.project
    if not p or p.mode != 'team':
        return
    can_edit = viewer_is_leader(p.id)
    with ui.card().classes('w-full gap-2'):
        ui.label('Teamleitung').classes('text-sm font-bold')
        ui.label('Legt fest, wer Rollen ändern und Führungsbereiche '
                 '(Budget, Stakeholder, RACI, Lieferanten, Änderungen, 1:1s, Flotte, Steckbrief) '
                 'sehen darf. Solange niemand festgelegt ist, sieht jeder alles.') \
            .classes('text-xs text-grey-6')
        options = {'': '– niemand festgelegt –', **{m.id: m.name for m in store.members}}
        sel = ui.select(options, value=p.leader_member_id or '',
                        on_change=lambda e: _set_leader(e.value)) \
            .props('outlined dense').classes('w-64')
        sel.set_enabled(can_edit)
        if not can_edit:
            ui.label('Nur die aktuelle Teamleitung kann das ändern.').classes('text-xs text-grey-5')


@ui.refreshable
def content() -> None:
    with ui.row().classes('w-full items-center'):
        ui.label('Crew').classes('kontor-title text-lg')
        ui.space()
        ui.button('Mitglied', icon='person_add', on_click=_member_form).props('no-caps')

    _leader_section()
    with ui.column().classes('w-full gap-2'):
        for m in store.members:
            with ui.card().classes('w-full flex-row items-center gap-3 py-2'):
                avatar(m, '34px')
                with ui.column().classes('gap-0 grow'):
                    ui.label(m.name).classes('font-medium')
                    ui.label(f'{m.role or "—"} · {m.weekly_hours:g} h/Woche' + (f' · {m.day_rate:g} EUR/Tag' if m.day_rate else '')).classes('text-xs text-grey-6')
                if not m.active:
                    ui.badge('inaktiv').props('color=grey-5')
                open_tasks = sum(1 for t in store.tasks if t.assignee_id == m.id and t.status != 'done')
                ui.label(f'{open_tasks} offene Tasks').classes('text-xs text-grey-6')
                ui.button(icon='edit', on_click=lambda m=m: _member_form(m)).props('flat dense')

    ui.separator()
    with ui.card().classes('w-full gap-2'):
        ui.label('Daten').classes('text-sm font-bold')
        ui.label(f'Speicherort: {DATA_FILE}').classes('text-xs text-grey-6')
        with ui.row().classes('gap-2'):
            ui.button('Auf Demodaten zuruecksetzen', icon='restart_alt', color='warning',
                      on_click=lambda: _confirm(True)).props('outline no-caps')
            ui.button('Alles leeren', icon='delete_forever', color='negative',
                      on_click=lambda: _confirm(False)).props('outline no-caps')


def _confirm(demo: bool) -> None:
    with ui.dialog() as d, ui.card():
        ui.label('Demodaten wiederherstellen?' if demo else 'Wirklich alle Daten loeschen?')
        with ui.row():
            ui.button('Abbrechen', on_click=d.close).props('flat')
            ui.button('OK', color='negative',
                      on_click=lambda: (store.reset(demo=demo), d.close(),
                                        ui.navigate.reload()))
    d.open()


def page() -> None:
    with frame('/team'):
        ui.label('Crew & Daten').classes('kontor-title text-xl')
        content()
