"""Datenhaltung + Domaenenlogik fuer das Kontor (Projektleitstand).

Alles liegt in einer JSON-Datei (app/data/pm.json) – kein DB-Server noetig,
gut nachvollziehbar und per Volume im Container persistent.

Die App verwaltet mehrere Projekte. Viele Objekte (Sprint, Task, Risiko …)
haben eine ``project_id``; Crew, Abwesenheiten und Standups sind teamweit.
"""
from __future__ import annotations

import json
import shutil
import threading
import uuid
from dataclasses import asdict, dataclass, field, fields
from datetime import date, timedelta
from pathlib import Path

DATA_FILE = Path(__file__).parent / 'data' / 'pm.json'
SCHEMA = 5  # bei Aenderung der Modelle hochzaehlen -> alte Datei wird gesichert & neu geseedet

STATUSES = ['backlog', 'todo', 'doing', 'review', 'done']
STATUS_LABELS = {
    'backlog': 'Backlog', 'todo': 'To Do', 'doing': 'In Arbeit',
    'review': 'Review', 'done': 'Fertig',
}
PRIORITIES = ['niedrig', 'mittel', 'hoch', 'kritisch']
PRIORITY_COLOR = {
    'niedrig': '#8ba1a8', 'mittel': '#5b8ca3', 'hoch': '#cf8a2e', 'kritisch': '#a63a3a',
}

# Wetter als Stimmungsskala (norddeutsch)
# Nur Icons aus der klassischen "Material Icons"-Schrift verwenden – Namen wie
# "partly_cloudy_day" oder "rainy" gibt es dort nicht und wurden als Text angezeigt.
WEATHER = {
    5: ('wb_sunny', 'Sonnenschein', '#e6b422'),
    4: ('wb_cloudy', 'Heiter', '#8bbf3f'),
    3: ('cloud', 'Wolkig', '#8ba1a8'),
    2: ('water_drop', 'Regen', '#5b8ca3'),
    1: ('thunderstorm', 'Sturm', '#a63a3a'),
}


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def today_iso() -> str:
    return date.today().isoformat()


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


# --------------------------------------------------------------------------
# Modelle
# --------------------------------------------------------------------------
@dataclass
class Project:
    id: str
    name: str
    key: str = ''
    description: str = ''
    color: str = '#1f4e5f'
    archived: bool = False
    dod: list[str] = field(default_factory=list)   # Definition of Done
    dor: list[str] = field(default_factory=list)   # Definition of Ready
    budget_eur: float = 0.0
    rag: str = 'gruen'          # Ampel im Statusbericht: gruen | gelb | rot
    status_note: str = ''       # manueller Zusatz zum Statusbericht
    # Projekt-Steckbrief / Charter
    vision: str = ''
    scope_in: list[str] = field(default_factory=list)
    scope_out: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    start_date: str = ''
    target_date: str = ''
    sponsor: str = ''
    created_at: str = field(default_factory=today_iso)


RAG = {'gruen': ('Grün', '#3d7a5d'), 'gelb': ('Gelb', '#cf8a2e'), 'rot': ('Rot', '#a63a3a')}


@dataclass
class Member:
    id: str
    name: str
    role: str = ''
    weekly_hours: float = 40.0
    day_rate: float = 0.0       # interner Tagessatz in EUR (fuer die Kostensicht)
    color: str = '#1f4e5f'
    active: bool = True

    @property
    def initials(self) -> str:
        parts = [p for p in self.name.split() if p]
        return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else '')).upper() if parts else '?'


@dataclass
class Sprint:
    id: str
    project_id: str
    name: str
    goal: str = ''
    start: str = ''
    end: str = ''
    status: str = 'planned'  # planned | active | done

    @property
    def start_date(self) -> date | None:
        return _d(self.start)

    @property
    def end_date(self) -> date | None:
        return _d(self.end)

    def days(self) -> list[date]:
        s, e = self.start_date, self.end_date
        if not s or not e or e < s:
            return []
        return [s + timedelta(days=i) for i in range((e - s).days + 1)]

    def workdays(self) -> list[date]:
        return [d for d in self.days() if d.weekday() < 5]

    @property
    def weeks(self) -> float:
        wd = self.workdays()
        return round(len(wd) / 5, 2) if wd else 0.0

    @property
    def days_left(self) -> int | None:
        e = self.end_date
        return (e - date.today()).days if e else None


@dataclass
class Task:
    id: str
    project_id: str
    title: str
    description: str = ''
    status: str = 'backlog'
    estimate_h: float = 0.0
    assignee_id: str | None = None
    sprint_id: str | None = None
    priority: str = 'mittel'
    labels: list[str] = field(default_factory=list)
    github_url: str = ''
    blocked: bool = False
    blocked_reason: str = ''
    depends_on: list[str] = field(default_factory=list)
    order: float = 0.0
    created_at: str = field(default_factory=today_iso)
    started_at: str | None = None
    done_at: str | None = None
    epic_id: str | None = None


@dataclass
class Capacity:
    id: str
    sprint_id: str
    member_id: str
    hours: float = 0.0
    note: str = ''


@dataclass
class WorkLog:
    id: str
    task_id: str
    member_id: str
    date: str
    hours: float
    note: str = ''


@dataclass
class Standup:
    id: str
    date: str
    member_id: str
    yesterday: str = ''
    today: str = ''
    blocker: str = ''


RETRO_CATEGORIES = {'gut': 'Lief gut', 'schlecht': 'Lief schlecht', 'idee': 'Ideen / Experimente'}


@dataclass
class RetroNote:
    id: str
    project_id: str
    sprint_id: str
    category: str
    text: str
    author_id: str | None = None
    votes: int = 0


@dataclass
class ActionItem:
    id: str
    project_id: str
    text: str
    owner_id: str | None = None
    sprint_id: str | None = None
    done: bool = False
    created_at: str = field(default_factory=today_iso)


ABSENCE_KINDS = {'urlaub': 'Urlaub', 'krank': 'Krank', 'fortbildung': 'Fortbildung', 'sonstiges': 'Sonstiges'}


@dataclass
class Absence:
    id: str
    member_id: str
    kind: str
    start: str
    end: str
    note: str = ''

    def workdays(self) -> list[date]:
        s, e = _d(self.start), _d(self.end)
        if not s or not e or e < s:
            return []
        return [s + timedelta(days=i) for i in range((e - s).days + 1) if (s + timedelta(days=i)).weekday() < 5]


RISK_LEVEL = {'niedrig': 1, 'mittel': 2, 'hoch': 3}
RISK_STATUS = {'offen': 'Offen', 'beobachtung': 'Beobachtung', 'eingetreten': 'Eingetreten', 'geschlossen': 'Geschlossen'}


@dataclass
class Risk:
    id: str
    project_id: str
    title: str
    description: str = ''
    likelihood: str = 'mittel'
    impact: str = 'mittel'
    mitigation: str = ''
    owner_id: str | None = None
    status: str = 'offen'
    created_at: str = field(default_factory=today_iso)

    @property
    def score(self) -> int:
        return RISK_LEVEL.get(self.likelihood, 2) * RISK_LEVEL.get(self.impact, 2)


@dataclass
class Decision:
    id: str
    project_id: str
    date: str
    title: str
    context: str = ''
    decision: str = ''
    consequences: str = ''
    owner_id: str | None = None


RELEASE_STATUS = {'geplant': 'Geplant', 'in_arbeit': 'In Arbeit', 'live': 'Live'}


@dataclass
class Release:
    id: str
    project_id: str
    version: str
    date: str = ''
    status: str = 'geplant'
    notes: str = ''
    task_ids: list[str] = field(default_factory=list)


IDEA_STATUS = {'neu': 'Neu', 'geprueft': 'Geprueft', 'uebernommen': 'Uebernommen', 'abgelehnt': 'Abgelehnt'}


@dataclass
class Idea:
    id: str
    project_id: str
    title: str
    description: str = ''
    votes: int = 0
    status: str = 'neu'
    author_id: str | None = None
    created_at: str = field(default_factory=today_iso)


@dataclass
class Mood:
    """Team-Wetter: Stimmung 1 (Sturm) .. 5 (Sonnenschein) pro Sprint und Person."""
    id: str
    project_id: str
    sprint_id: str
    member_id: str
    score: int = 3
    comment: str = ''


@dataclass
class OneOnOne:
    id: str
    member_id: str
    date: str
    notes: str = ''
    talking_points: str = ''
    actions: str = ''
    next_date: str = ''


EPIC_STATUS = {'geplant': 'Geplant', 'aktiv': 'Aktiv', 'fertig': 'Fertig', 'pausiert': 'Pausiert'}


@dataclass
class Epic:
    """Initiative / Arbeitspaket oberhalb der Sprint-Ebene (fuer die Roadmap)."""
    id: str
    project_id: str
    title: str
    description: str = ''
    color: str = '#5b8ca3'
    start: str = ''
    end: str = ''
    status: str = 'geplant'


MILESTONE_STATUS = {'offen': 'Offen', 'erreicht': 'Erreicht', 'verpasst': 'Verpasst'}


@dataclass
class Milestone:
    id: str
    project_id: str
    title: str
    due: str = ''
    status: str = 'offen'
    description: str = ''


@dataclass
class Objective:
    id: str
    project_id: str
    title: str
    period: str = ''
    owner_id: str | None = None


