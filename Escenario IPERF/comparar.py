#!/usr/bin/env python3
"""Comparación n78 (TDD) contra n3 (FDD): las cuatro rampas UDP en una figura.
Uso: python3 comparar.py   (lee rampa_udp_{dl,ul}_{n78,n3}.csv que genera rampa.py)"""
import csv, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analizar import AQUI, AZUL, NARANJA, TXT2

TECHO = {('dl', 'n78'): 71.7, ('ul', 'n78'): 35, ('dl', 'n3'): 113.4, ('ul', 'n3'): 121.3}
COLOR = {'n78': AZUL, 'n3': NARANJA}
NOMBRE = {'n78': 'n78 TDD (51 PRB, 30 kHz)', 'n3': 'n3 FDD (106 PRB, 15 kHz)'}
leer = lambda s, b: [{k: float(v) if k != 'caso' else v for k, v in r.items()}
                     for r in csv.DictReader(open(os.path.join(AQUI, f'rampa_udp_{s}_{b}.csv')))]
fig, ejes = plt.subplots(2, 2, figsize=(10, 7))
fig.suptitle('Rampas UDP · n78 (TDD) contra n3 (FDD) · DFT-s-OFDM en la subida', x=.01, ha='left',
             fontsize=11, fontweight='bold')
for col, s in enumerate(('dl', 'ul')):
    a, c = ejes[0][col], ejes[1][col]
    xmax = 0
    for b in ('n78', 'n3'):
        r = leer(s, b)
        x = [p['ofrecido'] for p in r]; xmax = max(xmax, max(x))
        a.plot(x, [p['entregado'] for p in r], color=COLOR[b], marker='o', ms=5, label=NOMBRE[b])
        a.axhline(TECHO[(s, b)], color=COLOR[b], lw=1, ls=':')
        a.annotate(f'pico teórico {b}: {TECHO[(s, b)]:g}', (0 if b == 'n3' else 1, TECHO[(s, b)]),
                   xycoords=('axes fraction', 'data'), xytext=(2 if b == 'n3' else -2, 3),
                   textcoords='offset points', fontsize=7.5, color=COLOR[b], ha='left' if b == 'n3' else 'right')
        c.plot(x, [p['rtt'] for p in r], color=COLOR[b], marker='o', ms=5, label=NOMBRE[b])
    a.plot([0, xmax], [0, xmax], color=TXT2, lw=1, ls='--', label='ideal (entregado = ofrecido)')
    a.set_title(f"{'Bajada' if s == 'dl' else 'Subida'}: tasa entregada [Mbit/s]" +
                (' (gNB, MAC)' if s == 'dl' else ' (receptor iperf3)'))
    a.set_ylim(0, 130); a.legend(frameon=False, fontsize=8, loc='upper left', bbox_to_anchor=(0, .8))
    c.set_yscale('log'); c.set_title(f"{'Bajada' if s == 'dl' else 'Subida'}: RTT mediano del ping [ms, log]")
    for e in (a, c):
        e.set_xlabel('Tasa ofrecida por iperf3 [Mbit/s]')
fig.tight_layout(rect=(0, 0, 1, .95))
salida = os.path.join(AQUI, 'graficas', 'comparacion_n78_n3.png')
fig.savefig(salida, dpi=150)
print(salida)
