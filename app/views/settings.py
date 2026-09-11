"""Einstellungen – app-weite Optionen, GitHub-Zugang und Datenverwaltung.

Alle Werte liegen (bis auf den Willkommens-Dialog, der pro Browser gilt) in
``pm.json`` unter ``settings`` und wirken sofort – kein Neustart noetig.
"""
from __future__ import annotations

import json

from nicegui import app, ui

from components import frame, help_hint
from i18n import t
from store import DATA_FILE, DEFAULT_SETTINGS, SCHEMA, VERSION, _MODELS, store


def _save(key: str, value) -> None:
    store.set_setting(key, value)
    ui.notify(t('common.saved'), type='positive')


# --------------------------------------------------------------------------
def _section_language() -> None:
    with ui.card().classes('w-full gap-2'):
        ui.label(t('settings.language.title')).classes('kontor-title text-md')
        ui.label(t('settings.language.hint')).classes('text-xs text-grey-6')

        def _change(e) -> None:
            store.set_setting('language', e.value)
            ui.navigate.reload()

        ui.select({'de': 'Deutsch', 'en': 'English'}, label=t('settings.language.label'),
                  value=store.setting('language', 'de'), on_change=_change) \
            .props('outlined dense').classes('w-56')


def _section_github() -> None:
    with ui.card().classes('w-full gap-2'):
        ui.label(t('settings.github.title')).classes('kontor-title text-md')
        ui.label(t('settings.github.hint')).classes('text-xs text-grey-6')
        repo = ui.input(t('settings.github.repo_label'),
                        value=store.setting('github_repo')) \
            .props('outlined dense').classes('w-full')
        repo.on('blur', lambda: _save('github_repo', repo.value.strip()))
        token = ui.input(t('settings.github.token_label'), value=store.setting('github_token'),
                         password=True, password_toggle_button=True) \
            .props('outlined dense').classes('w-full')
        token.on('blur', lambda: _save('github_token', token.value.strip()))
        ui.label(t('settings.github.token_hint')).classes('text-xs text-amber-8')


def _section_defaults() -> None:
    with ui.card().classes('w-full gap-2'):
        ui.label(t('settings.defaults.title')).classes('kontor-title text-md')
        with ui.row().classes('w-full gap-3 flex-wrap'):
            cur = ui.input(t('settings.defaults.currency'), value=store.setting('currency')) \
                .props('outlined dense').classes('w-40')
            cur.on('blur', lambda: _save('currency', cur.value.strip() or '€'))
            wh = ui.number(t('settings.defaults.weekly_hours'), value=store.setting('default_weekly_hours'),
                           min=0, step=0.5, format='%.1f').props('outlined dense').classes('w-56')
            wh.on('blur', lambda: _save('default_weekly_hours', float(wh.value or 0)))
            sd = ui.number(t('settings.defaults.sprint_days'), value=store.setting('default_sprint_days'),
                           min=1, step=1, format='%d').props('outlined dense').classes('w-48')
            sd.on('blur', lambda: _save('default_sprint_days', int(sd.value or 14)))


def _section_onboarding() -> None:
    with ui.card().classes('w-full gap-2'):
        ui.label(t('settings.onboarding.title')).classes('kontor-title text-md')
        ui.switch(t('settings.onboarding.show_welcome'),
                  value=bool(store.setting('show_welcome')),
                  on_change=lambda e: _save('show_welcome', bool(e.value)))

        def _show_again() -> None:
            try:
                app.storage.user.pop('kontor_onboarded', None)
                ui.notify(t('settings.onboarding.show_again_notice'), type='info')
            except Exception:  # noqa: BLE001
                ui.notify(t('settings.onboarding.no_storage'), type='warning')

        ui.button(t('settings.onboarding.show_again'), icon='waving_hand',
                  on_click=_show_again).props('flat no-caps')