@dataclass
class KeyResult:
    id: str
    objective_id: str
    title: str
    start_value: float = 0.0
    current_value: float = 0.0
    target_value: float = 100.0
    unit: str = '%'

    @property
    def progress(self) -> float:
        span = self.target_value - self.start_value
        if span == 0:
            return 1.0
        return max(0.0, min(1.0, (self.current_value - self.start_value) / span))


STAKEHOLDER_STANCE = {'befuerworter': 'Befürworter', 'neutral': 'Neutral', 'kritiker': 'Kritiker'}


@dataclass
class Stakeholder:
    id: str
    project_id: str
    name: str
    org: str = ''
    role: str = ''
    influence: int = 3     # 1..5  (Macht)
    interest: int = 3      # 1..5  (Interesse)
    stance: str = 'neutral'
    strategy: str = ''
    contact: str = ''

    @property
    def quadrant(self) -> str:
        hi_inf, hi_int = self.influence >= 3, self.interest >= 3
        if hi_inf and hi_int:
            return 'Eng einbinden'
        if hi_inf and not hi_int:
            return 'Zufrieden halten'
        if not hi_inf and hi_int:
            return 'Informieren'
        return 'Beobachten'


CHANGE_STATUS = {'offen': 'Offen', 'angenommen': 'Angenommen', 'abgelehnt': 'Abgelehnt'}


@dataclass
class ChangeRequest:
    id: str
    project_id: str
    title: str
    description: str = ''
    impact_hours: float = 0.0
    impact_days: int = 0
    status: str = 'offen'
    requested_by: str = ''
    date: str = field(default_factory=today_iso)


# -- Scope / Anforderungen ------------------------------------------------
MOSCOW = {'muss': 'Muss', 'soll': 'Soll', 'kann': 'Kann', 'nicht': 'Nicht'}
REQ_KIND = {'funktional': 'Funktional', 'nicht_funktional': 'Nicht-funktional', 'randbedingung': 'Randbedingung'}
REQ_STATUS = {'entwurf': 'Entwurf', 'abgestimmt': 'Abgestimmt', 'umgesetzt': 'Umgesetzt', 'abgenommen': 'Abgenommen'}


@dataclass
class Requirement:
    id: str
    project_id: str
    title: str
    kind: str = 'funktional'
    moscow: str = 'soll'
    status: str = 'entwurf'
    acceptance: str = ''
    note: str = ''
    task_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=today_iso)


# -- Qualitaet / Bugs ---------------------------------------------------
BUG_SEVERITY = {'kritisch': 'Kritisch', 'hoch': 'Hoch', 'mittel': 'Mittel', 'niedrig': 'Niedrig'}
BUG_STATUS = {'offen': 'Offen', 'in_arbeit': 'In Arbeit', 'behoben': 'Behoben', 'verifiziert': 'Verifiziert', 'wontfix': "Won't fix"}


@dataclass
class Bug:
    id: str
    project_id: str
    title: str
    description: str = ''
    severity: str = 'mittel'
    status: str = 'offen'
    environment: str = 'test'      # wo gefunden
    component: str = ''
    reporter_id: str | None = None
    assignee_id: str | None = None
    reopened: int = 0
    created_at: str = field(default_factory=today_iso)
    resolved_at: str | None = None


# -- Umgebungen & Deployments ----------------------------------------
ENV_STATUS = {'ok': 'OK', 'degraded': 'Eingeschränkt', 'down': 'Ausfall', 'wartung': 'Wartung'}


@dataclass
class Environment:
    id: str
    project_id: str
    name: str                      # dev | test | staging | prod ...
    url: str = ''
    version: str = ''
    status: str = 'ok'
    owner_id: str | None = None
    last_deploy: str = ''
    note: str = ''
    order: float = 0.0


@dataclass
class Deployment:
    id: str
    project_id: str
    environment: str
    version: str
    date: str = field(default_factory=today_iso)
    by: str = ''
    status: str = 'erfolgreich'    # erfolgreich | fehlgeschlagen | rollback
    note: str = ''


# -- Incidents / Betrieb -------------------------------------------
INCIDENT_SEV = {'sev1': 'SEV1 – kritisch', 'sev2': 'SEV2 – hoch', 'sev3': 'SEV3 – gering'}
INCIDENT_STATUS = {'offen': 'Offen', 'untersuchung': 'Untersuchung', 'behoben': 'Behoben', 'postmortem': 'Postmortem', 'geschlossen': 'Geschlossen'}


@dataclass
class Incident:
    id: str
    project_id: str
    title: str
    severity: str = 'sev2'
    status: str = 'offen'
    started_at: str = field(default_factory=today_iso)
    resolved_at: str | None = None
    impact: str = ''
    cause: str = ''
    postmortem: str = ''
    actions: str = ''
    lead_id: str | None = None


# -- Besprechungen ------------------------------------------------
MEETING_KINDS = {'steering': 'Steering', 'planung': 'Planung', 'review': 'Review',
                 'sync': 'Sync', 'workshop': 'Workshop', 'sonstiges': 'Sonstiges'}


@dataclass
class Meeting:
    id: str
    project_id: str
    title: str
    kind: str = 'sync'
    date: str = field(default_factory=today_iso)
    attendees: list[str] = field(default_factory=list)
    agenda: str = ''
    notes: str = ''
    decisions: str = ''
    actions: str = ''


# -- Dokumente ---------------------------------------------------
DOC_CATEGORIES = {'spec': 'Spezifikation', 'design': 'Design', 'vertrag': 'Vertrag',
                  'betrieb': 'Betrieb', 'bericht': 'Bericht', 'sonstiges': 'Sonstiges'}


@dataclass
class Document:
    id: str
    project_id: str
    title: str
    category: str = 'spec'
    url: str = ''
    owner_id: str | None = None
    updated: str = field(default_factory=today_iso)
    note: str = ''


# -- Lieferanten / Lizenzen ------------------------------------
VENDOR_KINDS = {'dienst': 'SaaS / Dienst', 'lizenz': 'Lizenz', 'dienstleister': 'Dienstleister', 'hardware': 'Hardware'}
COST_CYCLES = {'einmalig': 'einmalig', 'monatlich': 'monatlich', 'jaehrlich': 'jährlich'}


@dataclass
class Vendor:
    id: str
    project_id: str
    name: str
    kind: str = 'dienst'
    cost: float = 0.0
    cost_cycle: str = 'monatlich'
    renewal: str = ''
    owner_id: str | None = None
    active: bool = True
    note: str = ''

    @property
    def yearly(self) -> float:
        return {'einmalig': 0.0, 'monatlich': 12.0, 'jaehrlich': 1.0}[self.cost_cycle] * self.cost


# -- RACI --------------------------------------------------
RACI_LETTERS = {'R': 'Responsible', 'A': 'Accountable', 'C': 'Consulted', 'I': 'Informed'}


@dataclass
class RaciArea:
    id: str
    project_id: str
    name: str
    roles: dict = field(default_factory=dict)   # member_id -> 'R'|'A'|'C'|'I'
    order: float = 0.0


# -- Lessons Learned ------------------------------------
@dataclass
class Lesson:
    id: str
    project_id: str
    title: str
    category: str = 'prozess'      # prozess | technik | team | stakeholder | schaetzung
    situation: str = ''
    recommendation: str = ''
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=today_iso)


_MODELS = {
    'projects': Project, 'members': Member, 'sprints': Sprint, 'tasks': Task,
    'capacities': Capacity, 'worklogs': WorkLog, 'standups': Standup,
    'retro_notes': RetroNote, 'action_items': ActionItem, 'absences': Absence,
    'risks': Risk, 'decisions': Decision, 'releases': Release, 'ideas': Idea,
    'moods': Mood, 'one_on_ones': OneOnOne, 'epics': Epic, 'milestones': Milestone,
    'objectives': Objective, 'key_results': KeyResult, 'stakeholders': Stakeholder,
    'change_requests': ChangeRequest, 'requirements': Requirement, 'bugs': Bug,
    'environments': Environment, 'deployments': Deployment, 'incidents': Incident,
    'meetings': Meeting, 'documents': Document, 'vendors': Vendor,
    'raci_areas': RaciArea, 'lessons': Lesson,
}


