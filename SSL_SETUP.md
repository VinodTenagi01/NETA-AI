# NETA.AI — SSL / HTTPS Setup Guide

NETA.AI uses **Let's Encrypt** (free) for TLS via `certbot`.

---

## Prerequisites

- Domain DNS `A` record pointing to VPS IP (propagated)
- VPS with ports 80 and 443 open
- nginx installed (`apt install nginx`)
- certbot installed (`apt install certbot python3-certbot-nginx`)

---

## Obtain Certificate

```bash
# Stop nginx temporarily so certbot can use port 80
sudo systemctl stop nginx

# Obtain standalone certificate
sudo certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email admin@netaai.in \
    -d app.netaai.in

# Start nginx
sudo systemctl start nginx
```

Certificate files will be at:
```
/etc/letsencrypt/live/app.netaai.in/fullchain.pem
/etc/letsencrypt/live/app.netaai.in/privkey.pem
```

---

## nginx SSL Configuration

The `nginx/nginx.conf` is pre-configured for TLS. Before using it, replace the domain placeholder:

```bash
# Replace REPLACE_WITH_YOUR_DOMAIN with actual domain
sed -i 's/REPLACE_WITH_YOUR_DOMAIN/app.netaai.in/g' /etc/nginx/nginx.conf
nginx -t && systemctl reload nginx
```

Or use the configure-domain script:
```bash
bash scripts/configure-domain.sh app.netaai.in
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
sudo nginx -t && sudo systemctl reload nginx
```

---

## Verify HTTPS

```bash
curl -I https://app.netaai.in/api/health
# Should show: HTTP/2 200 and strict-transport-security header
```

```bash
# Check certificate expiry
openssl s_client -connect app.netaai.in:443 -servername app.netaai.in 2>/dev/null \
  | openssl x509 -noout -dates
```

---

## Auto-Renewal

Let's Encrypt certificates expire in 90 days. Certbot auto-renewal is set up by `setup-vps.sh`. To verify:

```bash
sudo crontab -l | grep certbot
# Should show: 0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'
```

Test renewal dry-run:
```bash
sudo certbot renew --dry-run
```

---

## Security Headers Included in nginx.conf

The nginx config includes these headers automatically:

| Header | Value |
|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` |

---

## Troubleshooting

**certbot: port 80 already in use**
```bash
sudo systemctl stop nginx
sudo certbot certonly --standalone -d app.netaai.in
sudo systemctl start nginx
```

**nginx: SSL_CTX_use_certificate_file failed**
- Certificate files don't exist yet — run certbot first, then start nginx.

**certificate not trusted**
- DNS may not have propagated yet. Check: `dig app.netaai.in +short`

**Renewal failing**
```bash
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```
