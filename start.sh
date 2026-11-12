#!/bin/bash
# Levanta la red 5G en Docker y abre la consola de control con 4 paneles.
# Sin configuración muestra un menú; elegir una opción o pasar un archivo TRANSMITE.
#
# Uso: ./start.sh [ARCHIVO_GNB.yml]. --confirmado se acepta por compatibilidad y no hace nada.
# Acepta también config/gnb/ARCHIVO_GNB.yml. Prioridad: argumento > GNB_CONFIG > menú.
# Otra configuración del núcleo: OPEN5GS_CONFIG=open5gs-5gc.yml ./start.sh gnb_b210.yml
set -eu

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

uso() {
    echo "Uso: ./start.sh [ARCHIVO_GNB.yml] [--confirmado] (en cualquier orden)" >&2
}

parsear_argumentos() {
    local argumento archivo_argumento=''
    confirmado=no
    for argumento in "$@"; do
        case "$argumento" in
            --confirmado) confirmado=si ;;
            *.yml)
                if [[ -n $archivo_argumento ]]; then
                    echo "Indicá un solo archivo de configuración del gNB." >&2
                    uso
                    return 1
                fi
                case "$argumento" in
                    config/gnb/*.yml) archivo_argumento=${argumento#config/gnb/} ;;
                    *) archivo_argumento=$argumento ;;
                esac
                if [[ $archivo_argumento == */* || $archivo_argumento == -* ]]; then
                    uso
                    return 1
                fi
                ;;
            *) uso; return 1 ;;
        esac
    done

    origen_config='menú'
    if [[ -n $archivo_argumento ]]; then
        if [[ ${GNB_CONFIG+x} && $GNB_CONFIG != "$archivo_argumento" ]]; then
            echo "Aviso: GNB_CONFIG='$GNB_CONFIG'; se usa el argumento '$archivo_argumento'." >&2
        fi
        GNB_CONFIG=$archivo_argumento
        origen_config=argumento
    elif [[ -n ${GNB_CONFIG:-} ]]; then
        origen_config=variable
    else
        GNB_CONFIG=''
    fi
    export GNB_CONFIG
}

parsear_argumentos "$@"
if [[ ${START_SH_SOLO_ARGS:-0} == 1 ]]; then
    printf 'GNB_CONFIG=%s\norigen=%s\nconfirmado=%s\n' "$GNB_CONFIG" "$origen_config" "$confirmado"
    exit 0
fi
export OPEN5GS_CONFIG="${OPEN5GS_CONFIG:-open5gs-5gc-zmq.yml}"
SESION=red5g

[[ -t 0 && -t 1 ]] || { echo "Correlo desde una terminal: abre una consola interactiva."; exit 1; }
if [[ -z $GNB_CONFIG ]]; then
    while true; do
        printf '\n=== TDD (n78, 3525 MHz) ===\n1) CP-OFDM\n2) DFT-s-OFDM\n=== FDD (n3, 1842,5 MHz) ===\n3) CP-OFDM\n4) DFT-s-OFDM (nunca probada)\n0) Salir sin transmitir\n'
        read -r -p 'Configuración: ' opcion || exit 0
        case "$opcion" in
            0) exit 0 ;;
            1) GNB_CONFIG=gnb_b210_00101_n78_cpofdm.yml; break ;;
            2) GNB_CONFIG=gnb_b210_00101_n78_dfts.yml; break ;;
            3) GNB_CONFIG=gnb_b210_00101_n3_cpofdm.yml; break ;;
            4) GNB_CONFIG=gnb_b210_00101_n3_dfts.yml; break ;;
            *) echo 'Opción inválida; elegí 0 a 4.' ;;
        esac
    done
fi
[[ -f "config/gnb/$GNB_CONFIG" ]] || { echo "No existe config/gnb/$GNB_CONFIG"; exit 1; }
[[ -f "config/open5gs/$OPEN5GS_CONFIG" ]] || { echo "No existe config/open5gs/$OPEN5GS_CONFIG"; exit 1; }

if ! lsusb | grep -qE 'Ettus|2500:0020|2500:0021|04b4:00f3'; then
    echo "No veo la B210 por USB. Conectala y volvé a correr."
    exit 1
fi

frecuencia=$(awk '/dl_arfcn:/{print $2}' "config/gnb/$GNB_CONFIG")
ganancia=$(awk '/tx_gain:/{print $2}' "config/gnb/$GNB_CONFIG")
plmn=$(awk -F"'" '/^  plmn:/{print $2}' "config/gnb/$GNB_CONFIG")
clock_ppm=$(awk '/clock_ppm:/{print $2}' "config/gnb/$GNB_CONFIG")
banda=$(awk '/^  band:/{print $2}' "config/gnb/$GNB_CONFIG")
duplexado=desconocido
case "$banda" in 78) duplexado=TDD ;; 3) duplexado=FDD ;; esac
onda=CP-OFDM
if awk '/^[[:space:]]*enable_transform_precoding:[[:space:]]*true/{found=1} END{exit !found}' "config/gnb/$GNB_CONFIG"; then
    onda=DFT-s-OFDM
fi
echo "=== CONFIGURACIÓN gNB: config/gnb/$GNB_CONFIG (origen: $origen_config) ==="
echo "  dl_arfcn $frecuencia, tx_gain $ganancia, PLMN $plmn, clock_ppm $clock_ppm"
echo "  Banda n$banda, $duplexado, subida $onda"
echo "  Aviso: el volcado IQ crece sin límite mientras haya subida; borrar /tmp/gnb_rx_symbols.bin del volumen gnb-logs al terminar."
echo
echo "ESTO TRANSMITE por la B210. La antena tiene que estar dentro de la jaula."
# Sin confirmación: quien ejecuta el script ya decidió transmitir (pedido del usuario, 2026-11-03).

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
docker compose up -d --no-build mongodb open5gs dashboard

echo "Dashboard: http://localhost:8080"

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

archivo_esperado="$PWD/config/gnb/$GNB_CONFIG"
montajes=$(docker inspect -f '{{range .Mounts}}{{.Source}} {{end}}' 5g-gnb-radio-1) || montajes=''
if [[ " $montajes " != *" $archivo_esperado "* ]]; then
    echo "ERROR: el gNB no montó el archivo elegido: $archivo_esperado" >&2
    echo "Montajes informados por Docker: ${montajes:-no disponibles}. Se detiene el gNB." >&2
    docker compose --profile radio stop gnb-radio
    exit 1
fi

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
