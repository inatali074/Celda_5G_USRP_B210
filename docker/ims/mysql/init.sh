#!/bin/bash
# La imagen de MySQL incorpora este archivo con "source" a su propio script:
# no usar "set -eu" acá, porque se aplicaría al script oficial y lo rompe.
[[ ${IMS_DB_PASSWORD:-} =~ ^[A-Za-z0-9_]{16,}$ && $IMS_DB_PASSWORD != CAMBIAR* ]] || { echo 'IMS_DB_PASSWORD inválida' >&2; exit 1; }
[[ ${MYSQL_ROOT_PASSWORD:-} != CAMBIAR* && ${#MYSQL_ROOT_PASSWORD} -ge 16 ]] || { echo 'MYSQL_ROOT_PASSWORD inválida' >&2; exit 1; }
for db in icscf scscf pcscf ims_hss_db; do
 user=$db; [[ $db != ims_hss_db ]] || user=pyhss
 docker_process_sql <<SQL
CREATE DATABASE IF NOT EXISTS $db;
CREATE USER IF NOT EXISTS '$user'@'10.53.2.%' IDENTIFIED WITH mysql_native_password BY '$IMS_DB_PASSWORD';
GRANT ALL ON $db.* TO '$user'@'10.53.2.%';
SQL
 [[ $? -eq 0 ]] || { echo "Falló la creación de $db" >&2; exit 1; }
done
