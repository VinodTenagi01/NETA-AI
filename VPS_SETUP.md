# NETA.AI — VPS Setup Guide

## Requirements

| Item | Specification |
|---|---|
| OS | Ubuntu 22.04 LTS or 24.04 LTS |
| CPU | 4 vCPU minimum |
| RAM | 8 GB minimum |
| Disk | 40 GB SSD minimum |
| Ports | 22, 80, 443 open inbound |
| Domain | A record → VPS IP (e.g. `app.netaai.in`) |

---

## Automated Setup

The script `scripts/setup-vps.sh` handles everything in one command:

```bash
sudo bash scripts/setup-vps.sh app.netaai.in
```

It will:
1. Install Docker CE
2. Install nginx + certbot
3. Configure nginx with your domain
4. Obtain Let's Encrypt SSL certificate
5. Start Docker Compose production stack
6. Set up certbot auto-renewal cron

---

## Manual Step-by-Step

### 1. SSH into VPS
```bash
ssh ubuntu@<VPS_IP>
```

### 2. Install Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

### 3. Install nginx and certbot
```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### 4. Upload project files
From your local machine:
```bash
scp -r D:\NETA.AI ubuntu@<VPS_IP>:/opt/neta-ai
```

### 5. Configure environment
```bash
cd /opt/neta-ai
cp .env.example .env
```

Edit `.env` — minimum required changes:
```env
SECRET_KEY=<run: python3 -c "import secrets; print(secrets.token_hex(32))">
POSTGRES_PASSWORD=<run: python3 -c "import secrets; print(secrets.token_urlsafe(32))">
REDIS_PASSWORD=<run: python3 -c "import secrets; print(secrets.token_urlsafe(32))">
ALLOWED_ORIGINS=["https://app.netaai.in"]
```

### 6. Configure nginx domain
```bash
bash scripts/configure-domain.sh app.netaai.in
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
sudo nginx -t
```

### 7. Obtain SSL certificate
```bash
sudo systemctl stop nginx
sudo certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email admin@netaai.in \
    -d app.netaai.in
sudo systemctl start nginx
```

### 8. Start production stack
```bash
cd /opt/neta-ai
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 9. Build and deploy frontend
On local machine:
```powershell
cd D:\NETA.AI\frontend
npm run build
scp -r dist\* ubuntu@<VPS_IP>:/var/www/neta-frontend/
```

### 10. Verify
```bash
curl https://app.netaai.in/api/health
# Expected: {"status":"ok","service":"neta-api","version":"1.0.0"}
```

---

## Firewall Setup (UFW)

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Systemd Service (optional — auto-start on reboot)

Create `/etc/systemd/system/neta-ai.service`:
```ini
[Unit]
Description=NETA.AI Docker Stack
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/neta-ai
ExecStart=/usr/bin/docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose stop
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable neta-ai
```

---

## Post-Deployment Checklist

- [ ] `https://app.netaai.in/api/health` returns `{"status":"ok"}`
- [ ] `https://app.netaai.in` loads React frontend
- [ ] Admin login works (`admin@netaai.in`)
- [ ] SSL certificate valid (green lock in browser)
- [ ] `docker compose ps` shows all 5 containers healthy
- [ ] Certbot renewal configured: `sudo crontab -l | grep certbot`
- [ ] Firewall enabled: `sudo ufw status`

---

## REMAINING: CLIENT INFRASTRUCTURE ACCESS REQUIRED

The following cannot be completed without client credentials:

| Item | Status |
|---|---|
| Provision VPS | Client must provision (DigitalOcean/Hetzner/AWS) |
| Set DNS A record | Client must access domain registrar |
| Run setup-vps.sh | Client must SSH into server |
| WhatsApp `WHATSAPP_API_TOKEN` | Client must obtain from Meta Developer Console |
| WhatsApp `WHATSAPP_PHONE_ID` | Client must obtain from Meta Developer Console |
| Register webhook URL | Client must complete in Meta Developer Console |
