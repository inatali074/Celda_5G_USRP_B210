#!/bin/bash
# Paneles de la consola de control. Solo leen, salvo el de métricas, que está conectado al gNB.
# Uso: scripts/panel.sh conexiones|metricas|eventos|ping
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

NUCLEO=5g-open5gs-1
GNB=5g-gnb-radio-1

# Del log del núcleo, una línea legible por cada cambio de estado de un celular.
filtro_conexiones() {
    sed -u -E 's/\x1b\[[0-9;]*m//g' | sed -u -Ef scripts/anonimizar.sed | awk -W interactive '
        function hora() { return substr($2, 1, 8) }
        function quien(   i) {
            for (i = 1; i <= NF; i++) if ($i ~ /(imsi|suci)-/) { sub(/.*(imsi|suci)-/, "&", $i); gsub(/[][]|SUPI/, "", $i); return $i }
            return ""
        }
        /InitialUEMessage/          { print hora(), "   conecta"; fflush(); next }
        /Registration complete/     { print hora(), " + REGISTRADO", quien(); fflush(); next }
        /Registration reject/       { print hora(), " x RECHAZADO ", quien(), $0 ~ /\[95\]/ ? "(abonado no cargado)" : ""; fflush(); next }
        /Authentication failure/ && /Synch/ { print hora(), "   resincroniza SQN", quien(); fflush(); next }
        /Authentication failure/ && !/Synch/ { print hora(), " x falla autenticacion", quien(); fflush(); next }
        /IPv4\[/ && /\[smf\]/ {
            ip = $0; sub(/.*IPv4\[/, "", ip); sub(/\].*/, "", ip)
            print hora(), " + SESION IP", ip, quien(); fflush(); next
        }
        /De-register|Deregistration|Implicit De/ { print hora(), " - SE DESREGISTRA", quien(); fflush(); next }
        /UE Context Release \[/     { print hora(), " - pierde conexion de radio"; fflush(); next }
        /Number of gNB-UEs is now/  { n = $NF; sub(/.*now /, ""); sub(/ .*/, ""); print "             conectados por radio:", $0; fflush(); next }
        /gNB-N2 accepted.*master_sm/ { print hora(), " = gNB conectado al AMF"; fflush(); next }
    '
}

# Del log del gNB, solo los eventos de radio. Las fallas de tiempo real se resumen.
filtro_eventos() {
    awk -W interactive '
        function hora() { return substr($1, 12, 8) }
        /\[PHY.*PRACH:/ && /detected_preambles=\[\{/ {
            r = $0; sub(/.*rssi=/, "", r); sub(/ .*/, "", r); print hora(), " PRACH rssi=" r; fflush(); next
        }
        /CCCH UL rrcSetupRequest/          { print hora(), " RRC setup"; fflush(); next }
        /rrcReestablishmentRequest/        { print hora(), " ! RRC reestablecimiento"; fflush(); next }
        /DCCH DL rrcRelease/               { print hora(), " - RRC liberado"; fflush(); next }
        /\[MAC.*RLF detected/ {
            c = $0; sub(/.*Cause: /, "", c); print hora(), " ! RLF:", c; fflush(); next
        }
        /Real-time failure/ {
            t = "FAPI"; if ($0 ~ /underflow/) t = "underflow"; else if ($0 ~ /RF: late/) t = "late"
            if (hora() != ult) { print hora(), " ~ tiempo real:", t; fflush(); ult = hora() }
            next
        }
    '
}

esperar() {
    until [[ $(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null) == true ]]; do
        sleep 2
    done
}

case "${1:-}" in
    conexiones)
        echo "=== CONEXIONES (núcleo) ==="
        while true; do
            esperar "$NUCLEO"
            docker logs -f --tail 300 "$NUCLEO" 2>&1 | filtro_conexiones
            sleep 2
        done
        ;;
    metricas)
        echo "=== GNB: métricas de usuarios (se prenden y apagan con t + Enter) ==="
        echo "Ctrl-C acá solo reconecta el panel, no apaga el gNB. Para apagar todo: ./stop.sh"
        while true; do
            esperar "$GNB"
            docker attach --detach-keys=ctrl-c "$GNB"
            sleep 2
        done
        ;;
    eventos)
        echo "=== EVENTOS DE RADIO (gNB) ==="
        echo "El log se escribe por bloques: con poco tráfico aparece con demora."
        while true; do
            esperar "$GNB"
            docker exec "$GNB" tail -F -n 0 /tmp/gnb.log 2>/dev/null | filtro_eventos
            sleep 2
        done
        ;;
    ping)
        echo "=== PING A LOS CELULARES (desde el núcleo) ==="
        while true; do
            ips=$(docker logs "$NUCLEO" 2>&1 | grep -oE 'IPv4\[10\.45\.[0-9.]+\]' | grep -oE '10\.45\.[0-9.]+' | awk '!v[$0]++' | tail -5)
            ultima=$(docker logs "$NUCLEO" 2>&1 | grep -oE 'IPv4\[10\.45\.[0-9.]+\]' | grep -oE '10\.45\.[0-9.]+' | tail -1)
            echo
            echo "IP asignadas: ${ips:-ninguna todavía}" | tr '\n' ' '
            echo
            read -r -p "IP a la que hacer ping [${ultima:-escribí una}]: " destino
            destino=${destino:-$ultima}
            if [[ ! $destino =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]]; then
                echo "IP inválida."
                continue
            fi
            echo "Ctrl-C corta el ping y vuelve acá."
            docker exec -it "$NUCLEO" python3 -c "$(cat scripts/ping_ue.py)" "$destino"
        done
        ;;
    *)
        echo "Uso: $0 conexiones|metricas|eventos|ping"
        exit 1
        ;;
esac
