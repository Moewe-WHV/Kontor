"""Inhalte für Anfänger: Seiten-Hilfe, Rollen, Tagesablauf, Glossar.

Zentrale Textsammlung – wird von der Kopfzeile (Info-Knopf), der Anleitung
(``views/handbook``), der Rollen-Seite (``views/roles``) und dem Fahrplan
(``views/today``) genutzt. Reiner Text, keine Logik.
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# Seiten-Hilfe:  Pfad -> (Titel, Wofür, [Schritte], [Tipps])
# --------------------------------------------------------------------------
PAGES: dict[str, dict] = {
    '/today': {
        'title': 'Fahrplan heute',
        'what': 'Dein Tagesplan als Teamleitung: was heute, morgens, mittags und '
                'wöchentlich ansteht – mit Häkchen zum Abarbeiten.',
        'steps': [
            'Von oben nach unten durchgehen und Erledigtes abhaken.',
            'Bei jedem Punkt sagt „Warum", wozu er gut ist.',
            'Über „Öffnen" springst du direkt zur passenden Seite.',
        ],
        'tips': [
            'Die Häkchen setzen sich jeden Tag automatisch zurück.',
            'Oben siehst du „Jetzt wichtig" – das sind Dinge, die die App '
            'gerade auffällig findet (offene Blocker, fehlende Stimmung …).',
        ],
    },
    '/roles': {
        'title': 'Rollen & Ablauf',
        'what': 'Wer macht was im Team – und was davon täglich bzw. wöchentlich. '
                'Gedacht als Nachschlagewerk, wenn du unsicher bist.',
        'steps': [
            'Deine Rolle (Teamleitung) zuerst lesen.',
            'Danach kurz die anderen Rollen überfliegen – damit du weißt, was '
            'du von wem erwarten kannst.',
            'Die Tabelle „Tagesrhythmus" zeigt den Ablauf über den Tag.',
        ],
        'tips': [
            'Im Klassenprojekt hat oft eine Person mehrere Rollen – das ist ok.',
            'Die „Roten Flaggen" helfen dir, Probleme früh zu erkennen.',
        ],
    },
    '/handbook': {
        'title': 'Anleitung',
        'what': 'Überblick über alle Bereiche der App: wo finde ich was, wofür ist '
                'das gut, und wie fange ich an.',
        'steps': [
            'Ganz oben „Erste Schritte" abarbeiten, wenn das Projekt neu ist.',
            'Sonst über das Suchfeld den Bereich finden, der dich interessiert.',
            'Jeder Eintrag lässt sich aufklappen und hat eine Kurzanleitung.',
        ],
        'tips': [
            'Unten steht ein Mini-Lexikon mit den wichtigsten Begriffen.',
            'Auf jeder Seite gibt es oben rechts den Info-Knopf (i) mit genau '
            'dieser Erklärung für die aktuelle Seite.',
        ],
    },
    '/': {
        'title': 'Leitstand',
        'what': 'Deine Startseite: Lage des laufenden Sprints, Blocker, Risiken, '
                'Betrieb und offene Pull Requests auf einen Blick.',
        'steps': [
            'Morgens einmal komplett überfliegen.',
            'Rote Zahlen und „Blockiert" zuerst ansehen.',
            'Bei Bedarf in die verlinkten Detailseiten wechseln.',
        ],
        'tips': [
            'Der Leitstand rechnet nur – gepflegt werden die Daten auf den '
            'anderen Seiten (Board, Standup, Risiken …).',
        ],
    },
    '/portfolio': {
        'title': 'Flotte (Portfolio)',
        'what': 'Alle Projekte nebeneinander – Fortschritt, Blocker, Auslastung. '
                'Im Klassenprojekt meist nur ein Projekt.',
        'steps': ['Projekt auswählen und mit „öffnen" zum Leitstand springen.'],
        'tips': ['Nützlich, sobald ihr mehrere Projekte oder Teilprojekte habt.'],
    },
    '/status': {
        'title': 'Statusbericht',
        'what': 'Kurzer Bericht für Betreuer / Auftraggeber: Ampel (grün/gelb/rot), '
                'was läuft, was hakt, nächste Schritte.',
        'steps': [
            'Ampel ehrlich setzen.',
            'Freitext knapp halten: Fortschritt, Probleme, nächste Schritte.',
            'Vor jedem Betreuer-Termin einmal aktualisieren.',
        ],
        'tips': ['Gelb heißt „läuft, aber mit Risiko" – nicht erst bei Rot melden.'],
    },
    '/metrics': {
        'title': 'Metriken',
        'what': 'Kennzahlen zum Tempo des Teams: Velocity (geschaffte Stunden je '
                'Sprint), Durchlaufzeiten, Prognose.',
        'steps': ['Nur lesen. Interessant wird es ab dem 2.–3. Sprint.'],
        'tips': ['Velocity ist kein Ziel, sondern eine Beobachtung – nicht '
                 'zwischen Personen vergleichen.'],
    },
    '/budget': {
        'title': 'Budget & Kosten',
        'what': 'Geplante vs. voraussichtliche Kosten. Im Klassenprojekt oft '
                'optional – dann leer lassen.',
        'steps': ['Budget im Steckbrief setzen, Tagessätze in der Crew.'],
        'tips': [],
    },
    '/calendar': {
        'title': 'Seekarte (Kalender)',
        'what': 'Termine, Sprint-Zeiträume, Abwesenheiten und Meilensteine auf '
                'einem Zeitstrahl.',
        'steps': ['Zur Wochenplanung und vor Terminen draufschauen.'],
        'tips': [],
    },
    '/charter': {
        'title': 'Steckbrief (Charter)',
        'what': 'Das Fundament: Vision, Ziel, was drin ist / was nicht (Scope), '
                'Erfolgskriterien, Annahmen, Termine.',
        'steps': [
            'Ganz am Anfang mit dem Team ausfüllen.',
            'Bei größeren Änderungen am Projekt anpassen.',
        ],
        'tips': ['„Nicht im Scope" ist genauso wichtig wie „im Scope" – schützt '
                 'euch vor ausuferndem Umfang.'],
    },
    '/requirements': {
        'title': 'Anforderungen',
        'what': 'Was das Produkt können muss – als Liste mit Priorität (MoSCoW: '
                'Muss/Soll/Kann) und Abnahmekriterien.',
        'steps': [
            'Anforderungen sammeln und mit Muss/Soll/Kann priorisieren.',
            'Zu jeder ein Abnahmekriterium notieren („fertig, wenn …").',
            'Später Tasks auf dem Board damit verknüpfen.',
        ],
        'tips': ['Lieber wenige klare „Muss" als eine lange Wunschliste.'],
    },
    '/roadmap': {
        'title': 'Roadmap',
        'what': 'Grobe Zeitplanung auf Ebene größerer Arbeitspakete (Epics) über '
                'mehrere Sprints.',
        'steps': ['Epics anlegen und grob auf Sprints / Zeiträume verteilen.'],
        'tips': ['Grob halten – Details kommen in die Sprint-Planung.'],
    },
    '/milestones': {
        'title': 'Meilensteine',
        'what': 'Feste Termine mit Ergebnis: Zwischenabgabe, Präsentation, '
                'Abgabe. Mit Datum und Status.',
        'steps': ['Alle Pflichttermine des Kurses als Meilenstein eintragen.'],
        'tips': ['Überfällige Meilensteine erscheinen rot auf dem Leitstand.'],
    },
    '/okrs': {
        'title': 'OKRs / Ziele',
        'what': 'Ziele (Objectives) mit messbaren Ergebnissen (Key Results). '
                'Optional – nur nutzen, wenn euer Kurs das verlangt.',
        'steps': ['Ziel formulieren, 2–3 messbare Key Results dazu.'],
        'tips': [],
    },
    '/raci': {
        'title': 'RACI',
        'what': 'Tabelle: wer ist bei welchem Thema verantwortlich (R), '
                'rechenschaftspflichtig (A), zu beraten (C) oder zu '
                'informieren (I).',
        'steps': [
            'Themen / Aufgabenbereiche als Zeilen anlegen.',
            'Pro Zeile genau ein „A" vergeben, sonst fühlt sich niemand zuständig.',
        ],
        'tips': ['Gut bei Streit „wer hätte das machen müssen?" – vorher klären.'],
    },
    '/board': {
        'title': 'Board (Kanban)',
        'what': 'Das Herz der täglichen Arbeit: Aufgaben in den Spalten Backlog → '
                'To Do → In Arbeit → Review → Fertig.',
        'steps': [
            'Aufgaben mit „+" anlegen: Titel, Schätzung, zuständige Person, Sprint.',
            'Karten beim Arbeiten in die nächste Spalte ziehen.',
            'Hängt etwas fest: Karte öffnen und „Blockiert" setzen mit Grund.',
        ],
        'tips': [
            'Kleine Aufgaben (½–2 Tage) sind leichter zu steuern als große.',
            '„In Arbeit" möglichst kurz halten – lieber fertig machen als neu anfangen.',
        ],
    },
    '/sprints': {
        'title': 'Sprint-Planung',
        'what': 'Ein Sprint ist ein fester Arbeitsabschnitt (z. B. 2 Wochen) mit '
                'einem Ziel. Hier legst du Sprints an und aktivierst einen.',
        'steps': [
            'Sprint anlegen: Name, Start, Ende, Ziel in einem Satz.',
            'Aufgaben aus dem Backlog in den Sprint ziehen (auf dem Board).',
            'Sprint „aktivieren" – dann rechnet der Leitstand damit.',
        ],
        'tips': [
            'Nicht mehr einplanen als Kapazität da ist (siehe Kapazität-Seite).',
            'Immer nur ein Sprint aktiv.',
        ],
    },
    '/capacity': {
        'title': 'Kapazität',
        'what': 'Wie viele Stunden hat jede Person im aktuellen Sprint wirklich '
                'Zeit – abzüglich Urlaub, Klausuren, anderer Kurse.',
        'steps': [
            'Pro Person die realistischen Stunden für den Sprint eintragen.',
            'Mit dem eingeplanten Aufwand auf dem Board vergleichen.',
        ],
        'tips': ['Im Studium sind 100 % nie erreichbar – lieber ehrlich niedrig ansetzen.'],
    },
    '/absences': {
        'title': 'Abwesenheiten',
        'what': 'Urlaub, Krankheit, Fortbildung, Klausurphasen – damit die '
                'Kapazitätsrechnung stimmt.',
        'steps': ['Bekannte Abwesenheiten früh eintragen (von–bis).'],
        'tips': ['Klausurwochen der Teammitglieder hier als „Sonstiges" eintragen.'],
    },
    '/standup': {
        'title': 'Standup',
        'what': 'Kurzer Tagesabgleich pro Person: Was gestern, was heute, welche '
                'Blocker. Asynchron – jede/r trägt selbst ein.',
        'steps': [
            'Team bittet einmal täglich (z. B. bis 10 Uhr) um Eintrag.',
            'Als TL die Blocker durchgehen und lösen / eskalieren.',
        ],
        'tips': ['Blocker aus dem Standup landen automatisch auf dem Leitstand.'],
    },
    '/timelog': {
        'title': 'Stunden',
        'what': 'Erfasste Arbeitszeit je Aufgabe. Zeigt Ist-Aufwand gegen '
                'Schätzung – nützlich fürs Schätzen lernen.',
        'steps': ['Team bucht Zeiten auf Aufgaben (kurz, grob reicht).'],
        'tips': ['Wenn euer Kurs keine Zeiterfassung verlangt: weglassen.'],
    },
    '/burndown': {
        'title': 'Burndown',
        'what': 'Kurve: wie viel Arbeit ist im Sprint noch offen. Ideal fällt '
                'gleichmäßig auf null. Liegt die echte Kurve darüber, wird es eng.',
        'steps': ['Im Sprint 2–3× pro Woche draufschauen.'],
        'tips': ['Flache Kurve = nichts wird fertig. Ursache im Standup / Board suchen.'],
    },
    '/quality': {
        'title': 'Qualität & Bugs',
        'what': 'Fehlerliste mit Schweregrad und Status. Zeigt auch, wie viele '
                'Fehler „nach Produktion" durchgerutscht sind.',
        'steps': ['Gefundene Bugs eintragen: Titel, Schweregrad, wo gefunden.'],
        'tips': ['Kritische Bugs vor neuen Features.'],
    },
    '/environments': {
        'title': 'Umgebungen',
        'what': 'Übersicht eurer Systeme (dev / test / staging / prod): welche '
                'Version läuft wo, ist alles erreichbar.',
        'steps': ['Umgebungen anlegen und nach Deployments die Version pflegen.'],
        'tips': ['Für kleine Projekte oft nur „Test" und „Live" nötig.'],
    },
    '/incidents': {
        'title': 'Incidents',
        'what': 'Störungen im Betrieb: was war kaputt, wie lange, Ursache, was '
                'macht ihr, damit es nicht wiederkommt.',
        'steps': ['Bei einer Störung Incident anlegen und nach Lösung ausfüllen.'],
        'tips': ['Meist erst relevant, wenn etwas produktiv läuft.'],
    },
    '/stakeholders': {
        'title': 'Stakeholder',
        'what': 'Alle, die ein Interesse am Projekt haben: Betreuer, Auftraggeber, '
                'Nutzer. Mit Einfluss / Interesse und wie ihr mit ihnen umgeht.',
        'steps': [
            'Personen eintragen und Einfluss + Interesse (1–5) schätzen.',
            'Für „viel Einfluss + viel Interesse" eine Umgangsstrategie notieren.',
        ],
        'tips': ['Euer Kurs-Betreuer ist ein Stakeholder mit hohem Einfluss.'],
    },
    '/meetings': {
        'title': 'Besprechungen',
        'what': 'Protokolle: Agenda, Notizen, Beschlüsse, Aufgaben aus dem Termin.',
        'steps': [
            'Vor dem Termin Agenda eintragen.',
            'Im / nach dem Termin Beschlüsse und Aufgaben festhalten.',
        ],
        'tips': ['Beschlüsse zusätzlich unter „Risiken & Entscheidungen" sichern.'],
    },
    '/changes': {
        'title': 'Änderungen',
        'what': 'Änderungswünsche am Umfang mit geschätzter Auswirkung (Stunden / '
                'Tage) und Entscheidung: angenommen oder abgelehnt.',
        'steps': ['Wunsch eintragen, Auswirkung schätzen, bewusst entscheiden.'],
        'tips': ['„Machen wir schnell nebenbei" ist der häufigste Grund für '
                 'Verzug – hier sichtbar machen.'],
    },
    '/raid': {
        'title': 'Risiken & Entscheidungen (RAID)',
        'what': 'RAID = Risks, Assumptions, Issues, Decisions. Was könnte '
                'schiefgehen, worauf verlassen wir uns, was ist gerade ein '
                'Problem, was haben wir entschieden.',
        'steps': [
            'Risiken mit Eintritts­wahrscheinlichkeit × Auswirkung bewerten.',
            'Pro Risiko eine Gegenmaßnahme und eine verantwortliche Person.',
            'Wichtige Entscheidungen mit Begründung festhalten.',
        ],
        'tips': ['1× pro Woche durchgehen und aktualisieren.'],
    },
    '/releases': {
        'title': 'Releases',
        'what': 'Geplante und erfolgte Auslieferungen mit Version und Datum.',
        'steps': ['Nächste Abgabe / Auslieferung als Release mit Datum anlegen.'],
        'tips': [],
    },
    '/documents': {
        'title': 'Dokumente',
        'what': 'Sammelstelle für Links zu euren Unterlagen (Spec, Design, '
                'Berichte) – die App speichert Links, nicht die Dateien.',
        'steps': ['Wichtige Dokumente als Link mit Kategorie und Verantwortlichem ablegen.'],
        'tips': [],
    },
    '/vendors': {
        'title': 'Lieferanten & Lizenzen',
        'what': 'Externe Dienste, Lizenzen, Abos mit Kosten und Verlängerungsdatum.',
        'steps': ['Genutzte kostenpflichtige Dienste eintragen.'],
        'tips': ['Im Klassenprojekt oft leer.'],
    },
    '/retro': {
        'title': 'Retrospektive',
        'what': 'Am Ende jedes Sprints: Was lief gut, was schlecht, was probieren '
                'wir aus. Ergebnis sind konkrete Maßnahmen.',
        'steps': [
            'Nach jedem Sprint 20–30 Min mit dem Team.',
            'Notizen sammeln, über die wichtigsten abstimmen.',
            'Aus den Top-Punkten 1–2 Maßnahmen mit verantwortlicher Person machen.',
        ],
        'tips': ['Ohne Maßnahme ist die Retro wertlos – lieber eine, die wirklich passiert.'],
    },
    '/wetter': {
        'title': 'Wetterlage',
        'what': 'Stimmung im Team pro Sprint als Wetter (Sturm bis Sonnenschein). '
                'Zeigt früh, wenn jemand unzufrieden oder überlastet ist.',
        'steps': [
            'Jede Person klickt ihr Wetter an, optional mit kurzem Kommentar.',
            'Als TL bei „Regen / Sturm" das Gespräch suchen (siehe 1:1).',
        ],
        'tips': ['1× pro Sprint reicht, am besten rund um die Retro.'],
    },
    '/lessons': {
        'title': 'Lessons Learned',
        'what': 'Erkenntnisse, die länger gelten als ein Sprint – gesammeltes '
                'Erfahrungswissen fürs nächste Projekt.',
        'steps': ['Aus Retros und Vorfällen die dauerhaften Lehren hierher übertragen.'],
        'tips': [],
    },
    '/ideas': {
        'title': 'Speicher (Ideen)',
        'what': 'Parkplatz für Ideen, die gerade nicht dran sind – damit sie nicht '
                'verloren gehen und nicht den Sprint stören.',
        'steps': ['Idee kurz notieren und weiterarbeiten.'],
        'tips': [],
    },
    '/one-on-ones': {
        'title': '1:1-Gespräche',
        'what': 'Notizen zu Vier-Augen-Gesprächen mit einzelnen Teammitgliedern: '
                'Themen, Vereinbarungen, nächster Termin.',
        'steps': [
            'Bei Spannungen oder „Regen" in der Wetterlage ein 1:1 ansetzen.',
            'Kurz festhalten: besprochen, vereinbart, wann wieder.',
        ],
        'tips': ['Auch ohne Problem hilft ein kurzes 1:1 pro Person und Sprint.'],
    },
    '/projects': {
        'title': 'Projekte (Werft)',
        'what': 'Projekte anlegen, umbenennen, archivieren. Hier startet alles, '
                'wenn die App neu ist.',
        'steps': ['Neues Projekt anlegen: Name, Kürzel, kurze Beschreibung.'],
        'tips': ['Ein Klassenprojekt = ein Projekt. Mehr braucht ihr selten.'],
    },
    '/team': {
        'title': 'Crew',
        'what': 'Die Teammitglieder mit Rolle, Wochenstunden und (optional) '
                'Tagessatz. Basis für Kapazität und Kosten.',
        'steps': [
            'Alle Teammitglieder eintragen.',
            'Rolle setzen (Teamleitung, Entwicklung, QA …) – siehe „Rollen & Ablauf".',
            'Realistische Wochenstunden fürs Projekt eintragen.',
        ],
        'tips': ['Die Rolle hier steuert, was auf der Seite „Rollen & Ablauf" '
                 'zu wem passt.'],
    },
    '/settings': {
        'title': 'Einstellungen',
        'what': 'App-weite Optionen: GitHub-Zugang für die PR-Sicht, Vorgaben für '
                'neue Crew/Sprints, Währung sowie Export/Import und Zurücksetzen '
                'der Daten.',
        'steps': [
            'GitHub-Repo (owner/name) eintragen, damit der Leitstand die richtigen PRs zeigt.',
            'Vorgaben anpassen – sie gelten nur für neu angelegte Einträge.',
            'Vor größeren Änderungen einen Export herunterladen.',
        ],
        'tips': [
            'Alles wird in pm.json gespeichert und wirkt sofort.',
            'Der Token liegt im Klartext in der Datei – auf geteilten Servern '
            'lieber die Umgebungsvariable GITHUB_TOKEN nutzen.',
        ],
    },
}


# --------------------------------------------------------------------------
# Erste Schritte  (für die Anleitung)
# --------------------------------------------------------------------------
FIRST_STEPS: list[tuple[str, str, str]] = [
    ('Crew eintragen', 'Alle Teammitglieder mit Rolle und Wochenstunden anlegen.', '/team'),
    ('Steckbrief ausfüllen', 'Vision, Ziel, Scope und Termine mit dem Team festhalten.', '/charter'),
    ('Meilensteine setzen', 'Alle Pflichttermine des Kurses mit Datum eintragen.', '/milestones'),
    ('Anforderungen sammeln', 'Was muss das Produkt können? Mit Muss/Soll/Kann priorisieren.', '/requirements'),
    ('Ersten Sprint anlegen', 'Zeitraum + Ziel festlegen und den Sprint aktivieren.', '/sprints'),
    ('Aufgaben aufs Board', 'Arbeit in kleine Aufgaben schneiden und in den Sprint ziehen.', '/board'),
    ('Kapazität eintragen', 'Realistische Stunden je Person für den Sprint.', '/capacity'),
    ('Täglich: Fahrplan', 'Ab jetzt jeden Morgen den „Fahrplan heute" abarbeiten.', '/today'),
]


# --------------------------------------------------------------------------
# Rollen
# --------------------------------------------------------------------------
ROLES: list[dict] = [
    {
        'name': 'Teamleitung (TL)',
        'match': ('teamleiter', 'teamleitung', 'tl', 'lead', 'projektleit'),
        'summary': 'Hält das Projekt zusammen: Überblick, Entscheidungen, '
                   'Hindernisse wegräumen, nach außen berichten. Programmiert '
                   'wenig bis gar nicht.',
        'daily': [
            'Fahrplan heute + Leitstand durchgehen',
            'Standup-Einträge lesen, Blocker aktiv lösen oder eskalieren',
            'Board kurz prüfen: hängt etwas fest, ist etwas unklar?',
            'Für Rückfragen des Teams ansprechbar sein',
        ],
        'weekly': [
            'Statusbericht für Betreuer / Auftraggeber aktualisieren',
            'Risiken & Entscheidungen (RAID) durchgehen',
            'Nächsten Sprint vorbereiten bzw. laufenden nachsteuern',
            'Retro moderieren und Maßnahmen nachhalten',
            'Wetterlage ansehen, bei Bedarf 1:1-Gespräche führen',
        ],
        'flags': [
            'Niemand weiß, woran gerade gearbeitet wird',
            'Immer dieselbe Person ist blockiert',
            'Aufgaben stehen tagelang in „In Arbeit"',
            'Betreuer erfährt Probleme zu spät',
        ],
    },
    {
        'name': 'Entwicklung',
        'match': ('backend', 'frontend', 'fullstack', 'entwickl', 'developer', 'dev', 'ux'),
        'summary': 'Setzt die Aufgaben um. Verantwortlich dafür, dass der eigene '
                   'Stand sichtbar ist (Board, Standup) und Probleme früh '
                   'gemeldet werden.',
        'daily': [
            'Standup ausfüllen (gestern / heute / Blocker)',
            'An einer Aufgabe arbeiten, Board-Karte aktuell halten',
            'Blocker sofort melden, nicht „noch schnell selbst lösen"',
            'Code der anderen reviewen, wenn etwas in „Review" liegt',
        ],
        'weekly': [
            'Bei Sprint-Planung und Schätzung mitmachen',
            'An der Retro teilnehmen, ehrlich',
            'Wissen teilen / dokumentieren, damit kein Einzelwissen entsteht',
        ],
        'flags': [
            'Eine Aufgabe ist seit Tagen „fast fertig"',
            'Viele angefangene, keine fertigen Aufgaben',
            'Schätzungen weichen ständig stark ab',
        ],
    },
    {
        'name': 'QA / Test',
        'match': ('qa', 'test', 'qualit'),
        'summary': 'Prüft, ob das Gebaute wirklich funktioniert und zu den '
                   'Anforderungen passt. Findet Fehler, bevor der Betreuer sie findet.',
        'daily': [
            'Fertige Aufgaben in „Review" testen',
            'Gefundene Fehler als Bug eintragen (Schweregrad, Schritte)',
            'Rückmeldung an die Entwicklung geben',
        ],
        'weekly': [
            'Testfälle zu neuen Anforderungen vorbereiten',
            'Testumgebung früh im Sprint anfragen',
            'Qualitäts-Überblick prüfen: was ist „nach Prod" durchgerutscht?',
        ],
        'flags': [
            'Aufgaben gehen ohne Test direkt auf „Fertig"',
            'Dieselben Fehler kommen wieder',
            'Testumgebung ist nie rechtzeitig da',
        ],
    },
    {
        'name': 'Auftraggeber / Product Owner',
        'match': ('owner', 'auftraggeber', 'po', 'kunde', 'sponsor', 'betreuer'),
        'summary': 'Sagt, was gebaut werden soll und in welcher Reihenfolge. Im '
                   'Kurs oft der Betreuer oder eine dafür bestimmte Person im Team.',
        'daily': [
            'Für Rückfragen zu Anforderungen erreichbar sein',
        ],
        'weekly': [
            'Backlog / Anforderungen priorisieren',
            'Sprint-Ergebnis abnehmen (Review)',
            'Änderungswünsche bewerten und entscheiden',
        ],
        'flags': [
            'Prioritäten ändern sich ständig',
            'Niemand nimmt Ergebnisse ab',
            'Anforderungen bleiben schwammig',
        ],
    },
    {
        'name': 'Vertretung der Teamleitung',
        'match': ('stellvertret', 'vertretung', 'co-lead', 'scrum'),
        'summary': 'Springt ein, wenn die TL ausfällt, und hält ihr den Rücken '
                   'frei (Protokolle, Termine organisieren, Retro moderieren).',
        'daily': [
            'Mitlesen, was die TL tut – damit Vertretung jederzeit möglich ist',
        ],
        'weekly': [
            'Meeting-Protokolle führen',
            'Termine und Einladungen organisieren',
            'Bei Bedarf Retro oder Standup übernehmen',
        ],
        'flags': [
            'Bei Ausfall der TL steht alles still',
            'Termine werden nicht protokolliert',
        ],
    },
]


# Tagesrhythmus: (Zeitfenster, {Rolle: Aufgabe})
DAY_RHYTHM: list[tuple[str, dict[str, str]]] = [
    ('Vor 10 Uhr', {
        'Alle': 'Standup ausfüllen',
        'Teamleitung': 'Fahrplan + Leitstand durchgehen',
    }),
    ('Vormittag', {
        'Teamleitung': 'Blocker lösen, Rückfragen beantworten',
        'Entwicklung': 'Fokus-Arbeit an einer Aufgabe',
        'QA / Test': 'Reviews von gestern testen',
    }),
    ('Nach dem Mittag', {
        'Entwicklung': 'Weiterarbeiten, Reviews für andere machen',
        'QA / Test': 'Bugs erfassen und rückmelden',
        'Teamleitung': 'Board pflegen, kurze 1:1s bei Bedarf',
    }),
    ('Nachmittag / Ende', {
        'Alle': 'Board-Karten auf den echten Stand bringen',
        'Teamleitung': 'Blick auf morgen: ist alles vorbereitet?',
    }),
]


# --------------------------------------------------------------------------
# Glossar
# --------------------------------------------------------------------------
GLOSSARY: list[tuple[str, str]] = [
    ('Sprint', 'Fester Arbeitsabschnitt (oft 1–2 Wochen) mit einem klaren Ziel.'),
    ('Backlog', 'Sammlung aller noch nicht eingeplanten Aufgaben und Ideen.'),
    ('Task / Karte', 'Eine einzelne, überschaubare Arbeitseinheit auf dem Board.'),
    ('Story-Stunden / Schätzung', 'Grobe Aufwandsschätzung einer Aufgabe in Stunden.'),
    ('Velocity', 'Wie viele Stunden Arbeit das Team pro Sprint tatsächlich schafft. '
                 'Erfahrungswert, kein Ziel.'),
    ('Kapazität', 'Verfügbare Arbeitszeit im Sprint – nach Abzug von Urlaub, '
                  'Klausuren, anderen Verpflichtungen.'),
    ('Commitment', 'Menge an Arbeit, die sich das Team für den Sprint vornimmt.'),
    ('Burndown', 'Kurve der noch offenen Arbeit über den Sprint. Sollte auf null fallen.'),
    ('Blocker', 'Etwas, das eine Aufgabe aufhält und von außen gelöst werden muss.'),
    ('Review', 'Prüfung einer fertigen Aufgabe durch eine zweite Person.'),
    ('Definition of Done', 'Checkliste, wann eine Aufgabe wirklich „fertig" ist.'),
    ('Retrospektive', 'Rückblick am Sprint-Ende: was besser machen? Mit Maßnahmen.'),
    ('Stakeholder', 'Person mit Interesse am Projekt (Betreuer, Nutzer, Auftraggeber).'),
    ('RACI', 'Wer ist verantwortlich / rechenschaftspflichtig / zu beraten / zu '
             'informieren.'),
    ('RAID', 'Risiken, Annahmen, Probleme (Issues), Entscheidungen – an einem Ort.'),
    ('Incident', 'Störung im laufenden Betrieb eines Systems.'),
    ('Meilenstein', 'Fester Termin mit einem konkreten Ergebnis (z. B. Abgabe).'),
    ('Epic', 'Größeres Arbeitspaket, das aus vielen Tasks besteht.'),
]
