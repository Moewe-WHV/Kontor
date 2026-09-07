"""Anforderungen – Scope-Register mit MoSCoW, Status und Akzeptanzkriterien."""
from __future__ import annotations

from nicegui import ui

from components import frame, stat_tile
from store import MOSCOW, REQ_KIND, REQ_STATUS, Requirement, store

MOSCOW_COLOR = {'muss': 'negative', 'soll': 'primary', 'kann': 'grey-6', 'nicht': 'grey-4'}
STATUS_COLOR = {'entwurf': 'grey-6', 'abgestimmt': 'info', 'umgesetzt': 'warning', 'abgenommen': 'positive'}
_flt = {'q': ''}


def _form(existing=None) -> None:
    is_new = existing is None
    tasks = {t.id: t.title for t in store.p_tasks()}
    with ui.dialog() as d, ui.card().classes('w-[34rem] gap-2'):
        ui.label('Neue Anforderung' if is_new else 'Anforderung bearbeiten').classes('kontor-title text-lg')
        title = ui.input('Titel', value='' if is_new else existing.title).props('outlined dense').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            kind = ui.select(REQ_KIND, label='Art', value='funktional' if is_new else existing.kind) \
                .props('outlined dense').classes('grow')
            moscow = ui.select(MOSCOW, label='Priorität (MoSCoW)', value='soll' if is_new else existing.moscow) \
                .props('outlined dense').classes('grow')
            status = ui.select(REQ_STATUS, label='Status', value='entwurf' if is_new else existing.status) \
                .props('outlined dense').classes('grow')
        acc = ui.textarea('Akzeptanzkriterien', value='' if is_new else existing.acceptance) \
            .props('outlined dense autogrow').classes('w-full')
        note = ui.textarea('Notiz', value='' if is_new else existing.note) \
            .props('outlined dense autogrow').classes('w-full')
        linked = ui.select(tasks, label='verknüpfte Tasks', multiple=True,
                           value=[] if is_new else list(existing.task_ids)) \
            .props('outlined dense use-chips').classes('w-full')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), kind=kind.value, moscow=moscow.value,
                        status=status.value, acceptance=acc.value or '', note=note.value or '',
                        task_ids=list(linked.value or []))
            if is_new:
                store.add('requirements', Requirement, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('requirements', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    reqs = store.p_requirements()
    with ui.row().classes('w-full items-center gap-2'):
        ui.label('Anforderungen').classes('kontor-title text-lg')
        ui.input(placeholder='filtern …', on_change=lambda e: (_flt.update(q=e.value.lower()), content.refresh())) \
            .props('dense outlined clearable').classes('w-48')
        ui.space()
        ui.button('Neue Anforderung', icon='add', on_click=_form).props('no-caps')

    must = [r for r in reqs if r.moscow == 'muss']
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(reqs), 'gesamt')
        stat_tile(f'{len([r for r in must if r.status == "abgenommen"])}/{len(must)}', 'Muss abgenommen',
                  'text-positive' if must and all(r.status == 'abgenommen' for r in must) else 'text-primary')
        stat_tile(len([r for r in reqs if r.status == 'entwurf']), 'im Entwurf', 'text-grey-5')
        stat_tile(len([r for r in reqs if r.status == 'abgenommen']), 'abgenommen', 'text-positive')

    q = _flt['q']
    shown = [r for r in reqs if not q or q in r.title.lower() or q in r.acceptance.lower()]
    for r in sorted(shown, key=lambda r: (list(MOSCOW).index(r.moscow), r.title.lower())):
        with ui.card().classes('w-full gap-1'):
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.badge(MOSCOW[r.moscow]).props(f'color={MOSCOW_COLOR[r.moscow]}')
                ui.label(r.title).classes('text-sm font-medium grow')
                ui.badge(REQ_KIND[r.kind]).props('outline color=grey-7')
                ui.badge(REQ_STATUS[r.status]).props(f'color={STATUS_COLOR[r.status]}')
                ui.button(icon='edit', on_click=lambda r=r: _form(r)).props('flat dense size=sm')
            if r.acceptance:
                ui.label('AK: ' + r.acceptance).classes('text-xs text-grey-6 whitespace-pre-line')
            if r.task_ids:
                done = len([1 for tid in r.task_ids if (t := store.task(tid)) and t.status == 'done'])
                ui.label(f'{done}/{len(r.task_ids)} verknüpfte Tasks fertig').classes('text-xs text-grey-5')


def page() -> None:
    with frame('/requirements'):
        ui.label('Anforderungen / Scope').classes('kontor-title text-xl')
        content()
