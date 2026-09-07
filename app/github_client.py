"""Schlanker async-Client fuer die GitHub-REST-API.

Nur die Endpunkte, die der Kontor-Leitstand braucht:
offene PRs inkl. Merge-Status, Reviews, CI-Checks und Milestones (= Sprints).
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

API_ROOT = 'https://api.github.com'


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def human_age(since: datetime | None) -> str:
    """'vor 3 Tagen' / 'vor 2 Std.' – kompakt fuer die Karten."""
    if since is None:
        return '?'
    delta = _utcnow() - since
    minutes = int(delta.total_seconds() // 60)
    if minutes < 60:
        return f'vor {minutes} Min.'
    hours = minutes // 60
    if hours < 24:
        return f'vor {hours} Std.'
    days = hours // 24
    if days < 30:
        return f'vor {days} Tag{"en" if days != 1 else ""}'
    return f'vor {days // 30} Mon.'


@dataclass
class RateLimit:
    remaining: int = 0
    limit: int = 0
    reset: datetime | None = None


@dataclass
class Milestone:
    title: str
    number: int
    url: str
    open_issues: int
    closed_issues: int
    due_on: datetime | None
    description: str = ''

    @property
    def total(self) -> int:
        return self.open_issues + self.closed_issues

    @property
    def progress(self) -> float:
        return self.closed_issues / self.total if self.total else 0.0

    @property
    def days_left(self) -> int | None:
        if self.due_on is None:
            return None
        return (self.due_on.date() - _utcnow().date()).days


@dataclass
class PullRequest:
    number: int
    title: str
    url: str
    author: str
    author_avatar: str
    created_at: datetime | None
    updated_at: datetime | None
    is_draft: bool
    base: str
    head: str
    labels: list[str] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    # per-PR Detail-Call:
    mergeable: bool | None = None          # None => GitHub rechnet noch
    mergeable_state: str = 'unknown'       # clean | dirty | blocked | behind | ...
    # aus Reviews:
    review_state: str = 'none'             # approved | changes_requested | commented | none
    reviewers: list[str] = field(default_factory=list)
    # aus Check-Runs:
    ci_state: str = 'none'                 # success | failure | pending | none

    @property
    def has_conflict(self) -> bool:
        return self.mergeable is False or self.mergeable_state == 'dirty'

    @property
    def ready_to_merge(self) -> bool:
        return (
            not self.is_draft
            and self.mergeable is True
            and self.mergeable_state == 'clean'
            and self.review_state == 'approved'
            and self.ci_state in ('success', 'none')
        )


@dataclass
class Snapshot:
    repo: str
    fetched_at: datetime
    pulls: list[PullRequest]
    milestones: list[Milestone]
    rate: RateLimit
    error: str | None = None


class GitHubClient:
    def __init__(self, repo: str, token: str | None = None) -> None:
        self.repo = repo.strip().strip('/')
        self.token = token or os.getenv('GITHUB_TOKEN') or None
        headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        self._headers = headers
        self._sem = asyncio.Semaphore(6)

    # -- interne Helfer -----------------------------------------------------
    async def _get(self, client: httpx.AsyncClient, path: str, **params):
        async with self._sem:
            resp = await client.get(f'{API_ROOT}{path}', params=params or None)
        resp.raise_for_status()
        return resp

    async def _enrich(self, client: httpx.AsyncClient, pr: PullRequest) -> None:
        """Detail-, Review- und CI-Infos fuer eine einzelne PR nachladen.

        Fehler bei einer einzelnen PR duerfen das Gesamt-Dashboard nicht kippen.
        """
        try:
            await self._enrich_inner(client, pr)
        except httpx.HTTPError:
            pr.mergeable_state = 'unknown'

    async def _enrich_inner(self, client: httpx.AsyncClient, pr: PullRequest) -> None:
        base = f'/repos/{self.repo}'
        detail_resp, reviews_resp = await asyncio.gather(
            self._get(client, f'{base}/pulls/{pr.number}'),
            self._get(client, f'{base}/pulls/{pr.number}/reviews', per_page=100),
        )
        detail = detail_resp.json()
        pr.mergeable = detail.get('mergeable')
        pr.mergeable_state = detail.get('mergeable_state', 'unknown')
        pr.additions = detail.get('additions', 0)
        pr.deletions = detail.get('deletions', 0)
        pr.changed_files = detail.get('changed_files', 0)
        head_sha = detail.get('head', {}).get('sha')

        # Reviews: letzter Stand je Reviewer gewinnt
        latest: dict[str, str] = {}
        for review in reviews_resp.json():
            user = (review.get('user') or {}).get('login')
            state = review.get('state', '')
            if not user or state == 'COMMENTED':
                continue
            latest[user] = state
        pr.reviewers = sorted(latest)
        if 'CHANGES_REQUESTED' in latest.values():
            pr.review_state = 'changes_requested'
        elif 'APPROVED' in latest.values():
            pr.review_state = 'approved'
        elif latest:
            pr.review_state = 'commented'

        # CI ueber Check-Runs am Head-Commit
        if head_sha:
            try:
                checks = (await self._get(
                    client, f'{base}/commits/{head_sha}/check-runs', per_page=100,
                )).json().get('check_runs', [])
            except httpx.HTTPError:
                checks = []
            if checks:
                conclusions = {c.get('conclusion') for c in checks}
                statuses = {c.get('status') for c in checks}
                if 'in_progress' in statuses or 'queued' in statuses or None in conclusions:
                    pr.ci_state = 'pending'
                elif {'failure', 'timed_out', 'cancelled'} & conclusions:
                    pr.ci_state = 'failure'
                elif conclusions <= {'success', 'neutral', 'skipped'}:
                    pr.ci_state = 'success'

    # -- oeffentliche API -------------------------------------------------
    async def fetch(self) -> Snapshot:
        async with httpx.AsyncClient(headers=self._headers, timeout=20.0) as client:
            try:
                pulls_resp, ms_resp = await asyncio.gather(
                    self._get(client, f'/repos/{self.repo}/pulls',
                              state='open', per_page=100, sort='created', direction='asc'),
                    self._get(client, f'/repos/{self.repo}/milestones',
                              state='open', sort='due_on', direction='asc', per_page=100),
                )
            except httpx.HTTPStatusError as exc:
                msg = {
                    401: 'Token ungueltig oder fehlt (401).',
                    403: 'Rate-Limit erreicht oder Zugriff verweigert (403).',
                    404: f'Repo "{self.repo}" nicht gefunden (404).',
                }.get(exc.response.status_code, f'HTTP {exc.response.status_code}')
                return Snapshot(self.repo, _utcnow(), [], [], RateLimit(), error=msg)
            except httpx.HTTPError as exc:
                return Snapshot(self.repo, _utcnow(), [], [], RateLimit(), error=str(exc))

            pulls = [self._to_pr(item) for item in pulls_resp.json()]
            await asyncio.gather(*(self._enrich(client, pr) for pr in pulls))

            milestones = [self._to_milestone(item) for item in ms_resp.json()]

            rate = RateLimit(
                remaining=int(pulls_resp.headers.get('x-ratelimit-remaining', 0)),
                limit=int(pulls_resp.headers.get('x-ratelimit-limit', 0)),
                reset=datetime.fromtimestamp(
                    int(pulls_resp.headers.get('x-ratelimit-reset', 0)), tz=timezone.utc,
                ),
            )
            return Snapshot(self.repo, _utcnow(), pulls, milestones, rate)

    # -- Mapping ----------------------------------------------------------
    @staticmethod
    def _to_pr(item: dict) -> PullRequest:
        user = item.get('user') or {}
        return PullRequest(
            number=item['number'],
            title=item['title'],
            url=item['html_url'],
            author=user.get('login', '?'),
            author_avatar=user.get('avatar_url', ''),
            created_at=_parse_ts(item.get('created_at')),
            updated_at=_parse_ts(item.get('updated_at')),
            is_draft=item.get('draft', False),
            base=item.get('base', {}).get('ref', '?'),
            head=item.get('head', {}).get('ref', '?'),
            labels=[lbl['name'] for lbl in item.get('labels', [])],
        )

    @staticmethod
    def _to_milestone(item: dict) -> Milestone:
        return Milestone(
            title=item['title'],
            number=item['number'],
            url=item['html_url'],
            open_issues=item.get('open_issues', 0),
            closed_issues=item.get('closed_issues', 0),
            due_on=_parse_ts(item.get('due_on')),
            description=item.get('description') or '',
        )
