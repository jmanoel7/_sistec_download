#!/bin/bash
set -e
source /srv/www/sistec_download/venv/sistec_download_dev/bin/activate
cd /srv/www/sistec_download/app/
exec ./flask_run.sh
