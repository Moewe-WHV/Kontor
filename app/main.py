"""Kontor – Projektleitstand.

Mehrprojekt-Werkzeugkasten für Teamleitungen in der Softwareentwicklung:
Portfolio, Kanban, Sprint- & Kapazitätsplanung, Abwesenheiten, Standup,
Stunden, Burndown/Metriken, Retro, Team-Wetter, Risiken & Entscheidungen,
Releases, Ideen-Speicher, 1:1-Gespräche, Kalender – plus GitHub-PR-Sicht.

Daten liegen in app/data/pm.json (per Docker-Volume persistent).

Umgebungsvariablen (optional):
    GITHUB_TOKEN   PAT für die GitHub-API (höheres Rate-Limit / private Repos)
    GITHUB_REPO    Default-Repo "owner/name" für den Leitstand
    STORAGE_SECRET Signatur der NiceGUI-Cookies
"""
from __future__ import annotations

import os

from nicegui import ui

import auth
from nicegui import app as nicegui_app
from store import store
from views import (absences, board, budget, burndown, calendar, capacity, changes,
                   charter, dashboard, documents, environments, handbook, ideas, incidents,
                   lessons, meetings, metrics, milestones, modules, okrs, one_on_ones,
                   portfolio, projects, quality, raci, raid, releases, requirements, retro,
                   roadmap, roles, settings, sprints, stakeholders, standup, status, team,
                   timelog, today, users, vendors, wetter)

ROUTES = {
    '/': dashboard,
    '/today': today, '/roles': roles, '/handbook': handbook,
    '/portfolio': portfolio, '/status': status, '/metrics': metrics,
    '/budget': budget, '/calendar': calendar,
    '/charter': charter, '/requirements': requirements, '/roadmap': roadmap,
    '/milestones': milestones, '/okrs': okrs, '/raci': raci,
    '/board': board, '/sprints': sprints, '/capacity': capacity, '/absences': absences,
    '/standup': standup, '/timelog': timelog, '/burndown': burndown,
    '/quality': quality, '/environments': environments, '/incidents': incidents,
    '/stakeholders': stakeholders, '/meetings': meetings, '/changes': changes,
    '/raid': raid, '/releases': releases, '/documents': documents, '/vendors': vendors,
    '/retro': retro, '/wetter': wetter, '/lessons': lessons,
    '/ideas': ideas, '/one-on-ones': one_on_ones,
    '/projects': projects, '/team': team, '/modules': modules, '/settings': settings,
    '/users': users,
}


@nicegui_app.get('/healthz')
def _healthz():
    """Liveness: der Prozess laeuft. Kein Datenzugriff, damit das immer schnell antwortet."""
    return {'status': 'ok'}


@nicegui_app.get('/readyz')
def _readyz():
    """Readiness: Datenhaltung ist geladen und ein aktuelles Projekt steht bereit."""
    ready = store.current_project_id is not None or not store.projects
    return {'status': 'ok' if ready else 'starting'}


def _register(path, mod) -> None:
    ui.page(path)(lambda: mod.page())


for _path, _mod in ROUTES.items():
    _register(_path, _mod)

auth.setup()


def _flag(name: str, default: str = '') -> bool:
    return os.getenv(name, default).strip().lower() in {'1', 'true', 'yes', 'on'}


ui.run(
    host='0.0.0.0',
    port=int(os.getenv('PORT', '8080')),
    reload=_flag('APP_RELOAD'),
    show=False,
    title='Kontor · Projektleitstand',
    storage_secret=os.getenv('STORAGE_SECRET', 'kontor-leitstand-dev'),
)
