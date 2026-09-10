"""Einstellungen – app-weite Optionen, GitHub-Zugang und Datenverwaltung.

Alle Werte liegen (bis auf den Willkommens-Dialog, der pro Browser gilt) in
``pm.json`` unter ``settings`` und wirken sofort – kein Neustart noetig.
"""
from __future__ import annotations

import json

from nicegui import app, ui

from components import frame, help_hint
from store import DATA_FILE, DEFAULT_SETTINGS, SCHEMA, VERSION, _MODELS, store


def _save(key: str, value) -> None:
    store.set_setting(key, value)
    ui.notify('Gespeichert', type='positive')


# --------------------------------------------------------------------------
def _section_github() -> None:
    with ui.card().classes('w-full gap-2'):
        ui.label('GitHub-Anbindung').classes('kontor-title text-md')
        ui.label('Fuer die Pull-Request-Sicht auf dem Leitstand. Leer lassen, um die '
                 'Umgebungsvariablen GITHUB_REPO / GITHUB_TOKEN zu verwenden.') \
            .classes('text-xs text-grey-6')
        repo = ui.input('Standard-Repository (owner/name)',
                        value=store.setting('github_repo')) \
            .props('outlined dense').classes('w-full')
        repo.on('blur', lambda: _save('github_repo', repo.value.strip()))
        token = ui.input('Personal Access Token', value=store.setting('github_token'),
                         password=True, password_toggle_button=True) \
            .props('outlined dense').classes('w-full')
        token.on('blur', lambda: _save('github_token', token.value.strip()))
        ui.label('Der Token wird im Klartext in pm.json abgelegt – auf einem geteilten '
                 'Server besser die Umgebungsvariable nutzen.').classes('text-xs text-amber-8')


def _section_defaults() -> None:
    with ui.card().classes('w-full gap-2'):
        ui.label('Vorgaben').classes('kontor-title text-md')
        with ui.row().classes('w-full gap-3 flex-wrap'):
            cur = ui.input('Waehrungssymbol', value=store.setting('currency')) \
                .props('outlined dense').classes('w-40')
            cur.on('blur', lambda: _save('currency', cur.value.strip() or '€'))
            wh = ui.number('Wochenstunden (neue Crew)', value=store.setting('default_weekly_hours'),
                           min=0, step=0.5, format='%.1f').props('outlined dense').classes('w-56')
            wh.on('blur', lambda: _save('default_weekly_hours', float(wh.value or 0)))
            sd = ui.number('Sprint-Laenge (Tage)', value=store.setting('default_sprint_days'),
                           min=1, step=1, format='%d').props('outlined dense').classes('w-48')
            sd.on('blur', lambda: _save('default_sprint_days', int(sd.value or 14)))


def _section_onboarding() -> None:
    with ui.card().classes('w-full gap-2'):
        ui.label('Einstieg & Hilfe').classes('kontor-title text-md')
        ui.switch('Willkommens-Dialog fuer neue Browser zeigen',
                  value=bool(store.setting('show_welcome')),
                  on_change=lambda e: _save('show_welcome', bool(e.value)))

        def _show_again() -> None:
            try:
                app.storage.user.pop('kontor_onboarded', None)
                ui.notify('Beim naechsten Seitenaufruf erscheint der Dialog wieder.', type='info')
            except Exception:  # noqa: BLE001
                ui.notify('Kein Browser-Speicher verfuegbar.', type='warning')

        ui.button('Willkommens-Dialog hier erneut anzeigen', icon='waving_hand',
                  on_click=_show_again).props('flat no-caps')


