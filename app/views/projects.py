"""Projekte verwalten (Werft)."""
from __future__ import annotations

from nicegui import ui

from components import frame
from store import PROJECT_MODE, Project, store
from views.modules import PRESETS

_PALETTE = ['#1f4e5f', '#5b8ca3', '#3d7a5d', '#b5533a', '#cf8a2e', '#7a5c99', '#a63a3a', '#2f6f6f']

# Vorschlaege fuer die Rolle im Solo-Schritt des Wizards – frei erweiterbar (add-unique).
_SOLO_ROLES = ['Entwickler:in', 'Product Owner', 'Berater:in/Freelancer', 'Sonstiges']


def _apply_mode_preset(mode: str) -> None:
    """Vorbelegung der sichtbaren Module gemaess Solo-/Team-Modus (nur Convenience,
    ueber /modules bleibt jederzeit alles fein einstellbar)."""
    if mode == 'solo':
        store.set_project_modules(sorted(PRESETS['Solo (Einzelkämpfer)']))
    else:
        store.set_project_modules([])


def _mode_badge(p) -> None:
    label, icon = PROJECT_MODE.get(p.mode, PROJECT_MODE['team'])
    with ui.row().classes('items-center gap-1 px-1.5 py-0.5 rounded-full bg-grey-3 dark:bg-grey-9') \
            .tooltip('Einzelperson' if p.mode == 'solo' else 'Team-Projekt'):
        ui.icon(icon, size='14px').classes('text-grey-7 dark:text-grey-4')
        ui.label(label).classes('text-xs text-grey-7 dark:text-grey-4')


def _wizard_new() -> None:
    """Gefuehrter Setup-Wizard fuer ein neues Projekt: Basisdaten -> Solo/Team -> Rolle."""
    state = {'mode': 'team'}
    with ui.dialog().props('persistent') as d, ui.card().classes('w-[32rem] max-w-full gap-2'):
        ui.label('Neues Projekt').classes('kontor-title text-lg')
        with ui.stepper().props('flat contracted').classes('w-full') as stepper:
            # -- Schritt A: Basisdaten -----------------------------------
            with ui.step('Projekt'):
                with ui.row().classes('w-full gap-2'):
                    name = ui.input('Name').props('outlined dense').classes('grow')
                    key = ui.input('Kürzel').props('outlined dense').classes('w-28')
                desc = ui.textarea('Beschreibung').props('outlined dense autogrow').classes('w-full')
                color = ui.select(_PALETTE, label='Farbe',
                                  value=_PALETTE[len(store.projects) % len(_PALETTE)]) \
                    .props('outlined dense').classes('w-full')

                def to_mode_step() -> None:
                    if not name.value.strip():
                        ui.notify('Name fehlt', type='warning')
                        return
                    stepper.next()

                with ui.stepper_navigation():
                    ui.button('Weiter', on_click=to_mode_step).props('no-caps')

            # -- Schritt B: Solo oder Team --------------------------------
            with ui.step('Arbeitsweise'):
                ui.label('Wie arbeitest du an diesem Projekt?').classes('text-sm text-grey-7')
                with ui.row().classes('w-full gap-3'):
                    with ui.button(on_click=lambda: choose_mode('solo')) \
                            .props('outline no-caps') \
                            .classes('grow flex-col items-center py-4 gap-1 normal-case'):
                        ui.icon('person').classes('text-3xl')
                        ui.label('Allein').classes('font-medium')
                        ui.label('Du arbeitest als Einzelperson an diesem Projekt') \
                            .classes('text-xs text-grey-6 text-center')
                    with ui.button(on_click=lambda: choose_mode('team')) \
                            .props('outline no-caps') \
                            .classes('grow flex-col items-center py-4 gap-1 normal-case'):
                        ui.icon('groups').classes('text-3xl')
                        ui.label('Im Team').classes('font-medium')
                        ui.label('Mehrere Personen arbeiten gemeinsam daran') \
                            .classes('text-xs text-grey-6 text-center')
                with ui.stepper_navigation():
                    ui.button('Zurück', on_click=stepper.previous).props('flat no-caps')

            # -- Schritt C: Rolle (abhaengig vom Modus) -------------------
            with ui.step('Rolle'):
                with ui.column().classes('w-full gap-1') as solo_role_col:
                    ui.label('Welche Rolle hast du in diesem Projekt?').classes('text-sm text-grey-7')
                    solo_role = ui.select(_SOLO_ROLES, value=_SOLO_ROLES[0],
                                          new_value_mode='add-unique') \
                        .props('outlined dense').classes('w-full')
                with ui.column().classes('w-full gap-1') as team_role_col:
                    ui.label('Deine Rolle im Team (optional)').classes('text-sm text-grey-7')
                    team_role = ui.input('z. B. Teamleitung, Entwickler:in …') \
                        .props('outlined dense').classes('w-full')
                solo_role_col.set_visibility(False)
                team_role_col.set_visibility(False)

                def finish() -> None:
                    role = (solo_role.value if state['mode'] == 'solo' else team_role.value) or ''
                    data = dict(name=name.value.strip(), key=key.value.strip().upper(),
                                description=desc.value or '', color=color.value,
                                mode=state['mode'], creator_role=role.strip())
                    p = store.add('projects', Project, **data)
                    store.set_current_project(p.id)
                    _apply_mode_preset(state['mode'])
                    d.close()
                    ui.notify('Projekt angelegt', type='positive')
                    ui.navigate.reload()

                with ui.stepper_navigation():
                    ui.button('Zurück', on_click=stepper.previous).props('flat no-caps')
                    ui.button('Projekt anlegen', icon='check', on_click=finish).props('no-caps')

        def choose_mode(mode: str) -> None:
            state['mode'] = mode
            solo_role_col.set_visibility(mode == 'solo')
            team_role_col.set_visibility(mode == 'team')
            stepper.next()

    d.open()


