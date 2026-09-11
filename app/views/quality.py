"""Qualität & Bugs – Fehlerregister getrennt vom Backlog, mit Qualitäts-KPIs."""
from __future__ import annotations

from nicegui import ui

from components import avatar, chart_opts, frame, stat_tile
from store import BUG_SEVERITY, BUG_STATUS, Bug, store, today_iso

SEV_COLOR = {'kritisch': '#a63a3a', 'hoch': '#cf8a2e', 'mittel': '#5b8ca3', 'niedrig': '#8ba1a8'}
STATUS_COLOR = {'offen': 'negative', 'in_arbeit': 'warning', 'behoben': 'info',
                'verifiziert': 'positive', 'wontfix': 'grey-5'}
_flt = {'status': 'aktiv'}


def _form(existing=None) -> None:
    is_new = existing is None
    members = {'': '– niemand –', **{m.id: m.name for m in store.active_members}}
    envs = {e.name: e.name for e in store.p_environments()} or {'test': 'test', 'prod': 'prod'}
    with ui.dialog() as d, ui.card().classes('w-[32rem] gap-2'):
        ui.label('Neuer Bug' if is_new else 'Bug bearbeiten').classes('kontor-title text-lg')
        title = ui.input('Titel', value='' if is_new else existing.title).props('outlined dense').classes('w-full')
        desc = ui.textarea('Beschreibung / Repro', value='' if is_new else existing.description) \
            .props('outlined dense autogrow').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            sev = ui.select(BUG_SEVERITY, label='Schwere', value='mittel' if is_new else existing.severity) \
                .props('outlined dense').classes('grow')
            status = ui.select(BUG_STATUS, label='Status', value='offen' if is_new else existing.status) \
                .props('outlined dense').classes('grow')
        with ui.row().classes('w-full gap-2'):
            env = ui.select(envs, label='gefunden in', value=(list(envs)[0] if is_new else existing.environment)) \
                .props('outlined dense').classes('grow')
            comp = ui.input('Komponente', value='' if is_new else existing.component) \
                .props('outlined dense').classes('grow')
        with ui.row().classes('w-full gap-2'):
            rep = ui.select(members, label='gemeldet von',
                            value='' if is_new or not existing.reporter_id else existing.reporter_id) \
                .props('outlined dense').classes('grow')
            asg = ui.select(members, label='zugewiesen',
                            value='' if is_new or not existing.assignee_id else existing.assignee_id) \
                .props('outlined dense').classes('grow')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), description=desc.value or '', severity=sev.value,
                        status=status.value, environment=env.value, component=comp.value or '',
                        reporter_id=rep.value or None, assignee_id=asg.value or None)
            if is_new:
                store.add('bugs', Bug, project_id=store.pid, **data)
            else:
                if existing.status in ('behoben', 'verifiziert') and status.value in ('offen', 'in_arbeit'):
                    data['reopened'] = existing.reopened + 1
                data['resolved_at'] = today_iso() if status.value in ('behoben', 'verifiziert') else None
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('bugs', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    q = store.quality_stats()
    with ui.row().classes('w-full items-center'):
        ui.label('Qualität').classes('kontor-title text-lg')
        ui.space()
        ui.button('Neuer Bug', icon='add', on_click=_form).props('no-caps')

    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(q['open'], 'offene Bugs', 'text-negative' if q['open'] else 'text-positive')
        stat_tile(q['critical_open'], 'kritisch/hoch offen', 'text-negative' if q['critical_open'] else 'text-grey-5')
        stat_tile(q['escaped'], 'in Prod gefunden', 'text-negative' if q['escaped'] else 'text-grey-5')
        stat_tile(q['reopened'], 'Wiedereröffnungen', 'text-warning' if q['reopened'] else 'text-grey-5')

    with ui.card().classes('w-full'):
        ui.label('Offene Bugs nach Schwere').classes('kontor-title text-sm')
        ui.echart(chart_opts({
            'grid': {'left': 40, 'right': 15, 'top': 15, 'bottom': 25},
            'xAxis': {'type': 'category', 'data': [BUG_SEVERITY[s] for s in BUG_SEVERITY]},
            'yAxis': {'type': 'value'},
            'series': [{'type': 'bar', 'data': [
                {'value': q['by_sev'][s], 'itemStyle': {'color': SEV_COLOR[s]}} for s in BUG_SEVERITY]}],
        })).classes('w-full h-48')

    bugs = store.p_bugs()
    with ui.row().classes('items-center gap-2'):
        ui.label('Liste').classes('kontor-title text-sm')
        ui.toggle({'aktiv': 'offen/in Arbeit', 'alle': 'alle'}, value=_flt['status'],
                  on_change=lambda e: (_flt.update(status=e.value), content.refresh())).props('dense')
    shown = bugs if _flt['status'] == 'alle' else [b for b in bugs if b.status in ('offen', 'in_arbeit')]
    order = list(BUG_SEVERITY)
    for b in sorted(shown, key=lambda b: (order.index(b.severity), b.created_at)):
        with ui.row().classes('w-full items-center gap-2 no-wrap border-b border-grey-2 py-1'):
            ui.element('div').style(f'width:8px;height:8px;border-radius:9999px;flex:none;'
                                    f'background:{SEV_COLOR[b.severity]}').tooltip(BUG_SEVERITY[b.severity])
            ui.label(b.title).classes('text-sm grow truncate')
            if b.component:
                ui.badge(b.component).props('outline color=grey-7').classes('text-[10px]')
            ui.badge(b.environment).props('color=grey-6').classes('text-[10px]')
            if b.reopened:
                ui.label(f'↻{b.reopened}').classes('text-xs text-warning')
            avatar(store.member(b.assignee_id), '20px')
            ui.badge(BUG_STATUS[b.status]).props(f'color={STATUS_COLOR[b.status]}')
            ui.button(icon='edit', on_click=lambda b=b: _form(b)).props('flat dense size=sm')


def page() -> None:
    with frame('/quality'):
        ui.label('Qualität & Bugs').classes('kontor-title text-xl')
        content()
