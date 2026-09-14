"""Projektzugriff verwalten – wer darf dieses eine Projekt sehen/leiten.

Ergaenzt die globale Nutzerverwaltung (siehe views/users.py) um eine
projekt-lokale Berechtigung (store.ProjectAccess): eine Teamleitung kann hier
Kolleg:innen einen Zugang geben, der nur das aktuell gewaehlte Projekt zeigt
(siehe store.visible_projects) und dort je nach Rolle Fuehrungsbereiche
ein-/ausblendet (siehe store.is_project_leader, LEADERSHIP_MODULES).

Sichtbar fuer System-Admins und fuer die (echte oder – solange fuer dieses
Projekt noch nichts konfiguriert ist – vorlaeufige) Teamleitung des Projekts.
"""
from __future__ import annotations

import auth
from nicegui import ui

from components import frame, viewer_is_leader
from store import store

MIN_PASSWORD_LENGTH = 8
ACCESS_ROLES = {'leader': 'Teamleitung', 'member': 'Mitglied'}


def _add_dialog() -> None:
    pid = store.pid
    existing_user_ids = {a.user_id for a in store.access_rows(pid)}
    candidates = [u for u in store.users if u.id not in existing_user_ids]

    with ui.dialog() as d, ui.card().classes('w-96 gap-2'):
        ui.label('Person hinzufügen').classes('text-lg font-bold')
        def _sync_visibility() -> None:
            existing_col.set_visibility(mode.value == 'existing')
            new_col.set_visibility(mode.value == 'new')

        mode = ui.toggle({'existing': 'Bestehende:r Nutzer:in', 'new': 'Neue:r Nutzer:in'},
                         value='existing' if candidates else 'new',
                         on_change=lambda: _sync_visibility()).props('dense no-caps')

        with ui.column().classes('w-full gap-2') as existing_col:
            user_select = ui.select({u.id: f'{u.display_name or u.username} (@{u.username})' for u in candidates},
                                    label='Nutzer:in', value=candidates[0].id if candidates else None) \
                .props('outlined dense').classes('w-full')
            if not candidates:
                ui.label('Alle bestehenden Nutzer:innen haben hier schon Zugriff.') \
                    .classes('text-xs text-grey-6')

        with ui.column().classes('w-full gap-2') as new_col:
            new_username = ui.input('Benutzername').props('outlined dense').classes('w-full')
            new_display_name = ui.input('Anzeigename').props('outlined dense').classes('w-full')
            new_password = ui.input('Startpasswort', password=True, password_toggle_button=True) \
                .props('outlined dense').classes('w-full')

        role = ui.select(ACCESS_ROLES, label='Rolle in diesem Projekt', value='member') \
            .props('outlined dense').classes('w-full')
        _sync_visibility()

        ui.label('Zugangsdaten müssen selbst weitergegeben werden – es gibt keinen automatischen Versand.') \
            .classes('text-xs text-grey-6')

        def save() -> None:
            if mode.value == 'existing':
                if not user_select.value:
                    ui.notify('Bitte eine Person auswählen', type='warning')
                    return
                user = store.by_id('users', user_select.value)
            else:
                uname = new_username.value.strip()
                if not uname:
                    ui.notify('Benutzername fehlt', type='warning')
                    return
                if store.user_by_username(uname):
                    ui.notify('Benutzername bereits vergeben', type='warning')
                    return
                if not new_password.value:
                    ui.notify('Startpasswort fehlt', type='warning')
                    return
                if len(new_password.value) < MIN_PASSWORD_LENGTH:
                    ui.notify(f'Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen haben', type='warning')
                    return
                user = store.add_user(username=uname, display_name=new_display_name.value.strip(),
                                       password=new_password.value, role='viewer')
            store.grant_access(pid, user.id, role=role.value)
            ui.notify('Zugriff vergeben', type='positive')
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Abbrechen', on_click=d.close).props('flat')
            ui.button('Speichern', on_click=save)
    d.open()


def _remove(access) -> None:
    store.revoke_access(access.id)
    ui.notify('Zugriff entfernt', type='positive')
    content.refresh()


def _change_role(access, role: str) -> None:
    store.set_access_role(access, role)
    content.refresh()


@ui.refreshable
def content() -> None:
    p = store.project
    rows = store.access_rows(p.id)

    with ui.row().classes('w-full items-center'):
        ui.label(f'Zugriff auf „{p.name}"').classes('kontor-title text-lg')
        ui.space()
        ui.button('Person hinzufügen', icon='person_add', on_click=_add_dialog).props('no-caps')

    if not rows:
        ui.label('Noch niemand eingeschränkt – aktuell sieht jede angemeldete Person dieses Projekt. '
                  'Sobald hier jemand eingetragen ist, sehen nur noch diese Personen (und Admins) '
                  'das Projekt.').classes('text-sm text-grey-6')

    with ui.column().classes('w-full gap-2'):
        for a in rows:
            u = store.by_id('users', a.user_id)
            if not u:
                continue
            with ui.card().classes('w-full flex-row items-center gap-3 py-2'):
                ui.icon('account_circle', size='28px').classes('text-primary' if u.active else 'text-grey-5')
                with ui.column().classes('gap-0 grow'):
                    ui.label(u.display_name or u.username).classes('font-medium')
                    ui.label(f'@{u.username}').classes('text-xs text-grey-6')
                ui.select(ACCESS_ROLES, value=a.role, on_change=lambda e, a=a: _change_role(a, e.value)) \
                    .props('outlined dense').classes('w-40')
                ui.button(icon='delete', on_click=lambda a=a: _remove(a)).props('flat dense color=negative')

    ui.label('Teamleitung sieht zusätzlich Führungsbereiche (Budget, Stakeholder, RACI, …) '
             'und kann hier selbst weitere Personen einladen.').classes('text-xs text-grey-6 mt-2')


def page() -> None:
    with frame('/zugriff'):
        ui.label('Projektzugriff').classes('kontor-title text-xl')
        if not (auth.has_role('admin') or viewer_is_leader()):
            ui.label('Diese Seite ist nur für die Teamleitung dieses Projekts sichtbar.').classes('text-grey-6')
            return
        content()
