"""Fahrplan heute – Tagesplan für die Teamleitung, mit Häkchen zum Abarbeiten."""
from __future__ import annotations

from datetime import date

from nicegui import app, ui

from components import frame, help_hint
from store import store, today_iso

WEEKDAYS = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

# Wochen-Fokus je Wochentag (0 = Montag)
WEEK_FOCUS = {
    0: 'Wochenstart: Woche grob planen, Ziele fürs Team klarmachen.',
    1: 'Normaler Arbeitstag – Fokus auf Fortschritt und Blocker.',
    2: 'Wochenmitte: kurz gegen den Plan prüfen – liegen wir richtig?',
    3: 'Normaler Arbeitstag – Reviews nicht liegen lassen.',
    4: 'Wochenabschluss: Statusbericht aktualisieren, offene Punkte sichern.',
    5: 'Wochenende – höchstens kurz reinschauen.',
    6: 'Wochenende – höchstens kurz reinschauen.',
}

# Feste Tagesroutine.  Abschnitt -> Liste von (key, Aufgabe, Warum, Zielseite)
ROUTINE: list[tuple[str, str, list[tuple[str, str, str, str]]]] = [
    ('Morgens (bis ca. 10 Uhr)', 'wb_sunny', [
        ('leitstand', 'Leitstand öffnen und einmal komplett überfliegen',
         'Damit du den Tag mit Überblick startest: Fortschritt, rote Zahlen, Betrieb.', '/'),
        ('standup', 'Team an das Standup erinnern und Einträge lesen',
         'Der schnellste Weg zu erfahren, wer woran ist und wo es klemmt.', '/standup'),
        ('blocker', 'Blocker aus dem Standup sofort angehen',
         'Ein Blocker kostet jeden Tag Zeit – dein wichtigster Hebel als TL.', '/standup'),
        ('tagesziel', 'Für dich festhalten: Was muss heute unbedingt vorankommen?',
         'Ein klares Tagesziel schützt dich vor Zerfaserung.', '/board'),
    ]),
    ('Im Lauf des Tages', 'schedule', [
        ('board', 'Board pflegen: hängt etwas, ist etwas unklar, staut sich „Review"?',
         'Das Board ist nur nützlich, wenn es den echten Stand zeigt.', '/board'),
        ('erreichbar', 'Ansprechbar bleiben und Rückfragen zügig beantworten',
         'Wartende Teammitglieder sind teurer als eine kurze Unterbrechung bei dir.', '/standup'),
        ('review', 'Darauf achten, dass fertige Aufgaben auch getestet / reviewt werden',
         'Sonst ist am Sprint-Ende „fast alles fertig" – aber nichts abgenommen.', '/board'),
    ]),
    ('Zum Feierabend', 'nights_stay', [
        ('stand', 'Kurzer Blick: sind alle Board-Karten auf dem echten Stand?',
         'Morgen früh willst du dich auf die Zahlen verlassen können.', '/board'),
        ('morgen', 'Blick auf morgen: Termine, Abgaben, ist alles vorbereitet?',
         'Überraschungen am Morgen kosten am meisten.', '/calendar'),
    ]),
]

# Wochen-Aufgaben (seltener, aber wichtig)
WEEKLY: list[tuple[str, str, str, str]] = [
    ('w_status', 'Statusbericht für Betreuer / Auftraggeber aktualisieren',
     'Probleme früh sichtbar machen – nicht erst, wenn es brennt.', '/status'),
    ('w_raid', 'Risiken & Entscheidungen (RAID) durchgehen',
     'Einmal pro Woche prüfen: was könnte schiefgehen, was ist neu?', '/raid'),
    ('w_sprint', 'Laufenden Sprint nachsteuern bzw. nächsten vorbereiten',
     'Kleine Korrekturen früh sind besser als ein gescheiterter Sprint.', '/sprints'),
    ('w_wetter', 'Wetterlage ansehen – wie geht es dem Team?',
     'Stimmung kippt meist leise. 1:1 anbieten, wenn jemand „Regen" meldet.', '/wetter'),
    ('w_retro', 'Am Sprint-Ende: Retro moderieren und Maßnahmen festhalten',
     'Ohne Retro wiederholt ihr dieselben Fehler.', '/retro'),
]


