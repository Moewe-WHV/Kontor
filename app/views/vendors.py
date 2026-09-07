"""Lieferanten & Lizenzen – externe Dienste, Kosten, Verlängerungstermine."""
from __future__ import annotations

from datetime import date

from nicegui import ui

from components import avatar, frame, stat_tile
from store import COST_CYCLES, VENDOR_KINDS, Vendor, store


def _eur(x: float) -> str:
    return f'{x:,.0f} €'.replace(',', '.')


def _form(existing=None) -> None:
    is_new = existing is None
    members = {'': '– niemand –', **{m.id: m.name for m in store.active_members}}
    with ui.dialog() as d, ui.card().classes('w-[32rem] gap-2'):
        ui.label('Neuer Eintrag' if is_new else 'Bearbeiten').classes('kontor-title text-lg')
        with ui.row().classes('w-full gap-2'):
            name = ui.input('Name', value='' if is_new else existing.name) \
                .props('outlined dense').classes('grow')
            kind = ui.select(VENDOR_KINDS, label='Art', value='dienst' if is_new else existing.kind) \
                .props('outlined dense').classes('w-40')
        with ui.row().classes('w-full gap-2'):
            cost = ui.number('Kosten (EUR)', value=0 if is_new else existing.cost, min=0, step=10, format='%g') \
                .props('outlined dense').classes('grow')
            cycle = ui.select(COST_CYCLES, label='Zyklus', value='monatlich' if is_new else existing.cost_cycle) \
                .props('outlined dense').classes('grow')
            renewal = ui.input('Verlängerung/Ablauf', value='' if is_new else existing.renewal) \
                .props('outlined dense type=date').classes('w-40')
        with ui.row().classes('w-full gap-2'):
            owner = ui.select(members, label='Vertrags-Owner',
                              value='' if is_new or not existing.owner_id else existing.owner_id) \
                .props('outlined dense').classes('grow')
            active = ui.checkbox('aktiv', value=True if is_new else existing.active)
        note = ui.input('Notiz', value='' if is_new else existing.note).props('outlined dense').classes('w-full')

        def save() -> None:
            if not name.value.strip():
                ui.notify('Name fehlt', type='warning')
                return
            data = dict(name=name.value.strip(), kind=kind.value, cost=float(cost.value or 0),
                        cost_cycle=cycle.value, renewal=renewal.value or '',
                        owner_id=owner.value or None, active=active.value, note=note.value or '')
            if is_new:
                store.add('vendors', Vendor, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('vendors', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    vs = store.p_vendors()
    today = date.today()
    with ui.row().classes('w-full items-center'):
        ui.label('Lieferanten & Lizenzen').classes('kontor-title text-lg')
        ui.space()
        ui.button('Neuer Eintrag', icon='add', on_click=_form).props('no-caps')

    yearly = store.vendor_cost_yearly()
    soon = [v for v in vs if v.active and v.renewal
            and 0 <= (date.fromisoformat(v.renewal) - today).days <= 60]
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(_eur(yearly), 'laufende Kosten / Jahr')
        stat_tile(_eur(yearly / 12), 'ø / Monat')
        stat_tile(len([v for v in vs if v.active]), 'aktive Verträge')
        stat_tile(len(soon), 'Verlängerung < 60 T', 'text-warning' if soon else 'text-grey-5')

    for v in sorted(vs, key=lambda v: (not v.active, v.name.lower())):
        with ui.row().classes('w-full items-center gap-2 no-wrap border-b border-grey-2 py-1'
                              + ('' if v.active else ' opacity-50')):
            ui.label(v.name).classes('text-sm font-medium w-52 truncate')
            ui.badge(VENDOR_KINDS[v.kind]).props('outline color=grey-7')
            ui.label(f'{v.cost:g} € {v.cost_cycle}').classes('text-xs text-grey-6 w-40')
            ui.label(_eur(v.yearly) + '/J').classes('text-xs text-grey-7 w-24 text-right')
            if v.renewal:
                dd = (date.fromisoformat(v.renewal) - today).days
                ui.label(f'⟳ {v.renewal}').classes('text-xs w-28 ' +
                                                   ('text-warning' if 0 <= dd <= 60 else 'text-grey-5'))
            avatar(store.member(v.owner_id), '18px')
            ui.space()
            ui.button(icon='edit', on_click=lambda v=v: _form(v)).props('flat dense size=sm')


def page() -> None:
    with frame('/vendors'):
        ui.label('Lieferanten & Lizenzen').classes('kontor-title text-xl')
        content()
