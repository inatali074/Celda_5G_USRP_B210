#!/bin/bash
# Validar antes de inicializar el volumen: evitar una base parcial por placeholders.
set -euo pipefail
[[ -n ${MYSQL_ROOT_PASSWORD:-} && ${MYSQL_ROOT_PASSWORD:-} != CAMBIAR* && ${#MYSQL_ROOT_PASSWORD} -ge 16 ]] \
 || { echo 'Configurar MYSQL_ROOT_PASSWORD (16+ caracteres).'; exit 1; }
[[ ${IMS_DB_PASSWORD:-} =~ ^[A-Za-z0-9_]{16,}$ && $IMS_DB_PASSWORD != CAMBIAR* ]] \
 || { echo 'Configurar IMS_DB_PASSWORD (16+ caracteres alfanuméricos/_).'; exit 1; }
[[ -z ${MYSQL_ROOT_HOST:-} ]] || { echo 'MYSQL_ROOT_HOST no está permitido: root sólo local.'; exit 1; }
exec /usr/local/bin/docker-entrypoint.sh "$@"
