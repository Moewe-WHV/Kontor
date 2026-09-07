"""Dokumente – zentraler Index für Specs, Verträge, Designs, Betriebsdoku."""
from __future__ import annotations

from nicegui import ui

from components import avatar, frame, stat_tile
from store import DOC_CATEGORIES, Document, store, today_iso

CAT_COLOR = {'spec': 'primary', 'design': 'secondary', 'vertrag': 'negative',
             'betrieb': 'info', 'bericht': 'warning', 'sonstiges': 'grey-6'}
_flt = {'cat': None}


def _form(existing=None) -> None:
    is_new = existing is None
    members = {'': '– niemand –', **{m.id: m.name for m in store.active_members}}
    with ui.dialog() as d, ui.card().classes('w-[32rem] gap-2'):
        ui.label('Neues Dokument' if is_new else 'Dokument bearbeiten').classes('kontor-title text-lg')
        title = ui.input('Titel', value='' if is_new else existing.title).props('outlined dense').classes('w-full')
        url = ui.input('Link', value='' if is_new else existing.url).props('outlined dense').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            cat = ui.select(DOC_CATEGORIES, label='Kategorie', value='spec' if is_new else existing.category) \
                .props('outlined dense').classes('grow')
            owner = ui.select(members, label='verantwortlich',
                              value='' if is_new or not existing.owner_id else existing.owner_id) \
                .props('outlined dense').classes('grow')
            upd = ui.input('Stand', value=today_iso() if is_new else existing.updated) \
                .props('outlined dense type=date').classes('w-40')
        note = ui.input('Notiz', value='' if is_new else existing.note).props('outlined dense').classes('w-full')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), url=url.value or '', category=cat.value,
                        owner_id=owner.value or None, updated=upd.value, note=note.value or '')
            if is_new:
                store.add('documents', Document, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('documents', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    docs = store.p_documents()
    with ui.row().classes('w-full items-center gap-2'):
        ui.label('Dokumente').classes('kontor-title text-lg')
        ui.select({None: 'alle Kategorien', **DOC_CATEGORIES}, value=_flt['cat'],
                  on_change=lambda e: (_flt.update(cat=e.value), content.refresh())) \
            .props('outlined dense').classes('w-48')
        ui.space()
        ui.button('Neues Dokument', icon='add', on_click=_form).props('no-caps')

    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(docs), 'gesamt')
        for c in ('spec', 'vertrag', 'betrieb'):
            stat_tile(len([x for x in docs if x.category == c]), DOC_CATEGORIES[c])

    shown = docs if not _flt['cat'] else [x for x in docs if x.category == _flt['cat']]
    for x in shown:
        with ui.row().classes('w-full items-center gap-2 no-wrap border-b border-grey-2 py-1'):
            ui.icon('description').classes('text-grey-5')
            (ui.link(x.title, x.url, new_tab=True) if x.url else ui.label(x.title)) \
                .classes('text-sm font-medium grow truncate')
            ui.badge(DOC_CATEGORIES[x.category]).props(f'color={CAT_COLOR[x.category]}')
            avatar(store.member(x.owner_id), '20px')
            ui.label(x.updated).classes('text-xs text-grey-5 w-24')
            ui.button(icon='edit', on_click=lambda x=x: _form(x)).props('flat dense size=sm')


def page() -> None:
    with frame('/documents'):
        ui.label('Dokumente').classes('kontor-title text-xl')
        content()
