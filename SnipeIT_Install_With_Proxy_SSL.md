# 🧾 Snipe-IT Installation Guide with Docker + Nginx Reverse Proxy + SSL (Let's Encrypt)

This guide walks you through installing **Snipe-IT** using Docker and Docker Compose **with HTTPS support via Nginx reverse proxy and Let's Encrypt SSL certificates**.

---

## ✅ Prerequisites

- Ubuntu 24.04 LTS
- Domain name pointed to your server (e.g., `snipeit.yourdomain.com`)
- User with `sudo` privileges
- Internet access

---

## 🛠️ Step 1: Install Docker & Docker Compose

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable docker --now
```

---

## 📥 Step 2: Clone and Prepare Snipe-IT

```bash
wget https://raw.githubusercontent.com/snipe/snipe-it/master/install.sh
chmod +x install.sh
./install.sh
cd snipe-it
cp .env.example .env
nano .env
```

Update these fields in `.env`:

```env
APP_URL=https://snipeit.yourdomain.com

DB_CONNECTION=mysql
DB_HOST=db
DB_PORT=3306
DB_DATABASE=snipeit
DB_USERNAME=snipeit
DB_PASSWORD=changeme

MYSQL_ROOT_PASSWORD=supersecret
APP_KEY=
```

---

## 🔐 Step 3: Generate the Laravel App Key

```bash
sudo docker compose run --rm -v $(pwd)/.env:/var/www/html/.env app php artisan key:generate
```

---

## 🚀 Step 4: Start Snipe-IT (Internally)

```bash
sudo docker compose up -d
```

This will run the app internally on port `8000`.

---

## 🌐 Step 5: Set Up Nginx Reverse Proxy with SSL

### Install Nginx and Certbot:
```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Create Nginx Config:
```bash
sudo nano /etc/nginx/sites-available/snipeit
```

Paste this config:

```nginx
server {
    listen 80;
    server_name snipeit.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/snipeit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Get SSL Cert with Certbot:
```bash
sudo certbot --nginx -d snipeit.yourdomain.com
```

Follow the prompts to install and enable HTTPS.

---

## ✅ Final Steps

Visit:
```
https://snipeit.yourdomain.com
```

Complete the setup wizard, create your admin account, and you're done!

---

## 🔒 Verify `.env` Is Not Exposed

Check:
```
https://snipeit.yourdomain.com/.env
```

You should see `404 Not Found`. If not, block dotfiles in Nginx:

```nginx
location ~ /\.(?!well-known).* {
    deny all;
}
```

---

## 🧼 Optional Cleanup

```bash
rm install.sh
```

---

## 📎 Notes

- Automatically renew SSL with: `sudo certbot renew --dry-run`
- Use UFW to restrict open ports: allow 80 and 443 only

