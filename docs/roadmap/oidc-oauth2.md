# OIDC/OAuth2 Single-Sign-On

## Ziel
Vollstaendiger OIDC/OAuth2 Authorization-Code-Flow (mit PKCE) gegen einen
konfigurierbaren Identity Provider, als Ergaenzung zum lokalen Passwort-Login.

## Ausgangslage
`app/oidc.py` (siehe `feature/security-multiuser-ops`) erkennt bereits, ob SSO
konfiguriert ist, und stellt die Platzhalter-Routen `/auth/oidc/login` und
`/auth/oidc/callback` bereit (liefern aktuell bewusst 501, statt ein
ungeprueftes ID-Token zu akzeptieren). `store.User.oidc_sub` existiert schon.

## Ansatz
- state + PKCE generieren, Redirect zu `{OIDC_ISSUER_URL}/authorize`.
- Token-Exchange im Callback via `httpx` (bereits Dependency).
- JWKS des Providers laden/cachen, ID-Token-Signatur + Claims (`iss`, `aud`,
  `exp`, `nonce`) pruefen – kein Decoding ohne Verifikation.
- Bei erstem SSO-Login automatisch Account anlegen/verknuepfen
  (`store.add_user(..., oidc_sub=sub)`), Default-Rolle konfigurierbar
  (z. B. `OIDC_DEFAULT_ROLE=viewer`).

## Betroffene Dateien
`app/oidc.py`, `app/auth.py`, `app/store.py`, ggf. `app/requirements.txt`
(falls eine JWKS/JWT-Bibliothek noetig wird).

## Voraussetzung
Baut auf der RBAC-Grundlage aus `feature/security-multiuser-ops` auf.
