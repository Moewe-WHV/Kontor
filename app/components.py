"""Gemeinsame UI-Bausteine: App-Rahmen (norddeutscher Touch), Kacheln, Task-Dialog."""
from __future__ import annotations

from contextlib import contextmanager

from nicegui import app, ui

import auth
import guide
import theme
from store import PRIORITIES, PRIORITY_COLOR, PROJECT_MODE, STATUS_LABELS, STATUSES, Task, store

# Navigation – Gruppen mit maritimem Anstrich, Funktion bleibt klar
NAV_GROUPS = [
    ('Lotse (Start hier)', [
        ('Fahrplan heute', 'explore', '/today'),
        ('Rollen & Ablauf', 'assignment_ind', '/roles'),
        ('Anleitung', 'menu_book', '/handbook'),
    ]),
    ('Ausguck', [
        ('Leitstand', 'dashboard', '/'),
        ('Flotte', 'sailing', '/portfolio'),
        ('Statusbericht', 'description', '/status'),
        ('Metriken', 'insights', '/metrics'),
        ('Budget & Kosten', 'euro', '/budget'),
        ('Seekarte', 'calendar_month', '/calendar'),
    ]),
    ('Kurs setzen', [
        ('Steckbrief', 'assignment', '/charter'),
        ('Anforderungen', 'checklist', '/requirements'),
        ('Roadmap', 'timeline', '/roadmap'),
        ('Meilensteine', 'outlined_flag', '/milestones'),
        ('OKRs / Ziele', 'flag_circle', '/okrs'),
        ('RACI', 'grid_on', '/raci'),
    ]),
    ('Törn', [
        ('Board', 'view_kanban', '/board'),
        ('Sprint-Planung', 'flag', '/sprints'),
        ('Kapazität', 'groups', '/capacity'),
        ('Abwesenheiten', 'beach_access', '/absences'),
        ('Standup', 'record_voice_over', '/standup'),
        ('Stunden', 'schedule', '/timelog'),
        ('Burndown', 'trending_down', '/burndown'),
    ]),
    ('Maschinenraum', [
        ('Qualität & Bugs', 'bug_report', '/quality'),
        ('Umgebungen', 'dns', '/environments'),
        ('Incidents', 'report', '/incidents'),
        ('Releases', 'rocket_launch', '/releases'),
    ]),
    ('Brücke', [
        ('Stakeholder', 'diversity_3', '/stakeholders'),
        ('Besprechungen', 'event', '/meetings'),
        ('Änderungen', 'published_with_changes', '/changes'),
        ('Risiken & Entscheidungen', 'policy', '/raid'),
        ('Dokumente', 'folder_open', '/documents'),
        ('Lieferanten & Lizenzen', 'shopping_cart', '/vendors'),
    ]),
    ('Mannschaft', [
        ('Wetterlage', 'wb_sunny', '/wetter'),
        ('Retrospektive', 'reviews', '/retro'),
        ('Lessons Learned', 'school', '/lessons'),
        ('1:1-Gespräche', 'forum', '/one-on-ones'),
        ('Speicher (Ideen)', 'lightbulb', '/ideas'),
    ]),
    ('Werft', [
        ('Projekte', 'inventory_2', '/projects'),
        ('Crew', 'badge', '/team'),
        ('Module', 'tune', '/modules'),
        ('Einstellungen', 'settings', '/settings'),
    ]),
]

def apply_theme() -> None:
    """Rueckwaertskompatibler Alias – Farben/Theme setzen (siehe theme.apply)."""
    theme.apply()


