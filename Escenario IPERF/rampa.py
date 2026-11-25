#!/usr/bin/env python3
"""Curva de saturación de una rampa UDP: tasa entregada, pérdida, RTT y cola contra la tasa ofrecida.
Uso: python3 rampa.py <prefijo de caso> <banda> <sentido> <techo teórico Mbit/s>
     ej.: python3 rampa.py 5- n78 dl 71.7
Usa casos.csv, datos/*.jsonl (monitorear.sh) y datos/perdidas_gnb.csv (contar_gnb.sh).
"""
import csv, os, re, statistics as st, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analizar import AQUI, AZUL, NARANJA, AQUA, VIOLETA, ROJO, TXT2, cargar, epoca, pings, iperf_por_segundo

prefijo, banda, sentido, techo = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
sufijo = sys.argv[5] if len(sys.argv) > 5 else ''  # ej.: _cpofdm, para no pisar la rampa DFT-s-OFDM
p = 'dl' if sentido == 'dl' else 'ul'
filas = cargar()
casos = [c for c in csv.DictReader(open(os.path.join(AQUI, 'casos.csv')))
         if c['caso'].startswith(prefijo) and c['banda'] == banda]
puntos = []
for c in casos:
    ofrecido = float(re.search(r'(\d+(?:\.\d+)?) Mbit/s', c['descripcion'])[1])
    t0, t1 = epoca(c['dia'], c['inicio_local']), epoca(c['dia'], c['fin_local'])
    w = [d['radio_ues'][0] for d in filas if t0 <= d['t'] <= t1 and d.get('radio_ues')]
    tasa = [u[f'{p}_brate'] / 1e6 for u in w]
    cola = [u['dl_bs' if p == 'dl' else 'bsr'] / 1e6 for u in w]
    rtt = [r for _, r in pings(filas, t0, t1 - 12) if r is not None]  # sin el ping que sigue al escalón
    entregado, perdida = st.mean(tasa), max(0.0, 100 * (1 - st.mean(tasa) / ofrecido))
    if p == 'ul':
        # En subida el servidor del panel recibe: tasa y pérdida medidas por iperf3.
        ip = iperf_por_segundo(filas, t0, t1 + 3, 'ul')
        entregado = st.median(v for _, v in ip if v > 0)  # sin resumen: mediana de los segundos con datos
        for d in filas:
            for l in (d.get('iperf') or {}).get('lines', []):
                if t0 <= l['time'] <= t1 + 5 and 'receiver' in l['text']:
                    m = re.search(r'(\d+)/(\d+) \(', l['text'])
                    perdida = 100 * int(m[1]) / int(m[2])
                    entregado = float(re.search(r'([\d.]+) Mbits/sec', l['text'])[1])  # resumen de iperf3
        if perdida is None or perdida == max(0.0, 100 * (1 - st.mean(tasa) / ofrecido)):
            # Sin resumen final: se suman los intervalos de 1 s (Lost/Total) del escalón.
            vis = {}
            for d in filas:
                for l in (d.get('iperf') or {}).get('lines', []):
                    m = re.search(r'Mbits/sec\s+[\d.]+ ms\s+(\d+)/(\d+)', l['text'])
                    if t0 <= l['time'] <= t1 + 3 and m and 'receiver' not in l['text']:
                        vis[(l['time'], l['text'])] = (int(m[1]), int(m[2]))
            if vis:
                perdida = 100 * sum(a for a, _ in vis.values()) / max(1, sum(b for _, b in vis.values()))
    puntos.append({'caso': c['caso'], 'ofrecido': ofrecido, 'entregado': entregado, 'maximo': max(tasa),
                   'perdida': perdida, 'phr': st.median([u['phr'] for u in w if u.get('phr') is not None]),
                   'sinr': st.median([u['sinr'] for u in w if u.get('sinr') is not None]),
                   'rtt': st.median(rtt) if rtt else None, 'cola': max(cola),
                   'mcs': st.median([u[f'{p}_mcs'] for u in w])})
puntos.sort(key=lambda r: r['ofrecido'])
x = [r['ofrecido'] for r in puntos]

fig, ejes = plt.subplots(2, 2, figsize=(10, 7))
nombre = 'bajada' if p == 'dl' else 'subida'
fig.suptitle(f'Rampa UDP de {nombre} · {banda}{sufijo.replace("_", " ")} · tasa ofrecida contra respuesta de la celda',
             x=.01, ha='left', fontsize=11, fontweight='bold')
a = ejes[0][0]
a.plot([0, max(x)], [0, max(x)], color=TXT2, lw=1, ls='--', label='ideal (entregado = ofrecido)')
a.axhline(techo, color=ROJO, lw=1, ls=':', label=f'pico teórico TS 38.306 ({techo:g})')
a.plot(x, [r['maximo'] for r in puntos], color=AQUA, marker='o', ms=5, label='máximo por segundo (gNB)')
a.plot(x, [r['entregado'] for r in puntos], color=AZUL, marker='o', ms=5, label='promedio del escalón' + (' (iperf3)' if p == 'ul' else ''))
a.set_title('Tasa entregada [Mbit/s]' + (' (iperf3 y gNB)' if p == 'ul' else ' por el gNB (MAC)'))
a.legend(frameon=False, fontsize=8, loc='upper left')
a.set_ylim(0, max(max(x), techo) * 1.08)
b = ejes[0][1]
b.bar(x, [r['perdida'] for r in puntos], width=min(b - a for a, b in zip(x, x[1:])) * .6, color=ROJO)
b.set_title('Pérdida [%] medida por iperf3 (Lost/Total)' if p == 'ul' else 'Pérdida estimada [%] = 1 − entregado / ofrecido')
b.set_ylim(0, 100)
c = ejes[1][0]
c.plot(x, [r['rtt'] for r in puntos], color=VIOLETA, marker='o', ms=5)
c.set_yscale('log')
c.set_title('RTT mediano del ping durante el escalón [ms, log]')
d = ejes[1][1]
if p == 'dl':
    d.plot(x, [r['cola'] for r in puntos], color=NARANJA, marker='o', ms=5)
    d.set_title('Cola máxima del gNB (dl_bs) [MB]')
    d.set_ylim(bottom=0)
else:  # el BSR queda clavado en el máximo en todos los escalones: se muestra la potencia
    d.plot(x, [r['phr'] for r in puntos], color=NARANJA, marker='o', ms=5)
    d.axhline(0, color=TXT2, lw=1, ls='--')
    d.set_title('PHR mediano [dB] · ≤ 0: el teléfono está a potencia máxima')
for e in (a, b, c, d):
    e.set_xlabel('Tasa ofrecida por iperf3 [Mbit/s]')
fig.tight_layout(rect=(0, 0, 1, .95))
salida = os.path.join(AQUI, 'graficas', f'rampa_udp_{p}_{banda}{sufijo}.png')
fig.savefig(salida, dpi=150)
with open(os.path.join(AQUI, f'rampa_udp_{p}_{banda}{sufijo}.csv'), 'w', newline='') as f:
    wr = csv.DictWriter(f, fieldnames=list(puntos[0]))
    wr.writeheader()
    wr.writerows({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()} for r in puntos)
for r in puntos:
    print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()})
print(salida)
