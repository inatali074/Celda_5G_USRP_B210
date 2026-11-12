#!/bin/bash
# Sólo consulta los contenedores; no transmite ni accede al AUC.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
dominio=ims.mnc001.mcc001.3gppnetwork.org
for par in pcscf:21 icscf:19 scscf:20 hss:18; do
 nombre=${par%:*}; octeto=${par#*:}
 valor=$(docker compose --profile ims exec -T ims-dns dig @127.0.0.1 +short "$nombre.$dominio" A)
 [[ $valor == "10.53.2.$octeto" ]] || { echo "DNS incorrecto: $nombre"; exit 1; }
done
# El listener SIP no alcanza: exigir Cx conectado a HSS en ambos CSCF.
for servicio in ims-icscf ims-scscf; do
 listo=no
 for ((intento=0; intento<60; intento++)); do
  if peers=$(docker compose --profile ims exec -T "$servicio" kamcmd -s unix:/var/run/kamailio/kamailio_ctl cdp.list_peers 2>/dev/null) \
     && [[ $peers == *"hss.$dominio"* ]] && [[ $peers =~ (I_Open|R_Open) ]]; then
   listo=si; break
  fi
  sleep 1
 done
 [[ $listo == si ]] || { echo "Sin peer Cx abierto en $servicio; revisar cdp.list_peers y logs."; exit 1; }
done
docker compose --profile ims exec -T ims-pyhss python3 -c \
 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8080/apn/list",timeout=5); print("API PyHSS OK")'
echo 'DNS, Cx I/S-CSCF y API OK. Falta validar PDU ims y REGISTER con los teléfonos.'
