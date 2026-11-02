#!/bin/bash
# Levanta la red 5G en Docker y abre la consola de control con 4 paneles.
# TRANSMITE por la B210: pide confirmación cada vez.
#
# Uso: ./start.sh
# Otra configuración: GNB_CONFIG=gnb_b210.yml OPEN5GS_CONFIG=open5gs-5gc.yml ./start.sh
set -eu

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

# Configuración con la que hoy funciona la navegación: PLMN 001/01, CSI aperiódico.
export GNB_CONFIG="${GNB_CONFIG:-gnb_b210_00101_csiaper.yml}"
export OPEN5GS_CONFIG="${OPEN5GS_CONFIG:-open5gs-5gc-zmq.yml}"
SESION=red5g

[[ -f "config/gnb/$GNB_CONFIG" ]] || { echo "No existe config/gnb/$GNB_CONFIG"; exit 1; }
[[ -f "config/open5gs/$OPEN5GS_CONFIG" ]] || { echo "No existe config/open5gs/$OPEN5GS_CONFIG"; exit 1; }
[[ -t 0 && -t 1 ]] || { echo "Correlo desde una terminal: abre una consola interactiva."; exit 1; }

if ! lsusb | grep -qE 'Ettus|2500:0020|2500:0021|04b4:00f3'; then
    echo "No veo la B210 por USB. Conectala y volvé a correr."
    exit 1
fi

frecuencia=$(awk '/dl_arfcn:/{print $2}' "config/gnb/$GNB_CONFIG")
ganancia=$(awk '/tx_gain:/{print $2}' "config/gnb/$GNB_CONFIG")
plmn=$(awk -F"'" '/^  plmn:/{print $2}' "config/gnb/$GNB_CONFIG")
echo "Configuración: $GNB_CONFIG"
echo "  dl_arfcn $frecuencia, tx_gain $ganancia, PLMN $plmn"
echo
echo "ESTO TRANSMITE por la B210. La antena tiene que estar dentro de la jaula."
# --confirmado: la confirmación ya se dio antes de lanzar el script, para esta corrida.
if [[ ${1:-} == --confirmado ]]; then
    echo "Transmisión confirmada al lanzar el script."
else
    read -r -p "¿Transmitir ahora? Escribí 'si' para seguir: " respuesta
    [[ $respuesta == si ]] || { echo "Cancelado: no se levantó nada."; exit 0; }
fi

gobernador=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo desconocido)
if [[ $gobernador != performance ]]; then
    echo
    echo "La CPU está en '$gobernador'. El comando para pasarla a 'performance' (pide tu contraseña):"
    echo "  echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
    read -r -p "¿Correrlo? [s/N]: " respuesta
    if [[ $respuesta == [sS] ]]; then
        echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null \
            || echo "No se pudo cambiar; sigo con '$gobernador'."
    fi
fi

echo
echo "--- Núcleo y MongoDB ---"
docker compose up -d --no-build mongodb open5gs

printf 'Esperando a Open5GS'
for _ in $(seq 1 40); do
    estado=$(docker inspect -f '{{.State.Health.Status}}' 5g-open5gs-1 2>/dev/null || echo ausente)
    [[ $estado == healthy ]] && break
    printf '.'
    sleep 1
done
echo
[[ $estado == healthy ]] || { echo "Open5GS no quedó sano. Revisá: docker logs 5g-open5gs-1"; exit 1; }

echo "--- gNB (empieza a transmitir) ---"
inicio_gnb=$(date -u +%Y-%m-%dT%H:%M:%SZ)
docker compose --profile radio up -d --no-build --no-deps --force-recreate gnb-radio

printf 'Esperando conexión con el AMF'
conectado=no
for _ in $(seq 1 45); do
    if docker logs --since "$inicio_gnb" 5g-gnb-radio-1 2>&1 | grep -q 'gNB started'; then
        conectado=si
        break
    fi
    printf '.'
    sleep 1
    if [[ $(docker inspect -f '{{.State.Running}}' 5g-gnb-radio-1) != true ]]; then
        break
    fi
done
echo
if [[ $conectado != si ]]; then
    echo "El gNB no arrancó. Últimas líneas:"
    docker logs --tail 15 5g-gnb-radio-1 2>&1
    exit 1
fi

# Si la consola ya estaba abierta, se la reutiliza.
if screen -ls 2>/dev/null | grep -q "\.$SESION"; then
    exec screen -d -r "$SESION"
fi

# Prende el panel de métricas de usuarios del gNB cuando la consola ya está abierta.
(sleep 4; screen -S "$SESION" -p metricas -X stuff $'t\n' >/dev/null 2>&1) &
exec screen -S "$SESION" -c scripts/red5g.screenrc