def _form_edit(existing) -> None:
    """Einfaches Ein-Seiten-Formular zum Bearbeiten eines bestehenden Projekts."""
    with ui.dialog() as d, ui.card().classes('w-[32rem] max-w-full gap-2'):
        ui.label('Projekt bearbeiten').classes('kontor-title text-lg')
        with ui.row().classes('w-full gap-2'):
            name = ui.input('Name', value=existing.name).props('outlined dense').classes('grow')
            key = ui.input('Kürzel', value=existing.key).props('outlined dense').classes('w-28')
        desc = ui.textarea('Beschreibung', value=existing.description) \
            .props('outlined dense autogrow').classes('w-full')
        color = ui.select(_PALETTE, label='Farbe', value=existing.color) \
            .props('outlined dense').classes('w-full')
        dod = ui.textarea('Definition of Done (eine Zeile pro Kriterium)',
                          value='\n'.join(existing.dod)) \
            .props('outlined dense autogrow').classes('w-full')
        archived = ui.checkbox('archiviert', value=existing.archived)

        with ui.row().classes('w-full items-center gap-2 mt-1'):
            ui.label('Modus:').classes('text-sm text-grey-7')
            mode = ui.toggle({'solo': 'Allein', 'team': 'Im Team'}, value=existing.mode) \
                .props('dense no-caps')
            ui.space()
            ui.button('Module feinjustieren', icon='tune',
                      on_click=lambda: (d.close(), ui.navigate.to('/modules'))) \
                .props('flat dense no-caps size=sm')
        role = ui.input('Rolle der anlegenden Person (informativ)', value=existing.creator_role) \
            .props('outlined dense').classes('w-full')

        def save() -> None:
            if not name.value.strip():
                ui.notify('Name fehlt', type='warning')
                return
            data = dict(name=name.value.strip(), key=key.value.strip().upper(),
                        description=desc.value or '', color=color.value,
                        dod=[x.strip() for x in (dod.value or '').splitlines() if x.strip()],
                        archived=archived.value, mode=mode.value or 'team',
                        creator_role=role.value or '')
            mode_changed = data['mode'] != existing.mode
            store.update(existing, **data)
            if mode_changed:
                _apply_mode_preset(data['mode'])
                ui.notify('Modus geändert – Module wurden entsprechend vorbelegt '
                          '(unter „Module" feinjustierbar).', type='info')
            d.close()
            ui.navigate.reload()

        with ui.row().classes('w-full justify-between'):
            if len(store.projects) > 1:
                ui.button('Löschen', color='negative', icon='delete',
                          on_click=lambda: _delete(existing, d)).props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


def _form(existing=None) -> None:
    if existing is None:
        _wizard_new()
    else:
        _form_edit(existing)


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
                _mode_badge(p)
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
