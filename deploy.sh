#!/usr/bin/env bash
# ============================================================
# deploy.sh — Deploy content-tracker to cPanel via SSH
#
# Usage:
#   SSH_HOST=example.com SSH_USER=cpaneluser APP_PATH=~/content-tracker \
#   GIT_BRANCH=main GIT_REPO=https://github.com/youruser/microboss.git \
#   PYTHON_BIN=python3.11 \
#   bash deploy.sh
#
# Required env vars:
#   SSH_HOST      — cPanel server hostname
#   SSH_USER      — cPanel SSH username
#   APP_PATH      — absolute path to the app on server (e.g., ~/content-tracker)
#
# Optional env vars:
#   GIT_REPO      — repo URL (default: origin remote)
#   GIT_BRANCH    — branch to deploy (default: main)
#   PYTHON_BIN    — Python binary on server (default: python3.11)
# ============================================================
set -euo pipefail

# ---- Required checks ----
: "${SSH_HOST:?Must set SSH_HOST}"
: "${SSH_USER:?Must set SSH_USER}"
: "${APP_PATH:?Must set APP_PATH}"

GIT_BRANCH="${GIT_BRANCH:-main}"
PYTHON_BIN="${PYTHON_BIN:-python3.11}"
SSH_STRING="${SSH_USER}@${SSH_HOST}"

echo "==> Deploying branch '${GIT_BRANCH}' to ${SSH_STRING}:${APP_PATH}"

# ---- 1. SSH in and deploy ----
ssh "${SSH_STRING}" bash -s <<-REMOTE
    set -euo pipefail
    cd "${APP_PATH}"

    echo "--- 1. Pull latest code ---"
    git fetch origin
    git checkout "${GIT_BRANCH}"
    git pull origin "${GIT_BRANCH}"

    echo "--- 2. Create/update virtualenv ---"
    if [ ! -d "venv" ]; then
        ${PYTHON_BIN} -m venv venv
    fi
    source venv/bin/activate

    echo "--- 3. Install/update dependencies ---"
    pip install --upgrade pip wheel setuptools
    pip install -r requirements.txt

    echo "--- 4. Run migrations ---"
    python manage.py migrate --settings=config.settings.prod

    echo "--- 5. Collect static files ---"
    python manage.py collectstatic --settings=config.settings.prod --noinput --clear

    echo "--- 6. Compile translation messages ---"
    python manage.py compilemessages --settings=config.settings.prod 2>/dev/null || true

    echo "--- 7. Restart Passenger ---"
    touch passenger_wsgi.py

    echo "--- 8. Verify ---"
    python manage.py check --settings=config.settings.prod --deploy
REMOTE

echo "==> Deployment complete!"
