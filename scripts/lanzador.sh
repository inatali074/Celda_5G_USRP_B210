#!/bin/bash
# Lanzador de la celda (lo abre el ícono "Celda 5G" del escritorio).
# 1. Toma un candado: solo puede haber un lanzador abierto.
# 2. Ofrece pasar la CPU a 'performance' (pide la contraseña de sudo).
# 3. Levanta el núcleo y el panel, SIN radio.
# 4. Abre el panel y deja corriendo el servicio de control (scripts/control_red.py),
#    con el que el panel inicia, cambia o frena la celda.
# Al cerrar esta ventana (o con Ctrl-C) se corta lo que esté en curso y se apaga todo
# con ./stop.sh, así la B210 no queda transmitiendo.
set -u
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
mkdir -p logs
registro=logs/lanzador_stop.log

pausa_y_salir() {
    read -r -p "Enter para cerrar." _ 2>/dev/null || true
    exit "$1"
}

echo "=== Celda 5G SA: lanzador ==="
echo

exec 9>logs/.lanzador.lock
if ! flock -n 9; then
    echo "Ya hay un lanzador abierto. Usá esa ventana (o cerrala antes de abrir otro)."
    pausa_y_salir 1
fi

gobernador=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo desconocido)
if [[ $gobernador != performance ]]; then
    echo "La CPU está en '$gobernador'. Para el tiempo real del gNB conviene 'performance'."
    echo "El comando es (pide tu contraseña):"
    echo "  echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
    read -r -p "¿Correrlo? [s/N]: " respuesta
    if [[ $respuesta == [sS] ]]; then
        echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null \
            && echo "CPU en 'performance'." \
            || echo "No se pudo cambiar; sigo con '$gobernador'."
    fi
else
    echo "CPU en 'performance'."
fi
echo

control_pid=''
apagar() {
    trap '' HUP INT TERM  # que una segunda señal no corte la limpieza
    trap - EXIT
    {
        echo "=== $(date '+%F %T') cierre del lanzador ==="
        if [[ -n $control_pid ]] && kill -0 "$control_pid" 2>/dev/null; then
            kill -TERM "$control_pid" 2>/dev/null
            wait "$control_pid" 2>/dev/null  # corta un inicio en curso y espera
        fi
        # En otra sesión y sin la terminal: al cerrar la ventana llega SIGHUP, y docker compose
        # (Go) lo atiende aunque esté ignorado, cancela la espera y deja las detenciones a medias.
        setsid -w ./stop.sh </dev/null
        codigo=$?
        estado=$(docker ps -a --filter 'name=^5g-gnb-radio-1$' --format '{{.State}}' 2>/dev/null) || estado=desconocido
        echo "stop.sh terminó con código $codigo; gNB: ${estado:-sin contenedor}"
    } >>"$registro" 2>&1
    if [[ $codigo == 0 && $estado != running && $estado != desconocido ]]; then
        echo "Red apagada. Detalle en $registro" 2>/dev/null
    else
        echo "ATENCIÓN: no se pudo confirmar el apagado (ver $registro). Revisá con: docker ps" 2>/dev/null
    fi
    exit 0
}
trap apagar EXIT HUP INT TERM

echo "--- Núcleo y panel (sin radio) ---"
docker compose up -d --no-build mongodb open5gs dashboard || { echo "No se pudo levantar el núcleo."; trap - EXIT HUP INT TERM; pausa_y_salir 1; }
printf 'Esperando a Open5GS'
sano=no
for _ in $(seq 1 40); do
    if [[ $(docker inspect -f '{{.State.Health.Status}}' 5g-open5gs-1 2>/dev/null) == healthy ]]; then
        sano=si
        break
    fi
    printf '.'
    sleep 1
done
echo
if [[ $sano != si ]]; then
    echo "Open5GS no quedó sano. Revisá: docker logs 5g-open5gs-1"
    read -r -p "Enter para apagar y cerrar." _ || true
    exit 1  # el trap de EXIT apaga lo que se haya levantado
fi

xdg-open http://localhost:8080 >/dev/null 2>&1 &
echo
echo "Panel: http://localhost:8080 . Desde ahí se elige la configuración y se inicia la celda."
echo "Consola de 4 paneles (con la celda andando): screen -r red5g"
echo "NO CIERRES ESTA VENTANA mientras uses la celda: al cerrarla se apaga todo."
echo
# En segundo plano + wait: así las señales se atienden enseguida y no al terminar Python.
python3 -I scripts/control_red.py 9>&- &
control_pid=$!
wait "$control_pid"
