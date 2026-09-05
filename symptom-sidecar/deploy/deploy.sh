#!/usr/bin/env bash
# -e stop on error · -u error on unset vars · -o pipefail catch pipe failures
set -euo pipefail

APP=/opt/sidecar/app
VENV=/opt/sidecar/venv

echo "==> pulling"
sudo -u sidecar git -C "$APP" pull --ff-only

echo "==> dependencies"
sudo -u sidecar "$VENV/bin/pip" install -q -r "$APP/requirements.txt"

echo "==> restarting"
sudo systemctl restart sidecar
sleep 2

echo "==> health check"
sudo curl -fsS --unix-socket /run/sidecar/gunicorn.sock http://localhost/healthz
echo
echo "==> deployed $(git -C "$APP" rev-parse --short HEAD)"
