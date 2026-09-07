"""Meilensteine – Schlüsseltermine pro Projekt."""
from __future__ import annotations

from datetime import date

from nicegui import ui

from components import frame, stat_tile
from store import MILESTONE_STATUS, Milestone, store, today_iso

STATUS_COLOR = {'offen': 'primary', 'erreicht': 'positive', 'verpasst': 'negative'}


def _form(existing=None) -> None:
    is_new = existing is None
    with ui.dialog() as d, ui.card().classes('w-96 gap-2'):
        ui.label('Neuer Meilenstein' if is_new else 'Bearbeiten').classes('kontor-title text-lg')
        title = ui.input('Titel', value='' if is_new else existing.title).props('outlined dense').classes('w-full')
        due = ui.input('Termin', value=today_iso() if is_new else existing.due) \
            .props('outlined dense type=date').classes('w-full')
        status = ui.select(MILESTONE_STATUS, label='Status',
                           value='offen' if is_new else existing.status).props('outlined dense').classes('w-full')
        desc = ui.textarea('Beschreibung', value='' if is_new else existing.description) \
            .props('outlined dense autogrow').classes('w-full')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), due=due.value, status=status.value,
                        description=desc.value or '')
            if is_new:
                store.add('milestones', Milestone, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('milestones', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    ms = store.p_milestones()
    today = date.today()
    with ui.row().classes('w-full items-center'):
        ui.label('Meilensteine').classes('kontor-title text-lg')
        ui.space()
        ui.button('Neuer Meilenstein', icon='add', on_click=_form).props('no-caps')

    overdue = [m for m in ms if m.status == 'offen' and m.due and date.fromisoformat(m.due) < today]
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len([m for m in ms if m.status == 'offen']), 'offen')
        stat_tile(len(overdue), 'überfällig', 'text-negative' if overdue else 'text-grey-5')
        stat_tile(len([m for m in ms if m.status == 'erreicht']), 'erreicht', 'text-positive')

    with ui.timeline(side='right'):
        for m in ms:
            d = date.fromisoformat(m.due) if m.due else None
            days = (d - today).days if d else None
            if m.status == 'erreicht':
                icon, col = 'check_circle', 'positive'
            elif days is not None and days < 0:
                icon, col = 'error', 'negative'
            elif days is not None and days <= 14:
                icon, col = 'schedule', 'warning'
            else:
                icon, col = 'outlined_flag', 'primary'
            sub = m.due
            if days is not None and m.status == 'offen':
                sub += f'  ·  {"überfällig" if days < 0 else f"in {days} Tagen"}'
            with ui.timeline_entry(m.description or '', title=m.title, subtitle=sub, icon=icon, color=col):
                with ui.row().classes('gap-1 mt-1'):
                    for st, lbl in MILESTONE_STATUS.items():
                        ui.button(lbl, on_click=lambda m=m, st=st: (store.update(m, status=st), content.refresh())) \
                            .props('flat dense size=sm no-caps' + ('' if m.status != st else ' color=primary'))
                    ui.button(icon='edit', on_click=lambda m=m: _form(m)).props('flat dense size=sm')


def page() -> None:
    with frame('/milestones'):
        ui.label('Meilensteine').classes('kontor-title text-xl')
        content()
