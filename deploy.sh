#!/usr/bin/env bash
set -euo pipefail

cd /home/elvessora/web/elvessora.ae/private/elvessora

sudo -u elvessora git pull origin main
sudo -u elvessora git submodule update --init --recursive
sudo -u elvessora venv/bin/pip install -r requirements.txt
sudo -u elvessora venv/bin/python manage.py migrate
sudo -u elvessora venv/bin/python manage.py collectstatic --no-input

systemctl restart elvessora.service
