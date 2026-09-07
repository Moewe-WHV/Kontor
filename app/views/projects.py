"""Projekte verwalten (Werft)."""
from __future__ import annotations

from nicegui import ui

from components import frame
from store import Project, store

_PALETTE = ['#1f4e5f', '#5b8ca3', '#3d7a5d', '#b5533a', '#cf8a2e', '#7a5c99', '#a63a3a', '#2f6f6f']


def _form(existing=None) -> None:
    is_new = existing is None
    with ui.dialog() as d, ui.card().classes('w-[32rem] gap-2'):
        ui.label('Neues Projekt' if is_new else 'Projekt bearbeiten').classes('kontor-title text-lg')
        with ui.row().classes('w-full gap-2'):
            name = ui.input('Name', value='' if is_new else existing.name) \
                .props('outlined dense').classes('grow')
            key = ui.input('Kuerzel', value='' if is_new else existing.key) \
                .props('outlined dense').classes('w-28')
        desc = ui.textarea('Beschreibung', value='' if is_new else existing.description) \
            .props('outlined dense autogrow').classes('w-full')
        color = ui.select(_PALETTE, label='Farbe',
                          value=_PALETTE[len(store.projects) % len(_PALETTE)] if is_new else existing.color) \
            .props('outlined dense').classes('w-full')
        dod = ui.textarea('Definition of Done (eine Zeile pro Kriterium)',
                          value='' if is_new else '\n'.join(existing.dod)) \
            .props('outlined dense autogrow').classes('w-full')
        archived = ui.checkbox('archiviert', value=False if is_new else existing.archived)

        def save() -> None:
            if not name.value.strip():
                ui.notify('Name fehlt', type='warning')
                return
            data = dict(name=name.value.strip(), key=key.value.strip().upper(),
                        description=desc.value or '', color=color.value,
                        dod=[x.strip() for x in (dod.value or '').splitlines() if x.strip()],
                        archived=archived.value)
            if is_new:
                p = store.add('projects', Project, **data)
                store.set_current_project(p.id)
            else:
                store.update(existing, **data)
            d.close()
            ui.navigate.reload()

        with ui.row().classes('w-full justify-between'):
            if not is_new and len(store.projects) > 1:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: _delete(existing, d)).props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


def _delete(project, dialog) -> None:
    with ui.dialog() as c, ui.card():
        ui.label(f'Projekt „{project.name}" mit allen Sprints, Tasks, Risiken … loeschen?')
        with ui.row():
            ui.button('Abbrechen', on_click=c.close).props('flat')

            def do() -> None:
                for lst in ('sprints', 'tasks', 'releases', 'risks', 'decisions', 'ideas',
                            'retro_notes', 'action_items', 'moods', 'epics', 'milestones',
                            'objectives', 'stakeholders', 'change_requests', 'requirements',
                            'bugs', 'environments', 'deployments', 'incidents', 'meetings',
                            'documents', 'vendors', 'raci_areas', 'lessons'):
                    setattr(store, lst, [x for x in getattr(store, lst)
                                         if getattr(x, 'project_id', None) != project.id])
                store.remove('projects', project.id)
                store.current_project_id = store.projects[0].id if store.projects else None
                store.save()
                ui.navigate.reload()

            ui.button('Loeschen', color='negative', on_click=do)
    c.open()


@ui.refreshable
def content() -> None:
    with ui.row().classes('w-full items-center'):
        ui.label('Projekte').classes('kontor-title text-lg')
        ui.space()
        ui.button('Neues Projekt', icon='add', on_click=_form).props('no-caps')

    for p in store.projects:
        sprints = store.p_sprints(p.id)
        tasks = store.p_tasks(p.id)
        with ui.card().classes('w-full gap-1').style(f'border-left:4px solid {p.color}'):
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.label(p.key or '·').classes('kontor-title text-xs px-1 rounded') \
                    .style(f'background:{p.color};color:#fff')
                ui.label(p.name).classes('font-medium grow')
                if p.archived:
                    ui.badge('archiviert').props('color=grey-5')
                if p.id == store.current_project_id:
                    ui.badge('aktiv').props('color=positive')
                ui.label(f'{len(sprints)} Sprints · {len(tasks)} Tasks') \
                    .classes('text-xs text-grey-6')
                ui.button('Steckbrief', icon='assignment',
                          on_click=lambda p=p: (store.set_current_project(p.id), ui.navigate.to('/charter'))) \
                    .props('flat dense size=sm no-caps')
                ui.button(icon='edit', on_click=lambda p=p: _form(p)).props('flat dense size=sm')
            if p.description:
                ui.label(p.description).classes('text-sm text-grey-7')


def page() -> None:
    with frame('/projects'):
        ui.label('Werft – Projekte').classes('kontor-title text-xl')
        content()
