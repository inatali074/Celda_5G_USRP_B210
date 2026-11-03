#!/bin/bash
# Deja de transmitir, guarda los logs y detiene la red 5G y la consola de control.
# Uso: ./stop.sh
set -u

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
SESION=red5g
marca=$(date +%Y-%m-%d_%H%M%S)

echo "--- gNB (deja de transmitir) ---"
docker compose --profile radio stop -t 15 gnb-radio
estado_gnb() {
    if ! docker inspect 5g-gnb-radio-1 >/dev/null 2>&1; then
        echo ausente  # El contenedor no existe: no hay gNB.
    else
        docker inspect -f '{{.State.Running}}' 5g-gnb-radio-1 2>/dev/null || echo desconocido
    fi
}
if [[ $(estado_gnb) == true ]]; then
    echo "ATENCIÓN: el gNB sigue corriendo; se fuerza la detención."
    docker kill 5g-gnb-radio-1
fi
gnb=$(estado_gnb)
if [[ $gnb != false && $gnb != ausente ]]; then
    echo "ERROR: no se pudo confirmar que el gNB esté detenido (estado: $gnb). PUEDE SEGUIR TRANSMITIENDO."
    echo "Desconectá la B210 del USB y revisá con: docker ps"
    exit 1
fi
echo "La B210 ya no transmite."

echo "--- Logs ---"
mkdir -p logs
if docker cp 5g-gnb-radio-1:/tmp/gnb.log "logs/${marca}_gnb.log" 2>/dev/null; then
    gzip -f "logs/${marca}_gnb.log"
    echo "  logs/${marca}_gnb.log.gz"
else
    echo "  No había log del gNB para guardar."
fi
if docker logs 5g-open5gs-1 >/dev/null 2>&1; then
    # Sin identificadores de terceros: solo quedan los SUCI de los PLMN de laboratorio.
    docker logs 5g-open5gs-1 2>&1 \
        | sed -E 's/\x1b\[[0-9;]*m//g' \
        | scripts/anonimizar.sed \
        | gzip > "logs/${marca}_nucleo.log.gz"
    echo "  logs/${marca}_nucleo.log.gz"
fi

echo "--- Núcleo y MongoDB ---"
docker compose stop dashboard open5gs mongodb

echo "--- Consola ---"
screen -S "$SESION" -X quit >/dev/null 2>&1 && echo "  Consola cerrada." || echo "  No estaba abierta."

gobernador=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo desconocido)
if [[ $gobernador == performance ]]; then
    echo
    echo "La CPU sigue en 'performance' (vuelve sola a 'powersave' al reiniciar la PC). Para volver ahora:"
    echo "  echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
fi

echo
docker compose --profile radio ps --format '{{.Service}} {{.Status}}'
echo "--- Red detenida. Los abonados quedan guardados en MongoDB. ---"
