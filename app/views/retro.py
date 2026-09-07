"""Retrospektive: Notizen sammeln, voten, Action-Items nachhalten."""
from __future__ import annotations

from nicegui import ui

from components import avatar, frame, resolve_sprint
from store import RETRO_CATEGORIES, ActionItem, RetroNote, store

_sel = {'sprint': None}
CAT_COLOR = {'gut': 'positive', 'schlecht': 'negative', 'idee': 'primary'}


def _current():
    return resolve_sprint(_sel['sprint'])


def _add_note(sid: str, category: str) -> None:
    with ui.dialog() as d, ui.card().classes('w-96 gap-2'):
        ui.label(RETRO_CATEGORIES[category]).classes('font-bold')
        txt = ui.textarea('Notiz').props('outlined dense autogrow').classes('w-full')
        author = ui.select({'': '– anonym –', **{m.id: m.name for m in store.active_members}},
                           label='von', value='').props('outlined dense').classes('w-full')

        def save() -> None:
            if txt.value.strip():
                store.add('retro_notes', RetroNote, project_id=store.pid, sprint_id=sid, category=category,
                          text=txt.value.strip(), author_id=author.value or None)
            d.close()
            content.refresh()
        with ui.row().classes('w-full justify-end'):
            ui.button('Abbrechen', on_click=d.close).props('flat')
            ui.button('Hinzufuegen', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    if not store.p_sprints():
        ui.label('Kein Sprint vorhanden.').classes('text-grey-6')
        return
    sp = _current()
    with ui.row().classes('w-full items-center gap-2'):
        ui.select({s.id: s.name for s in store.p_sprints()}, value=sp.id,
                  on_change=lambda e: (_sel.update(sprint=e.value), content.refresh())) \
            .props('outlined dense').classes('w-64')

    notes = [n for n in store.p_retro_notes() if n.sprint_id == sp.id]
    with ui.row().classes('w-full gap-3 items-start no-wrap flex-wrap'):
        for cat, title in RETRO_CATEGORIES.items():
            with ui.card().classes('grow min-w-[16rem] gap-2'):
                with ui.row().classes('w-full items-center'):
                    ui.label(title).classes(f'text-sm font-bold text-{CAT_COLOR[cat]}')
                    ui.space()
                    ui.button(icon='add', on_click=lambda c=cat: _add_note(sp.id, c)).props('flat dense size=sm')
                col_notes = sorted([n for n in notes if n.category == cat], key=lambda n: -n.votes)
                if not col_notes:
                    ui.label('—').classes('text-xs text-grey-5')
                for n in col_notes:
                    with ui.row().classes('w-full items-center gap-1 no-wrap border-t border-grey-2 py-1'):
                        ui.button(f'▲ {n.votes}', on_click=lambda n=n: (store.update(n, votes=n.votes + 1),
                                                                       content.refresh())) \
                            .props('flat dense size=sm').classes('shrink-0')
                        ui.label(n.text).classes('text-sm grow')
                        if n.author_id:
                            avatar(store.member(n.author_id), '18px')
                        ui.button(icon='close', on_click=lambda n=n: (store.remove('retro_notes', n.id),
                                                                     content.refresh())) \
                            .props('flat dense size=sm color=grey-5')

    # -- Action Items -------------------------------------------------
    with ui.card().classes('w-full gap-1'):
        with ui.row().classes('w-full items-center'):
            ui.label('Action-Items').classes('text-sm font-bold')
            ui.space()
            new = ui.input(placeholder='Neues Action-Item …').props('outlined dense').classes('w-72')
            owner = ui.select({'': '– wer? –', **{m.id: m.name for m in store.active_members}},
                              value='').props('outlined dense').classes('w-40')

            def add_ai() -> None:
                if new.value.strip():
                    store.add('action_items', ActionItem, project_id=store.pid, text=new.value.strip(),
                              owner_id=owner.value or None, sprint_id=sp.id)
                    new.value = ''
                    content.refresh()
            ui.button(icon='add', on_click=add_ai).props('flat dense')

        items = [a for a in store.p_action_items() if a.sprint_id == sp.id]
        open_items = [a for a in store.p_action_items() if not a.done]
        if not items:
            ui.label('—').classes('text-xs text-grey-5')
        for a in items:
            with ui.row().classes('w-full items-center gap-2 no-wrap border-t border-grey-2 py-1'):
                ui.checkbox(value=a.done, on_change=lambda e, a=a: (store.update(a, done=e.value),
                                                                   content.refresh()))
                ui.label(a.text).classes('text-sm grow ' + ('line-through text-grey-5' if a.done else ''))
                if a.owner_id:
                    avatar(store.member(a.owner_id), '20px')
                ui.button(icon='delete', on_click=lambda a=a: (store.remove('action_items', a.id),
                                                              content.refresh())) \
                    .props('flat dense size=sm color=grey-5')
        ui.label(f'{len(open_items)} offene Action-Items in diesem Projekt (sprintuebergreifend)') \
            .classes('text-xs text-grey-5')


def page() -> None:
    with frame('/retro'):
        ui.label('Retrospektive').classes('kontor-title text-xl')
        content()
