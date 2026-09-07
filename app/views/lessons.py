"""Lessons Learned – kumulierte Erkenntnisse über Sprints & Projekte hinweg."""
from __future__ import annotations

from nicegui import ui

from components import frame, stat_tile
from store import Lesson, store

CATS = {'prozess': 'Prozess', 'technik': 'Technik', 'team': 'Team',
        'stakeholder': 'Stakeholder', 'schaetzung': 'Schätzung'}
CAT_COLOR = {'prozess': 'primary', 'technik': 'secondary', 'team': 'positive',
             'stakeholder': 'warning', 'schaetzung': 'info'}
_flt = {'scope': 'projekt'}


def _form(existing=None) -> None:
    is_new = existing is None
    with ui.dialog() as d, ui.card().classes('w-[32rem] gap-2'):
        ui.label('Neue Lesson' if is_new else 'Lesson bearbeiten').classes('kontor-title text-lg')
        title = ui.input('Titel / Kernaussage', value='' if is_new else existing.title) \
            .props('outlined dense').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            cat = ui.select(CATS, label='Kategorie', value='prozess' if is_new else existing.category) \
                .props('outlined dense').classes('grow')
            tags = ui.input('Tags (Komma)', value='' if is_new else ', '.join(existing.tags)) \
                .props('outlined dense').classes('grow')
        situation = ui.textarea('Was ist passiert?', value='' if is_new else existing.situation) \
            .props('outlined dense autogrow').classes('w-full')
        rec = ui.textarea('Empfehlung / künftig', value='' if is_new else existing.recommendation) \
            .props('outlined dense autogrow').classes('w-full')

        def save() -> None:
            if not title.value.strip():
                ui.notify('Titel fehlt', type='warning')
                return
            data = dict(title=title.value.strip(), category=cat.value, situation=situation.value or '',
                        recommendation=rec.value or '',
                        tags=[x.strip() for x in (tags.value or '').split(',') if x.strip()])
            if is_new:
                store.add('lessons', Lesson, project_id=store.pid, **data)
            else:
                store.update(existing, **data)
            d.close()
            content.refresh()

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', color='negative', icon='delete',
                          on_click=lambda: (store.remove('lessons', existing.id), d.close(), content.refresh())) \
                    .props('flat')
            else:
                ui.element()
            ui.button('Speichern', on_click=save)
    d.open()


@ui.refreshable
def content() -> None:
    with ui.row().classes('w-full items-center gap-2'):
        ui.label('Lessons Learned').classes('kontor-title text-lg')
        ui.toggle({'projekt': 'dieses Projekt', 'alle': 'alle Projekte'}, value=_flt['scope'],
                  on_change=lambda e: (_flt.update(scope=e.value), content.refresh())).props('dense')
        ui.space()
        ui.button('Neue Lesson', icon='add', on_click=_form).props('no-caps')

    lessons = store.p_lessons() if _flt['scope'] == 'projekt' else list(store.lessons)
    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(lessons), 'Erkenntnisse')
        for c in ('prozess', 'technik', 'schaetzung'):
            stat_tile(len([x for x in lessons if x.category == c]), CATS[c])

    # Kandidaten aus offenen Retro-Action-Items
    open_ai = [a for a in store.p_action_items() if not a.done]
    if _flt['scope'] == 'projekt' and open_ai:
        with ui.card().classes('w-full gap-1 bg-amber-1'):
            ui.label('Offene Retro-Maßnahmen (Kandidaten für Lessons)').classes('text-xs font-bold text-warning')
            for a in open_ai[:4]:
                ui.label('• ' + a.text).classes('text-xs')

    for x in lessons:
        with ui.card().classes('w-full gap-1'):
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.badge(CATS[x.category]).props(f'color={CAT_COLOR[x.category]}')
                ui.label(x.title).classes('text-sm font-medium grow')
                if _flt['scope'] == 'alle':
                    pr = store.by_id('projects', x.project_id)
                    if pr:
                        ui.badge(pr.key or pr.name).props('outline color=grey-7')
                ui.button(icon='edit', on_click=lambda x=x: _form(x)).props('flat dense size=sm')
            if x.situation:
                ui.label('Situation: ' + x.situation).classes('text-xs text-grey-6')
            if x.recommendation:
                ui.label('→ ' + x.recommendation).classes('text-sm text-primary')
            if x.tags:
                with ui.row().classes('gap-1'):
                    for t in x.tags:
                        ui.badge(t).props('outline color=grey-6').classes('text-[10px]')


def page() -> None:
    with frame('/lessons'):
        ui.label('Lessons Learned').classes('kontor-title text-xl')
        content()
