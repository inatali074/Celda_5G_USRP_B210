#!/bin/bash
# Cuenta en el log completo del gNB (PC de Santi, solo lectura) los paquetes de bajada
# de un caso: recibidos del núcleo por GTP-U, enviados por PDCP y descartados en el gNB.
# Uso: ./contar_gnb.sh <caso> <inicio HH:MM:SS> <fin HH:MM:SS> [AAAA-MM-DD]
# Hora local (UTC-3); el log del gNB está en UTC. Agrega una fila a datos/perdidas_gnb.csv.
set -eu
caso=$1; ini=$2; fin=$3; dia=${4:-$(date +%F)}
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
REMOTO=${REMOTO:-$(cat remoto.local.txt 2>/dev/null)}; : "${REMOTO:?Falta REMOTO (usuario@IP) o remoto.local.txt}"
utc() { date -u -d "$dia $1 -0300" +%Y-%m-%dT%H:%M:%S; }
a=$(utc "$ini"); b=$(utc "$fin")
fila=$(ssh -n -o BatchMode=yes "$REMOTO" "docker exec 5g-gnb-radio-1 awk -v a='$a' -v b='$b' '
  !/^20[0-9][0-9]-/ { next }
  { t = substr(\$1, 1, 19) }
  t < a { next }
  t > b { exit }
  /\\[GTPU/ && / DL teid/ && /RX SDU/ { rx++ }
  /\\[PDCP/ && /DRB1 DL: TX PDU/ && /is_retx=false/ { tx++ }
  /Discarding SDUs/ { split(\$0, m, \"pdcp_sn=\"); split(m[2], r, \"[.][.]\"); desc += r[2] - r[1] + 1 }
  /UL processor is busy/ { busy++ }
  END { printf \"%d,%d,%d,%d\", rx, tx, desc, busy }' /tmp/gnb.log")
[[ -f datos/perdidas_gnb.csv ]] || echo 'caso,inicio,fin,gtpu_dl_rx,pdcp_dl_tx,pdcp_descartados,ul_busy' > datos/perdidas_gnb.csv
echo "$caso,$ini,$fin,$fila" | tee -a datos/perdidas_gnb.csv