@contextmanager
def frame(active_path: str):
    dark = theme.apply()
    drawer = ui.left_drawer(value=True, bordered=True).classes('gap-0 px-2 pb-6')
    with ui.header(elevated=True).classes('bg-primary items-center px-3 gap-2 text-white'):
        ui.button(icon='menu', on_click=drawer.toggle).props('flat round color=white')
        ui.icon('anchor').classes('text-2xl')
        with ui.column().classes('gap-0'):
            ui.label('Kontor').classes('kontor-title text-xl leading-none')
            ui.label('Projektleitstand').classes('text-[10px] uppercase tracking-widest opacity-70 leading-none')

        projects = store.active_projects
        if projects:
            ui.select({p.id: f'{p.key or "·"}  {p.name}' for p in projects},
                      value=store.current_project_id, on_change=_switch_project) \
                .props('dense options-dense borderless dark').classes('ml-3 min-w-[13rem]')
            if store.project:
                _, mode_icon = PROJECT_MODE.get(store.project.mode, PROJECT_MODE['team'])
                ui.icon(mode_icon, size='18px').classes('opacity-70') \
                    .tooltip('Solo-Projekt' if store.project.mode == 'solo' else 'Team-Projekt')
        ui.space()
        sp = store.active_sprint
        ui.badge(f'Kurs: {sp.name}' if sp else 'vor Anker').props('color=accent text-color=dark')
        ui.button(icon='help_outline', on_click=lambda: _page_help_dialog(active_path)) \
            .props('flat round color=white').tooltip('Was ist diese Seite? (Hilfe)')
        theme.toggle_button(dark)
        if auth.enabled():
            ui.button(icon='logout', on_click=auth.logout) \
                .props('flat round color=white').tooltip('Abmelden')

    with drawer:
        for group, items in NAV_GROUPS:
            visible = [it for it in items
                       if store.module_enabled(it[2]) or it[2] == active_path]
            if not visible:
                continue
            group_active = any(path == active_path for _, _, path in visible)
            exp = ui.expansion(group, value=group_active or group.startswith('Lotse')).classes('w-full') \
                .props('dense header-class="kontor-title text-xs uppercase text-grey-7 tracking-widest px-1"')
            with exp:
                for label, icon, path in visible:
                    active = path == active_path
                    off = not store.module_enabled(path)
                    row = ui.row().classes(
                        'nav-item w-full items-center gap-3 px-2 py-1 rounded-lg cursor-pointer no-wrap '
                        + ('nav-active' if active else '') + (' opacity-50' if off else ''))
                    row.on('click', lambda p=path: ui.navigate.to(p))
                    with row:
                        ui.icon(icon).classes('text-lg')
                        ui.label(label).classes('text-sm')
                        if off:
                            ui.icon('visibility_off', size='14px').classes('text-grey-5')

    with ui.column().classes('w-full max-w-6xl mx-auto p-4 gap-3'):
        if not store.project:
            ui.label('Noch kein Projekt – lege in der Werft eines an.').classes('text-grey-6')
        elif not store.module_enabled(active_path):
            with ui.card().classes('w-full bg-amber-1 border border-amber-3 gap-1'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('visibility_off').classes('text-amber-9')
                    ui.label('Dieser Bereich ist für das aktuelle Projekt ausgeblendet.') \
                        .classes('text-sm')
                    ui.button('Module verwalten', icon='tune',
                              on_click=lambda: ui.navigate.to('/modules')) \
                        .props('flat dense no-caps size=sm')
        yield

    _maybe_welcome()


def _switch_project(e) -> None:
    store.set_current_project(e.value)
    ui.navigate.reload()


# --------------------------------------------------------------------------
# Hilfe / Onboarding für Einsteiger
# --------------------------------------------------------------------------
def _page_help_dialog(path: str) -> None:
    """Kontext-Hilfe zur aktuellen Seite (Info-Knopf in der Kopfzeile)."""
    h = guide.PAGES.get(path)
    with ui.dialog() as d, ui.card().classes('w-[34rem] max-w-full gap-2'):
        if not h:
            ui.label('Für diese Seite gibt es noch keine Kurzhilfe.').classes('text-sm')
            ui.button('Alles klar', on_click=d.close).props('flat')
        else:
            with ui.row().classes('items-center gap-2 no-wrap'):
                ui.icon('info').classes('text-primary text-xl')
                ui.label(h['title']).classes('kontor-title text-lg')
            ui.label(h['what']).classes('text-sm text-grey-8')
            if h.get('steps'):
                ui.label('So gehst du vor').classes('text-xs font-bold uppercase text-grey-6 mt-1')
                for i, s in enumerate(h['steps'], 1):
                    ui.label(f'{i}. {s}').classes('text-sm')
            if h.get('tips'):
                ui.label('Tipps').classes('text-xs font-bold uppercase text-grey-6 mt-1')
                for t in h['tips']:
                    with ui.row().classes('items-start gap-1 no-wrap'):
                        ui.icon('lightbulb', size='16px').classes('text-accent mt-0.5')
                        ui.label(t).classes('text-sm')
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Zur Anleitung', icon='menu_book',
                          on_click=lambda: (d.close(), ui.navigate.to('/handbook'))).props('flat no-caps')
                ui.button('Verstanden', on_click=d.close).props('unelevated no-caps')
    d.open()