def _section_data() -> None:
    with ui.card().classes('w-full gap-2'):
        ui.label(t('settings.data.title')).classes('kontor-title text-md')
        ui.label(t('settings.data.location', path=DATA_FILE)).classes('text-xs text-grey-6 break-all')

        with ui.row().classes('gap-2 flex-wrap'):
            ui.button(t('settings.data.export'), icon='download',
                      on_click=lambda: ui.download.file(DATA_FILE, 'kontor-export.json')) \
                .props('outline no-caps')

        ui.separator()
        ui.label(t('settings.data.import_hint')).classes('text-xs text-grey-7')

        def _on_upload(e) -> None:
            try:
                raw = json.loads(e.content.read().decode('utf-8'))
                store.import_payload(raw)
            except Exception as exc:  # noqa: BLE001
                ui.notify(t('settings.data.import_failed', error=exc), type='negative')
                return
            ui.notify(t('settings.data.import_ok'), type='positive')
            ui.navigate.to('/')

        ui.upload(on_upload=_on_upload, auto_upload=True, label=t('settings.data.import_label')) \
            .props('accept=.json flat bordered').classes('w-full max-w-md')

        ui.separator()
        with ui.row().classes('gap-2 flex-wrap'):
            ui.button(t('settings.data.reseed'), icon='restart_alt', color='warning',
                      on_click=lambda: _confirm_reset(demo=True)).props('outline no-caps')
            ui.button(t('settings.data.clear_all'), icon='delete_forever', color='negative',
                      on_click=lambda: _confirm_reset(demo=False)).props('outline no-caps')


def _confirm_reset(*, demo: bool) -> None:
    with ui.dialog() as d, ui.card().classes('gap-2'):
        ui.label(t('settings.confirm.reseed_title') if demo else t('settings.confirm.clear_title')) \
            .classes('kontor-title text-md')
        ui.label(t('settings.confirm.body')).classes('text-sm text-grey-7')
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button(t('common.cancel'), on_click=d.close).props('flat')

            def _do() -> None:
                store.reset(demo=demo)
                d.close()
                ui.navigate.to('/')

            ui.button(t('settings.confirm.proceed'), color='negative', on_click=_do)
    d.open()


def _section_info() -> None:
    counts = {name: len(getattr(store, name)) for name in _MODELS}
    total = sum(counts.values())
    with ui.card().classes('w-full gap-1'):
        ui.label(t('settings.info.title')).classes('kontor-title text-md')
        with ui.row().classes('gap-6 flex-wrap text-sm'):
            ui.label(t('settings.info.version', version=VERSION))
            ui.label(t('settings.info.schema', schema=SCHEMA))
            ui.label(t('settings.info.projects', n=len(store.projects)))
            ui.label(t('settings.info.records', n=total))
        biggest = sorted(counts.items(), key=lambda kv: -kv[1])[:5]
        ui.label(t('settings.info.biggest',
                   list=', '.join(f'{k} ({v})' for k, v in biggest if v))) \
            .classes('text-xs text-grey-6')


# --------------------------------------------------------------------------
@ui.refreshable
def content() -> None:
    help_hint(t('settings.hint_body'), title=t('settings.hint_title'))
    _section_language()
    _section_github()
    _section_defaults()
    _section_onboarding()
    _section_data()
    _section_info()

    changed = {k: v for k, v in store.settings.items()
               if DEFAULT_SETTINGS.get(k) != v and k != 'github_token'}
    if changed:
        with ui.row().classes('items-center gap-2'):
            ui.label(t('settings.deviating', list=', '.join(changed))).classes('text-xs text-grey-5')
            ui.button(t('settings.reset_defaults'), icon='settings_backup_restore',
                      on_click=_reset_settings).props('flat dense no-caps size=sm')


def _reset_settings() -> None:
    store.update_settings(**DEFAULT_SETTINGS)
    ui.notify(t('settings.reset_done'), type='positive')
    content.refresh()


def page() -> None:
    with frame('/settings'):
        ui.label(t('settings.page_title')).classes('kontor-title text-xl')
        content()
