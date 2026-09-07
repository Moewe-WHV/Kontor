# Deployment auf dem VPS

Produktions-Stack: **NiceGUI-App** hinter **Caddy** (Reverse Proxy mit
automatischem HTTPS via Let's Encrypt). Die App selbst ist nur im
Docker-Netz erreichbar, nach außen spricht ausschließlich Caddy.

## Voraussetzungen

- VPS mit Docker + Docker Compose (v2)
- Eine Domain/Subdomain, deren **A**- (und ggf. **AAAA**-) Record auf die
  VPS-IP zeigt
- Ports **80** und **443** am VPS offen (Firewall/Security-Group)

## Einrichtung

```bash
# Code auf den VPS bringen (git clone / scp / rsync), dann im Projektordner:
cp .env.prod.example .env.prod
```

`.env.prod` ausfüllen:

| Variable         | Bedeutung                                                        |
|------------------|-----------------------------------------------------------------|
| `DOMAIN`         | z. B. `leitstand.example.com`                                    |
| `ACME_EMAIL`     | E-Mail für Let's-Encrypt-Benachrichtigungen                      |
| `APP_USERNAME`   | Login-Benutzer (Default `admin`)                                 |
| `APP_PASSWORD`   | **Pflicht.** Langes Zufallspasswort: `openssl rand -base64 24`   |
| `STORAGE_SECRET` | Signiert die Session-Cookies: `openssl rand -hex 32`             |
| `GITHUB_TOKEN`   | optional, für die PR-Ansicht                                     |
| `GITHUB_REPO`    | Default-Repo `owner/name`                                        |

Starten:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Beim ersten Aufruf von `https://<DOMAIN>` holt Caddy automatisch das
Zertifikat. Danach: Login mit `APP_USERNAME` / `APP_PASSWORD`.

## Betrieb

```bash
# Logs
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f

# Nach Code-Update neu bauen & ausrollen
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Stoppen
docker compose -f docker-compose.prod.yml --env-file .env.prod down
```

## Daten & Backup

Alle Inhalte liegen in **`app/data/pm.json`** (per Bind-Mount aus dem
Container heraus persistent). Backup = diese Datei sichern, z. B. per Cron:

```bash
0 3 * * *  cp /pfad/zum/projekt/app/data/pm.json /backups/pm-$(date +\%F).json
```

Caddys Zertifikate liegen im Docker-Volume `caddy_data` und überstehen
`down`/`up`.

## Hinweise

- **Login:** Der Schutz greift, sobald `APP_PASSWORD` gesetzt ist. Ohne
  Passwort (lokale Entwicklung) sind alle Seiten offen.
- Die App läuft mit `reload=False`; Hot-Reload gibt es nur im
  Dev-Setup (`docker-compose.yml`, `APP_RELOAD=true`).
- Der Debug-Port 5678 (debugpy) ist im Produktions-Image **nicht** aktiv.
- Mehrere Nutzer teilen sich ein Login; eine echte Benutzerverwaltung
  ist nicht vorgesehen.
