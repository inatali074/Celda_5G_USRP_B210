"""PUSCH CP-OFDM/DFT-s-OFDM, grilla variable y un puerto; sin acceso a radio."""
import argparse
from bisect import bisect_left
from collections import deque
from functools import lru_cache
import math
import os
import re
import time

import numpy as np

SLOT = re.compile(r'\[\s*(\d{1,4})\.(\d{1,2})\]')
RX = re.compile(r'RX_SYMBOL:\s*sector=(\d+)\s+offset=(\d+)\s+size=(\d+)')
PUSCH = re.compile(r'PUSCH:.*?rnti=(0x[\da-f]+).*?prb=\[(\d+),\s*(\d+)\).*?symb=\[(\d+),\s*(\d+)\).*?mod=([\w-]+)', re.I)


class NoChannel(ValueError):
    pass


def parse_line(line, scs=30, n_sc=None):
    slot = SLOT.search(line)
    if not slot or not ('RX_SYMBOL:' in line or 'PUSCH:' in line):
        return None
    key = tuple(map(int, slot.groups()))
    if not (0 <= key[0] < 1024 and 0 <= key[1] < 10*scs//15):
        raise ValueError('SFN.slot incompatible con la SCS configurada')
    rx = RX.search(line)
    if rx:
        sector, offset, size = map(int, rx.groups())
        if sector != 0 or size <= 0 or size % (14*12) or (n_sc is not None and size != 14*n_sc):
            raise ValueError('Se requiere sector 0, un puerto y size=14×N_sc compatible')
        return key, 'rx', {'offset': offset, 'size': size}
    p = PUSCH.search(line)
    if not p:
        raise ValueError('Formato RX_SYMBOL/PUSCH no reconocido')
    rnti, a, b, c, d, mod = p.groups()
    a, b, c, d = map(int, (a, b, c, d))
    mod = mod.upper().replace('-', '')
    mod = {'QAM16': '16QAM', 'QAM64': '64QAM', 'QAM256': '256QAM'}.get(mod, mod)
    if mod not in ('QPSK', '16QAM', '64QAM', '256QAM') or not (0 <= a < b <= (n_sc//12 if n_sc else 275) and 0 <= c < d <= 14):
        raise ValueError('Modulación o asignación PUSCH incompatible')
    sinr = re.search(r'sinr=([-+\d.]+)dB', line)
    return key, 'pusch', dict(rnti=rnti, prb=(a, b), symb=(c, d), mod=mod,
                             sinr=float(sinr[1]) if sinr else None)


@lru_cache(maxsize=512)
def dmrs(slot, symbol, nid=1, delta=0, n_sc=612):
    # TS 38.211 5.2.1 y 6.4.1.1.1.1; índice desde punto A.
    init = (2**17 * (14*slot+symbol+1)*(2*nid+1)+2*nid) % 2**31
    length = 1600+n_sc
    x1, x2 = np.zeros(length+31, dtype=np.uint8), np.zeros(length+31, dtype=np.uint8)
    x1[0] = 1
    x2[:31] = [(init >> i) & 1 for i in range(31)]
    for n in range(length):
        x1[n+31] = x1[n+3] ^ x1[n]
        x2[n+31] = x2[n+3] ^ x2[n+2] ^ x2[n+1] ^ x2[n]
    bits = (x1[1600:length] ^ x2[1600:length]).astype(float)
    return ((1-2*bits[::2])+1j*(1-2*bits[1::2]))/np.sqrt(2)


@lru_cache(maxsize=512)
def low_papr(length, u):
    # TS 38.211 §5.2.2: v=0, sin hopping ni desplazamiento cíclico.
    if length < 36:
        raise NoChannel('DMRS DFT-s-OFDM M_ZC < 36: tablas cortas no implementadas')
    prime = next(n for n in range(length-1, 1, -1)
                 if all(n % d for d in range(2, math.isqrt(n)+1)))
    q = math.floor(prime*(u+1)/31+.5)
    m = np.arange(length) % prime
    return np.exp(-1j*np.pi*q*m*(m+1)/prime)


def levels(mod):
    m = {'QPSK': 2, '16QAM': 4, '64QAM': 8, '256QAM': 16}[mod]
    return np.arange(1-m, m, 2)/np.sqrt(2*(m*m-1)/3)


def process_grid(grid, slot, p, transform_precoding=False, nid=1):
    if grid.ndim != 2 or grid.shape[0] != 14 or grid.shape[1] % 12 or not np.isfinite(grid).all():
        raise ValueError('IQ no es una grilla complex64 finita de 14×N_sc, sin encabezado')
    start, stop = (12*x for x in p['prb'])
    a, b = p['symb']
    if not (0 <= start < stop <= grid.shape[1] and 0 <= a < b <= 14):
        raise ValueError('Asignación fuera de la grilla IQ')
    energy = np.abs(grid[a:b, start:stop])**2
    even, odd = energy[:, ::2].mean(axis=1), energy[:, 1::2].mean(axis=1)
    detected = [a+i for i in range(b-a) if max(even[i], odd[i]) > 5*min(even[i], odd[i]) and max(even[i], odd[i]) > 1e-15]
    pilots = detected or [l for l in (2, 7, 11) if a <= l < b]
    if not pilots:
        raise NoChannel('Sin símbolos DMRS en la asignación')
    def estimate(nid, ns, delta):
        k = np.arange(start+delta, stop, 2)
        h = np.array([grid[l, k]/(low_papr((stop-start)//2, nid % 30) if transform_precoding else dmrs(ns, l, nid, n_sc=grid.shape[1])[k//2]) for l in pilots])
        den = np.sum(np.abs(h)**2)
        coherence = float(abs(np.sum(h[:, 1:]*h[:, :-1].conj()))/den) if den else 0.
        return coherence, h, k
    convention = (nid % 30 if transform_precoding else nid, slot, 0)
    best = estimate(*convention)
    if best[0] < .5:
        for candidate_id in (range(30) if transform_precoding else dict.fromkeys((nid, 1, 0))):
            for ns in ((slot,) if transform_precoding else (slot, slot+1)):
                for delta in (0, 1):
                    candidate = estimate(candidate_id, ns, delta)
                    if candidate[0] > best[0]:
                        best, convention = candidate, (candidate_id, ns, delta)
    coherence, h, k = best
    if coherence < .5:
        raise NoChannel('Sin canal: coherencia DMRS < 0,5; revisar formato, orden, PCI y precodificación')
    # Suavizado LS local para reducir ruido de pilotos sin borrar fase lineal.
    phase = np.unwrap(np.angle(h), axis=1)
    amp = np.abs(h)
    for values in (phase, amp):
        padded = np.pad(values, ((0, 0), (7, 7)), mode='edge')
        values[:] = sum(padded[:, i:i+values.shape[1]] for i in range(15))/15
    full_k = np.arange(start, stop)
    hf = np.array([np.interp(full_k, k, amp[i])*np.exp(1j*np.interp(full_k, k, phase[i])) for i in range(len(pilots))])
    data_l = [l for l in range(a, b) if l not in pilots]
    if not data_l:
        raise NoChannel('Sin símbolos de datos')
    # Interpolar módulo y fase en tiempo; mantener bordes constantes.
    ht = np.array([np.interp(data_l, pilots, np.abs(hf[:, i])) * np.exp(1j*np.interp(data_l, pilots, np.unwrap(np.angle(hf[:, i])))) for i in range(stop-start)]).T
    if np.min(np.abs(ht)) < 1e-12:
        raise NoChannel('Canal nulo: ZF no definido')
    z = grid[data_l, start:stop]/ht
    if transform_precoding:
        z = np.fft.ifft(z, axis=1, norm='ortho')
    z = z.ravel()
    power = np.mean(np.abs(z)**2)
    if not np.isfinite(power) or power <= 0:
        raise NoChannel('Potencia de datos inválida')
    z /= np.sqrt(power)
    lev = levels(p['mod'])
    ref = lev[np.abs(z.real[:, None]-lev).argmin(axis=1)] + 1j*lev[np.abs(z.imag[:, None]-lev).argmin(axis=1)]
    error, reference = float(np.sum(np.abs(z-ref)**2)), float(np.sum(np.abs(ref)**2))
    ratio = error/reference
    return {**p, 'dmrs_symbols': pilots, 'dmrs_fallback': not bool(detected),
            'dmrs_check': dict(n_id=convention[0], n_slot=convention[1], delta=convention[2], n_scid=0, coherence=coherence, waveform='DFT-s-OFDM' if transform_precoding else 'CP-OFDM', u=convention[0] if transform_precoding else None, v=0 if transform_precoding else None),
            'error': error, 'reference': reference, 'evm_pct': 100*math.sqrt(ratio),
            'snr_db': -10*math.log10(max(ratio, 1e-30)),
            'points': np.round(np.column_stack((z.real, z.imag))[-3000:], 3).tolist()}


def process_slot(path, key, rx, allocations, transform_precoding=False, nid=1, scs=30):
    with open(path, 'rb') as handle:
        size = os.fstat(handle.fileno()).st_size
        if rx['size'] <= 0 or rx['size'] % (14*12) or rx['offset'] < 0 or not 0 <= key[1] < 10*scs//15:
            raise ValueError('Bloque IQ incompatible')
        if (rx['offset']+rx['size'])*8 > size:
            raise ValueError('Bloque IQ incompleto o archivo reiniciado: offset/size exceden archivo')
        grid = np.fromfile(handle, dtype='<c8', count=rx['size'], offset=rx['offset']*8)
    if grid.size != rx['size']:
        raise ValueError('IQ truncado durante la lectura')
    return [process_grid(grid.reshape(14, rx['size']//14), key[1], p, transform_precoding, nid) for p in allocations]


class Monitor:
    def __init__(self, path='/logs/gnb/gnb_rx_symbols.bin'):
        self.scs, self.n_sc = 30, None
        self.path = path
        self.reset()

    def reset(self):
        self.pending, self.ul = {}, {}
        self.stats = dict(procesados=0, descartados_por_tasa=0, sin_canal=0, ultimo_error=None)
        self.identity = None
        self.size = 0
        self.prefix = b''
        self.grew = 0
        self.last_job = -math.inf
        self.generation = getattr(self, 'generation', 0)+1

    def feed(self, line, stamp=None):
        parsed = parse_line(line, self.scs, self.n_sc)
        if parsed:
            key, kind, value = parsed
            entry = self.pending.setdefault(key, dict(at=time.monotonic(), rx=None, pusch=[]))
            if kind == 'rx':
                entry['rx'] = value
            else:
                value['time'] = stamp if stamp is not None else time.time()
                if value not in entry['pusch']:
                    entry['pusch'].append(value)
            if len(self.pending) > 4096:
                self.pending.pop(next(iter(self.pending)))

    def poll(self):
        stat = os.stat(self.path)
        identity = (stat.st_dev, stat.st_ino)
        with open(self.path, 'rb') as handle:
            prefix = handle.read(128)
        if self.identity is not None and (identity != self.identity or stat.st_size < self.size or (self.prefix and not prefix.startswith(self.prefix))):
            self.reset()
        self.identity = identity
        self.prefix = prefix
        if stat.st_size > self.size:
            self.grew = time.monotonic()
        self.size = stat.st_size
        now = time.monotonic()
        jobs = []
        for key, entry in list(self.pending.items()):
            if now-entry['at'] < 2:
                continue
            del self.pending[key]
            if not entry['rx'] or not entry['pusch']:
                continue
            if (entry['rx']['offset']+entry['rx']['size'])*8 > self.size:
                self.reset()
                raise ValueError('IQ reiniciado o incompleto: offset excede tamaño; estado limpiado')
            if now-self.last_job < .25:
                self.stats['descartados_por_tasa'] += 1
                continue
            self.last_job = now
            jobs.append((key, entry['rx'], entry['pusch']))
        return jobs

    def accept(self, results):
        self.stats['procesados'] += 1
        grouped = {}
        for result in results:
            grouped.setdefault(result['mod'], []).append(result)
        for mod, group in grouped.items():
            entry = self.ul.setdefault(mod, dict(points=deque(maxlen=3000), powers=deque(maxlen=50)))
            for result in group:
                entry['points'].extend(result['points'])
            entry['powers'].append((sum(r['error'] for r in group), sum(r['reference'] for r in group)))
            entry['dmrs_check'] = group[-1]['dmrs_check']
            entry['updated'] = time.monotonic()

    def snapshot(self):
        try:
            stat = os.stat(self.path)
            exists = (stat.st_dev, stat.st_ino) == self.identity and stat.st_size >= self.size
        except OSError:
            exists = False
        fresh = exists and time.monotonic()-self.grew < 5 and bool(self.ul)
        ul = {}
        if fresh:
            for mod, entry in self.ul.items():
                if time.monotonic()-entry['updated'] >= 5:
                    continue
                ratio = sum(e for e, r in entry['powers'])/sum(r for e, r in entry['powers'])
                ul[mod] = dict(points=list(entry['points']), evm_pct=100*math.sqrt(ratio),
                               snr_db=-10*math.log10(max(ratio, 1e-30)), n_slots=len(entry['powers']), dmrs_check=entry['dmrs_check'])
        return dict(source='phy_rx_symbols' if fresh else None, ul=ul, stats=dict(self.stats))


def probar():
    rng = np.random.default_rng(20261105)
    expected = 100*10**(-25/20)
    for n_sc, band in ((612, 'n78'), (1272, 'n3')):
        for transform in (False, True):
            grid = np.zeros((14, n_sc), complex)
            # Asignación hasta el borde: ejercita Gold más allá de 612 bits en n3.
            first, last = n_sc//12-24, n_sc//12
            start, stop = first*12, last*12
            p = dict(rnti='0x4601', prb=(first, last), symb=(0, 14), mod='16QAM', sinr=25.)
            lev = levels(p['mod'])
            qam = rng.choice(lev, (14, 288))+1j*rng.choice(lev, (14, 288))
            grid[:, start:stop] = np.fft.fft(qam, axis=1, norm='ortho') if transform else qam
            for l in (2, 7, 11):
                grid[l, start:stop] = 0
                grid[l, start:stop:2] = low_papr(144, 1) if transform else dmrs(7, l, n_sc=n_sc)[start//2:stop//2]
            channel = np.exp(1j*(.3+.003*np.arange(n_sc)))
            grid *= channel
            grid += (rng.normal(size=grid.shape)+1j*rng.normal(size=grid.shape))*np.sqrt(10**(-25/10)/2)
            result = process_grid(grid, 7, p, transform)
            assert abs(result['evm_pct']-expected) <= .5, result['evm_pct']
            assert result['dmrs_symbols'] == [2, 7, 11]
            print(f"OK: {band} {'DFT-s-OFDM' if transform else 'CP-OFDM'} N_sc={n_sc} EVM={result['evm_pct']:.2f}% (esperado {expected:.2f}% ±0,5 pp)")
            if transform:
                for l in (2, 7, 11):
                    grid[l, start:stop] = 0
                    grid[l, start+1:stop:2] = low_papr(144, 17)*channel[start+1:stop:2]
                check = process_grid(grid, 7, p, True)['dmrs_check']
                assert check['u'] == 17 and check['delta'] == 1, check
    for scs, n_sc in ((15, 1272), (30, 612)):
        assert parse_line(f'[0.0] RX_SYMBOL: sector=0 offset=0 size={14*n_sc}', scs, n_sc)
        try:
            parse_line(f'[0.{10*scs//15}] RX_SYMBOL: sector=0 offset=0 size={14*n_sc}', scs, n_sc)
        except ValueError:
            pass
        else:
            raise AssertionError('Se aceptó slot fuera de trama')
    print('OK: búsqueda u=17/delta=1 y validación de grillas/slots')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bin')
    parser.add_argument('--log')
    parser.add_argument('--max', type=int, default=20)
    parser.add_argument('--scs', type=int, choices=(15, 30), default=30)
    parser.add_argument('--nid', type=int, default=1)
    parser.add_argument('--dfts', action='store_true')
    parser.add_argument('--probar', action='store_true')
    args = parser.parse_args()
    if args.probar:
        probar()
        return
    if not args.bin or not args.log or args.max < 1:
        parser.error('Usá --bin y --log, --max positivo; o --probar')
    # Dos pasadas: la cercanía en el log distingue vueltas del SFN.
    selected, occurrences = [], {}
    with open(args.log) as log:
        for index, line in enumerate(log):
            parsed = parse_line(line, args.scs)
            if parsed and parsed[1] == 'rx':
                key, _, rx = parsed
                chosen = len(selected) if len(selected) < args.max else None
                if chosen is not None:
                    selected.append((key, dict(rx=rx, pusch=[])))
                if chosen is not None or key in occurrences:
                    occurrences.setdefault(key, []).append((index, chosen))
    with open(args.log) as log:
        for index, line in enumerate(log):
            parsed = parse_line(line, args.scs)
            if parsed and parsed[0] in occurrences and parsed[1] == 'pusch':
                anchors = occurrences[parsed[0]]
                pos = bisect_left(anchors, (index, -1))
                candidates = anchors[max(0, pos-1):pos+1]
                _, chosen = min(candidates, key=lambda item: abs(item[0]-index))
                if chosen is not None:
                    selected[chosen][1]['pusch'].append(parsed[2])
    for key, entry in selected:
        try:
            for r in process_slot(args.bin, key, entry['rx'], entry['pusch'], args.dfts, args.nid, args.scs):
                print(f"{key[0]}.{key[1]} {r['rnti']} {r['mod']} PRB={r['prb']} DMRS={r['dmrs_symbols']} respaldo={r['dmrs_fallback']} {r['dmrs_check']} EVM={r['evm_pct']:.2f}% sinr_log={r['sinr']}dB")
        except (OSError, ValueError) as exc:
            print(f'{key[0]}.{key[1]} ERROR: {exc}')


if __name__ == '__main__':
    main()