def _section_data() -> None:
    with ui.card().classes('w-full gap-2'):
        ui.label('Daten').classes('kontor-title text-md')
        ui.label(f'Ablage: {DATA_FILE}').classes('text-xs text-grey-6 break-all')

        with ui.row().classes('gap-2 flex-wrap'):
            ui.button('Export (JSON herunterladen)', icon='download',
                      on_click=lambda: ui.download.file(DATA_FILE, 'kontor-export.json')) \
                .props('outline no-caps')

        ui.separator()
        ui.label('Import – ersetzt den gesamten Datenbestand durch die hochgeladene Datei.') \
            .classes('text-xs text-grey-7')

        def _on_upload(e) -> None:
            try:
                raw = json.loads(e.content.read().decode('utf-8'))
                store.import_payload(raw)
            except Exception as exc:  # noqa: BLE001
                ui.notify(f'Import fehlgeschlagen: {exc}', type='negative')
                return
            ui.notify('Import erfolgreich – Seite wird neu geladen.', type='positive')
            ui.navigate.to('/')

        ui.upload(on_upload=_on_upload, auto_upload=True, label='Kontor-Export waehlen') \
            .props('accept=.json flat bordered').classes('w-full max-w-md')

        ui.separator()
        with ui.row().classes('gap-2 flex-wrap'):
            ui.button('Demo-Daten neu laden', icon='restart_alt', color='warning',
                      on_click=lambda: _confirm_reset(demo=True)).props('outline no-caps')
            ui.button('Alles leeren', icon='delete_forever', color='negative',
                      on_click=lambda: _confirm_reset(demo=False)).props('outline no-caps')


def _confirm_reset(*, demo: bool) -> None:
    with ui.dialog() as d, ui.card().classes('gap-2'):
        ui.label('Demo-Daten neu laden?' if demo else 'Wirklich alle Daten loeschen?') \
            .classes('kontor-title text-md')
        ui.label('Der aktuelle Bestand geht dabei verloren (vorher ggf. exportieren).') \
            .classes('text-sm text-grey-7')
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Abbrechen', on_click=d.close).props('flat')

            def _do() -> None:
                store.reset(demo=demo)
                d.close()
                ui.navigate.to('/')

            ui.button('Fortfahren', color='negative', on_click=_do)
    d.open()


def _section_info() -> None:
    counts = {name: len(getattr(store, name)) for name in _MODELS}
    total = sum(counts.values())
    with ui.card().classes('w-full gap-1'):
        ui.label('Ueber diese Installation').classes('kontor-title text-md')
        with ui.row().classes('gap-6 flex-wrap text-sm'):
            ui.label(f'Version {VERSION}')
            ui.label(f'Datenschema {SCHEMA}')
            ui.label(f'{len(store.projects)} Projekte')
            ui.label(f'{total} Datensaetze gesamt')
        biggest = sorted(counts.items(), key=lambda kv: -kv[1])[:5]
        ui.label('Groesste Sammlungen: '
                 + ', '.join(f'{k} ({v})' for k, v in biggest if v)) \
            .classes('text-xs text-grey-6')


# --------------------------------------------------------------------------
@ui.refreshable
def content() -> None:
    help_hint('Diese Optionen gelten fuer den ganzen Leitstand und werden in pm.json '
              'gespeichert. Aenderungen wirken sofort. Der Willkommens-Dialog-Schalter '
              'unter „Einstieg & Hilfe" bezieht sich auf deinen Browser.',
              title='Was hier passiert')
    _section_github()
    _section_defaults()
    _section_onboarding()
    _section_data()
    _section_info()

    changed = {k: v for k, v in store.settings.items()
               if DEFAULT_SETTINGS.get(k) != v and k != 'github_token'}
    if changed:
        with ui.row().classes('items-center gap-2'):
            ui.label('Von der Voreinstellung abweichend: '
                     + ', '.join(changed)).classes('text-xs text-grey-5')
            ui.button('Auf Standard zuruecksetzen', icon='settings_backup_restore',
                      on_click=_reset_settings).props('flat dense no-caps size=sm')


def _reset_settings() -> None:
    store.update_settings(**DEFAULT_SETTINGS)
    ui.notify('Einstellungen zurueckgesetzt', type='positive')
    content.refresh()


def page() -> None:
    with frame('/settings'):
        ui.label('Einstellungen').classes('kontor-title text-xl')
        content()
