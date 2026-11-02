"""Ping por ICMP desde el contenedor del núcleo, que no trae el comando ping.

Se ejecuta adentro con: docker exec -it 5g-open5gs-1 python3 -c "$(cat scripts/ping_ue.py)" <IP> [cantidad]
Sale por ogstun hacia el celular. Al cortar muestra pérdida y RTT.
"""
import os
import select
import socket
import struct
import sys
import time


def suma(d):
    if len(d) % 2:
        d += b"\0"
    s = sum(struct.unpack("!%dH" % (len(d) // 2), d))
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    return ~s & 0xFFFF


destino = sys.argv[1]
cantidad = int(sys.argv[2]) if len(sys.argv) > 2 else 0
ident = os.getpid() & 0xFFFF
sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
enviados, tiempos, seq = 0, [], 0

try:
    while not cantidad or enviados < cantidad:
        seq += 1
        datos = bytes(56)
        cab = struct.pack("!BBHHH", 8, 0, 0, ident, seq & 0xFFFF)
        cab = struct.pack("!BBHHH", 8, 0, suma(cab + datos), ident, seq & 0xFFFF)
        inicio = time.monotonic()
        sock.sendto(cab + datos, (destino, 0))
        enviados += 1
        limite = inicio + 1.0
        respondio = False
        while time.monotonic() < limite:
            listo, _, _ = select.select([sock], [], [], limite - time.monotonic())
            if not listo:
                break
            r, origen = sock.recvfrom(2048)
            ihl = (r[0] & 15) * 4
            tipo, _, _, rid, rseq = struct.unpack("!BBHHH", r[ihl:ihl + 8])
            if tipo == 0 and rid == ident and rseq == seq & 0xFFFF and origen[0] == destino:
                rtt = (time.monotonic() - inicio) * 1000
                tiempos.append(rtt)
                print(f"{time.strftime('%H:%M:%S')} {destino} seq={seq} rtt={rtt:.1f} ms", flush=True)
                respondio = True
                break
        if not respondio:
            print(f"{time.strftime('%H:%M:%S')} {destino} seq={seq} sin respuesta", flush=True)
        espera = limite - time.monotonic()
        if espera > 0:
            time.sleep(espera)
except KeyboardInterrupt:
    pass

perdidos = enviados - len(tiempos)
print(f"\n{enviados} enviados, {len(tiempos)} recibidos, {100 * perdidos / max(enviados, 1):.0f} % de pérdida")
if tiempos:
    print(f"RTT min/prom/max = {min(tiempos):.1f}/{sum(tiempos) / len(tiempos):.1f}/{max(tiempos):.1f} ms")
