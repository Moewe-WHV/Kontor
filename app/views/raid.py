"""Risiken & Entscheidungen – RAID-Log light + Decision Records."""
from __future__ import annotations

from nicegui import ui

from components import avatar, frame, stat_tile
from store import (Decision, RISK_LEVEL, RISK_STATUS, Risk, store, today_iso)

LEVELS = list(RISK_LEVEL)
STATUS_COLOR = {'offen': 'negative', 'beobachtung': 'warning', 'eingetreten': 'purple', 'geschlossen': 'positive'}


def _score_color(score: int) -> str:
    return '#ef4444' if score >= 6 else '#f59e0b' if score >= 3 else '#10b981'


def _risk_form(existing=None) -> None:
    is_new = existing is None
    members = {'': '– niemand –', **{m.id: m.name for m in store.active_members}}
    with ui.dialog() as d, ui.card().classes('w-[32rem] gap-2'):
        ui.label('Risiko' if is_new else 'Risiko bearbeiten').classes('text-lg font-bold')
        title = ui.input('Titel', value='' if is_new else existing.title).props('outlined dense').classes('w-full')
        desc = ui.textarea('Beschreibung', value='' if is_new else existing.description) \
            .props('outlined dense autogrow').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            likel = ui.select(LEVELS, label='Eintritt',
                              value='mittel' if is_new else existing.likelihood).props('outlined dense').classes('grow')
            impact = ui.select(LEVELS, label='Auswirkung',
                               value='mittel' if is_new else existing.impact).props('outlined dense').classes('grow')
            status = ui.select(RISK_STATUS, label='Status',
                               value='offen' if is_new else existing.status).props('outlined dense').classes('grow')
        mit = ui.textarea('Gegenmassnahme', value='' if is_new else existing.mitigation) \
            .props('outlined dense autogrow').classes('w-full')
        owner = ui.select(members, label='Owner',
                          value='' if is_new or not existing.owner_id else existing.owner_id) \
            .props('outlined dense').classes('w-full')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), description=desc.value or '',
                        likelihood=likel.value, impact=impact.value, status=status.value,
                        mitigation=mit.value or '', owner_id=owner.value or None)
            if is_new:
                store.add('risks', Risk, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('risks', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


def _decision_form(existing=None) -> None:
    is_new = existing is None
    members = {'': '– niemand –', **{m.id: m.name for m in store.active_members}}
    with ui.dialog() as d, ui.card().classes('w-[32rem] gap-2'):
        ui.label('Entscheidung' if is_new else 'Entscheidung bearbeiten').classes('text-lg font-bold')
        title = ui.input('Titel', value='' if is_new else existing.title).props('outlined dense').classes('w-full')
        dt = ui.input('Datum', value=today_iso() if is_new else existing.date) \
            .props('outlined dense type=date').classes('w-full')
        context = ui.textarea('Kontext / Problem', value='' if is_new else existing.context) \
            .props('outlined dense autogrow').classes('w-full')
        decision = ui.textarea('Entscheidung', value='' if is_new else existing.decision) \
            .props('outlined dense autogrow').classes('w-full')
        cons = ui.textarea('Konsequenzen / Trade-offs', value='' if is_new else existing.consequences) \
            .props('outlined dense autogrow').classes('w-full')
        owner = ui.select(members, label='verantwortlich',
                          value='' if is_new or not existing.owner_id else existing.owner_id) \
            .props('outlined dense').classes('w-full')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), date=dt.value, context=context.value or '',
                        decision=decision.value or '', consequences=cons.value or '',
                        owner_id=owner.value or None)
            if is_new:
                store.add('decisions', Decision, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('decisions', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    risks = sorted(store.p_risks(), key=lambda r: (r.status == 'geschlossen', -r.score))
    active_risks = [r for r in risks if r.status != 'geschlossen']
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(active_risks), 'aktive Risiken', 'text-negative' if active_risks else 'text-grey-5')
        stat_tile(len([r for r in active_risks if r.score >= 6]), 'davon hoch', 'text-negative')
        stat_tile(len(store.p_decisions()), 'Entscheidungen')

    with ui.card().classes('w-full gap-1'):
        with ui.row().classes('w-full items-center'):
            ui.label('Risiken').classes('text-sm font-bold')
            ui.space()
            ui.button('Risiko', icon='add', on_click=_risk_form).props('no-caps size=sm')
        with ui.row().classes('w-full text-xs font-bold text-grey-6 px-1'):
            ui.label('Score').classes('w-12')
            ui.label('Risiko').classes('grow')
            ui.label('E×A').classes('w-16')
            ui.label('Status').classes('w-28')
            ui.label('Owner').classes('w-10')
        for r in risks:
            with ui.row().classes('w-full items-center gap-2 no-wrap border-t border-grey-2 py-1'):
                ui.label(str(r.score)).style(
                    f'width:26px;height:26px;border-radius:6px;flex:none;color:#fff;font-weight:700;'
                    f'display:flex;align-items:center;justify-content:center;background:{_score_color(r.score)}'
                ).tooltip(f'Eintritt × Auswirkung = {r.score}')
                with ui.column().classes('grow gap-0 min-w-0'):
                    ui.label(r.title).classes('text-sm font-medium truncate '
                                              + ('line-through text-grey-5' if r.status == 'geschlossen' else ''))
                    if r.mitigation:
                        ui.label('↳ ' + r.mitigation).classes('text-xs text-grey-6 truncate')
                ui.label(f'{r.likelihood[:1].upper()}×{r.impact[:1].upper()}').classes('text-xs text-grey-6 w-16')
                ui.badge(RISK_STATUS[r.status]).props(f'color={STATUS_COLOR.get(r.status, "grey")}').classes('w-28')
                avatar(store.member(r.owner_id), '20px')
                ui.button(icon='edit', on_click=lambda r=r: _risk_form(r)).props('flat dense size=sm')

    with ui.card().classes('w-full gap-1'):
        with ui.row().classes('w-full items-center'):
            ui.label('Entscheidungs-Log').classes('text-sm font-bold')
            ui.space()
            ui.button('Entscheidung', icon='add', on_click=_decision_form).props('no-caps size=sm')
        for dec in sorted(store.p_decisions(), key=lambda x: x.date, reverse=True):
            with ui.expansion().classes('w-full border border-grey-2 rounded') as exp:
                with exp.add_slot('header'):
                    with ui.row().classes('w-full items-center gap-2 no-wrap'):
                        ui.label(dec.date).classes('text-xs text-grey-5 w-24')
                        ui.label(dec.title).classes('text-sm font-medium grow truncate')
                        avatar(store.member(dec.owner_id), '20px')
                with ui.column().classes('gap-1 p-2'):
                    for lbl, val in (('Kontext', dec.context), ('Entscheidung', dec.decision),
                                     ('Konsequenzen', dec.consequences)):
                        if val:
                            ui.label(lbl).classes('text-xs font-bold text-grey-6')
                            ui.label(val).classes('text-sm mb-1')
                    ui.button('Bearbeiten', icon='edit', on_click=lambda dec=dec: _decision_form(dec)) \
                        .props('flat dense size=sm no-caps')


def page() -> None:
    with frame('/raid'):
        ui.label('Risiken & Entscheidungen').classes('kontor-title text-xl')
        content()
