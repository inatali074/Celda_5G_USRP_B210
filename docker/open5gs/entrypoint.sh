#!/bin/sh
set -eu
# Estos valores deben coincidir con el pool y la interfaz definidos en config/.
: "${UE_SUBNET:?Falta UE_SUBNET en config/open5gs/network.env}"
: "${OGSTUN_ADDRESS:?Falta OGSTUN_ADDRESS en config/open5gs/network.env}"
ip tuntap add name ogstun mode tun
ip addr add "$OGSTUN_ADDRESS" dev ogstun
ip link set ogstun up
# Solo se modifica el namespace de red del contenedor.
iptables -t nat -A POSTROUTING -s "$UE_SUBNET" ! -o ogstun -j MASQUERADE
exec "$@"
