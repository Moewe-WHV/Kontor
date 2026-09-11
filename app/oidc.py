"""OIDC/OAuth2 Single-Sign-On – Anschlussstelle fuer eine spaetere Ausbaustufe.

Aktueller Stand: Erkennung, ob SSO konfiguriert ist (``enabled()``), und die
beiden Routen, die ``auth.py`` bereits erwartet (``UNRESTRICTED`` dort). Der
eigentliche Authorization-Code-Flow – Redirect zum Identity Provider mit
state/PKCE, Token-Tausch, Signaturpruefung des ID-Tokens gegen die JWKS des
Providers – ist bewusst NICHT implementiert. Eine kurzgeschlossene Variante
(z. B. ein ID-Token ungeprueft uebernehmen) waere ein Sicherheitsloch, kein
Feature, deshalb bleibt das ein eigenes Stueck Arbeit (siehe Feature-Liste
"Security, Multi-User & Ops").

Bis dahin: ``enabled()`` liefert nur dann True, wenn ein Identity Provider
vollstaendig konfiguriert ist, damit die lokale Passwort-Anmeldung
(``auth.py``, ``store.verify_login``) fuer alle bestehenden Installationen
unveraendert weiterfunktioniert. Ist SSO konfiguriert, erscheint der Knopf
auf der Login-Seite, fuehrt aktuell aber nur zu einem klaren Hinweis statt
zu einem stillen Fehlschlag.

Umgebungsvariablen (alle drei noetig, damit SSO als "konfiguriert" gilt):
    OIDC_ISSUER_URL     z. B. https://accounts.google.com
    OIDC_CLIENT_ID
    OIDC_CLIENT_SECRET
"""
from __future__ import annotations

import os

from fastapi.responses import PlainTextResponse
from nicegui import app

_NOT_IMPLEMENTED = (
    'Single Sign-On ist fuer diese Installation konfiguriert, der Login-Ablauf '
    'selbst ist aber noch nicht umgesetzt (naechster Ausbauschritt). '
    'Bitte mit Benutzername/Passwort anmelden.'
)


def enabled() -> bool:
    """True, sobald Issuer, Client-ID und Client-Secret gesetzt sind."""
    return bool(os.getenv('OIDC_ISSUER_URL') and os.getenv('OIDC_CLIENT_ID')
                and os.getenv('OIDC_CLIENT_SECRET'))


def setup_routes() -> None:
    """OIDC-Routen registrieren. Vor ``ui.run`` aufrufen (siehe auth.setup)."""

    @app.get('/auth/oidc/login')
    def _oidc_login():
        return PlainTextResponse(_NOT_IMPLEMENTED, status_code=501)

    @app.get('/auth/oidc/callback')
    def _oidc_callback():
        return PlainTextResponse(_NOT_IMPLEMENTED, status_code=501)