# --------------------------------------------------------------------------
def _checks() -> dict:
    """Häkchen des heutigen Tages aus dem Browser-Speicher (setzt sich täglich zurück)."""
    try:
        store_ = app.storage.user
    except Exception:  # noqa: BLE001
        return {}
    alld = store_.get('daychecks') or {}
    day = today_iso()
    if day not in alld:
        alld = {day: {}}          # alten Tag verwerfen -> täglicher Reset
        store_['daychecks'] = alld
    return alld[day]


def _toggle(key: str, value: bool) -> None:
    try:
        store_ = app.storage.user
    except Exception:  # noqa: BLE001
        return
    alld = store_.get('daychecks') or {}
    day = today_iso()
    alld.setdefault(day, {})[key] = value
    store_['daychecks'] = alld


# --------------------------------------------------------------------------
def _alerts() -> list[tuple[str, str, str]]:
    """(Text, Zielseite, Button-Label) – Dinge, die heute Aufmerksamkeit brauchen."""
    out: list[tuple[str, str, str]] = []
    sp = store.active_sprint
    members = store.active_members
    is_workday = date.today().weekday() < 5

    if not sp:
        out.append(('Kein aktiver Sprint. Lege einen an und aktiviere ihn – '
                    'sonst rechnet der Leitstand nicht mit.', '/sprints', 'Sprint anlegen'))
    else:
        dl = sp.days_left
        if dl is not None and dl < 0:
            out.append((f'Sprint „{sp.name}" ist seit {-dl} Tag(en) über der Zeit – '
                        'abschließen oder Enddatum anpassen.', '/sprints', 'Sprint'))
        elif dl is not None and dl <= 1:
            out.append(('Sprint endet fast – Review / Demo und Retro vorbereiten.',
                        '/retro', 'Retro'))

    # Standup heute
    if is_workday and members:
        today = today_iso()
        have = {s.member_id for s in store.standups if s.date == today
                and (s.yesterday or s.today or s.blocker)}
        missing = [m for m in members if m.id not in have]
        if missing and len(missing) != len(members):
            out.append((f'{len(missing)} von {len(members)} haben heute noch kein Standup: '
                        + ', '.join(m.name.split()[0] for m in missing), '/standup', 'Standup'))
        elif not have:
            out.append(('Heute hat noch niemand ein Standup eingetragen.', '/standup', 'Standup'))

    # Blocker
    blocked_tasks = [t for t in store.p_tasks() if t.blocked and t.status != 'done']
    today = today_iso()
    su_block = [s for s in store.standups if s.date == today and s.blocker.strip()]
    if blocked_tasks or su_block:
        n = len(blocked_tasks) + len(su_block)
        out.append((f'{n} offene(r) Blocker – das ist heute deine Nr. 1.',
                    '/board' if blocked_tasks else '/standup', 'Ansehen'))

    # Review-Stau
    review = [t for t in store.p_tasks() if t.status == 'review']
    if len(review) >= 3:
        out.append((f'{len(review)} Aufgaben stauen sich in „Review" – wer testet?',
                    '/board', 'Board'))

    # Kapazität überbucht
    if sp:
        committed = store.committed_hours(sp.id)
        cap = store.capacity_hours(sp)
        if cap and committed > cap * 1.05:
            out.append((f'Sprint ist überbucht: {committed:g} h eingeplant, nur {cap:g} h Kapazität.',
                        '/capacity', 'Kapazität'))

    # Stimmung einsammeln (gegen Sprint-Ende)
    if sp and members:
        moods = {m.member_id for m in store.moods if m.sprint_id == sp.id}
        dl = sp.days_left
        if len(moods) < len(members) and dl is not None and 0 <= dl <= 3:
            out.append(('Sprint-Ende naht – Team-Wetter ist noch nicht vollständig.',
                        '/wetter', 'Wetterlage'))

    # Überfällige Meilensteine
    overdue = [m for m in store.p_milestones()
               if m.status == 'offen' and m.due and m.due < today_iso()]
    if overdue:
        out.append((f'{len(overdue)} überfällige(r) Meilenstein: '
                    + ', '.join(m.title for m in overdue[:2]), '/milestones', 'Meilensteine'))

    return out


