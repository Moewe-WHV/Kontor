# Skills-Matrix

## Ziel
Pro Crew-Mitglied hinterlegte Skills (Technologie/Kompetenz + Level),
sichtbar in der Crew-Ansicht und nutzbar fuer Zuweisungsvorschlaege.

## Ansatz
- `store.py`: neue `Skill`-Dataclass (`member_id`, `name`, `level` 1-5) +
  `p_skills`/`member_skills`-Helfer, analog zu bestehenden Mustern.
- `app/views/team.py`: Skills-Editor je Mitglied (Chips mit Level).
- Optional: `components.task_dialog` schlaegt beim Zuweisen Personen mit
  passendem Skill vor (Label/Tag-Abgleich mit `Task.labels`).

## Betroffene Dateien
`app/store.py`, `app/views/team.py`, ggf. `app/components.py`.
