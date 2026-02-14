# GitHub Secrets Setup Guide

## Overview
Your deployment uses **GitHub Secrets** to securely pass environment variables to your server. Secrets are:
- ✅ Never stored in your repository
- ✅ Encrypted by GitHub
- ✅ Only accessible to your GitHub Actions workflows
- ✅ Never logged in workflow output

The `.env` file is created dynamically on your server **during each deployment** from these secrets.

## Required Secrets

Set these in your GitHub repository settings under **Settings → Secrets and variables → Actions**:

### 1. **DB_PASSWORD**
A strong PostgreSQL password for the `manadia` user.

**Generate with:**
```bash
openssl rand -base64 32
```

Example output: `j7K9mW2xL4pQr8vN3hB5cF6gT1uY9zX0aE2sD5wM8n`

---

### 2. **CADDY_ADMIN_PASSWORD_HASH**
Hashed password for Caddy admin panel (`/admin` endpoints).

**Generate with:**
```bash
# Replace 'admin' username and 'yourpassword' with your actual password
htpasswd -bcB - admin yourpassword | cut -d: -f2
```

Or use Apache's apr1 hashing:
```bash
htpasswd -bc - admin yourpassword | cut -d: -f2 | base64
```

Example output: `$apr1$r61jtLof$HqJZimcKQWAeEofIqBaDi1`

---

### 3. **CADDY_OWNTRACKS_PASSWORD_HASH**
Hashed password for OwnTracks location uploads (`/pub` endpoint).

**Generate with (same process as CADDY_ADMIN_PASSWORD_HASH):**
```bash
htpasswd -bcB - owntracks yourotherpassword | cut -d: -f2
```

Example output: `$apr1$x61jtLof$HqJZimcKQWAeEofIqBaDi2`

---

### 4. **HOST**
Your DigitalOcean droplet IP or domain name.

Example: `123.45.67.89` or `your-droplet.example.com`

---

### 5. **USERNAME**
SSH username on your droplet (usually `root`).

---

### 6. **SSH_KEY**
Your SSH private key for authentication.

**To generate:**
```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy  # Copy this as the secret value
```

Then add the public key to your droplet:
```bash
cat ~/.ssh/github_deploy.pub | ssh root@YOUR_DROPLET_IP "cat >> ~/.ssh/authorized_keys"
```

---

### 7. **SSH_PASSPHRASE**
Passphrase for your SSH key (can be empty if key has no passphrase).

---

## Step-by-Step Setup

1. **Generate secure passwords:**
   ```bash
   # Generate DB password
   DB_PWD=$(openssl rand -base64 32)
   echo "DB_PASSWORD: $DB_PWD"
   
   # Generate Caddy hashes
   ADMIN_HASH=$(htpasswd -bcB - admin yourpassword | cut -d: -f2)
   echo "CADDY_ADMIN_PASSWORD_HASH: $ADMIN_HASH"
   
   OWNTRACKS_HASH=$(htpasswd -bcB - owntracks yourpassword | cut -d: -f2)
   echo "CADDY_OWNTRACKS_PASSWORD_HASH: $OWNTRACKS_HASH"
   ```

2. **Go to GitHub:**
   - Repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"

3. **Add each secret:**
   - DB_PASSWORD
   - CADDY_ADMIN_PASSWORD_HASH
   - CADDY_OWNTRACKS_PASSWORD_HASH
   - HOST
   - USERNAME
   - SSH_KEY
   - SSH_PASSPHRASE

4. **Deploy:**
   ```bash
   git push
   ```
   
   GitHub Actions will automatically:
   - Build your Docker image
   - SSH into your server
   - Create `.env` file from secrets
   - Start containers with `docker compose up -d`

---

## Security Benefits

| Approach | Storage | Security | Risk |
|----------|---------|----------|------|
| `.env` in repo | Git history | ❌ Public | HIGH - Anyone can read history |
| `.env` on server | File system | ⚠️ Medium | Medium - SSH access needed |
| GitHub Secrets | GitHub vault | ✅ Encrypted | LOW - Secrets never touch repo |

Your setup uses **GitHub Secrets**, which is the best practice for CI/CD deployments.

---

## Troubleshooting

**"password authentication failed for user manadia"**
- Check if `DB_PASSWORD` secret is set and not empty
- Redeploy: `git push`

**"CADDY_ADMIN_PASSWORD_HASH is not set"**
- Add the secret to GitHub with the exact name
- Wait a few seconds for GitHub to sync
- Redeploy

**SSH connection fails**
- Verify `SSH_KEY` contains the full private key (including `-----BEGIN` and `-----END` lines)
- Verify `HOST`, `USERNAME` are correct
- Ensure public key is in `~/.ssh/authorized_keys` on server