def _item_row(key: str, text: str, why: str, path: str, checks: dict) -> None:
    done = bool(checks.get(key))
    with ui.row().classes('w-full items-start gap-2 no-wrap border-t border-grey-2 py-2'):
        cb = ui.checkbox(value=done, on_change=lambda e, k=key: (_toggle(k, e.value),
                                                                content.refresh()))
        cb.props('dense')
        with ui.column().classes('gap-0 grow'):
            ui.label(text).classes('text-sm ' + ('line-through text-grey-4' if done else 'font-medium'))
            if not done:
                with ui.row().classes('items-start gap-1 no-wrap'):
                    ui.icon('info', size='14px').classes('text-blue-4 mt-0.5')
                    ui.label(why).classes('text-xs text-grey-6')
        if path:
            ui.button('Öffnen', on_click=lambda p=path: ui.navigate.to(p)) \
                .props('flat dense no-caps size=sm')


@ui.refreshable
def content() -> None:
    checks = _checks()
    wd = date.today().weekday()
    sp = store.active_sprint

    # -- Kopf --------------------------------------------------------
    with ui.card().classes('w-full gap-1'):
        with ui.row().classes('w-full items-center gap-2 flex-wrap'):
            ui.label(f'{WEEKDAYS[wd]}, {date.today():%d.%m.%Y}').classes('kontor-title text-lg')
            if sp:
                days = sp.days() or []
                total = len([d for d in days])
                gone = len([d for d in days if d <= date.today()])
                dl = sp.days_left
                txt = f'{sp.name}'
                if total:
                    txt += f' · Tag {max(1, gone)}/{total}'
                if dl is not None:
                    txt += f' · {dl} Tag(e) übrig' if dl >= 0 else ' · über der Zeit'
                ui.badge(txt).props('color=primary')
            else:
                ui.badge('kein aktiver Sprint').props('color=grey-6')
        ui.label(WEEK_FOCUS.get(wd, '')).classes('text-sm text-grey-7')

    help_hint('Diese Liste ist ein Vorschlag, kein Gesetz. Hak ab, was erledigt ist – '
              'morgen sind die Häkchen wieder weg. Die Punkte unter „Jetzt wichtig" '
              'kommen automatisch aus euren Daten.', title='Wie der Fahrplan funktioniert')

    # -- Jetzt wichtig ---------------------------------------------
    alerts = _alerts()
    with ui.card().classes('w-full gap-1 ' + ('bg-red-1 border border-red-2' if alerts
                                              else 'bg-green-1 border border-green-2')):
        with ui.row().classes('items-center gap-2'):
            ui.icon('priority_high' if alerts else 'check_circle') \
                .classes('text-negative' if alerts else 'text-positive')
            ui.label('Jetzt wichtig' if alerts else 'Jetzt wichtig – alles im grünen Bereich') \
                .classes('kontor-title text-md')
        for text, path, label in alerts:
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.icon('chevron_right', size='18px').classes('text-negative')
                ui.label(text).classes('text-sm grow')
                if path:
                    ui.button(label, on_click=lambda p=path: ui.navigate.to(p)) \
                        .props('flat dense no-caps size=sm')
        if not alerts:
            ui.label('Keine dringenden Punkte. Trotzdem lohnt sich der Blick auf die Routine unten.') \
                .classes('text-sm text-grey-7')

    # -- Tagesroutine --------------------------------------------
    for title, icon, items in ROUTINE:
        with ui.card().classes('w-full gap-0'):
            with ui.row().classes('items-center gap-2'):
                ui.icon(icon).classes('text-primary')
                ui.label(title).classes('kontor-title text-md')
                done_n = sum(1 for k, *_ in items if checks.get(k))
                ui.badge(f'{done_n}/{len(items)}').props('color=grey-5' if done_n < len(items)
                                                         else 'color=positive')
            for key, text, why, path in items:
                _item_row(key, text, why, path, checks)

    # -- Diese Woche -------------------------------------------
    with ui.card().classes('w-full gap-0'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('date_range').classes('text-primary')
            ui.label('Diese Woche (nicht jeden Tag nötig)').classes('kontor-title text-md')
        for key, text, why, path in WEEKLY:
            _item_row(key, text, why, path, checks)

    ui.label('Tipp: Wenn dir ein Punkt dauerhaft unklar ist, öffne oben rechts den '
             '(i)-Knopf oder schau in die Anleitung.').classes('text-xs text-grey-5 mt-1')


def page() -> None:
    with frame('/today'):
        ui.label('Fahrplan heute').classes('kontor-title text-xl')
        content()
