"""Umgebungen & Deployments – welche Version läuft wo, plus Deploy-Log."""
from __future__ import annotations

from nicegui import ui

from components import avatar, frame, stat_tile
from store import ENV_STATUS, Deployment, Environment, store, today_iso

ENV_COLOR = {'ok': 'positive', 'degraded': 'warning', 'down': 'negative', 'wartung': 'grey-6'}
DEP_COLOR = {'erfolgreich': 'positive', 'fehlgeschlagen': 'negative', 'rollback': 'warning'}


def _env_form(existing=None) -> None:
    is_new = existing is None
    members = {'': '– niemand –', **{m.id: m.name for m in store.active_members}}
    with ui.dialog() as d, ui.card().classes('w-96 gap-2'):
        ui.label('Neue Umgebung' if is_new else 'Umgebung bearbeiten').classes('kontor-title text-lg')
        name = ui.input('Name', value='' if is_new else existing.name, placeholder='dev / test / staging / prod') \
            .props('outlined dense').classes('w-full')
        url = ui.input('URL', value='' if is_new else existing.url).props('outlined dense').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            version = ui.input('Version', value='' if is_new else existing.version) \
                .props('outlined dense').classes('grow')
            status = ui.select(ENV_STATUS, label='Status', value='ok' if is_new else existing.status) \
                .props('outlined dense').classes('grow')
        owner = ui.select(members, label='verantwortlich',
                          value='' if is_new or not existing.owner_id else existing.owner_id) \
            .props('outlined dense').classes('w-full')
        note = ui.input('Notiz', value='' if is_new else existing.note).props('outlined dense').classes('w-full')

        def save() -> None:
            if not name.value.strip():
                ui.notify('Name fehlt', type='warning')
                return
            data = dict(name=name.value.strip(), url=url.value or '', version=version.value or '',
                        status=status.value, owner_id=owner.value or None, note=note.value or '')
            if is_new:
                data['order'] = len(store.p_environments())
                store.add('environments', Environment, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('environments', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


def _deploy_form(env=None) -> None:
    with ui.dialog() as d, ui.card().classes('w-96 gap-2'):
        ui.label('Deployment protokollieren').classes('kontor-title text-lg')
        envs = {e.name: e.name for e in store.p_environments()}
        target = ui.select(envs, label='Umgebung', value=env.name if env else (list(envs)[0] if envs else None)) \
            .props('outlined dense').classes('w-full')
        version = ui.input('Version', value=env.version if env else '').props('outlined dense').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            dt = ui.input('Datum', value=today_iso()).props('outlined dense type=date').classes('grow')
            status = ui.select({'erfolgreich': 'erfolgreich', 'fehlgeschlagen': 'fehlgeschlagen',
                                'rollback': 'rollback'}, value='erfolgreich', label='Ergebnis') \
                .props('outlined dense').classes('grow')
        by = ui.input('durch', value='').props('outlined dense').classes('w-full')
        note = ui.input('Notiz', value='').props('outlined dense').classes('w-full')

        def save() -> None:
            if not target.value or not version.value.strip():
                ui.notify('Umgebung & Version nötig', type='warning')
                return
            store.add('deployments', Deployment, project_id=store.pid, environment=target.value,
                      version=version.value.strip(), date=dt.value, by=by.value or '',
                      status=status.value, note=note.value or '')
            e = next((x for x in store.p_environments() if x.name == target.value), None)
            if e and status.value == 'erfolgreich':
                store.update(e, version=version.value.strip(), last_deploy=dt.value)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-end'):
            ui.button('Abbrechen', on_click=d.close).props('flat')
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    envs = store.p_environments()
    deploys = store.p_deployments()
    with ui.row().classes('w-full items-center gap-2'):
        ui.label('Umgebungen').classes('kontor-title text-lg')
        ui.space()
        ui.button('Deployment', icon='publish', on_click=lambda: _deploy_form()).props('no-caps outline')
        ui.button('Umgebung', icon='add', on_click=lambda: _env_form()).props('no-caps')

    prod = next((e for e in envs if e.name.lower().startswith('prod')), None)
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(prod.version if prod else '–', 'Prod-Version')
        stat_tile(len([e for e in envs if e.status != 'ok']), 'nicht grün',
                  'text-negative' if any(e.status != 'ok' for e in envs) else 'text-positive')
        last = deploys[0] if deploys else None
        stat_tile(last.date if last else '–', 'letztes Deployment',
                  hint=f'{last.environment} · {last.version}' if last else '')

    with ui.row().classes('w-full gap-3 flex-wrap'):
        for e in envs:
            with ui.card().classes('grow min-w-[14rem] gap-1'):
                with ui.row().classes('w-full items-center gap-2 no-wrap'):
                    ui.label(e.name).classes('kontor-title text-base grow')
                    ui.badge(ENV_STATUS[e.status]).props(f'color={ENV_COLOR[e.status]}')
                ui.label(e.version or '—').classes('text-sm')
                if e.url:
                    ui.link(e.url, e.url, new_tab=True).classes('text-xs truncate')
                with ui.row().classes('items-center gap-1 text-xs text-grey-6'):
                    avatar(store.member(e.owner_id), '18px')
                    ui.label(f'zuletzt: {e.last_deploy or "?"}')
                if e.note:
                    ui.label(e.note).classes('text-xs text-warning')
                ui.button(icon='edit', on_click=lambda e=e: _env_form(e)).props('flat dense size=sm')

    with ui.card().classes('w-full gap-1'):
        ui.label('Deployment-Log').classes('kontor-title text-sm')
        for dep in deploys[:20]:
            with ui.row().classes('w-full items-center gap-2 no-wrap border-b border-grey-2 py-1 text-sm'):
                ui.label(dep.date).classes('text-xs text-grey-6 w-24')
                ui.badge(dep.environment).props('color=grey-6')
                ui.label(dep.version).classes('font-medium')
                ui.badge(dep.status).props(f'color={DEP_COLOR.get(dep.status, "grey")}')
                ui.label(dep.note).classes('text-xs text-grey-5 grow truncate')
                ui.label(dep.by).classes('text-xs text-grey-6')


def page() -> None:
    with frame('/environments'):
        ui.label('Umgebungen & Deployments').classes('kontor-title text-xl')
        content()