# --------------------------------------------------------------------------
# Store
# --------------------------------------------------------------------------
class Store:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        for key in _MODELS:
            setattr(self, key, [])
        self.current_project_id: str | None = None
        self._listeners: list = []

    # -- Laden / Speichern ------------------------------------------------
    def load(self) -> 'Store':
        if DATA_FILE.exists():
            raw = json.loads(DATA_FILE.read_text('utf-8'))
            if raw.get('_schema') != SCHEMA:
                backup = DATA_FILE.with_suffix('.bak')
                shutil.copy(DATA_FILE, backup)
                print(f'[store] Schema {raw.get("_schema")} != {SCHEMA} – alte Daten gesichert nach {backup.name}, seede neu.')
                seed(self)
                self.save()
                return self
            for key, cls in _MODELS.items():
                names = {f.name for f in fields(cls)}
                setattr(self, key, [
                    cls(**{k: v for k, v in row.items() if k in names})
                    for row in raw.get(key, [])
                ])
            self.current_project_id = raw.get('current_project')
        else:
            seed(self)
            self.save()
        if not self.by_id('projects', self.current_project_id):
            self.current_project_id = self.projects[0].id if self.projects else None
        return self

    def save(self) -> None:
        with self._lock:
            DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            payload = {key: [asdict(x) for x in getattr(self, key)] for key in _MODELS}
            payload['_schema'] = SCHEMA
            payload['current_project'] = self.current_project_id
            tmp = DATA_FILE.with_suffix('.tmp')
            tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), 'utf-8')
            tmp.replace(DATA_FILE)
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:  # noqa: BLE001
                pass

    def on_change(self, callback) -> None:
        self._listeners.append(callback)

    # -- generische Helfer ------------------------------------------------
    def add(self, listname: str, cls, **kw):
        obj = cls(id=_uid(), **kw)
        getattr(self, listname).append(obj)
        self.save()
        return obj

    def update(self, obj, **kw) -> None:
        for k, v in kw.items():
            setattr(obj, k, v)
        self.save()

    def remove(self, listname: str, oid: str) -> None:
        setattr(self, listname, [x for x in getattr(self, listname) if x.id != oid])
        self.save()

    def by_id(self, listname: str, oid: str | None):
        return next((x for x in getattr(self, listname) if x.id == oid), None)

    # -- Projekte -------------------------------------------------------
    @property
    def project(self) -> Project | None:
        return self.by_id('projects', self.current_project_id)

    @property
    def pid(self) -> str | None:
        return self.current_project_id

    @property
    def active_projects(self) -> list[Project]:
        return [p for p in self.projects if not p.archived]

    def set_current_project(self, pid: str) -> None:
        self.current_project_id = pid
        self.save()

    def _scoped(self, listname: str, pid: str | None = None):
        pid = pid or self.current_project_id
        return [x for x in getattr(self, listname) if getattr(x, 'project_id', None) == pid]

    def p_sprints(self, pid: str | None = None) -> list[Sprint]:
        return sorted(self._scoped('sprints', pid), key=lambda s: s.start or '')

    def p_tasks(self, pid: str | None = None) -> list[Task]:
        return self._scoped('tasks', pid)

    def p_releases(self, pid: str | None = None) -> list[Release]:
        return self._scoped('releases', pid)

    def p_risks(self, pid: str | None = None) -> list[Risk]:
        return self._scoped('risks', pid)

    def p_decisions(self, pid: str | None = None) -> list[Decision]:
        return self._scoped('decisions', pid)

    def p_ideas(self, pid: str | None = None) -> list[Idea]:
        return self._scoped('ideas', pid)

    def p_action_items(self, pid: str | None = None) -> list[ActionItem]:
        return self._scoped('action_items', pid)

    def p_retro_notes(self, pid: str | None = None) -> list[RetroNote]:
        return self._scoped('retro_notes', pid)

    def p_epics(self, pid: str | None = None) -> list[Epic]:
        return self._scoped('epics', pid)

    def p_milestones(self, pid: str | None = None) -> list[Milestone]:
        return sorted(self._scoped('milestones', pid), key=lambda x: x.due or '')

    def p_objectives(self, pid: str | None = None) -> list[Objective]:
        return self._scoped('objectives', pid)

    def p_stakeholders(self, pid: str | None = None) -> list[Stakeholder]:
        return self._scoped('stakeholders', pid)

    def p_changes(self, pid: str | None = None) -> list[ChangeRequest]:
        return self._scoped('change_requests', pid)

    def p_requirements(self, pid: str | None = None) -> list[Requirement]:
        return self._scoped('requirements', pid)

    def p_bugs(self, pid: str | None = None) -> list[Bug]:
        return self._scoped('bugs', pid)

    def p_environments(self, pid: str | None = None) -> list[Environment]:
        return sorted(self._scoped('environments', pid), key=lambda e: e.order)

    def p_deployments(self, pid: str | None = None) -> list[Deployment]:
        return sorted(self._scoped('deployments', pid), key=lambda d: d.date, reverse=True)

    def p_incidents(self, pid: str | None = None) -> list[Incident]:
        return sorted(self._scoped('incidents', pid), key=lambda i: i.started_at, reverse=True)

    def p_meetings(self, pid: str | None = None) -> list[Meeting]:
        return sorted(self._scoped('meetings', pid), key=lambda m: m.date, reverse=True)

    def p_documents(self, pid: str | None = None) -> list[Document]:
        return sorted(self._scoped('documents', pid), key=lambda d: d.title.lower())

    def p_vendors(self, pid: str | None = None) -> list[Vendor]:
        return self._scoped('vendors', pid)

    def p_raci(self, pid: str | None = None) -> list[RaciArea]:
        return sorted(self._scoped('raci_areas', pid), key=lambda a: a.order)

    def p_lessons(self, pid: str | None = None) -> list[Lesson]:
        return self._scoped('lessons', pid)

    # -- abgeleitete Kennzahlen -------------------------------------
    def quality_stats(self, pid: str | None = None) -> dict:
        bugs = self.p_bugs(pid)
        opn = [b for b in bugs if b.status in ('offen', 'in_arbeit')]
        return {
            'open': len(opn),
            'by_sev': {s: len([b for b in opn if b.severity == s]) for s in BUG_SEVERITY},
            'critical_open': len([b for b in opn if b.severity in ('kritisch', 'hoch')]),
            'escaped': len([b for b in bugs if b.environment == 'prod']),
            'reopened': sum(b.reopened for b in bugs),
            'resolved': len([b for b in bugs if b.status in ('behoben', 'verifiziert')]),
            'total': len(bugs),
        }

    def vendor_cost_yearly(self, pid: str | None = None) -> float:
        return round(sum(v.yearly for v in self.p_vendors(pid) if v.active), 2)

    def open_incidents(self, pid: str | None = None) -> list[Incident]:
        return [i for i in self.p_incidents(pid) if i.status not in ('geschlossen',)]

    def krs_of(self, objective_id: str) -> list[KeyResult]:
        return [k for k in self.key_results if k.objective_id == objective_id]

    def objective_progress(self, objective_id: str) -> float:
        krs = self.krs_of(objective_id)
        return round(sum(k.progress for k in krs) / len(krs), 3) if krs else 0.0

    # -- Kosten -----------------------------------------------------
    def _rate_per_hour(self, member_id: str | None) -> float:
        m = self.member(member_id)
        avg = [x.day_rate for x in self.active_members if x.day_rate] or [0]
        rate = (m.day_rate if m and m.day_rate else sum(avg) / len(avg))
        return rate / 8.0

    def project_cost(self, pid: str) -> dict:
        tasks = self.p_tasks(pid)
        planned = sum(t.estimate_h * self._rate_per_hour(t.assignee_id) for t in tasks)
        actual = 0.0
        task_ids = {t.id for t in tasks}
        for w in self.worklogs:
            if w.task_id in task_ids:
                actual += w.hours * self._rate_per_hour(w.member_id)
        remaining = sum(max(0.0, t.estimate_h - self.logged_for_task(t.id))
                        * self._rate_per_hour(t.assignee_id)
                        for t in tasks if t.status != 'done')
        proj = self.by_id('projects', pid)
        budget = proj.budget_eur if proj else 0.0
        return {'planned': round(planned), 'actual': round(actual),
                'eac': round(actual + remaining), 'budget': round(budget),
                'remaining': round(remaining)}

    # -- Statusbericht -------------------------------------------
    def weekly_report(self, pid: str) -> dict:
        monday = date.today() - timedelta(days=date.today().weekday())
        tasks = self.p_tasks(pid)
        done_week = [t for t in tasks if t.done_at and _d(t.done_at) >= monday]
        blockers = [t for t in tasks if t.blocked and t.status != 'done']
        risks = [r for r in self.p_risks(pid) if r.status not in ('geschlossen',) and r.score >= 4]
        soon = date.today() + timedelta(days=21)
        ms = [m for m in self.p_milestones(pid)
              if m.status == 'offen' and m.due and _d(m.due) <= soon]
        sp = self.active_sprint_of(pid)
        next_up = []
        if sp:
            next_up = [t for t in tasks if t.sprint_id == sp.id and t.status in ('todo', 'doing')]
        q = self.quality_stats(pid)
        return {'done_week': done_week, 'blockers': blockers, 'risks': risks,
                'milestones': ms, 'next': next_up, 'sprint': sp,
                'incidents': self.open_incidents(pid),
                'bugs_critical': q['critical_open'], 'bugs_open': q['open'],
                'changes_open': [c for c in self.p_changes(pid) if c.status == 'offen']}

    # -- Lookups ------------------------------------------------------
    def member(self, mid: str | None) -> Member | None:
        return self.by_id('members', mid)

    def sprint(self, sid: str | None) -> Sprint | None:
        return self.by_id('sprints', sid)

    def task(self, tid: str | None) -> Task | None:
        return self.by_id('tasks', tid)

    @property
    def active_members(self) -> list[Member]:
        return [m for m in self.members if m.active]

    def active_sprint_of(self, pid: str) -> Sprint | None:
        return next((s for s in self.sprints if s.project_id == pid and s.status == 'active'), None)

    @property
    def active_sprint(self) -> Sprint | None:
        return self.active_sprint_of(self.current_project_id) if self.current_project_id else None

    def sprint_tasks(self, sid: str | None) -> list[Task]:
        return sorted((t for t in self.tasks if t.sprint_id == sid),
                      key=lambda t: (STATUSES.index(t.status), t.order))

    def backlog_tasks(self, pid: str | None = None) -> list[Task]:
        pid = pid or self.current_project_id
        return sorted((t for t in self.tasks if t.project_id == pid and not t.sprint_id),
                      key=lambda t: t.order)

    # -- Mutationen -------------------------------------------------
    def add_member(self, **kw) -> Member:
        return self.add('members', Member, **kw)

    def add_sprint(self, **kw) -> Sprint:
        return self.add('sprints', Sprint, **kw)

    def activate_sprint(self, sid: str) -> None:
        target = self.sprint(sid)
        if not target:
            return
        for s in self.sprints:
            if s.project_id == target.project_id and s.status == 'active':
                s.status = 'done'
        target.status = 'active'
        self.save()

    def add_task(self, **kw) -> Task:
        order = max((t.order for t in self.tasks), default=0.0) + 1
        return self.add('tasks', Task, order=order, **kw)

    def set_task_status(self, tid: str, status: str) -> None:
        t = self.task(tid)
        if not t:
            return
        t.status = status
        if status in ('doing', 'review', 'done') and not t.started_at:
            t.started_at = today_iso()
        if status == 'done':
            t.done_at = t.done_at or today_iso()
        else:
            t.done_at = None
        self.save()

    def delete_task(self, tid: str) -> None:
        self.tasks = [t for t in self.tasks if t.id != tid]
        self.worklogs = [w for w in self.worklogs if w.task_id != tid]
        for t in self.tasks:
            if tid in t.depends_on:
                t.depends_on = [d for d in t.depends_on if d != tid]
        self.save()

    def set_capacity(self, sprint_id: str, member_id: str, hours: float, note: str = '') -> None:
        cap = next((c for c in self.capacities
                    if c.sprint_id == sprint_id and c.member_id == member_id), None)
        if cap:
            cap.hours, cap.note = hours, note
        else:
            self.capacities.append(Capacity(_uid(), sprint_id, member_id, hours, note))
        self.save()

    def capacity_of(self, sprint_id: str, member_id: str) -> Capacity | None:
        return next((c for c in self.capacities
                     if c.sprint_id == sprint_id and c.member_id == member_id), None)

    def add_worklog(self, **kw) -> WorkLog:
        return self.add('worklogs', WorkLog, **kw)

    def delete_worklog(self, wid: str) -> None:
        self.remove('worklogs', wid)

    def standup_for(self, day: str, member_id: str) -> Standup | None:
        return next((s for s in self.standups if s.date == day and s.member_id == member_id), None)

    def upsert_standup(self, day: str, member_id: str, **fields_) -> None:
        s = self.standup_for(day, member_id)
        if s:
            for k, v in fields_.items():
                setattr(s, k, v)
        else:
            self.standups.append(Standup(_uid(), day, member_id, **fields_))
        self.save()

    def set_mood(self, project_id: str, sprint_id: str, member_id: str, score: int, comment: str = '') -> None:
        m = next((x for x in self.moods if x.sprint_id == sprint_id and x.member_id == member_id), None)
        if m:
            m.score, m.comment = score, comment
        else:
            self.moods.append(Mood(_uid(), project_id, sprint_id, member_id, score, comment))
        self.save()

    def reset(self, *, demo: bool) -> None:
        for key in _MODELS:
            setattr(self, key, [])
        self.current_project_id = None
        if demo:
            seed(self)
        else:
            self.projects.append(Project(_uid(), 'Neues Projekt', 'PRJ'))
            self.current_project_id = self.projects[0].id
        self.save()

    # -- Kennzahlen ------------------------------------------------
    def logged_for_task(self, tid: str) -> float:
        return sum(w.hours for w in self.worklogs if w.task_id == tid)

    def committed_hours(self, sid: str) -> float:
        return sum(t.estimate_h for t in self.tasks if t.sprint_id == sid)

    def done_hours(self, sid: str) -> float:
        return sum(t.estimate_h for t in self.tasks if t.sprint_id == sid and t.status == 'done')

    def logged_hours(self, sid: str) -> float:
        ids = {t.id for t in self.tasks if t.sprint_id == sid}
        return sum(w.hours for w in self.worklogs if w.task_id in ids)

    def absence_hours(self, member: Member, sprint: Sprint) -> float:
        sprint_days = set(sprint.workdays())
        if not sprint_days:
            return 0.0
        per_day = member.weekly_hours / 5
        days_off = {d for a in self.absences if a.member_id == member.id
                    for d in a.workdays() if d in sprint_days}
        return round(len(days_off) * per_day, 1)

    def member_richtwert(self, sprint: Sprint, member: Member) -> float:
        return round(max(0.0, member.weekly_hours * sprint.weeks - self.absence_hours(member, sprint)), 1)

    def capacity_hours(self, sprint: Sprint) -> float:
        declared = [c.hours for c in self.capacities if c.sprint_id == sprint.id]
        if declared:
            return sum(declared)
        return round(sum(self.member_richtwert(sprint, m) for m in self.active_members), 1)

    def member_load(self, sid: str, member_id: str) -> float:
        return sum(t.estimate_h for t in self.tasks
                   if t.sprint_id == sid and t.assignee_id == member_id)

    def dependency_warnings(self, pid: str | None = None) -> list[tuple[Task, Task]]:
        """(Task, blockierender Task), wo der Vorlaeufer noch nicht fertig ist."""
        out = []
        for t in self.p_tasks(pid):
            if t.status == 'done':
                continue
            for dep_id in t.depends_on:
                dep = self.task(dep_id)
                if dep and dep.status != 'done':
                    out.append((t, dep))
        return out

    # -- Metriken (projektbezogen) --------------------------------
    def velocity_history(self, pid: str | None = None):
        seq = [s for s in self.p_sprints(pid) if s.status in ('done', 'active')]
        return [(s, self.committed_hours(s.id), self.done_hours(s.id)) for s in seq]

    def avg_velocity(self, n: int = 3, pid: str | None = None) -> float:
        done = [self.done_hours(s.id) for s in self.p_sprints(pid) if s.status == 'done']
        done = done[-n:]
        return round(sum(done) / len(done), 1) if done else 0.0

    def lead_times(self, pid: str | None = None) -> list[int]:
        return [(_d(t.done_at) - _d(t.created_at)).days for t in self.p_tasks(pid)
                if t.done_at and t.created_at]

    def cycle_times(self, pid: str | None = None) -> list[int]:
        return [max(0, (_d(t.done_at) - _d(t.started_at)).days) for t in self.p_tasks(pid)
                if t.done_at and t.started_at]

    def throughput_by_week(self, weeks: int = 8, pid: str | None = None) -> dict[str, int]:
        monday = date.today() - timedelta(days=date.today().weekday())
        buckets = {(monday - timedelta(weeks=i)): 0 for i in range(weeks)}
        for t in self.p_tasks(pid):
            if not t.done_at:
                continue
            d = _d(t.done_at)
            wk = d - timedelta(days=d.weekday())
            if wk in buckets:
                buckets[wk] += 1
        return {k.strftime('%d.%m.'): v for k, v in sorted(buckets.items())}

    def forecast_sprints(self, pid: str | None = None) -> tuple[float, float, float]:
        backlog = sum(t.estimate_h for t in self.p_tasks(pid) if t.status != 'done' and not t.sprint_id)
        vel = self.avg_velocity(pid=pid)
        needed = round(backlog / vel, 1) if vel else 0.0
        return round(backlog, 1), vel, needed

    def project_health(self, pid: str) -> dict:
        sp = self.active_sprint_of(pid)
        tasks = self.p_tasks(pid)
        open_risks = [r for r in self.p_risks(pid) if r.status not in ('geschlossen',)]
        blocked = [t for t in tasks if t.blocked and t.status != 'done']
        committed = self.committed_hours(sp.id) if sp else 0.0
        done = self.done_hours(sp.id) if sp else 0.0
        moods = [m.score for m in self.moods if m.project_id == pid and (not sp or m.sprint_id == sp.id)]
        return {
            'sprint': sp,
            'progress': (done / committed) if committed else 0.0,
            'committed': committed, 'done': done,
            'open_tasks': len([t for t in tasks if t.status != 'done']),
            'blocked': len(blocked),
            'high_risks': len([r for r in open_risks if r.score >= 6]),
            'open_risks': len(open_risks),
            'incidents': len(self.open_incidents(pid)),
            'bugs_critical': self.quality_stats(pid)['critical_open'],
            'mood': round(sum(moods) / len(moods), 1) if moods else None,
        }

    def burndown(self, sprint: Sprint) -> dict:
        workdays = sprint.workdays()
        if not workdays:
            return {'days': [], 'ideal': [], 'remaining': [], 'logged': []}
        sprint_tasks = [t for t in self.tasks if t.sprint_id == sprint.id]
        total = sum(t.estimate_h for t in sprint_tasks) or self.committed_hours(sprint.id)
        ids = {t.id for t in sprint_tasks}
        n = len(workdays)
        ideal, remaining, logged = [], [], []
        for i, d in enumerate(workdays):
            ideal.append(round(total * (1 - i / (n - 1)), 1) if n > 1 else 0.0)
            remaining.append(round(sum(
                t.estimate_h for t in sprint_tasks if not t.done_at or _d(t.done_at) > d), 1))
            logged.append(round(sum(
                w.hours for w in self.worklogs
                if w.task_id in ids and _d(w.date) and _d(w.date) <= d), 1))
        return {'days': [d.strftime('%d.%m.') for d in workdays],
                'ideal': ideal, 'remaining': remaining, 'logged': logged}