def _maybe_welcome() -> None:
    """Einmalige Begrüßung pro Browser – verweist auf Fahrplan & Anleitung."""
    if not store.setting('show_welcome'):
        return
    try:
        if app.storage.user.get('kontor_onboarded'):
            return
    except Exception:  # noqa: BLE001 – kein Storage-Kontext
        return

    def _dismiss(target: str | None = None) -> None:
        try:
            app.storage.user['kontor_onboarded'] = True
        except Exception:  # noqa: BLE001
            pass
        dlg.close()
        if target:
            ui.navigate.to(target)

    with ui.dialog().props('persistent') as dlg, ui.card().classes('w-[32rem] max-w-full gap-3'):
        with ui.row().classes('items-center gap-2 no-wrap'):
            ui.icon('sailing').classes('text-primary text-2xl')
            ui.label('Moin! Neu hier?').classes('kontor-title text-lg')
        ui.label('Dieses Werkzeug hilft dir, den Überblick als Teamleitung zu behalten. '
                 'Zwei Seiten machen den Anfang leicht:').classes('text-sm text-grey-8')
        with ui.column().classes('gap-1 text-sm'):
            ui.label('• Fahrplan heute – sagt dir jeden Tag, was ansteht.')
            ui.label('• Anleitung – erklärt jeden Bereich der App.')
            ui.label('• Der (i)-Knopf oben rechts erklärt immer die aktuelle Seite.')
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Später', on_click=lambda: _dismiss()).props('flat no-caps')
            ui.button('Anleitung öffnen', icon='menu_book',
                      on_click=lambda: _dismiss('/handbook')).props('flat no-caps')
            ui.button('Zum Fahrplan', icon='explore',
                      on_click=lambda: _dismiss('/today')).props('unelevated no-caps')
    dlg.open()


def help_hint(text: str, *, title: str = 'Hinweis') -> None:
    """Kleine, aufklappbare Infobox für den Seiteninhalt."""
    with ui.expansion(title, icon='info').props('dense').classes(
            'w-full bg-blue-1 rounded-lg text-sm border border-blue-2'):
        ui.label(text).classes('text-sm text-grey-8 p-1')


def resolve_sprint(sel_id):
    """Sprint aus einer (evtl. veralteten) Auswahl-ID, faellt auf aktiven/letzten Sprint zurueck."""
    s = store.sprint(sel_id)
    if s and s.project_id == store.pid:
        return s
    sprints = store.p_sprints()
    return store.active_sprint or (sprints[-1] if sprints else None)


# --------------------------------------------------------------------------
# ECharts: neutrale Achsen-/Text-/Rasterfarben, die auf hellem UND dunklem
# Grund lesbar sind (ECharts rendert auf Canvas, CSS greift dort nicht).
_CHART_INK = '#8a969b'
_CHART_GRID = 'rgba(138,150,155,0.22)'


def chart_opts(o: dict) -> dict:
    """ECharts-Optionen um themen-neutrale Chrome-Farben ergaenzen."""
    o = dict(o)
    o.setdefault('backgroundColor', 'transparent')
    o['textStyle'] = {'color': _CHART_INK, **o.get('textStyle', {})}
    if 'legend' in o and isinstance(o['legend'], dict):
        o['legend'] = {**o['legend'],
                       'textStyle': {'color': _CHART_INK, **o['legend'].get('textStyle', {})}}
    for ax in ('xAxis', 'yAxis'):
        a = o.get(ax)
        if not isinstance(a, dict):
            continue
        a = dict(a)
        a['axisLabel'] = {'color': _CHART_INK, **a.get('axisLabel', {})}
        a['nameTextStyle'] = {'color': _CHART_INK, **a.get('nameTextStyle', {})}
        line = dict(a.get('axisLine', {}))
        line['lineStyle'] = {'color': _CHART_GRID, **line.get('lineStyle', {})}
        a['axisLine'] = line
        split = dict(a.get('splitLine', {}))
        split['lineStyle'] = {'color': _CHART_GRID, **split.get('lineStyle', {})}
        a['splitLine'] = split
        o[ax] = a
    return o


def stat_tile(value, label: str, color: str = 'text-primary', hint: str = '') -> None:
    with ui.card().classes('items-center p-3 min-w-32 grow gap-0'):
        ui.label(str(value)).classes(f'kontor-title text-2xl {color}')
        ui.label(label).classes('text-xs text-grey-6 uppercase tracking-wide text-center')
        if hint:
            ui.label(hint).classes('text-xs text-grey-5 text-center')


def bar(value: float, total: float, color: str = 'primary', label: str | None = None) -> None:
    frac = value / total if total else 0.0
    with ui.column().classes('w-full gap-1'):
        if label:
            with ui.row().classes('w-full justify-between text-xs text-grey-7'):
                ui.label(label)
                ui.label(f'{value:g} / {total:g} h  ({frac * 100:.0f}%)')
        ui.linear_progress(min(frac, 1.0), show_value=False, size='10px',
                           color='negative' if frac > 1.001 else color).classes('w-full')


def avatar(member, size: str = '26px') -> None:
    if member is None:
        ui.avatar('?', size=size, color='grey-4').classes('text-xs')
    else:
        ui.avatar(member.initials, size=size, color=member.color).classes('text-xs text-white') \
            .tooltip(f'{member.name} · {member.role}')


