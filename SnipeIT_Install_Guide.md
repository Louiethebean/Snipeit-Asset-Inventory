# 🧾 Snipe-IT Installation Guide (Docker) - Ubuntu 24.04

This guide walks you through installing and configuring **Snipe-IT** (an open-source IT asset management system) using **Docker and Docker Compose** on **Ubuntu 24.04**.

## ✅ Prerequisites

- Ubuntu 24.04 LTS
- User with `sudo` privileges
- Internet access

## 🛠️ Step 1: Install Docker & Docker Compose

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker engine and Compose plugin
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable Docker service
sudo systemctl enable docker --now
```

## 📥 Step 2: Download the Official Snipe-IT Installer

```bash
wget https://raw.githubusercontent.com/snipe/snipe-it/master/install.sh
chmod +x install.sh
./install.sh
```

## 🧾 Step 3: Configure the `.env` File

```bash
cd snipe-it
cp .env.example .env
nano .env
```

Update the following values:

```env
APP_URL=http://localhost:8000

DB_CONNECTION=mysql
DB_HOST=db
DB_PORT=3306
DB_DATABASE=snipeit
DB_USERNAME=snipeit
DB_PASSWORD=changeme

MYSQL_ROOT_PASSWORD=supersecret
APP_KEY=
```

## 🔐 Step 4: Generate the Laravel App Key

```bash
sudo docker compose run --rm -v $(pwd)/.env:/var/www/html/.env app php artisan key:generate
```

## 🚀 Step 5: Start Snipe-IT

```bash
sudo docker compose up -d
```

## 🌐 Step 6: Access the Web Interface

```
http://localhost:8000
```

## 🔒 Step 7: Verify `.env` File is Not Public

Test in browser:

```
http://localhost:8000/.env
```

You should **not** see any content (404 or access denied is correct).

## 🧼 Cleanup (Optional)

```bash
rm install.sh
```

## 📎 Notes

- The app will be exposed on port **8000**
- If hosting remotely, ensure port 8000 is allowed in UFW or firewall
- You can later configure Nginx/Apache for HTTPS
