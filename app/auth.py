"""Login + RBAC (rollenbasierte Rechte) fuer den Leitstand.

Nutzerverwaltung liegt in ``store.py`` (``User``-Dataclass, Passwoerter per
PBKDF2 gehasht, siehe ``store.hash_password``/``verify_password``). Diese
Datei kuemmert sich um:

    - die Starlette-Middleware, die nicht angemeldete Besucher auf ``/login``
      umleitet (wie bisher),
    - den lokalen Login (Benutzername/Passwort gegen ``store.users``),
    - Migration bestehender Installationen,
    - ``current_user()`` / ``has_role()`` als RBAC-Helfer fuer die Views,
    - die Login-Seite, inkl. optionalem "Mit SSO anmelden"-Knopf (siehe
      ``app/oidc.py``).

Migration / Abwaertskompatibilitaet
------------------------------------
Bisher gab es nur ein gemeinsames Passwort aus ``APP_USERNAME``/``APP_PASSWORD``.
Damit bestehende Deployments beim Upgrade nicht ausgesperrt werden: existieren
beim ersten Start noch KEINE Nutzer und ist ``APP_PASSWORD`` gesetzt, wird
automatisch ein Admin-Nutzer mit diesen Zugangsdaten angelegt
(``_bootstrap_users``). Gibt es weder Nutzer noch ``APP_PASSWORD``, bleibt der
Leitstand wie bisher komplett offen (nur fuer lokale Entwicklung sinnvoll).

Sobald mindestens ein aktiver Nutzer existiert, ist Auth aktiv (``enabled()``).
"""
from __future__ import annotations

import os

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import Client, app, ui
from starlette.middleware.base import BaseHTTPMiddleware

import oidc
from store import ROLES, User, role_at_least, store

# Nur fuer die einmalige Migration gelesen (siehe _bootstrap_users) – der
# eigentliche Login prueft danach ausschliesslich gegen store.users.
USERNAME = os.getenv('APP_USERNAME', 'admin')
PASSWORD = os.getenv('APP_PASSWORD', '')

# Seiten (bzw. Routen), die auch ohne Login erreichbar bleiben muessen.
UNRESTRICTED = {'/login', '/auth/oidc/login', '/auth/oidc/callback',
                 '/healthz', '/readyz', '/metrics'}


def _bootstrap_users() -> None:
    """Einmalige Migration: aus APP_USERNAME/APP_PASSWORD einen Admin anlegen,
    falls noch keine Nutzer existieren. Verhindert, dass bestehende
    Installationen beim Upgrade auf RBAC ausgesperrt werden."""
    if store.users or not PASSWORD:
        return
    store.add_user(username=USERNAME, display_name=USERNAME, password=PASSWORD, role='admin')
    print(f'[auth] Migration: Admin-Nutzer "{USERNAME}" aus APP_USERNAME/APP_PASSWORD angelegt.')


def enabled() -> bool:
    """True, sobald mindestens ein aktiver Nutzer existiert.

    Ohne Nutzer (und ohne APP_PASSWORD, siehe _bootstrap_users) bleibt der
    Leitstand wie in Version 1/2 komplett offen – bewusst fuer lokale
    Entwicklung/Demo, NICHT fuer den produktiven Einsatz.
    """
    return any(u.active for u in store.users)


def current_user() -> User | None:
    """Der angemeldete Nutzer, oder ``None`` (auch wenn Auth abgeschaltet ist)."""
    try:
        uid = app.storage.user.get('user_id')
    except Exception:  # noqa: BLE001 – kein Storage-Kontext (z. B. ausserhalb einer Seite)
        return None
    u = store.by_id('users', uid) if uid else None
    return u if (u and u.active) else None


def has_role(minimum: str) -> bool:
    """RBAC-Check fuer Views: mindestens Rolle ``minimum`` (siehe store.ROLES)?

    Ist Auth komplett abgeschaltet (kein Nutzer/kein Passwort konfiguriert),
    gilt das wie bisher als "alles erlaubt" – lokaler Dev-Modus.
    """
    if not enabled():
        return True
    u = current_user()
    return bool(u) and role_at_least(u.role, minimum)


def require_role(minimum: str, *, message: str = 'Dafuer fehlen dir die Rechte.') -> bool:
    """Fuer Aktions-Handler (Buttons etc.): False + Hinweis, wenn die Rolle nicht reicht."""
    if has_role(minimum):
        return True
    ui.notify(message, type='warning')
    return False


def logout() -> None:
    app.storage.user.clear()
    ui.navigate.to('/login')


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if enabled() and not current_user():
            path = request.url.path
            if path in Client.page_routes.values() and path not in UNRESTRICTED:
                app.storage.user['referrer_path'] = path
                return RedirectResponse('/login')
        return await call_next(request)


def setup() -> None:
    """Middleware + Login-Seite (+ ggf. OIDC-Routen) registrieren. Vor ``ui.run`` aufrufen."""
    _bootstrap_users()
    app.add_middleware(AuthMiddleware)
    oidc.setup_routes()

    @ui.page('/login')
    def login_page():
        if not enabled() or current_user():
            ui.navigate.to('/')
            return

        def try_login() -> None:
            user = store.verify_login(username.value, password.value)
            if user:
                app.storage.user.update({'authenticated': True, 'user_id': user.id})
                ui.navigate.to(app.storage.user.get('referrer_path', '/'))
            else:
                ui.notify('Falsche Zugangsdaten', color='negative')

        import theme
        theme.apply()
        with ui.card().classes('absolute-center w-80 gap-3 items-stretch'):
            ui.label('Kontor · Projektleitstand').classes('text-lg font-medium text-center')
            username = ui.input('Benutzer').props('outlined dense').on('keydown.enter', try_login)
            password = ui.input('Passwort', password=True, password_toggle_button=True) \
                .props('outlined dense').on('keydown.enter', try_login)
            ui.button('Anmelden', on_click=try_login).classes('w-full')

            if oidc.enabled():
                ui.separator()
                ui.button('Mit SSO anmelden', icon='vpn_key',
                          on_click=lambda: ui.navigate.to('/auth/oidc/login')) \
                    .props('outline no-caps').classes('w-full')
