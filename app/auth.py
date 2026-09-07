"""Einfacher Passwort-Login, der alle Seiten des Leitstands schuetzt.

Zugangsdaten kommen aus Umgebungsvariablen:
    APP_USERNAME   Benutzername (Default: admin)
    APP_PASSWORD   Passwort – ist es leer, ist der Schutz komplett aus
                   (nur fuer lokale Entwicklung sinnvoll).

Umsetzung nach dem offiziellen NiceGUI-Auth-Beispiel: eine Starlette-Middleware
leitet nicht angemeldete Besucher auf ``/login`` um; nach dem Login geht es
zurueck auf die urspruenglich gewuenschte Seite.
"""
from __future__ import annotations

import hmac
import os

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import Client, app, ui
from starlette.middleware.base import BaseHTTPMiddleware

USERNAME = os.getenv('APP_USERNAME', 'admin')
PASSWORD = os.getenv('APP_PASSWORD', '')

# Seiten, die auch ohne Login erreichbar bleiben muessen.
UNRESTRICTED = {'/login'}


def enabled() -> bool:
    """True, sobald ein Passwort gesetzt ist."""
    return bool(PASSWORD)


def _valid(user: str | None, pw: str | None) -> bool:
    return (hmac.compare_digest(user or '', USERNAME)
            and hmac.compare_digest(pw or '', PASSWORD))


def logout() -> None:
    app.storage.user.clear()
    ui.navigate.to('/login')


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if enabled() and not app.storage.user.get('authenticated', False):
            path = request.url.path
            if path in Client.page_routes.values() and path not in UNRESTRICTED:
                app.storage.user['referrer_path'] = path
                return RedirectResponse('/login')
        return await call_next(request)


def setup() -> None:
    """Middleware + Login-Seite registrieren. Vor ``ui.run`` aufrufen."""
    app.add_middleware(AuthMiddleware)

    @ui.page('/login')
    def login_page():
        if not enabled() or app.storage.user.get('authenticated', False):
            ui.navigate.to('/')
            return

        def try_login() -> None:
            if _valid(username.value, password.value):
                app.storage.user.update({'authenticated': True})
                ui.navigate.to(app.storage.user.get('referrer_path', '/'))
            else:
                ui.notify('Falsche Zugangsdaten', color='negative')

        ui.query('body').style('background:#e7ece9')
        with ui.card().classes('absolute-center w-80 gap-3 items-stretch'):
            ui.label('Kontor · Projektleitstand').classes('text-lg font-medium text-center')
            username = ui.input('Benutzer').props('outlined dense').on('keydown.enter', try_login)
            password = ui.input('Passwort', password=True, password_toggle_button=True) \
                .props('outlined dense').on('keydown.enter', try_login)
            ui.button('Anmelden', on_click=try_login).classes('w-full')
