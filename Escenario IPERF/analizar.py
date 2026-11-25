#!/usr/bin/env python3
"""Gráficas y resumen de cada caso del escenario iperf.

Lee casos.csv (un caso por fila, con horario de inicio y fin) y la grabación de
monitorear.sh (datos/*.jsonl), y genera por caso:
  graficas/<caso>_<banda>_<forma>.png   serie temporal en paneles apilados
  resumen.csv                           medianas y extremos por caso
Uso: python3 analizar.py [caso ...]     (sin argumentos, todos)
"""
import csv, datetime as dt, glob, json, os, re, statistics as st, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
# Paleta de referencia (skill dataviz), modo claro.
AZUL, NARANJA, AQUA, VIOLETA, ROJO = '#2a78d6', '#eb6834', '#1baf7a', '#6250d6', '#e34948'
SUP, TXT, TXT2, GRILLA = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'figure.facecolor': SUP, 'axes.facecolor': SUP, 'axes.edgecolor': GRILLA,
                     'axes.labelcolor': TXT2, 'xtick.color': TXT2, 'ytick.color': TXT2,
                     'text.color': TXT, 'axes.grid': True, 'grid.color': GRILLA, 'grid.linewidth': .8,
                     'axes.spines.top': False, 'axes.spines.right': False, 'font.size': 9,
                     'axes.titlesize': 9, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
                     'lines.linewidth': 2})


def cargar():
    filas = []
    for f in sorted(glob.glob(os.path.join(AQUI, 'datos', '*.jsonl'))):
        dia = os.path.basename(f)[:10]
        for linea in open(f):
            try:
                d = json.loads(linea)
            except ValueError:
                continue
            if 't' in d:
                d['_dia'] = dia
                filas.append(d)
    filas.sort(key=lambda d: d['t'])
    return filas


def epoca(dia, hhmmss):
    return dt.datetime.strptime(f'{dia} {hhmmss}', '%Y-%m-%d %H:%M:%S').timestamp()


def iperf_por_segundo(filas, t0, t1, sentido=None):
    """Tasa por intervalo de la salida del servidor iperf3 del panel (sin omitidos ni totales)."""
    vistos, puntos = set(), []
    for d in filas:
        for l in (d.get('iperf') or {}).get('lines', []):
            if not t0 <= l['time'] <= t1 or (l['time'], l['text']) in vistos:
                continue
            vistos.add((l['time'], l['text']))
            # [  5] ... | [SUM] ... | [  5][TX-S] ... (con --bidir: TX-S = bajada, RX-S = subida)
            m = re.search(r'\[\s*(\w+)\](?:\[(\w\w-\w)\])?\s+[\d.]+-[\d.]+\s+sec\s+[\d.]+ \w+\s+([\d.]+) (K|M|G)bits/sec(.*)', l['text'])
            if m and not re.search(r'omitted|sender|receiver', m[5]):
                puntos.append((l['time'], float(m[3]) * {'K': 1e-3, 'M': 1, 'G': 1e3}[m[4]], m[1], m[2]))
    if sentido and any(p[3] for p in puntos):
        puntos = [p for p in puntos if p[3] == {'dl': 'TX-S', 'ul': 'RX-S'}[sentido]]
    if any(p[2] == 'SUM' for p in puntos):  # -P N: solo la suma de los flujos
        puntos = [p for p in puntos if p[2] == 'SUM']
    return sorted((t, v) for t, v, *_ in puntos)


def pings(filas, t0, t1):
    vistos = {}
    for d in filas:
        for clave, p in (d.get('pings') or {}).items():
            for l in p.get('lines', []):
                if t0 - 2 <= l['time'] <= t1 + 12:
                    vistos[(clave, l['seq'])] = (l['time'], l['rtt_ms'])
    return sorted(vistos.values())