def priority_dot(priority: str) -> None:
    ui.element('div').style(
        f'width:8px;height:8px;border-radius:9999px;flex:none;background:{PRIORITY_COLOR.get(priority, "#999")}'
    ).tooltip(f'Prioritaet: {priority}')


def task_dialog(task: Task | None = None, *, default_sprint: str | None = None,
                default_status: str = 'backlog', on_saved=None) -> None:
    is_new = task is None
    members = {'': '– niemand –', **{m.id: m.name for m in store.active_members}}
    sprints = {'': '– Backlog –', **{s.id: s.name for s in store.p_sprints()}}
    epics = {'': '– kein Epic –', **{e.id: e.title for e in store.p_epics()}}
    others = {t.id: t.title for t in store.p_tasks() if not task or t.id != task.id}

    with ui.dialog() as dialog, ui.card().classes('w-[36rem] max-w-full gap-2'):
        ui.label('Neuer Task' if is_new else 'Task bearbeiten').classes('kontor-title text-lg')
        title = ui.input('Titel', value='' if is_new else task.title).props('outlined dense').classes('w-full')
        desc = ui.textarea('Beschreibung', value='' if is_new else task.description) \
            .props('outlined dense autogrow').classes('w-full')
        with ui.row().classes('w-full gap-2'):
            status = ui.select({s: STATUS_LABELS[s] for s in STATUSES}, label='Status',
                               value=default_status if is_new else task.status).props('outlined dense').classes('grow')
            estimate = ui.number('Schaetzung (h)', value=0 if is_new else task.estimate_h,
                                 min=0, step=0.5, format='%.1f').props('outlined dense').classes('grow')
        with ui.row().classes('w-full gap-2'):
            assignee = ui.select(members, label='Zustaendig',
                                 value='' if is_new or not task.assignee_id else task.assignee_id) \
                .props('outlined dense').classes('grow')
            sprint = ui.select(sprints, label='Sprint',
                               value=(default_sprint or '') if is_new else (task.sprint_id or '')) \
                .props('outlined dense').classes('grow')
        with ui.row().classes('w-full gap-2'):
            priority = ui.select(PRIORITIES, label='Prioritaet',
                                 value='mittel' if is_new else task.priority).props('outlined dense').classes('grow')
            epic = ui.select(epics, label='Epic',
                             value='' if is_new or not task.epic_id else task.epic_id) \
                .props('outlined dense').classes('grow')
        labels = ui.input('Labels (Komma)', value='' if is_new else ', '.join(task.labels)) \
            .props('outlined dense').classes('w-full')
        depends = ui.select(others, label='Haengt ab von', multiple=True,
                            value=[] if is_new else list(task.depends_on)) \
            .props('outlined dense use-chips').classes('w-full')
        gh = ui.input('Link (Issue/PR/Doku)', value='' if is_new else task.github_url) \
            .props('outlined dense').classes('w-full')
        with ui.row().classes('w-full items-center gap-2'):
            blocked = ui.checkbox('Blockiert', value=False if is_new else task.blocked)
            reason = ui.input('Grund', value='' if is_new else task.blocked_reason) \
                .props('outlined dense').classes('grow')
            reason.bind_visibility_from(blocked, 'value')

        with ui.row().classes('w-full justify-between'):
            if not is_new:
                ui.button('Loeschen', icon='delete', color='negative',
                          on_click=lambda: (store.delete_task(task.id), dialog.close(),
                                            on_saved and on_saved())).props('flat')
            else:
                ui.element()
            with ui.row():
                ui.button('Abbrechen', on_click=dialog.close).props('flat')

                def save() -> None:
                    if not title.value.strip():
                        ui.notify('Titel fehlt', type='warning')
                        return
                    data = dict(
                        title=title.value.strip(), description=desc.value or '',
                        estimate_h=float(estimate.value or 0),
                        assignee_id=assignee.value or None, sprint_id=sprint.value or None,
                        priority=priority.value,
                        labels=[x.strip() for x in (labels.value or '').split(',') if x.strip()],
                        epic_id=epic.value or None,
                        depends_on=list(depends.value or []),
                        github_url=gh.value or '', blocked=blocked.value,
                        blocked_reason=reason.value or '',
                    )
                    if is_new:
                        store.add_task(project_id=store.pid, status=status.value, **data)
                    else:
                        for k, v in data.items():
                            setattr(task, k, v)
                        store.set_task_status(task.id, status.value)
                    dialog.close()
                    ui.notify('Gespeichert', type='positive')
                    if on_saved:
                        on_saved()

                ui.button('Speichern', icon='save', on_click=save)
    dialog.open()
