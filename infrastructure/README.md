# Nginx Configuration for Nutrition Chat

This directory contains the nginx configuration for routing HTTP traffic to the Nutrition Chat application.

## Installation

### 1. Copy the configuration to nginx sites-available:

```bash
sudo cp infrastructure/nginx.conf /etc/nginx/sites-available/nutrition-chat
```

### 2. Create a symbolic link to enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/nutrition-chat /etc/nginx/sites-enabled/
```

### 3. Test nginx configuration:

```bash
sudo nginx -t
```

### 4. Reload nginx:

```bash
sudo systemctl reload nginx
```

### 5. Ensure your FastAPI server is running on port 8000:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Configuration Details

- **Listens on**: Port 80 (HTTP)
- **Proxies to**: localhost:8000 (FastAPI application)
- **Max upload size**: 50MB (for CSV files)
- **Timeouts**: 300 seconds (5 minutes) for LLM responses

## Optional: SSL/HTTPS Setup

To enable HTTPS with Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

This will automatically configure HTTPS and redirect HTTP to HTTPS.

## Customization

Edit `/etc/nginx/sites-available/nutrition-chat` and change:
- `server_name _` to your actual domain name
- Adjust timeouts if needed for longer LLM responses
- Modify `client_max_body_size` for larger file uploads

## Logs

- Access log: `/var/log/nginx/nutrition-chat-access.log`
- Error log: `/var/log/nginx/nutrition-chat-error.log`

## Troubleshooting

Check nginx status:
```bash
sudo systemctl status nginx
```

View recent errors:
```bash
sudo tail -f /var/log/nginx/nutrition-chat-error.log
```

Test if port 8000 is accessible:
```bash
curl http://localhost:8000
```
