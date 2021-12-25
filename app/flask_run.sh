#!/bin/bash
set -e
source ${SISTEC_DOWNLOAD_CONFIG:-../config}/sistec_download.env
export FLASK_ENV='development'
export FLASK_APP='sistec_download.py'
#exec flask run --host 192.168.100.32 --port 8080
exec flask run --host localhost --port 8080
