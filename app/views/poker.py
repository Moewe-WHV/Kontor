"""Planning Poker – gemeinsame Story-Schaetzung im Sprint-Planning.

Bewusst NICHT in pm.json persistiert (siehe docs/roadmap/planning-poker.md):
eine laufende Abstimmungsrunde ist fluechtiger Team-Zustand fuer die Dauer
eines Plannings, kein Datensatz. Erst "Uebernehmen" schreibt das Ergebnis
explizit in Task.estimate_h (echte Domainlogik, landet in store.save()).

Anders als z. B. die GitHub-Kachel auf dem Leitstand (siehe dashboard.py,
dort bewusst pro Browser-Tab) soll eine Poker-Runde hier fuer alle sichtbar
sein, die gerade am selben Projekt schaetzen – der State liegt daher pro
Projekt in einem modulweiten Dict. Damit alle offenen Tabs den Stand
zeitnah nachziehen, pollt jede Seite sich per ui.timer selbst.
"""
from __future__ import annotations

from statistics import mean, median

from nicegui import app, ui

from components import acting_member_id, avatar, frame, stat_tile
from store import store

DECK = [0.5, 1, 2, 3, 5, 8, 13, 20, 40]
SPECIAL_CARDS = ['?', '☕']

_sessions: dict[str, dict] = {}   # project_id -> {'task_id', 'votes': {member_id: card}, 'revealed': bool}


def _card_label(card) -> str:
    return f'{card:g} h' if isinstance(card, (int, float)) else str(card)


def _session() -> dict:
    pid = store.pid
    return _sessions.setdefault(pid, {'task_id': None, 'votes': {}, 'revealed': False})


def _candidate_tasks() -> list:
    """Tasks, die sich fuers Schaetzen anbieten: alles Offene im aktuellen Projekt."""
    return sorted((t for t in store.p_tasks() if t.status != 'done'),
                  key=lambda t: (t.status != 'backlog', t.order))


def _pick_task(tid: str | None) -> None:
    s = _session()
    s['task_id'] = tid
    s['votes'] = {}
    s['revealed'] = False
    panel.refresh()


def _vote(card) -> None:
    mid = acting_member_id()
    if not mid:
        ui.notify('Erst oben in der Kopfzeile auswaehlen, als wer du arbeitest', type='warning')
        return
    s = _session()
    if not s['task_id']:
        ui.notify('Erst einen Task waehlen', type='warning')
        return
    if s['revealed']:
        return
    s['votes'][mid] = card
    panel.refresh()


def _reveal() -> None:
    s = _session()
    if not s['votes']:
        ui.notify('Noch niemand hat abgestimmt', type='warning')
        return
    s['revealed'] = True
    panel.refresh()


def _new_round() -> None:
    s = _session()
    s['votes'] = {}
    s['revealed'] = False
    panel.refresh()


def _next_task() -> None:
    tasks = _candidate_tasks()
    if not tasks:
        return
    ids = [t.id for t in tasks]
    s = _session()
    if s['task_id'] in ids:
        idx = ids.index(s['task_id'])
        nxt = ids[(idx + 1) % len(ids)]
    else:
        nxt = ids[0]
    _pick_task(nxt)


def _apply(task, value: float) -> None:
    store.update(task, estimate_h=value)
    ui.notify(f'Schaetzung uebernommen: {value:g} h', type='positive')
    _new_round()


def _numeric_votes(votes: dict) -> list[float]:
    return [v for v in votes.values() if isinstance(v, (int, float))]


