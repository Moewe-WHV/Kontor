"""Incidents – Produktionsstörungen inkl. Postmortem & Maßnahmen."""
from __future__ import annotations

from datetime import date

from nicegui import ui

from components import avatar, frame, stat_tile
from store import INCIDENT_SEV, INCIDENT_STATUS, Incident, store, today_iso

SEV_COLOR = {'sev1': 'negative', 'sev2': 'warning', 'sev3': 'info'}
STATUS_COLOR = {'offen': 'negative', 'untersuchung': 'warning', 'behoben': 'info',
                'postmortem': 'secondary', 'geschlossen': 'positive'}


def _form(existing=None) -> None:
    is_new = existing is None
    members = {'': '– niemand –', **{m.id: m.name for m in store.active_members}}
    with ui.dialog() as d, ui.card().classes('w-[34rem] gap-2'):
        ui.label('Neuer Incident' if is_new else 'Incident bearbeiten').classes('kontor-title text-lg')
        title = ui.input('Titel', value='' if is_new else existing.title).props('outlined dense').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            sev = ui.select(INCIDENT_SEV, label='Schweregrad', value='sev2' if is_new else existing.severity) \
                .props('outlined dense').classes('grow')
            status = ui.select(INCIDENT_STATUS, label='Status', value='offen' if is_new else existing.status) \
                .props('outlined dense').classes('grow')
            lead = ui.select(members, label='Incident-Lead',
                             value='' if is_new or not existing.lead_id else existing.lead_id) \
                .props('outlined dense').classes('grow')
        with ui.row().classes('w-full gap-2'):
            start = ui.input('Beginn', value=today_iso() if is_new else existing.started_at) \
                .props('outlined dense type=date').classes('grow')
            end = ui.input('Behoben', value='' if is_new or not existing.resolved_at else existing.resolved_at) \
                .props('outlined dense type=date').classes('grow')
        impact = ui.textarea('Auswirkung', value='' if is_new else existing.impact) \
            .props('outlined dense autogrow').classes('w-full')
        cause = ui.textarea('Ursache', value='' if is_new else existing.cause) \
            .props('outlined dense autogrow').classes('w-full')
        pm = ui.textarea('Postmortem / Zusammenfassung', value='' if is_new else existing.postmortem) \
            .props('outlined dense autogrow').classes('w-full')
        actions = ui.textarea('Folgemaßnahmen', value='' if is_new else existing.actions) \
            .props('outlined dense autogrow').classes('w-full')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), severity=sev.value, status=status.value,
                        started_at=start.value, resolved_at=end.value or None,
                        impact=impact.value or '', cause=cause.value or '',
                        postmortem=pm.value or '', actions=actions.value or '', lead_id=lead.value or None)
            if is_new:
                store.add('incidents', Incident, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('incidents', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    inc = store.p_incidents()
    opn = store.open_incidents()
    with ui.row().classes('w-full items-center'):
        ui.label('Incidents').classes('kontor-title text-lg')
        ui.space()
        ui.button('Neuer Incident', icon='add', on_click=_form).props('no-caps')

    year = date.today().year
    ytd = [i for i in inc if i.started_at[:4] == str(year)]
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(opn), 'aktiv', 'text-negative' if opn else 'text-positive')
        stat_tile(len([i for i in opn if i.severity == 'sev1']), 'davon SEV1', 'text-negative')
        stat_tile(len(ytd), f'gesamt {year}')
        pend_pm = [i for i in inc if i.status == 'behoben' and not i.postmortem]
        stat_tile(len(pend_pm), 'Postmortem offen', 'text-warning' if pend_pm else 'text-grey-5')

    for i in inc:
        with ui.card().classes('w-full gap-1'):
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.badge(INCIDENT_SEV[i.severity].split(' ')[0]).props(f'color={SEV_COLOR[i.severity]}')
                ui.label(i.title).classes('text-sm font-medium grow')
                ui.badge(INCIDENT_STATUS[i.status]).props(f'color={STATUS_COLOR[i.status]}')
                avatar(store.member(i.lead_id), '20px')
                ui.button(icon='edit', on_click=lambda i=i: _form(i)).props('flat dense size=sm')
            with ui.row().classes('gap-3 text-xs text-grey-6'):
                ui.label(f'Beginn {i.started_at}')
                if i.resolved_at:
                    ui.label(f'behoben {i.resolved_at}')
            if i.impact:
                ui.label('Auswirkung: ' + i.impact).classes('text-xs')
            if i.cause:
                ui.label('Ursache: ' + i.cause).classes('text-xs')
            if i.actions:
                ui.label('Maßnahmen: ' + i.actions).classes('text-xs text-primary whitespace-pre-line')


def page() -> None:
    with frame('/incidents'):
        ui.label('Incidents & Postmortems').classes('kontor-title text-xl')
        content()
