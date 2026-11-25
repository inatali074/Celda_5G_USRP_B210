#!/usr/bin/env python3
"""Subida con CP-OFDM contra DFT-s-OFDM: rampas UDP de n3 y n78 en una figura.
Uso: python3 comparar_formas.py   (lee rampa_udp_ul_{n3,n78}{,_cpofdm}.csv de rampa.py)"""
import csv, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analizar import AQUI, AZUL, NARANJA, TXT2

leer = lambda n: [{k: float(v) if k != 'caso' else v for k, v in r.items()}
                  for r in csv.DictReader(open(os.path.join(AQUI, f'rampa_udp_ul_{n}.csv')))]
FORMAS = [('', 'DFT-s-OFDM (24/11)', AZUL), ('_cpofdm', 'CP-OFDM (25/11)', NARANJA)]
fig, ejes = plt.subplots(2, 2, figsize=(10, 7))
fig.suptitle('Subida: CP-OFDM contra DFT-s-OFDM · rampas UDP', x=.01, ha='left', fontsize=11, fontweight='bold')
for col, (banda, techo) in enumerate((('n78', 35), ('n3', 121.3))):
    a, c = ejes[0][col], ejes[1][col]
    xmax = 0
    for suf, nombre, color in FORMAS:
        r = leer(banda + suf)
        x = [p['ofrecido'] for p in r]; xmax = max(xmax, max(x))
        a.plot(x, [p['entregado'] for p in r], color=color, marker='o', ms=5, label=nombre)
        c.plot(x, [p['sinr'] for p in r], color=color, marker='o', ms=5, label=nombre)
    a.plot([0, xmax], [0, xmax], color=TXT2, lw=1, ls='--', label='ideal')
    a.set_title(f'{banda}: tasa recibida por iperf3 [Mbit/s] (pico teórico {techo:g})')
    a.set_ylim(0, xmax * 1.1); a.legend(frameon=False, fontsize=8, loc='upper left')
    c.set_title(f'{banda}: SINR mediana del PUSCH [dB]'); c.set_ylim(10, 40)
    for e in (a, c):
        e.set_xlabel('Tasa ofrecida por iperf3 [Mbit/s]')
fig.tight_layout(rect=(0, 0, 1, .95))
salida = os.path.join(AQUI, 'graficas', 'comparacion_cpofdm_dfts.png')
fig.savefig(salida, dpi=150)
print(salida)