@ui.refreshable
def panel() -> None:
    s = _session()
    tasks = _candidate_tasks()
    task = store.task(s['task_id']) if s['task_id'] else None
    if task and task.project_id != store.pid:
        task = None

    with ui.row().classes('w-full items-center gap-2'):
        ui.select({t.id: f'{t.title} · aktuell {t.estimate_h:g} h' for t in tasks},
                  label='Task', value=task.id if task else None,
                  on_change=lambda e: _pick_task(e.value)) \
            .props('outlined dense options-dense clearable').classes('grow min-w-[16rem]')
        ui.button('Naechster Task', icon='skip_next', on_click=_next_task).props('flat no-caps')

    if not task:
        with ui.card().classes('w-full items-center py-8'):
            ui.icon('style', size='32px').classes('text-grey-4')
            ui.label('Task waehlen, um mit dem Schaetzen zu beginnen.').classes('text-sm text-grey-6')
        return

    with ui.card().classes('w-full gap-1'):
        ui.label(task.title).classes('kontor-title text-lg')
        if task.description:
            ui.label(task.description).classes('text-sm text-grey-7')
        ui.label(f'Aktuelle Schaetzung: {task.estimate_h:g} h').classes('text-xs text-grey-6')

    mid = acting_member_id()
    my_card = s['votes'].get(mid) if mid else None
    with ui.row().classes('w-full gap-2 flex-wrap'):
        for card in [*DECK, *SPECIAL_CARDS]:
            selected = my_card == card
            ui.button(_card_label(card), on_click=lambda c=card: _vote(c)) \
                .props(f'{"unelevated color=primary" if selected else "outline"} no-caps') \
                .classes('min-w-[3.5rem]').set_enabled(not s['revealed'])

    ui.separator()

    members = store.active_members
    if not members:
        ui.label('Keine aktive Crew im Projekt.').classes('text-xs text-grey-6')
    with ui.row().classes('w-full gap-4 flex-wrap'):
        for m in members:
            voted = m.id in s['votes']
            with ui.column().classes('items-center gap-1'):
                avatar(m)
                if s['revealed'] and voted:
                    ui.label(_card_label(s['votes'][m.id])).classes('text-sm font-bold')
                elif voted:
                    ui.icon('check_circle', size='16px').classes('text-positive').tooltip('Hat abgestimmt')
                else:
                    ui.icon('hourglass_empty', size='16px').classes('text-grey-4').tooltip('Wartet noch')

    with ui.row().classes('w-full gap-2'):
        ui.button('Aufdecken', icon='visibility', on_click=_reveal) \
            .props('unelevated no-caps').set_enabled(bool(s['votes']) and not s['revealed'])
        ui.button('Neue Runde', icon='refresh', on_click=_new_round).props('outline no-caps')

    if s['revealed']:
        nums = _numeric_votes(s['votes'])
        if nums:
            with ui.row().classes('w-full gap-3 flex-wrap'):
                stat_tile(f'{mean(nums):.1f} h', 'Mittelwert')
                stat_tile(f'{median(nums):g} h', 'Median')
                stat_tile(f'{min(nums):g}–{max(nums):g} h', 'Spanne')
            if len(set(nums)) > 1:
                ui.label('Grosse Abweichung? Kurz begruenden und neue Runde schaetzen.') \
                    .classes('text-xs text-warning')
            with ui.row().classes('w-full gap-2 flex-wrap items-center'):
                ui.label('Uebernehmen als Schaetzung:').classes('text-xs text-grey-6')
                for v in sorted(set(nums)):
                    ui.button(f'{v:g} h', on_click=lambda v=v: _apply(task, v)).props('outline dense no-caps')
                avg = round(mean(nums), 1)
                ui.button(f'Mittelwert ({avg:g} h)', on_click=lambda: _apply(task, avg)) \
                    .props('unelevated dense no-caps')
        else:
            ui.label('Keine schaetzbaren Stimmen (nur „?" / „☕").').classes('text-xs text-grey-6')


def page() -> None:
    prefill = app.storage.user.pop('poker_prefill_task', None)
    if prefill:
        task = store.task(prefill)
        if task and task.project_id == store.pid:
            _session()['task_id'] = prefill
            _session()['votes'] = {}
            _session()['revealed'] = False

    with frame('/poker'):
        with ui.row().classes('w-full items-center'):
            ui.label('Planning Poker').classes('kontor-title text-xl')
            ui.label(f'· {store.project.name}' if store.project else '').classes('text-grey-6')
        ui.label('Gemeinsam schaetzen: Task waehlen, verdeckt eine Karte legen, gemeinsam aufdecken.') \
            .classes('text-sm text-grey-6')
        if not store.project:
            ui.label('Kein Projekt ausgewählt – lege in der Werft eines an.').classes('text-grey-6')
            return
        panel()
        ui.timer(1.5, panel.refresh)
