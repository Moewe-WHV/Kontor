# Slack/Discord Bots

## Ziel
Wichtige Ereignisse zusaetzlich direkt als Nachricht in Slack/Discord
posten; perspektivisch einfache Bot-Befehle (z. B. "/kontor status").

## Ansatz
- Baut auf `feature/webhooks` auf: Slack Incoming Webhook / Discord
  Webhook als vorgefertigte Ziel-Typen.
- Fuer Befehle: kleiner FastAPI-Endpoint fuer Slack Slash-Commands bzw.
  Discord Interactions – Signatur-Verifikation der jeweiligen Plattform
  ist Pflicht (kein ungepruefter Endpoint).

## Betroffene Dateien
Abhaengig von `app/webhooks.py`, neu: `app/integrations/slack.py` bzw.
`app/integrations/discord.py`, `app/main.py` (Routen).
