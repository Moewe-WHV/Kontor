"""Nutzerverwaltung (RBAC) – Konten anlegen, Rolle & Aktiv-Status pflegen.

Nur fuer Admins sichtbar (siehe auth.has_role). Ohne diese Seite waere der
in store.py/auth.py angelegte Nutzer-Unterbau totes Gewicht: der beim ersten
Start aus APP_USERNAME/APP_PASSWORD gebootstrappte Admin haette sonst keine
Moeglichkeit, weitere Konten anzulegen.
"""
from __future__ import annotations

import auth
from nicegui import ui

from components import frame
from store import ROLES, store


def _user_form(existing=None) -> None:
    is_new = existing is None
    with ui.dialog() as d, ui.card().classes('w-96 gap-2'):
        ui.label('Neuer Nutzer' if is_new else f'Nutzer bearbeiten: {existing.username}') \
            .classes('text-lg font-bold')
        username = ui.input('Benutzername', value='' if is_new else existing.username) \
            .props('outlined dense').classes('w-full')
        username.set_enabled(is_new)  # Benutzername ist der Login-Schluessel, nicht nachtraeglich aenderbar
        name = ui.input('Anzeigename', value='' if is_new else existing.display_name) \
            .props('outlined dense').classes('w-full')
        role = ui.select(ROLES, label='Rolle', value='viewer' if is_new else existing.role) \
            .props('outlined dense').classes('w-full')
        pw_label = 'Passwort' if is_new else 'Neues Passwort (leer = unveraendert)'
        password = ui.input(pw_label, password=True, password_toggle_button=True) \
            .props('outlined dense').classes('w-full')
        active = ui.checkbox('aktiv', value=True if is_new else existing.active)

        def save() -> None:
            uname = username.value.strip()
            if is_new and not uname:
                ui.notify('Benutzername fehlt', type='warning')
                return
            if is_new and store.user_by_username(uname):
                ui.notify('Benutzername bereits vergeben', type='warning')
                return
            if is_new and not password.value:
                ui.notify('Passwort fehlt', type='warning')
                return
            if is_new:
                store.add_user(username=uname, display_name=name.value.strip(),
                                password=password.value, role=role.value, active=active.value)
            else:
                existing.display_name = name.value.strip() or existing.username
                existing.role = role.value
                existing.active = active.value
                if password.value:
                    store.set_user_password(existing, password.value)
                store.save()
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Abbrechen', on_click=d.close).props('flat')
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    me = auth.current_user()
    with ui.row().classes('w-full items-center'):
        ui.label('Nutzer').classes('kontor-title text-lg')
        ui.space()
        ui.button('Nutzer anlegen', icon='person_add', on_click=_user_form).props('no-caps')

    with ui.column().classes('w-full gap-2'):
        for u in sorted(store.users, key=lambda x: x.username.lower()):
            with ui.card().classes('w-full flex-row items-center gap-3 py-2'):
                ui.icon('account_circle', size='28px').classes(
                    'text-primary' if u.active else 'text-grey-5')
                with ui.column().classes('gap-0 grow'):
                    ui.label(u.display_name or u.username).classes('font-medium')
                    ui.label(f'@{u.username} · {u.role}'
                              + (' · SSO' if u.oidc_sub else '')).classes('text-xs text-grey-6')
                if not u.active:
                    ui.badge('gesperrt').props('color=grey-5')
                if u.id == (me.id if me else None):
                    ui.badge('du').props('color=primary')
                ui.button(icon='edit', on_click=lambda u=u: _user_form(u)).props('flat dense')

    ui.label('Rollen: viewer (lesen) < member (Tagesgeschaeft) < admin '
             '(Nutzer, Einstellungen, Struktur).').classes('text-xs text-grey-6 mt-2')


def page() -> None:
    with frame('/users'):
        ui.label('Nutzer & Rechte').classes('kontor-title text-xl')
        if not auth.has_role('admin'):
            ui.label('Diese Seite ist nur fuer Admins sichtbar.').classes('text-grey-6')
            return
        content()
