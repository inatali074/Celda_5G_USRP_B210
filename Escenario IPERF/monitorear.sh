#!/bin/bash
# Monitorea la celda de la PC de Santi una vez por segundo, solo lectura, y lo guarda acá.
# Uso: ./monitorear.sh <etiqueta>      (ej.: n78_tcp_dl)   Ctrl-C o kill para terminar.
# Guarda:
#   datos/<marca>_<etiqueta>.jsonl        estado del panel (/api/state sin historia ni eventos)
#   datos/<marca>_<etiqueta>_gnb.log      filas de métricas y avisos de la consola del gNB
# No toca nada en la PC remota: solo lee el panel (127.0.0.1:8080) y docker logs.
set -u
etiqueta=${1:?Uso: ./monitorear.sh <etiqueta>}
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
marca=$(date +%Y-%m-%d_%H%M%S)
base="datos/${marca}_${etiqueta}"
# Usuario@IP de la PC de la celda: variable REMOTO o archivo remoto.local.txt (fuera de git).
REMOTO=${REMOTO:-$(cat remoto.local.txt 2>/dev/null)}; : "${REMOTO:?Falta REMOTO (usuario@IP) o remoto.local.txt}"
SSH=(ssh -o BatchMode=yes -o ServerAliveInterval=5 "$REMOTO")

echo "Guardando en $base.jsonl y ${base}_gnb.log (Ctrl-C para terminar)"

# Consola del gNB con marca de tiempo de Docker, desde ahora.
"${SSH[@]}" 'docker logs -t -f --since 1s 5g-gnb-radio-1 2>&1' >"${base}_gnb.log" &
pid_logs=$!

# Estado del panel: una línea JSON por segundo, sin campos pesados ni eventos del núcleo.
"${SSH[@]}" 'while :; do
  curl -s --max-time 2 http://127.0.0.1:8080/api/state | python3 -c "
import json,sys,time
try: d=json.load(sys.stdin)
except Exception: print(json.dumps({\"t\":time.time(),\"error\":\"sin respuesta\"})); sys.exit()
for k in (\"history\",\"metrics_history\",\"events\",\"raw\"): d.pop(k,None)
d[\"t\"]=time.time()
print(json.dumps(d,separators=(\",\",\":\")),flush=True)" || exit
  sleep 1
done' >"$base.jsonl" &
pid_estado=$!

terminar() { kill "$pid_logs" "$pid_estado" 2>/dev/null; wait 2>/dev/null; echo; echo "Listo: $(wc -l <"$base.jsonl") muestras."; exit 0; }
trap terminar INT TERM
wait
