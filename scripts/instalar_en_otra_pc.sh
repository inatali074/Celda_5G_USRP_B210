#!/bin/bash
# Instala en esta PC lo que armó empaquetar_para_otra_pc.sh. No transmite: nunca arranca el gNB.
# No usa sudo: si falta algo del sistema, lo informa con el comando para corregirlo.
#
# Uso, desde la carpeta del paquete: ./instalar_en_otra_pc.sh <carpeta donde instalar>
set -eu
set -o pipefail

[[ $# -eq 1 ]] || { echo "Uso: $0 <carpeta donde instalar>"; exit 1; }
paquete=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
destino=$1

echo "=== 1. Requisitos ==="
falta=0
for c in docker git screen lsusb gzip python3; do
    if command -v "$c" >/dev/null 2>&1; then
        echo "  ok     $c"
    else
        echo "  FALTA  $c"
        falta=1
    fi
done
if ! docker compose version >/dev/null 2>&1; then
    echo "  FALTA  docker compose"
    falta=1
fi
if [[ $falta == 1 ]]; then
    echo "Instalalo (en Debian/Ubuntu: sudo apt install docker.io docker-compose-v2 git screen usbutils python3)"
    echo "y volvé a correr este script. Si docker pide permisos: sudo usermod -aG docker \$USER, y reiniciá la sesión."
    exit 1
fi
docker info >/dev/null 2>&1 || { echo "Docker no responde: ¿está el servicio activo y tenés permisos?"; exit 1; }

grep -q avx2 /proc/cpuinfo || { echo "La CPU no tiene AVX2: las imágenes (x86-64-v3) no van a correr."; exit 1; }
echo "  ok     CPU con AVX2 ($(nproc) hilos, $(awk '/MemTotal/{printf "%.1f", $2/1048576}' /proc/meminfo) GiB de RAM)"

(cd -- "$paquete" && sha256sum -c --quiet SHA256SUMS.txt) || { echo "El paquete está dañado: volvé a copiarlo."; exit 1; }
echo "  ok     paquete íntegro"

echo "=== 2. Proyecto ==="
if [[ -e $destino ]]; then
    echo "$destino ya existe: elegí otra carpeta para no pisarla."
    exit 1
fi
git clone --quiet "$paquete/proyecto.bundle" "$destino"
destino=$(cd -- "$destino" && pwd)
(umask 077; tar -C "$destino" -xf "$paquete/secretos.tar")
chmod 700 "$destino/config/secretos"
chmod 600 "$destino"/config/secretos/*
echo "  $destino"

echo "=== 3. Imágenes ==="
cd -- "$destino"
if [[ -f $paquete/imagenes.tar.gz ]]; then
    gzip -dc "$paquete/imagenes.tar.gz" | docker load
else
    echo "El paquete no trae imágenes: se construyen ahora, y puede llevar horas."
    docker pull mongo:6.0
    docker compose build open5gs
    docker compose --profile radio build gnb-radio
fi

echo "=== 4. Abonados ==="
docker compose up -d --no-build mongodb
for _ in $(seq 1 40); do
    [[ $(docker inspect -f '{{.State.Health.Status}}' 5g-mongodb-1 2>/dev/null) == healthy ]] && break
    sleep 1
done
for imsi in 001010000000003 001010000000004 001010000000001 722999000000003 722999000000001; do
    bash scripts/cargar_abonado.sh "$imsi"
done
docker compose stop mongodb

echo "=== 5. Por revisar antes de transmitir ==="
if lsusb | grep -qE 'Ettus|2500:002[01]|04b4:00f3'; then
    echo "  ok     B210 conectada. Debe quedar en USB 3: start.sh muestra 'Operating over USB 3' en el log."
else
    echo "  AVISO  No veo la B210: conectala a un puerto USB 3, directo y sin hub."
fi
if [[ ! -e /dev/net/tun ]]; then
    echo "  AVISO  Falta /dev/net/tun: sudo modprobe tun"
fi
if ! lsmod | grep -q '^sctp' && ! modprobe -n sctp >/dev/null 2>&1; then
    echo "  AVISO  El kernel no parece tener SCTP, que usa el N2. Probá: sudo modprobe sctp"
fi
echo
echo "Listo. Sin transmitir. Seguí con la sección 'Antes de transmitir' de docs/LEVANTAR_EN_OTRA_PC.md."
