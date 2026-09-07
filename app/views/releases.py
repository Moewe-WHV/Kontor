"""Release-Planung & Changelog."""
from __future__ import annotations

from nicegui import ui

from components import frame, stat_tile
from store import RELEASE_STATUS, Release, store, today_iso

STATUS_COLOR = {'geplant': 'grey-6', 'in_arbeit': 'warning', 'live': 'positive'}


def _form(existing=None) -> None:
    is_new = existing is None
    task_opts = {t.id: f'#{t.id[:4]} {t.title}' for t in store.p_tasks() if t.status != 'backlog'}
    with ui.dialog() as d, ui.card().classes('w-[32rem] gap-2'):
        ui.label('Release' if is_new else 'Release bearbeiten').classes('text-lg font-bold')
        with ui.row().classes('w-full gap-2'):
            version = ui.input('Version', value='' if is_new else existing.version) \
                .props('outlined dense').classes('grow')
            dt = ui.input('Ziel-/Datum', value=today_iso() if is_new else existing.date) \
                .props('outlined dense type=date').classes('grow')
            status = ui.select(RELEASE_STATUS, label='Status',
                               value='geplant' if is_new else existing.status).props('outlined dense').classes('grow')
        notes = ui.textarea('Changelog / Notizen', value='' if is_new else existing.notes) \
            .props('outlined dense autogrow').classes('w-full')
        tasks = ui.select(task_opts, label='enthaltene Tasks', multiple=True,
                          value=[] if is_new else list(existing.task_ids)) \
            .props('outlined dense use-chips').classes('w-full')

        def save() -> None:
            if not version.value.strip():
                ui.notify('Version fehlt', type='warning')
                return
            data = dict(version=version.value.strip(), date=dt.value, status=status.value,
                        notes=notes.value or '', task_ids=list(tasks.value or []))
            if is_new:
                store.add('releases', Release, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('releases', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    with ui.row().classes('w-full items-center'):
        ui.label('Releases').classes('text-lg font-bold')
        ui.space()
        ui.button('Neuer Release', icon='add', on_click=_form).props('no-caps')

    rels = sorted(store.p_releases(), key=lambda r: r.date, reverse=True)
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len([r for r in rels if r.status == 'live']), 'live')
        stat_tile(len([r for r in rels if r.status == 'in_arbeit']), 'in Arbeit', 'text-warning')
        stat_tile(len([r for r in rels if r.status == 'geplant']), 'geplant', 'text-grey-5')

    for r in rels:
        tasks = [store.task(tid) for tid in r.task_ids]
        tasks = [t for t in tasks if t]
        done = [t for t in tasks if t.status == 'done']
        with ui.card().classes('w-full gap-1'):
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.label(r.version).classes('text-base font-bold')
                ui.badge(RELEASE_STATUS[r.status]).props(f'color={STATUS_COLOR[r.status]}')
                ui.label(r.date).classes('text-xs text-grey-6')
                ui.space()
                if tasks:
                    ui.label(f'{len(done)}/{len(tasks)} Tasks fertig') \
                        .classes('text-xs ' + ('text-positive' if len(done) == len(tasks) else 'text-grey-6'))
                ui.button(icon='edit', on_click=lambda r=r: _form(r)).props('flat dense size=sm')
            if tasks:
                ui.linear_progress(len(done) / len(tasks), show_value=False, size='6px').classes('w-full')
            if r.notes:
                ui.label(r.notes).classes('text-sm text-grey-8 whitespace-pre-line')
            for t in tasks:
                icon = 'check_circle' if t.status == 'done' else 'radio_button_unchecked'
                color = 'text-positive' if t.status == 'done' else 'text-grey-5'
                with ui.row().classes('items-center gap-1'):
                    ui.icon(icon, size='15px').classes(color)
                    ui.label(t.title).classes('text-xs text-grey-7')


def page() -> None:
    with frame('/releases'):
        ui.label('Release-Management').classes('kontor-title text-xl')
        content()
