#!/bin/bash
# Arma una carpeta con lo necesario para levantar la red en otra PC. No transmite ni toca la red.
#
# Uso: scripts/empaquetar_para_otra_pc.sh <carpeta destino> [--sin-imagenes]
#
# La carpeta contiene K, OPc y ADM de las SIM de laboratorio: no la subas a ningún lado.
# Las imágenes ocupan varios GB. Con --sin-imagenes, se construyen en la otra PC (lleva horas).
set -eu
set -o pipefail

[[ $# -ge 1 && $# -le 2 ]] || { echo "Uso: $0 <carpeta destino> [--sin-imagenes]"; exit 1; }
raiz=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
destino=$1
imagenes=si
if [[ ${2:-} == --sin-imagenes ]]; then
    imagenes=no
elif [[ -n ${2:-} ]]; then
    echo "Opción desconocida: $2"
    exit 1
fi

cd -- "$raiz"
if [[ -n $(git status --porcelain) ]]; then
    echo "Hay cambios sin commit: no irían en el paquete. Hacé el commit y volvé a correr."
    exit 1
fi
for s in config/secretos/usim.env config/secretos/sim_adm.env; do
    [[ -r $s ]] || { echo "Falta $s"; exit 1; }
done

umask 077
mkdir -p -- "$destino"
destino=$(cd -- "$destino" && pwd)

echo "--- Proyecto (con historial de git) ---"
git bundle create "$destino/proyecto.bundle" --all
git bundle verify "$destino/proyecto.bundle" >/dev/null

echo "--- Secretos de las SIM ---"
tar -C "$raiz" -cf "$destino/secretos.tar" config/secretos/usim.env config/secretos/sim_adm.env

cp -- scripts/instalar_en_otra_pc.sh docs/LEVANTAR_EN_OTRA_PC.md "$destino/"

if [[ $imagenes == si ]]; then
    faltan=0
    for i in 5g-gnb-radio:latest 5g-open5gs:latest mongo:6.0; do
        docker image inspect "$i" >/dev/null 2>&1 || { echo "Falta la imagen $i"; faltan=1; }
    done
    [[ $faltan == 0 ]] || exit 1
    echo "--- Imágenes de Docker (puede tardar varios minutos) ---"
    docker save 5g-gnb-radio:latest 5g-open5gs:latest mongo:6.0 | gzip -1 > "$destino/imagenes.tar.gz"
fi

(cd -- "$destino" && sha256sum -- * > SHA256SUMS.txt)
echo
du -sh -- "$destino"/*
echo
echo "Listo: $destino"
echo "Copiala a la otra PC y seguí LEVANTAR_EN_OTRA_PC.md. Contiene claves: borrala del medio de copia después."
