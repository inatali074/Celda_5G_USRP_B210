#!/bin/bash
# Deja de transmitir, guarda los logs y detiene la red 5G y la consola de control.
# Uso: ./stop.sh            apaga todo (radio, SIP, IMS, núcleo, panel y consola).
#      ./stop.sh --solo-radio  apaga el gNB, la central SIP, el IMS y la consola, y deja
#                              el núcleo y el panel andando (lo usa el inicio desde el panel).
set -u
solo_radio=no
case "${1:-}" in
    '') ;;
    --solo-radio) solo_radio=si ;;
    *) echo "Uso: ./stop.sh [--solo-radio]" >&2; exit 2 ;;
esac

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
SESION=red5g
marca=$(date +%Y-%m-%d_%H%M%S)

echo "--- gNB (deja de transmitir) ---"
docker compose --profile radio stop -t 15 gnb-radio
estado_gnb() {
    # true / false según el contenedor; ausente solo si Docker confirma que no existe;
    # desconocido si Docker no responde (no se puede asegurar que no transmita).
    local estado
    if ! estado=$(timeout 15 docker ps -a --filter 'name=^5g-gnb-radio-1$' --format '{{.State}}' 2>/dev/null); then
        echo desconocido
    elif [[ -z $estado ]]; then
        echo ausente
    elif [[ $estado == running || $estado == restarting ]]; then
        echo true
    else
        echo false
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

echo "--- Central SIP (si estaba levantada) ---"
docker compose --profile voz stop sip

echo "--- IMS (si estaba levantado) ---"
docker compose --profile ims stop ims-pcscf ims-scscf ims-icscf ims-pyhss ims-dns ims-mysql

if [[ $solo_radio == no ]]; then
    echo "--- Núcleo y MongoDB ---"
    # Uno por uno: Open5GS sale con código 139 al apagarse (aborto conocido de un hilo) y
    # Compose lo informa como error; en un solo comando eso dejaba MongoDB andando.
    for servicio in dashboard open5gs mongodb; do
        docker compose stop "$servicio"
    done
fi

echo "--- Consola ---"
screen -S "$SESION" -X quit >/dev/null 2>&1 && echo "  Consola cerrada." || echo "  No estaba abierta."

gobernador=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo desconocido)
if [[ $gobernador == performance ]]; then
    echo
    echo "La CPU sigue en 'performance' (vuelve sola a 'powersave' al reiniciar la PC). Para volver ahora:"
    echo "  echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
fi

echo
docker compose --profile radio --profile voz --profile ims ps --format '{{.Service}} {{.Status}}'
echo "--- Red detenida. Los abonados quedan guardados en MongoDB. ---"