# --------------------------------------------------------------------------
# Demo-/Startdaten – generisch (Softwareentwicklung, mehrere Projekte)
# --------------------------------------------------------------------------
def seed(s: Store) -> None:
    tim = Member(_uid(), 'Tim Klein', 'Teamleiter', 20.0, 720, '#1f4e5f')
    d1 = Member(_uid(), 'Anke Brahms', 'Senior Backend', 40.0, 780, '#5b8ca3')
    d2 = Member(_uid(), 'Jan Petersen', 'Backend', 40.0, 640, '#3d7a5d')
    d3 = Member(_uid(), 'Maike Onken', 'Frontend / UX', 32.0, 620, '#b5533a')
    d4 = Member(_uid(), 'Sören Dähn', 'Fullstack', 36.0, 660, '#7a5c99')
    qa = Member(_uid(), 'Frauke Lührs', 'QA / Test', 24.0, 560, '#cf8a2e')
    s.members = [tim, d1, d2, d3, d4, qa]

    monday = date.today() - timedelta(days=date.today().weekday())

    def sprint_block(project, num, offset_weeks, status, goal=''):
        st = monday + timedelta(weeks=offset_weeks)
        return Sprint(_uid(), project.id, f'Sprint {num}', goal,
                      st.isoformat(), (st + timedelta(days=11)).isoformat(), status)

    def T(project, sprint, title, status, est, who, prio='mittel', labels=None,
          blocked=False, reason='', deps=None):
        created = (sprint.start if sprint else monday.isoformat())
        return Task(_uid(), project.id, title, '', status, est, who.id if who else None,
                    sprint.id if sprint else None, prio, labels or [], '', blocked, reason,
                    deps or [], 0.0, created)

    # ---- Projekt 1: Webshop-Relaunch (voll bestueckt) -------------------
    p1 = Project(_uid(), 'Webshop-Relaunch', 'WEB',
                 'Ablösung des Alt-Shops durch eine headless Storefront.', '#1f4e5f',
                 dod=['Code-Review durch 2. Person', 'Tests gruen', 'Doku aktualisiert',
                      'auf Staging abgenommen', 'keine offenen Blocker'])
    p1s = [sprint_block(p1, n, w, st) for n, w, st in
           [(7, -6, 'done'), (8, -4, 'done'), (9, -2, 'active'), (10, 0, 'planned')]]
    p1s[2].goal = 'Checkout end-to-end funktionsfaehig, Zahlungsanbindung steht.'
    p1s[3].goal = 'Suche & Filter produktiv.'
    active1 = p1s[2]

    p1_tasks = [
        T(p1, None, 'Alt-Shop: Redirect-Map für SEO', 'backlog', 8, None, 'mittel', ['seo']),
        T(p1, None, 'Wunschliste für Gäste', 'backlog', 5, None, 'niedrig'),
        T(p1, None, 'A/B-Test-Framework einbinden', 'backlog', 13, None, 'mittel'),
        T(p1, active1, 'Checkout: Adress-Validierung', 'done', 5, d2, 'hoch', ['checkout']),
        T(p1, active1, 'Zahlungsanbindung Stripe', 'doing', 13, d1, 'kritisch', ['checkout', 'payment']),
        T(p1, active1, 'Warenkorb: Mengen-Update ohne Reload', 'done', 5, d4, 'mittel', ['cart']),
        T(p1, active1, 'Bestellbestätigung per E-Mail', 'review', 3, d2, 'mittel'),
        T(p1, active1, 'Fehlerseite 500 mit Support-Kontakt', 'todo', 2, d3, 'niedrig'),
        T(p1, active1, 'Checkout-Flow QA-Durchlauf', 'doing', 5, qa, 'hoch', ['qa']),
        T(p1, active1, 'Lasttest Checkout (500 parallele Sessions)', 'todo', 5, qa, 'hoch', ['qa'],
          blocked=True, reason='Wartet auf Freigabe der Last-Test-Umgebung'),
        T(p1, active1, 'Design-Review Checkout mit Fachbereich', 'doing', 3, tim, 'mittel'),
        T(p1, active1, 'Sprint-9-Demo vorbereiten', 'todo', 2, tim, 'mittel'),
    ]
    for j in range(4):  # Alt-Sprint-Tasks fuer Velocity
        for n, sp in ((7, p1s[0]), (8, p1s[1])):
            dd = sp.start_date + timedelta(days=2 + j)
            p1_tasks.append(Task(_uid(), p1.id, f'S{n}-Aufgabe {j + 1}', '', 'done',
                                 [5, 8, 3, 5][j], s.members[1 + j % 5].id, sp.id, 'mittel', [], '',
                                 False, '', [], 0.0, sp.start, sp.start, dd.isoformat()))

    # ---- Projekt 2: Mobile-App (mittel) --------------------------------
    p2 = Project(_uid(), 'Mobile-App', 'APP',
                 'Native App für iOS/Android mit Offline-Modus.', '#b5533a')
    p2s = [sprint_block(p2, n, w, st) for n, w, st in [(3, -2, 'active'), (4, 0, 'planned')]]
    active2 = p2s[0]
    active2.goal = 'Offline-Sync stabil, Push-Notifications angebunden.'
    p2_tasks = [
        T(p2, None, 'Biometrie-Login', 'backlog', 8, None, 'mittel'),
        T(p2, None, 'Deep-Links aus E-Mails', 'backlog', 5, None, 'niedrig'),
        T(p2, active2, 'Offline-Queue für Mutationen', 'doing', 13, d4, 'hoch', ['offline']),
        T(p2, active2, 'Konfliktauflösung beim Sync', 'todo', 8, d1, 'hoch', ['offline'],
          deps=[]),
        T(p2, active2, 'Push-Notifications (FCM/APNs)', 'doing', 8, d2, 'mittel'),
        T(p2, active2, 'Onboarding-Screens', 'done', 5, d3, 'niedrig', ['ux']),
        T(p2, active2, 'Crash-Reporting einbinden', 'done', 2, d4, 'mittel'),
        T(p2, active2, 'Regressionstest Sync-Szenarien', 'todo', 5, qa, 'hoch', ['qa']),
    ]
    # Abhaengigkeit setzen: Konfliktaufloesung haengt an Offline-Queue
    p2_tasks[3].depends_on = [p2_tasks[2].id]

    # ---- Projekt 3: Plattform-Migration (Planungsphase) ---------------
    p3 = Project(_uid(), 'Plattform-Migration', 'INF',
                 'Umzug der Dienste in die neue Cloud-Umgebung.', '#3d7a5d')
    p3s = [sprint_block(p3, 1, 2, 'planned')]
    p3s[0].goal = 'Erste zwei Dienste laufen in der neuen Umgebung.'
    p3_tasks = [
        T(p3, None, 'Infrastruktur als Code (Terraform-Grundgerüst)', 'backlog', 13, None, 'hoch', ['infra']),
        T(p3, None, 'Secrets-Management umstellen', 'backlog', 8, None, 'hoch', ['infra']),
        T(p3, None, 'CI/CD-Pipeline auf neue Registry', 'backlog', 8, None, 'mittel'),
        T(p3, None, 'Monitoring & Alerting neu aufsetzen', 'backlog', 8, None, 'mittel'),
        T(p3, None, 'Datenbank-Migration Dienst A', 'backlog', 13, None, 'kritisch', ['db']),
        T(p3, p3s[0], 'Netzwerk-Konzept abstimmen', 'todo', 5, tim, 'hoch'),
    ]

    s.projects = [p1, p2, p3]
    s.sprints = p1s + p2s + p3s
    s.tasks = p1_tasks + p2_tasks + p3_tasks
    s.current_project_id = p1.id

    # started_at / done_at fuer laufende & fertige Tasks
    for proj_active in (active1, active2):
        wd = proj_active.workdays()
        for i, t in enumerate([x for x in s.tasks if x.sprint_id == proj_active.id]):
            if t.status in ('doing', 'review', 'done') and not t.started_at:
                t.started_at = (wd[1] if len(wd) > 1 else proj_active.start_date).isoformat()
            if t.status == 'done' and not t.done_at:
                t.done_at = (wd[min(2 + i, len(wd) - 1)] if wd else proj_active.start_date).isoformat()

    # Kapazitaeten fuer die aktiven Sprints
    for m, h in [(tim, 8), (d1, 60), (d2, 64), (d4, 40), (qa, 30)]:
        s.capacities.append(Capacity(_uid(), active1.id, m.id, float(h)))
    for m, h in [(d1, 20), (d2, 30), (d3, 40), (d4, 55), (qa, 25)]:
        s.capacities.append(Capacity(_uid(), active2.id, m.id, float(h)))

    # Stundenbuchungen fuer active1
    wd = active1.workdays()
    booked = [t for t in s.tasks if t.sprint_id == active1.id and t.assignee_id
              and t.status in ('done', 'doing', 'review')]
    for i, t in enumerate(booked):
        target = t.estimate_h * (1.0 if t.status == 'done' else 0.45)
        per_day = round(target / 3, 1) if target else 0
        for d in wd[i % 2: i % 2 + 3]:
            if per_day:
                s.worklogs.append(WorkLog(_uid(), t.id, t.assignee_id, d.isoformat(), per_day))

    today = today_iso()
    s.standups = [
        Standup(_uid(), today, d1.id, 'Stripe-Sandbox angebunden', 'Webhooks & Fehlerfälle', ''),
        Standup(_uid(), today, d2.id, 'Bestätigungsmail fertig', 'Review-Kommentare einarbeiten', ''),
        Standup(_uid(), today, d4.id, 'Offline-Queue-Prototyp', 'Persistenz mit SQLite', ''),
        Standup(_uid(), today, qa.id, 'Checkout-Testfälle', 'Lasttest vorbereiten',
                'Last-Test-Umgebung noch nicht freigegeben'),
    ]

    s.retro_notes = [
        RetroNote(_uid(), p1.id, active1.id, 'gut', 'Pairing bei der Stripe-Anbindung war effektiv', d1.id, 3),
        RetroNote(_uid(), p1.id, active1.id, 'gut', 'Klare Akzeptanzkriterien diesmal', tim.id, 2),
        RetroNote(_uid(), p1.id, active1.id, 'schlecht', 'Zu viele Kontextwechsel wegen Support', d2.id, 4),
        RetroNote(_uid(), p1.id, active1.id, 'schlecht', 'Test-Umgebung zu spät angefragt', qa.id, 3),
        RetroNote(_uid(), p1.id, active1.id, 'idee', 'Feste Fokus-Zeit ohne Meetings (Di/Do vormittags)', tim.id, 5),
    ]
    s.action_items = [
        ActionItem(_uid(), p1.id, 'Support-Rotation einführen (1 Person/Woche)', tim.id, active1.id, False),
        ActionItem(_uid(), p1.id, 'Test-Umgebungen früh im Sprint anfragen (Checkliste)', qa.id, active1.id, False),
        ActionItem(_uid(), p1.id, 'Fokus-Zeit im Kalender blocken', tim.id, active1.id, True),
    ]

    s.absences = [
        Absence(_uid(), d3.id, 'urlaub', (monday + timedelta(days=2)).isoformat(),
                (monday + timedelta(days=6)).isoformat(), 'lange geplant'),
        Absence(_uid(), qa.id, 'fortbildung', (monday + timedelta(days=15)).isoformat(),
                (monday + timedelta(days=16)).isoformat(), 'Testautomatisierung'),
        Absence(_uid(), d1.id, 'urlaub', (monday + timedelta(days=21)).isoformat(),
                (monday + timedelta(days=32)).isoformat(), ''),
    ]

    s.risks = [
        Risk(_uid(), p1.id, 'Zahlungsanbieter-Zertifizierung (PCI) verzögert Go-Live',
             'Ohne abgeschlossene Prüfung kein produktiver Zahlungsverkehr.',
             'mittel', 'hoch', 'Zertifizierungspartner früh eingebunden, Checkliste abgearbeitet',
             tim.id, 'beobachtung'),
        Risk(_uid(), p1.id, 'SEO-Einbruch nach Relaunch',
             'Fehlende Redirects kosten Rankings und Umsatz.',
             'mittel', 'hoch', 'Vollständige Redirect-Map + Monitoring der Rankings ab Tag 1',
             d3.id, 'offen'),
        Risk(_uid(), p1.id, 'Wissen zur Legacy-Preislogik nur bei einer Person',
             'Bus-Faktor 1 bei der Migration der Rabattregeln.', 'mittel', 'hoch',
             'Doku-Session + Pairing eingeplant', tim.id, 'offen'),
        Risk(_uid(), p2.id, 'App-Store-Review-Zeiten unkalkulierbar',
             'Release-Termine können durch Ablehnung rutschen.',
             'hoch', 'mittel', 'Puffer von 1 Woche vor jedem Release, Review-Guidelines-Check',
             d4.id, 'offen'),
        Risk(_uid(), p3.id, 'Datenmigration mit Downtime',
             'Längere Nichtverfügbarkeit von Dienst A beim Umzug.',
             'mittel', 'hoch', 'Dual-Write-Phase + Rückfallplan', d1.id, 'offen'),
    ]

    s.decisions = [
        Decision(_uid(), p1.id, (monday - timedelta(days=20)).isoformat(),
                 'Headless-Architektur mit getrenntem Frontend',
                 'Der Monolith bremst UI-Iterationen und Time-to-Market.',
                 'Storefront als eigenständige Anwendung, Anbindung über API.',
                 'Zusätzliche Deployment-Einheit, API-Vertrag muss gepflegt werden.', d1.id),
        Decision(_uid(), p1.id, (monday - timedelta(days=6)).isoformat(),
                 'Stripe als Zahlungsanbieter',
                 'Eigenbetrieb der Zahlungsabwicklung ist zu aufwändig und riskant.',
                 'Stripe für Karten & Wallets, SEPA folgt später.',
                 'Abhängigkeit von externem Anbieter, Gebühren pro Transaktion.', tim.id),
        Decision(_uid(), p2.id, (monday - timedelta(days=10)).isoformat(),
                 'Offline-First mit lokaler SQLite und Sync-Queue',
                 'Nutzer arbeiten häufig ohne stabile Verbindung.',
                 'Lokale DB als Quelle der Wahrheit, Hintergrund-Sync mit Konfliktstrategie.',
                 'Sync-Logik ist komplex und testintensiv.', d4.id),
    ]

    s.releases = [
        Release(_uid(), p1.id, '2.0.0-beta', (monday + timedelta(days=11)).isoformat(), 'in_arbeit',
                'Neuer Checkout, Warenkorb-Redesign, Bestätigungsmails.',
                [t.id for t in p1_tasks if t.sprint_id == active1.id and t.status in ('done', 'review')][:3]),
        Release(_uid(), p1.id, '2.0.0', (monday + timedelta(days=25)).isoformat(), 'geplant',
                'Produktiver Go-Live inkl. Suche & Filter.', []),
        Release(_uid(), p1.id, '1.9.4', (monday - timedelta(days=8)).isoformat(), 'live',
                'Hotfix: Warenkorb verlor Artikel bei Sprachwechsel.', []),
        Release(_uid(), p2.id, '1.2.0', (monday + timedelta(days=14)).isoformat(), 'geplant',
                'Offline-Modus, Push-Notifications.', []),
    ]

    s.ideas = [
        Idea(_uid(), p1.id, 'Gespeicherte Warenkörbe teilen', 'Kunden schicken sich Wunschlisten als Link.',
             4, 'neu', d3.id),
        Idea(_uid(), p1.id, 'Express-Checkout in einem Schritt', '', 6, 'geprueft', d1.id),
        Idea(_uid(), p1.id, 'Dark Mode für die Storefront', '', 2, 'abgelehnt', d4.id),
        Idea(_uid(), p2.id, 'Widget für den Home-Screen', 'Letzte Bestellung & Status auf einen Blick.',
             5, 'neu', d4.id),
    ]

    s.moods = []
    for i, m in enumerate([d1, d2, d3, d4, qa]):
        s.moods.append(Mood(_uid(), p1.id, active1.id, m.id, [4, 3, 4, 2, 3][i],
                            ['', 'viel Kontextwechsel', '', 'Blocker nervt', ''][i]))

    s.one_on_ones = [
        OneOnOne(_uid(), d1.id, (monday - timedelta(days=7)).isoformat(),
                 'Fühlt sich wohl, will mehr Architektur-Verantwortung.',
                 'Karrierepfad Senior→Lead; Urlaub im Sommer',
                 'Anke bei Architektur-Entscheid Migration einbinden',
                 (monday + timedelta(days=7)).isoformat()),
        OneOnOne(_uid(), d3.id, (monday - timedelta(days=3)).isoformat(),
                 'Etwas frustriert über Design-Abstimmungen mit Fachbereich.',
                 'Prozess Design-Reviews; Weiterbildung Accessibility',
                 'Klaren Design-Review-Termin pro Sprint etablieren',
                 (monday + timedelta(days=11)).isoformat()),
    ]

    # Budgets
    p1.budget_eur = 48000
    p2.budget_eur = 30000
    p3.budget_eur = 18000
    p2.rag = 'gelb'
    p2.status_note = 'Offline-Sync komplexer als geschätzt, Termin unter Beobachtung.'

    # Epics (Roadmap)
    def E(project, title, w_from, w_to, status, color):
        st = monday + timedelta(weeks=w_from)
        return Epic(_uid(), project.id, title, '', color,
                    st.isoformat(), (monday + timedelta(weeks=w_to)).isoformat(), status)

    e_checkout = E(p1, 'Checkout & Bezahlung', -4, 2, 'aktiv', '#1f4e5f')
    e_search = E(p1, 'Suche & Filter', 2, 6, 'geplant', '#5b8ca3')
    e_seo = E(p1, 'SEO & Migration Altshop', 0, 8, 'geplant', '#b5533a')
    e_offline = E(p2, 'Offline-Modus', -2, 2, 'aktiv', '#b5533a')
    e_push = E(p2, 'Benachrichtigungen', 0, 3, 'aktiv', '#cf8a2e')
    e_infra = E(p3, 'Infrastruktur-Grundlage', 2, 8, 'geplant', '#3d7a5d')
    s.epics = [e_checkout, e_search, e_seo, e_offline, e_push, e_infra]

    for t in p1_tasks:
        if 'checkout' in t.labels or 'payment' in t.labels or 'cart' in t.labels or 'Checkout' in t.title:
            t.epic_id = e_checkout.id
    for t in p2_tasks:
        if 'offline' in t.labels or 'Sync' in t.title:
            t.epic_id = e_offline.id
        elif 'Push' in t.title or 'Notification' in t.title:
            t.epic_id = e_push.id

    # Milestones
    s.milestones = [
        Milestone(_uid(), p1.id, 'Feature-Freeze Checkout', (monday + timedelta(days=11)).isoformat(),
                  'offen', 'Ab hier nur noch Bugfixes am Checkout.'),
        Milestone(_uid(), p1.id, 'Go-Live Webshop 2.0', (monday + timedelta(days=39)).isoformat(),
                  'offen', 'Produktiver Umschalt-Termin.'),
        Milestone(_uid(), p1.id, 'Design-Abnahme Fachbereich', (monday - timedelta(days=5)).isoformat(),
                  'erreicht', ''),
        Milestone(_uid(), p2.id, 'Beta an Testgruppe', (monday + timedelta(days=18)).isoformat(),
                  'offen', ''),
        Milestone(_uid(), p3.id, 'Architektur-Freigabe', (monday + timedelta(days=25)).isoformat(),
                  'offen', ''),
    ]

    # OKRs
    o1 = Objective(_uid(), p1.id, 'Reibungsloser Relaunch ohne Umsatzdelle', f'Q{(monday.month - 1) // 3 + 1}', tim.id)
    o2 = Objective(_uid(), p1.id, 'Checkout-Erlebnis auf Bestwerte', f'Q{(monday.month - 1) // 3 + 1}', d3.id)
    s.objectives = [o1, o2]
    s.key_results = [
        KeyResult(_uid(), o1.id, 'Organischer Traffic hält Niveau', 100, 92, 100, '%'),
        KeyResult(_uid(), o1.id, 'Kritische Bugs in Woche 1', 10, 6, 0, 'Stk'),
        KeyResult(_uid(), o1.id, 'Migrierte Alt-URLs', 0, 1800, 2400, 'URLs'),
        KeyResult(_uid(), o2.id, 'Checkout-Conversion', 2.1, 2.4, 3.0, '%'),
        KeyResult(_uid(), o2.id, 'Checkout-Abbruchrate', 68, 61, 45, '%'),
    ]

    # Stakeholder
    s.stakeholders = [
        Stakeholder(_uid(), p1.id, 'Leitung E-Commerce', 'Fachbereich', 'Auftraggeberin', 5, 5,
                    'befuerworter', 'Wöchentliches Steering, früh in Entscheidungen einbinden', 'ecom-lead@intern'),
        Stakeholder(_uid(), p1.id, 'Marketing', 'Fachbereich', 'SEO/Kampagnen', 3, 5, 'neutral',
                    'Redirect-Konzept gemeinsam abstimmen, Launch-Termin teilen', ''),
        Stakeholder(_uid(), p1.id, 'IT-Betrieb', 'Intern', 'Hosting & Betrieb', 4, 2, 'kritiker',
                    'Betriebshandbuch früh liefern, Lasttests gemeinsam planen', ''),
        Stakeholder(_uid(), p1.id, 'Datenschutz', 'Intern', 'DSB', 4, 3, 'neutral',
                    'Zahlungs- und Tracking-Konzept zur Prüfung vorlegen', ''),
        Stakeholder(_uid(), p1.id, 'Kundenservice', 'Fachbereich', 'Support', 2, 4, 'befuerworter',
                    'Vor Go-Live schulen, FAQ gemeinsam erstellen', ''),
    ]

    # Change Requests
    s.change_requests = [
        ChangeRequest(_uid(), p1.id, 'Zusätzlich Apple Pay zum Launch',
                      'Fachbereich wünscht Apple Pay bereits zum Go-Live statt später.',
                      16, 3, 'offen', 'Leitung E-Commerce', (monday - timedelta(days=2)).isoformat()),
        ChangeRequest(_uid(), p1.id, 'Gastbestellung doch ermöglichen',
                      'Ursprünglich Pflicht-Login; jetzt Gast-Checkout gefordert.',
                      24, 5, 'angenommen', 'Leitung E-Commerce', (monday - timedelta(days=12)).isoformat()),
        ChangeRequest(_uid(), p2.id, 'Tablet-Layout mitliefern',
                      'Nur Phone geplant; Tablet-Optimierung zusätzlich gewünscht.',
                      40, 8, 'abgelehnt', 'Produktmanagement', (monday - timedelta(days=6)).isoformat()),
    ]

    # -- Projekt-Steckbrief p1 ---------------------------------------
    p1.vision = 'Ein schneller, moderner Webshop, den der Fachbereich selbst weiterentwickeln kann.'
    p1.sponsor = 'Leitung E-Commerce'
    p1.start_date = (monday - timedelta(days=70)).isoformat()
    p1.target_date = (monday + timedelta(days=39)).isoformat()
    p1.scope_in = ['Storefront (Katalog, Suche, Checkout)', 'Anbindung Warenwirtschaft & Zahlung',
                   'SEO-Migration des Altshops', 'Redaktions-Oberfläche für Inhalte']
    p1.scope_out = ['Neues ERP', 'Marktplatz-Anbindungen', 'B2B-Preislogik (Folgeprojekt)']
    p1.success_criteria = ['Organischer Traffic hält Niveau (±5 %)', 'Checkout-Conversion +0,5 pp',
                           'Ladezeit Produktseite < 1,5 s', 'Go-Live ohne SEV1-Incident']
    p1.constraints = ['Go-Live-Fenster nur außerhalb der Aktionswochen', 'Budget 48 T€',
                      'Bestehende Zahlungsverträge weiternutzen']
    p1.assumptions = ['Warenwirtschafts-API bleibt stabil', 'Fachbereich stellt 20 % Kapazität für Reviews']
    p1.dor = ['Akzeptanzkriterien vorhanden', 'Abhängigkeiten geklärt', 'geschätzt', 'Design verlinkt']
    p2.vision = 'Die wichtigsten Funktionen jederzeit verfügbar – auch offline.'
    p2.dor = ['Akzeptanzkriterien vorhanden', 'geschätzt', 'Sync-Verhalten spezifiziert']

    # -- Anforderungen ---------------------------------------------
    def RQ(project, title, kind, moscow, status, acc=''):
        return Requirement(_uid(), project.id, title, kind, moscow, status, acc)
    s.requirements = [
        RQ(p1, 'Gast-Checkout ohne Konto', 'funktional', 'muss', 'abgestimmt',
           'Bestellung ist ohne Registrierung abschließbar; E-Mail genügt.'),
        RQ(p1, 'Zahlung per Karte & PayPal', 'funktional', 'muss', 'umgesetzt',
           'Beide Verfahren im Checkout wählbar, Fehlerfälle abgefangen.'),
        RQ(p1, 'Apple Pay', 'funktional', 'kann', 'entwurf', ''),
        RQ(p1, 'Ladezeit Produktseite < 1,5 s (p75)', 'nicht_funktional', 'soll', 'entwurf',
           'Lighthouse/Field-Data p75 LCP < 1,5 s auf 4G.'),
        RQ(p1, 'WCAG 2.1 AA für Checkout', 'nicht_funktional', 'muss', 'abgestimmt', ''),
        RQ(p1, 'Alle Alt-URLs werden 301-weitergeleitet', 'funktional', 'muss', 'entwurf',
           'Redirect-Map deckt 100 % der indexierten URLs ab.'),
        RQ(p1, 'DSGVO-konformes Consent-Management', 'randbedingung', 'muss', 'abgestimmt', ''),
        RQ(p2, 'Offline erfassen & später synchronisieren', 'funktional', 'muss', 'umgesetzt', ''),
        RQ(p2, 'Konflikt-Auflösung nachvollziehbar', 'funktional', 'soll', 'entwurf', ''),
        RQ(p3, 'Kein Datenverlust bei der Migration', 'randbedingung', 'muss', 'entwurf', ''),
    ]

    # -- Bugs -----------------------------------------------------
    def BUG(project, title, sev, status, env, comp, rep, asg, reopened=0, age=3):
        b = Bug(_uid(), project.id, title, '', sev, status, env, comp,
                rep.id if rep else None, asg.id if asg else None, reopened)
        b.created_at = (monday - timedelta(days=age)).isoformat()
        if status in ('behoben', 'verifiziert'):
            b.resolved_at = (monday - timedelta(days=max(0, age - 2))).isoformat()
        return b
    s.bugs = [
        BUG(p1, 'Checkout-Button auf iOS Safari nicht klickbar', 'kritisch', 'in_arbeit', 'staging', 'Checkout', qa, d4, 1, 2),
        BUG(p1, 'Falsche MwSt bei Gutscheinen', 'hoch', 'offen', 'test', 'Warenkorb', qa, d2, 0, 1),
        BUG(p1, 'Produktbilder laden verzögert', 'mittel', 'offen', 'test', 'Katalog', d3, None, 0, 4),
        BUG(p1, 'Bestätigungsmail ohne Rechnungsanhang', 'mittel', 'behoben', 'test', 'E-Mail', qa, d2, 0, 6),
        BUG(p1, 'Suchfilter „Preis" springt zurück', 'niedrig', 'offen', 'test', 'Suche', d3, d3, 0, 5),
        BUG(p1, 'Session-Timeout zu kurz im Checkout', 'hoch', 'verifiziert', 'staging', 'Checkout', qa, d1, 0, 8),
        BUG(p1, 'Warenkorb verliert Artikel bei Sprachwechsel', 'hoch', 'behoben', 'prod', 'Warenkorb', tim, d4, 2, 10),
        BUG(p2, 'App stürzt bei leerer Sync-Queue ab', 'kritisch', 'behoben', 'test', 'Sync', qa, d4, 0, 3),
        BUG(p2, 'Push-Token nach Reinstall ungültig', 'mittel', 'offen', 'test', 'Push', d4, d2, 0, 2),
    ]

    # -- Umgebungen & Deployments -------------------------------
    s.environments = [
        Environment(_uid(), p1.id, 'dev', 'https://dev.shop.intern', '2.0.0-rc4', 'ok', d4.id,
                    monday.isoformat(), '', 0),
        Environment(_uid(), p1.id, 'test', 'https://test.shop.intern', '2.0.0-rc3', 'ok', qa.id,
                    (monday - timedelta(days=1)).isoformat(), '', 1),
        Environment(_uid(), p1.id, 'staging', 'https://staging.shop.intern', '2.0.0-rc2', 'degraded', d1.id,
                    (monday - timedelta(days=2)).isoformat(), 'Checkout-Bug SEV, Fix unterwegs', 2),
        Environment(_uid(), p1.id, 'prod', 'https://www.shop.de', '1.9.4', 'ok', tim.id,
                    (monday - timedelta(days=8)).isoformat(), 'Altshop bis Go-Live', 3),
        Environment(_uid(), p2.id, 'test', 'TestFlight / internes Track', '1.2.0-b14', 'ok', d4.id,
                    (monday - timedelta(days=1)).isoformat(), '', 0),
    ]
    s.deployments = [
        Deployment(_uid(), p1.id, 'staging', '2.0.0-rc2', (monday - timedelta(days=2)).isoformat(),
                   'CI', 'erfolgreich', ''),
        Deployment(_uid(), p1.id, 'test', '2.0.0-rc3', (monday - timedelta(days=1)).isoformat(),
                   'CI', 'erfolgreich', ''),
        Deployment(_uid(), p1.id, 'staging', '2.0.0-rc1', (monday - timedelta(days=5)).isoformat(),
                   'CI', 'rollback', 'Migrationsskript fehlerhaft, zurückgerollt'),
        Deployment(_uid(), p1.id, 'prod', '1.9.4', (monday - timedelta(days=8)).isoformat(),
                   'Tim Klein', 'erfolgreich', 'Hotfix Sprachwechsel'),
    ]

    # -- Incidents ---------------------------------------------
    s.incidents = [
        Incident(_uid(), p1.id, 'Staging-Checkout nicht bedienbar (iOS)', 'sev2', 'untersuchung',
                 (monday - timedelta(days=2)).isoformat(), None,
                 'Kein Testabschluss auf Staging möglich', 'vermutlich CSS-Regression, in Analyse',
                 '', '', d4.id),
        Incident(_uid(), p1.id, 'Warenkorb-Datenverlust in Produktion', 'sev1', 'postmortem',
                 (monday - timedelta(days=11)).isoformat(), (monday - timedelta(days=10)).isoformat(),
                 '~2 % der Sessions verloren Artikel über 3 h',
                 'Race Condition bei Sprachwechsel-Handler',
                 'Hotfix 1.9.4 ausgerollt; Regressionstest ergänzt.',
                 'Feature-Flag für Sprachwechsel; Last-Test vor jedem Prod-Deploy', tim.id),
        Incident(_uid(), p2.id, 'Crash-Rate nach Beta-Build erhöht', 'sev3', 'geschlossen',
                 (monday - timedelta(days=4)).isoformat(), (monday - timedelta(days=3)).isoformat(),
                 'Beta-Tester betroffen', 'Null-Pointer bei leerer Queue',
                 'Fix in b14', '', d4.id),
    ]

    # -- Besprechungen --------------------------------------
    s.meetings = [
        Meeting(_uid(), p1.id, 'Steering Webshop KW ' + str((monday).isocalendar().week),
                'steering', (monday - timedelta(days=1)).isoformat(),
                [tim.id, d1.id], 'Statusampel, Budget, Apple-Pay-Antrag, Go-Live-Termin',
                'Ampel gelb bestätigt wegen Checkout-Bug. Budget im Rahmen.',
                'Apple Pay nicht zum Launch – als Fast-Follow nach Go-Live.',
                'Tim: Go-Live-Termin mit Marketing final abstimmen'),
        Meeting(_uid(), p1.id, 'Sprint-9-Review', 'review', (monday - timedelta(days=3)).isoformat(),
                [tim.id, d1.id, d2.id, d3.id, d4.id, qa.id],
                'Demo Checkout-Strecke, Warenkorb-Redesign',
                'Fachbereich zufrieden mit Checkout-Flow; Wunsch: klarere Fehlermeldungen.',
                '', 'Maike: Fehlermeldungs-Texte überarbeiten'),
        Meeting(_uid(), p3.id, 'Kickoff Plattform-Migration', 'planung',
                (monday + timedelta(days=13)).isoformat(), [tim.id, d1.id, d2.id],
                'Zielbild, Vorgehen, erste Risiken', '', '', ''),
    ]

    # -- Dokumente ----------------------------------------
    s.documents = [
        Document(_uid(), p1.id, 'Fachkonzept Webshop 2.0', 'spec', 'https://wiki.intern/webshop/fachkonzept', d1.id),
        Document(_uid(), p1.id, 'Figma – Storefront & Checkout', 'design', 'https://figma.com/file/webshop', d3.id),
        Document(_uid(), p1.id, 'Redirect-Map (Sheet)', 'betrieb', 'https://sheets.intern/redirects', d3.id),
        Document(_uid(), p1.id, 'Rahmenvertrag Zahlungsanbieter', 'vertrag', 'https://dms.intern/vertraege/psp', tim.id),
        Document(_uid(), p1.id, 'Betriebshandbuch (Entwurf)', 'betrieb', 'https://wiki.intern/webshop/runbook', d1.id),
        Document(_uid(), p2.id, 'Sync-Konzept Offline-Modus', 'spec', 'https://wiki.intern/app/sync', d4.id),
    ]

    # -- Lieferanten / Lizenzen -------------------------
    s.vendors = [
        Vendor(_uid(), p1.id, 'Zahlungsanbieter (PSP)', 'dienst', 0.9, 'monatlich',
               (monday + timedelta(days=300)).isoformat(), tim.id, True, '+ 1,2 % pro Transaktion'),
        Vendor(_uid(), p1.id, 'Such-as-a-Service', 'dienst', 290, 'monatlich',
               (monday + timedelta(days=120)).isoformat(), d1.id, True, ''),
        Vendor(_uid(), p1.id, 'CDN & WAF', 'dienst', 180, 'monatlich', '', d1.id, True, ''),
        Vendor(_uid(), p1.id, 'Design-Tool Team-Lizenz', 'lizenz', 540, 'jaehrlich',
               (monday + timedelta(days=60)).isoformat(), d3.id, True, '3 Editoren'),
        Vendor(_uid(), p1.id, 'Pen-Test Dienstleister', 'dienstleister', 6500, 'einmalig',
               '', tim.id, True, 'vor Go-Live'),
        Vendor(_uid(), p2.id, 'Push-Notification-Dienst', 'dienst', 49, 'monatlich', '', d4.id, True, ''),
    ]

    # -- RACI ------------------------------------------
    def RA(project, name, order, **roles):
        return RaciArea(_uid(), project.id, name, dict(roles), order)
    s.raci_areas = [
        RA(p1, 'Anforderungen & Scope', 0, **{tim.id: 'A', d1.id: 'C', d3.id: 'R'}),
        RA(p1, 'Architektur', 1, **{d1.id: 'A', d2.id: 'R', tim.id: 'I', d4.id: 'C'}),
        RA(p1, 'Checkout-Umsetzung', 2, **{d1.id: 'R', d2.id: 'R', tim.id: 'A', qa.id: 'C'}),
        RA(p1, 'Qualitätssicherung', 3, **{qa.id: 'R', tim.id: 'A', d2.id: 'C'}),
        RA(p1, 'Betrieb & Go-Live', 4, **{d1.id: 'R', tim.id: 'A', qa.id: 'C', d4.id: 'I'}),
        RA(p1, 'Stakeholder-Kommunikation', 5, **{tim.id: 'R', d1.id: 'I'}),
    ]

    # -- Lessons Learned -------------------------------
    s.lessons = [
        Lesson(_uid(), p1.id, 'Testumgebungen früh reservieren', 'prozess',
               'Last-Test-Umgebung wurde erst mitten im Sprint angefragt und war blockiert.',
               'In die Definition of Ready aufnehmen: benötigte Umgebungen zu Sprint-Beginn buchen.',
               ['sprint', 'infrastruktur']),
        Lesson(_uid(), p1.id, 'Sprachwechsel-Handler war unter-getestet', 'technik',
               'Race Condition führte zu Datenverlust in Produktion (SEV1).',
               'Nebenläufige Zustandsänderungen brauchen dedizierte Tests + Feature-Flag beim Rollout.',
               ['qualität', 'incident']),
        Lesson(_uid(), p1.id, 'Akzeptanzkriterien senken Rückfragen', 'schaetzung',
               'Sprints mit klaren Kriterien liefen deutlich ruhiger.',
               'Kein Task ohne Akzeptanzkriterien in den Sprint.',
               ['anforderungen']),
    ]


store = Store().load()