def analizar(caso, filas):
    t0, t1 = epoca(caso['dia'], caso['inicio_local']), epoca(caso['dia'], caso['fin_local'])
    ventana = [d for d in filas if t0 - 5 <= d['t'] <= t1 + 5]
    if not ventana:
        print(f"caso {caso['caso']}: sin datos en la ventana")
        return None
    sentido = caso['sentido']
    x = lambda t: t - t0
    ue = [(d['t'], (d.get('radio_ues') or [None])[0]) for d in ventana]
    ue = [(t, u) for t, u in ue if u]
    serie = lambda k, f=1: ([x(t) for t, u in ue if u.get(k) is not None],
                            [u[k] * f for t, u in ue if u.get(k) is not None])
    ip = iperf_por_segundo(filas, t0, t1 + 3, sentido)
    pg = pings(filas, t0, t1)
    # Cambios de C-RNTI: el teléfono volvió a entrar (RLF + reestablecimiento o nuevo acceso).
    cambios, previo = [], None
    for t, u in ue:
        if previo is not None and u['rnti'] != previo:
            cambios.append(x(t))
        previo = u['rnti']

    p = 'dl' if sentido == 'dl' else 'ul'
    paneles = ['tasa', 'rtt', 'cola', 'mcs', 'bler'] + (['sinr', 'phr'] if p == 'ul' else [])
    fig, ejes = plt.subplots(len(paneles), 1, figsize=(8, 1.55 * len(paneles) + .9), sharex=True)
    titulo = f"Caso {caso['caso']} · {caso['descripcion']} · {caso['banda']} {caso['forma_onda']}"
    fig.suptitle(titulo, x=.01, ha='left', fontsize=11, fontweight='bold')
    for eje, panel in zip(ejes, paneles):
        if panel == 'tasa':
            xs, ys = serie(f'{p}_brate', 1e-6)
            eje.plot(xs, ys, color=AZUL, label='gNB (MAC)')
            if ip:
                eje.plot([x(t) for t, _ in ip], [v for _, v in ip], color=NARANJA, label=('iperf3: ofrecido por el servidor' if 'UDP' in caso['descripcion'] and p == 'dl' else 'iperf3 (aplicación)'))
            eje.set_title(f"Tasa de {'bajada' if p == 'dl' else 'subida'} [Mbit/s]")
            eje.legend(loc='lower right', bbox_to_anchor=(1, 1.02), frameon=False, ncol=2, borderaxespad=0)
            eje.set_ylim(bottom=0)
        elif panel == 'rtt':
            ok = [(x(t), r) for t, r in pg if r is not None]
            perdidos = [x(t) for t, r in pg if r is None]
            if ok:
                eje.plot([a for a, _ in ok], [b for _, b in ok], color=VIOLETA, marker='o', ms=3.5)
                eje.set_yscale('log')
            for a in perdidos:
                eje.axvline(a, color=ROJO, lw=1, alpha=.6)
            eje.set_title('RTT del ping al teléfono [ms, escala log]' + (' · rojo = sin respuesta' if perdidos else '')
                          if pg else 'RTT del ping: no se corrió ping en este caso')
        elif panel == 'cola':
            k, nombre = ('dl_bs', 'Cola de bajada en el gNB (dl_bs) [kB]') if p == 'dl' else ('bsr', 'Cola de subida del teléfono (BSR) [kB]')
            xs, ys = serie(k, 1e-3)
            eje.fill_between(xs, ys, color=AQUA, alpha=.35, lw=0)
            eje.plot(xs, ys, color=AQUA)
            eje.set_title(nombre)
            eje.set_ylim(bottom=0)
        elif panel == 'mcs':
            xs, ys = serie(f'{p}_mcs')
            eje.plot(xs, ys, color=AZUL)
            eje.set_title(f"MCS de {'bajada' if p == 'dl' else 'subida'} (índice, tabla 256QAM)")
            eje.set_ylim(0, 28)
        elif panel == 'bler':
            xs, ys = serie(f'{p}_bler')
            eje.plot(xs, ys, color=ROJO)
            eje.set_title(f"BLER de {'bajada' if p == 'dl' else 'subida'} [%]")
            eje.set_ylim(0, 100)
        elif panel == 'sinr':
            xs, ys = serie('sinr')
            eje.plot(xs, ys, color=VIOLETA)
            eje.set_title('SINR del PUSCH [dB]')
        elif panel == 'phr':
            xs, ys = serie('phr')
            eje.plot(xs, ys, color=NARANJA)
            eje.axhline(0, color=TXT2, lw=1, ls='--')
            eje.set_title('Power headroom (PHR) [dB] · ≤ 0: el teléfono está a potencia máxima')
        for c in cambios:
            eje.axvline(c, color=TXT, lw=1.2, ls=':')
    if cambios:
        ejes[0].annotate('cambio de C-RNTI\n(RLF / reacceso)', (cambios[0], ejes[0].get_ylim()[1]),
                         xytext=(4, -4), textcoords='offset points', va='top', fontsize=8, color=TXT2)
    ejes[-1].set_xlabel('Tiempo desde el inicio del caso [s]')
    ejes[-1].set_xlim(-3, t1 - t0 + 5)
    fig.tight_layout(rect=(0, 0, 1, .97))
    salida = os.path.join(AQUI, 'graficas', f"caso{caso['caso']}_{caso['banda']}_{caso['forma_onda'].replace('-', '')}.png")
    fig.savefig(salida, dpi=150)
    plt.close(fig)

    med = lambda k: (lambda v: round(st.median(v), 1) if v else None)([u[k] for _, u in ue if t0 <= _ <= t1 and u.get(k) is not None])
    rtts = [r for _, r in pg if r is not None]
    tasas = [v for t, v in ip if t0 <= t <= t1 + 3]
    return {'caso': caso['caso'], 'banda': caso['banda'], 'forma_onda': caso['forma_onda'], 'sentido': sentido,
            'iperf_media_mbps': round(st.mean(tasas), 2) if tasas else None,
            'iperf_max_mbps': max(tasas) if tasas else None,
            'segundos_en_cero': sum(1 for v in tasas if v == 0),
            'rtt_min_ms': round(min(rtts), 1) if rtts else None,
            'rtt_mediana_ms': round(st.median(rtts), 1) if rtts else None,
            'rtt_max_ms': round(max(rtts), 1) if rtts else None,
            'ping_perdidos': sum(1 for _, r in pg if r is None),
            'mcs_mediana': med(f'{p}_mcs'), 'bler_mediana': med(f'{p}_bler'),
            'sinr_pusch_mediana': med('sinr'), 'phr_mediana': med('phr'),
            'cola_max_kB': (lambda v: round(max(v) / 1e3) if v else None)(
                [u['dl_bs' if p == 'dl' else 'bsr'] for t, u in ue if t0 <= t <= t1 and u.get('dl_bs' if p == 'dl' else 'bsr') is not None]),
            'cambios_rnti': len(cambios), 'grafica': os.path.relpath(salida, AQUI)}


def main():
    casos = list(csv.DictReader(open(os.path.join(AQUI, 'casos.csv'))))
    pedidos = set(sys.argv[1:])
    filas = cargar()
    res = [r for c in casos if not pedidos or c['caso'] in pedidos if (r := analizar(c, filas))]
    if res:
        with open(os.path.join(AQUI, 'resumen.csv'), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(res[0]))
            w.writeheader()
            w.writerows(res)
        for r in res:
            print(r)


if __name__ == '__main__':
    main()
