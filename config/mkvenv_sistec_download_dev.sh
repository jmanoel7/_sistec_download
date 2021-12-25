#!/bin/bash
set -e
mkdir -p /srv/www/sistec_download/venv/
virtualenv -p /usr/bin/python3.9 /srv/www/sistec_download/venv/sistec_download_dev
source /srv/www/sistec_download/venv/sistec_download_dev/bin/activate
cd /srv/www/sistec_download/config/
pip install -U -r requirements.dev.txt
exit 0
