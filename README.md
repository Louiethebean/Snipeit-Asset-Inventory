# 📦 Snipe-IT Docker Deployment (Ubuntu 24.04)

![License](https://img.shields.io/badge/license-MIT-blue) ![Platform](https://img.shields.io/badge/platform-Ubuntu%2024.04-orange) ![Tool](https://img.shields.io/badge/tool-Snipe--IT-0077b6)

This repository provides a clean and reliable installation guide for deploying [Snipe-IT](https://snipeitapp.com) using Docker and Docker Compose on Ubuntu 24.04.

![Architecture](./architecture.svg)

## 📄 Installation Guide

For full step-by-step instructions, refer to the [SnipeIT_Install_Guide](./SnipeIT_Install_Guide.md) in this repository.

## 🧰 Features

- Dockerized Snipe-IT and MariaDB
- Laravel `.env` configuration
- Secure key generation
- Web interface setup wizard

## 🚀 Quick Start

```bash
wget https://raw.githubusercontent.com/snipe/snipe-it/master/install.sh
chmod +x install.sh
./install.sh
```

Then follow the steps in the full guide.

## 🔒 Security Tip

Always verify that your `.env` file is not publicly accessible via the web.

## 🎯 What I Learned / Skills Demonstrated

- **Multi-container app deployment** — coordinating a Laravel app container and a MariaDB container via Docker Compose, including service dependencies and persistent volumes.
- **Application secrets handling** — generating a Laravel `APP_KEY` correctly and keeping `.env` out of both git and public web access.
- **IT asset management domain knowledge** — why organizations track hardware/license lifecycle in a dedicated system instead of spreadsheets, and what that system needs to expose (audit trail, checkouts, depreciation).
- **Production-adjacent hardening** — verifying `.env` isn't web-accessible, a real misconfiguration that has caused actual credential leaks in the wild.

**Problem solved:** a repeatable Docker-based deployment of an open-source asset management platform, with the security gotchas (`.env` exposure) called out instead of glossed over.

## 📄 License

This project is licensed under the MIT License. See [LICENSE](./MIT%20License.txt) for details.
