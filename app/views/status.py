"""Statusbericht – wöchentliche Projektampel, automatisch aus den Daten zusammengestellt."""
from __future__ import annotations

from datetime import date

from nicegui import ui

from components import frame, stat_tile
from store import RAG, store


def _report_text(p) -> str:
    r = store.weekly_report(p.id)
    c = store.project_cost(p.id)
    lines = [f'# Statusbericht {p.name} — KW {date.today().isocalendar().week}',
             f'Ampel: {RAG[p.rag][0]}']
    if p.status_note:
        lines.append(p.status_note)
    lines.append('')
    if r['sprint']:
        prog = (store.done_hours(r['sprint'].id) / store.committed_hours(r['sprint'].id) * 100) \
            if store.committed_hours(r['sprint'].id) else 0
        lines.append(f'Sprint: {r["sprint"].name} — {prog:.0f}% erledigt, '
                     f'{r["sprint"].days_left} Tage übrig')
    if c['budget']:
        lines.append(f'Budget: {c["actual"]:.0f} € von {c["budget"]:.0f} € verbraucht, '
                     f'Prognose {c["eac"]:.0f} €')
    if r['bugs_open'] or r['incidents']:
        lines.append(f'Qualität: {r["bugs_open"]} offene Bugs ({r["bugs_critical"]} kritisch/hoch), '
                     f'{len(r["incidents"])} offene Incidents')
    lines.append('')
    lines.append('## Erledigt diese Woche')
    lines += [f'- {t.title}' for t in r['done_week']] or ['- (nichts abgeschlossen)']
    lines.append('')
    lines.append('## Risiken & Blocker')
    lines += [f'- ⛔ {t.title}: {t.blocked_reason}' for t in r['blockers']]
    lines += [f'- 🔥 Incident {inc.title} ({inc.severity.upper()})' for inc in r['incidents']]
    lines += [f'- ⚠ {rk.title} (Score {rk.score})' for rk in r['risks']]
    lines += [f'- 📝 offener Änderungsantrag: {cr.title}' for cr in r['changes_open']]
    if not (r['blockers'] or r['risks'] or r['incidents'] or r['changes_open']):
        lines.append('- keine kritischen Punkte')
    lines.append('')
    lines.append('## Als Nächstes')
    lines += [f'- 🏁 {m.title} ({m.due})' for m in r['milestones']]
    lines += [f'- {t.title}' for t in r['next'][:6]]
    if not r['milestones'] and not r['next']:
        lines.append('- (kein aktiver Sprint)')
    return '\n'.join(lines)


@ui.refreshable
def content() -> None:
    p = store.project
    if not p:
        return
    r = store.weekly_report(p.id)
    c = store.project_cost(p.id)

    with ui.card().classes('w-full gap-2'):
        with ui.row().classes('w-full items-center gap-2'):
            ui.label('Projekt-Ampel').classes('kontor-title text-sm')
            for key, (lbl, col) in RAG.items():
                sel = p.rag == key
                ui.button(lbl, on_click=lambda k=key: (store.update(p, rag=k), content.refresh())) \
                    .props('no-caps ' + ('unelevated' if sel else 'flat')) \
                    .style(f'background:{col}{"" if sel else "22"};color:{"#fff" if sel else col}')
        note = ui.textarea('Einschätzung der Projektleitung', value=p.status_note) \
            .props('outlined dense autogrow').classes('w-full')
        note.on('blur', lambda: store.update(p, status_note=note.value or ''))

    with ui.row().classes('w-full gap-3 flex-wrap'):
        stat_tile(len(r['done_week']), 'erledigt (Woche)', 'text-positive')
        stat_tile(len(r['blockers']), 'Blocker', 'text-negative' if r['blockers'] else 'text-grey-5')
        stat_tile(len(r['incidents']), 'offene Incidents', 'text-negative' if r['incidents'] else 'text-grey-5')
        stat_tile(r['bugs_critical'], 'Bugs kritisch/hoch', 'text-negative' if r['bugs_critical'] else 'text-grey-5')
        stat_tile(len(r['risks']), 'Risiken ≥ mittel', 'text-warning' if r['risks'] else 'text-grey-5')
        stat_tile(len(r['milestones']), 'Meilensteine < 3 Wo')

    def section(title, items, empty, render):
        with ui.card().classes('w-full gap-1'):
            ui.label(title).classes('kontor-title text-sm')
            if not items:
                ui.label(empty).classes('text-xs text-grey-5')
            for it in items:
                render(it)

    section('Erledigt diese Woche', r['done_week'], 'nichts abgeschlossen',
            lambda t: ui.label('• ' + t.title).classes('text-sm'))
    section('Blocker', r['blockers'], 'keine',
            lambda t: ui.label(f'⛔ {t.title} — {t.blocked_reason}').classes('text-sm text-negative'))
    section('Offene Incidents', r['incidents'], 'keine',
            lambda i: ui.label(f'🔥 {i.title} ({i.severity.upper()}) — {i.status}').classes('text-sm text-negative'))
    section('Risiken (Eintritt×Auswirkung ≥ 4)', r['risks'], 'keine',
            lambda rk: ui.label(f'⚠ {rk.title} (Score {rk.score})').classes('text-sm text-warning'))
    section('Anstehende Meilensteine', r['milestones'], 'keine in den nächsten 3 Wochen',
            lambda m: ui.label(f'🏁 {m.title} — {m.due}').classes('text-sm'))
    section('Als Nächstes im Sprint', r['next'][:8], 'kein aktiver Sprint',
            lambda t: ui.label('• ' + t.title).classes('text-sm text-grey-7'))

    with ui.card().classes('w-full gap-2'):
        ui.label('Bericht als Text').classes('kontor-title text-sm')
        text = _report_text(p)
        ui.textarea(value=text).props('outlined readonly autogrow').classes('w-full font-mono text-xs')
        ui.button('In Zwischenablage', icon='content_copy',
                  on_click=lambda: (ui.clipboard.write(text), ui.notify('kopiert', type='positive'))) \
            .props('no-caps flat')


def page() -> None:
    with frame('/status'):
        ui.label('Statusbericht').classes('kontor-title text-xl')
        content()
