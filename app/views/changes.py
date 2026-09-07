"""Änderungsanträge – Scope-Änderungen mit Auswirkung nachhalten."""
from __future__ import annotations

from nicegui import ui

from components import frame, stat_tile
from store import CHANGE_STATUS, ChangeRequest, store, today_iso

STATUS_COLOR = {'offen': 'warning', 'angenommen': 'positive', 'abgelehnt': 'negative'}


def _form(existing=None) -> None:
    is_new = existing is None
    with ui.dialog() as d, ui.card().classes('w-[32rem] gap-2'):
        ui.label('Neuer Änderungsantrag' if is_new else 'Bearbeiten').classes('kontor-title text-lg')
        title = ui.input('Titel', value='' if is_new else existing.title).props('outlined dense').classes('w-full')
        desc = ui.textarea('Beschreibung / Begründung', value='' if is_new else existing.description) \
            .props('outlined dense autogrow').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            hrs = ui.number('Mehraufwand (h)', value=0 if is_new else existing.impact_hours,
                            min=0, step=1, format='%g').props('outlined dense').classes('grow')
            days = ui.number('Termin-Verzug (Tage)', value=0 if is_new else existing.impact_days,
                             min=0, step=1).props('outlined dense').classes('grow')
        with ui.row().classes('w-full gap-2'):
            by = ui.input('Beantragt von', value='' if is_new else existing.requested_by) \
                .props('outlined dense').classes('grow')
            dt = ui.input('Datum', value=today_iso() if is_new else existing.date) \
                .props('outlined dense type=date').classes('grow')
            status = ui.select(CHANGE_STATUS, label='Status',
                               value='offen' if is_new else existing.status).props('outlined dense').classes('grow')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), description=desc.value or '',
                        impact_hours=float(hrs.value or 0), impact_days=int(days.value or 0),
                        requested_by=by.value or '', date=dt.value, status=status.value)
            if is_new:
                store.add('change_requests', ChangeRequest, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('change_requests', existing.id), d.close(),
                                            content.refresh())).props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    crs = sorted(store.p_changes(), key=lambda c: c.date, reverse=True)
    with ui.row().classes('w-full items-center'):
        ui.label('Änderungsanträge').classes('kontor-title text-lg')
        ui.space()
        ui.button('Neuer Antrag', icon='add', on_click=_form).props('no-caps')

    accepted = [c for c in crs if c.status == 'angenommen']
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len([c for c in crs if c.status == 'offen']), 'offen', 'text-warning')
        stat_tile(f'{sum(c.impact_hours for c in accepted):g} h', 'genehmigter Mehraufwand', 'text-primary')
        stat_tile(f'{sum(c.impact_days for c in accepted)} T', 'genehmigter Verzug',
                  'text-negative' if any(c.impact_days for c in accepted) else 'text-grey-5')

    for c in crs:
        with ui.card().classes('w-full gap-1'):
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.label(c.title).classes('text-sm font-medium grow')
                ui.badge(CHANGE_STATUS[c.status]).props(f'color={STATUS_COLOR[c.status]}')
                ui.button(icon='edit', on_click=lambda c=c: _form(c)).props('flat dense size=sm')
            if c.description:
                ui.label(c.description).classes('text-xs text-grey-6')
            with ui.row().classes('gap-4 text-xs text-grey-6'):
                ui.label(f'+{c.impact_hours:g} h')
                ui.label(f'+{c.impact_days} Tage Termin')
                ui.label(f'von {c.requested_by or "?"}')
                ui.label(c.date)
                if c.status == 'offen':
                    ui.button('annehmen', on_click=lambda c=c: (store.update(c, status='angenommen'),
                                                               content.refresh())) \
                        .props('flat dense size=sm no-caps color=positive')
                    ui.button('ablehnen', on_click=lambda c=c: (store.update(c, status='abgelehnt'),
                                                               content.refresh())) \
                        .props('flat dense size=sm no-caps color=negative')


def page() -> None:
    with frame('/changes'):
        ui.label('Änderungsmanagement').classes('kontor-title text-xl')
        content()
