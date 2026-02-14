# manadia

manadia is an open source location tracker application using owntracks, another open source application, as the location service provider. manadia aims to provide a customizable approach to location tracking and consumption of the location data.

_readme.md last updated 14 february 2026_

---

## limitations (arranged by severity)

### security

✅ **FIXED**: API keys are now hashed with bcrypt and cannot be recovered after generation.  
✅ **FIXED**: Database credentials are no longer hardcoded; managed via environment variables.  
✅ **FIXED**: Caddy authentication hashes are loaded from environment variables.

See [SECURITY.md](SECURITY.md) for details on the security improvements.

### battery consumption

depending on the mode selected in owntracks, battery consumption varies anywhere from 2–30% over a normal day.

### documentation

there is no publicly available documentation for manadia as of today.

### ui

as of now, manadia does not have a client interface that is accessible.

### multi user support

manadia currently does not natively support onboarding more than 1 user. it is possible, but not documented at this point.

---

## hosting prerequisites

1. docker and docker compose
2. a vps or local server running on your machine
3. domain name for ssl certificates via caddy (preferred but not necessary)
4. ssh access to your server

---

## hosting quick guide

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd manadia
   ```

2. **Create `.env` file with required credentials**

   ```bash
   cp .env.example .env
   # Edit .env with your secure credentials (see instructions below)
   ```

3. **Generate secure credentials for Caddy**

   ```bash
   # For OwnTracks authentication
   htpasswd -bc - owntracks yourpassword | cut -d: -f2

   # For Admin authentication
   htpasswd -bc - admin yourpassword | cut -d: -f2
   ```

   Place these hashes in your `.env` file as:
   - `CADDY_OWNTRACKS_PASSWORD_HASH`
   - `CADDY_ADMIN_PASSWORD_HASH`

4. **Update Caddyfile with your domain**
   Edit `Caddyfile` and replace `manadia.wandanial.com` with your actual domain.

5. **Start services**

   ```bash
   docker compose pull
   docker compose up -d
   ```

6. **Verify deployment**
   ```bash
   docker ps
   # All services should show "Up"
   ```

---

## environment variables

See [.env.example](.env.example) for all available configuration options.

**Required variables:**

- `DB_PASSWORD` - PostgreSQL password (generate: `openssl rand -base64 32`)
- `CADDY_OWNTRACKS_PASSWORD_HASH` - Basic auth for /pub endpoint
- `CADDY_ADMIN_PASSWORD_HASH` - Basic auth for /admin endpoints

---

## api key management

### Generating a new API key

```bash
curl -X POST "http://your-domain/admin/generate-api-key?user_name=alice&description=my+tracker" \
  -H "Authorization: Basic $(echo -n 'admin:password' | base64)"
```

**Important:** The API key is only shown once at generation time. Copy and save it immediately. If lost, revoke the key and generate a new one.

### Using API keys

```bash
curl "http://your-domain/history" \
  -H "X-API-Key: your_api_key_here"
```

### Revoking a key

```bash
curl -X POST "http://your-domain/admin/revoke-api-key?api_key=your_api_key_here" \
  -H "Authorization: Basic $(echo -n 'admin:password' | base64)"
```

---

## owntracks configuration

1.  host - yourdomain.com
2.  port - 443
3.  proto - http
4.  tls - on
5.  userid - owntracks (from Caddy basicauth)
6.  password - yourpassword (from Caddy basicauth)
7.  authentication - on

---

## security best practices

- ✅ Never commit `.env` files to git
- ✅ Always use HTTPS in production (Caddy handles this)
- ✅ Generate strong passwords: `openssl rand -base64 32`
- ✅ Rotate API keys periodically
- ✅ Store API keys in a secure location
- ✅ Monitor audit logs for suspicious activity
- ✅ Keep Docker images updated

coming soon.
