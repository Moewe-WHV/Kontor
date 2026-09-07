"""Speicher – Ideen sammeln, bewerten, in Tasks ueberfuehren."""
from __future__ import annotations

from nicegui import ui

from components import avatar, frame, stat_tile
from store import IDEA_STATUS, Idea, store

STATUS_COLOR = {'neu': 'grey-6', 'geprueft': 'info', 'uebernommen': 'positive', 'abgelehnt': 'negative'}


def _form(existing=None) -> None:
    is_new = existing is None
    with ui.dialog() as d, ui.card().classes('w-[30rem] gap-2'):
        ui.label('Neue Idee' if is_new else 'Idee bearbeiten').classes('kontor-title text-lg')
        title = ui.input('Titel', value='' if is_new else existing.title).props('outlined dense').classes('w-full')
        desc = ui.textarea('Beschreibung', value='' if is_new else existing.description) \
            .props('outlined dense autogrow').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            author = ui.select({'': '– anonym –', **{m.id: m.name for m in store.active_members}},
                               label='von', value='' if is_new or not existing.author_id else existing.author_id) \
                .props('outlined dense').classes('grow')
            status = ui.select(IDEA_STATUS, label='Status',
                               value='neu' if is_new else existing.status).props('outlined dense').classes('grow')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), description=desc.value or '',
                        author_id=author.value or None, status=status.value)
            if is_new:
                store.add('ideas', Idea, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('ideas', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


def _to_task(idea) -> None:
    store.add_task(project_id=idea.project_id, title=idea.title,
                   description=idea.description, status='backlog', priority='mittel')
    store.update(idea, status='uebernommen')
    ui.notify('Als Task im Backlog angelegt', type='positive')
    content.refresh()


@ui.refreshable
def content() -> None:
    ideas = sorted(store.p_ideas(), key=lambda i: (i.status in ('uebernommen', 'abgelehnt'), -i.votes))
    with ui.row().classes('w-full items-center'):
        ui.label('Ideen').classes('kontor-title text-lg')
        ui.space()
        ui.button('Idee einwerfen', icon='add', on_click=_form).props('no-caps')
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len([i for i in ideas if i.status == 'neu']), 'neu')
        stat_tile(len([i for i in ideas if i.status == 'geprueft']), 'in Pruefung', 'text-info')
        stat_tile(len([i for i in ideas if i.status == 'uebernommen']), 'uebernommen', 'text-positive')

    for i in ideas:
        faded = i.status in ('uebernommen', 'abgelehnt')
        with ui.card().classes('w-full gap-1' + (' opacity-60' if faded else '')):
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.button(f'▲ {i.votes}', on_click=lambda i=i: (store.update(i, votes=i.votes + 1),
                                                               content.refresh())) \
                    .props('flat dense size=sm')
                ui.label(i.title).classes('text-sm font-medium grow')
                ui.badge(IDEA_STATUS[i.status]).props(f'color={STATUS_COLOR[i.status]}')
                if i.author_id:
                    avatar(store.member(i.author_id), '20px')
                if i.status != 'uebernommen':
                    ui.button(icon='playlist_add', on_click=lambda i=i: _to_task(i)) \
                        .props('flat dense size=sm').tooltip('→ Task im Backlog')
                ui.button(icon='edit', on_click=lambda i=i: _form(i)).props('flat dense size=sm')
            if i.description:
                ui.label(i.description).classes('text-xs text-grey-6')


def page() -> None:
    with frame('/ideas'):
        ui.label('Speicher – Ideen').classes('kontor-title text-xl')
        content()
