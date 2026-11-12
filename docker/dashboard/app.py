"""Monitoreo pasivo y herramientas de diagnóstico; nunca controla el gNB."""
import asyncio
from collections import Counter, deque
from contextlib import asynccontextmanager
import ipaddress
import json
import math
import os
from datetime import datetime
from pathlib import Path
import re
import time
import uuid

from fastapi import FastAPI, HTTPException, Request, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import websockets
import yaml

from iq import Monitor, NoChannel, process_slot

# Único lugar para ajustar nombres. No se suponen unidades para aliases ambiguos.
FIELDS = {
    'rnti': ('rnti', 'c_rnti', 'crnti'), 'imsi': ('imsi', 'supi'),
    'cqi': ('cqi', 'wideband_cqi'), 'ri': ('ri', 'rank_indicator'),
    'dl_mcs': ('dl_mcs', 'mcs_dl'), 'ul_mcs': ('ul_mcs', 'mcs_ul'),
    'sinr': ('pusch_snr_db', 'pusch_sinr_db', 'ul_sinr_db', 'snr_db'),
    'dl_brate': ('dl_brate', 'dl_bitrate', 'dl_bit_rate'),
    'ul_brate': ('ul_brate', 'ul_bitrate', 'ul_bit_rate'),
    'dl_ok': ('dl_nof_ok', 'dl_ok'), 'dl_nok': ('dl_nof_nok', 'dl_nok'),
    'ul_ok': ('ul_nof_ok', 'ul_ok'), 'ul_nok': ('ul_nof_nok', 'ul_nok'),
    'bsr': ('bsr', 'buffer_status'), 'ta': ('ta', 'timing_advance'),
    'phr': ('last_phr', 'phr', 'power_headroom'),
    **{k: (k,) for k in ('pusch_rsrp_db', 'pucch_snr_db', 'ta_ns', 'pusch_ta_ns', 'pucch_ta_ns', 'dl_ri', 'ul_ri', 'dl_bs')},
}
UE_NAMES = {'001010000000003': 'SIM 3', '001010000000004': 'SIM 4', '001010000000001': 'srsUE (sim)'}
evm_history = {}
dl_history = {}
START = time.monotonic()
START_WALL = time.time()
state = {'gnb_connected': False, 'metrics_at': None, 'raw': None, 'radio_ues': [],
         'config': None, 'errors': {}, 'ogstun': {}, 'host': {}, 'rt': {},
         'radio_at': None, 'alarm': False, 'busy_threshold': 10, 'gnb_since': None}
iq_monitor = Monitor()
metrics_history = deque(maxlen=30)
events = deque(maxlen=150)
history = deque(maxlen=180)
subscribers = {}  # IMSI -> estado observado en el núcleo, sin unión especulativa con RNTI.
pings = {}
iperf = {'server': False, 'client': False, 'results': deque(maxlen=10)}
processes = {}
tasks = set()
rt = Counter()
rt_total = Counter()
rt_window = deque(maxlen=60)
log_buffers = {s: deque(maxlen=400) for s in ('gnb', 'core')}
creations = deque(maxlen=256)
registrations = deque(maxlen=256)
associations = {}
# Unión determinística: índice de UE del CU-CP (gNB) = RAN_UE_NGAP_ID del AMF.
ue_indexes = deque(maxlen=256)   # (stamp, índice, rnti)
ngap_ids = deque(maxlen=256)     # (stamp, RAN_UE_NGAP_ID, imsi)
last_suci = [None, None]         # (stamp, imsi) del último SUCI sin cifrar
nf_seen = {}
ANSI = re.compile(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))')


def private_text(text):
    return re.sub(r'(?<!\d)\d{14,15}(?!\d)',
                  lambda m: m[0] if m[0].startswith('00101') else '****'+m[0][-4:], text)


def log_time(line):
    m = re.search(r'\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d(?:[.,]\d+)?', line)
    if m:
        try:
            return datetime.fromisoformat(m[0].replace(',', '.')).timestamp()
        except ValueError:
            pass
    m = re.search(r'(\d\d/\d\d) (\d\d:\d\d:\d\d(?:[.,]\d+)?)', line)
    if m:
        try:
            now = datetime.now()
            dt = datetime.strptime(f'{now.year}/{m[1]} {m[2]}'.replace(',', '.'), '%Y/%m/%d %H:%M:%S.%f' if '.' in m[2] or ',' in m[2] else '%Y/%m/%d %H:%M:%S')
            return dt.timestamp()
        except ValueError:
            pass
    return None


def associate():
    # Recalcular por timestamp: el orden de lectura de ambos archivos no importa.
    associations.clear()
    used = set()
    # 1) Por índice: el gNB escribe 'ue=N c-rnti=X: UE created' y el AMF 'RAN_UE_NGAP_ID[N]'
    #    tras el SUCI del InitialUEMessage. Sirve también para Service Request (sin registro nuevo).
    for stamp, idx, imsi in sorted(ngap_ids):
        candidates = [(abs(stamp-t), t, r) for t, i, r in ue_indexes if i == idx and abs(stamp-t) <= 5 and (t, r) not in used]
        if candidates:
            _, t, r = min(candidates)
            used.add((t, r))
            associations[r] = (imsi, t)
    # 2) Respaldo por tiempo de 'Registration complete'.
    for stamp, imsi in sorted(registrations):
        candidates = [(t, r) for t, r in creations if 0 <= stamp-t <= 5 and (t, r) not in used]
        if candidates:
            t, r = max(candidates)
            used.add((t, r))
            if r not in associations:
                associations[r] = (imsi, t)
    # Una creación posterior del mismo RNTI invalida la unión anterior.
    for t, r in creations:
        if r in associations and t > associations[r][1]:
            del associations[r]



def event(source, text):
    events.append({'time': time.time(), 'source': source, 'text': private_text(text[:1000])})


def number(value):
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (ValueError, TypeError):
        return None


def radio_rnti(value):
    try:
        return int(value, 16) if isinstance(value, str) and value.startswith('0x') else int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def prune_evm(now):
    for history_by_rnti in (evm_history, dl_history):
        for rnti in list(history_by_rnti):
            if now-history_by_rnti[rnti][-1]['time'] > 30:
                del history_by_rnti[rnti]


def extract(payload):
    """Busca registros identificables recursivamente, incluso dentro de listas desconocidas."""
    rows = {}
    def visit(node):
        if isinstance(node, dict):
            normalized = {re.sub(r'[^a-z0-9]', '', k.lower()): v for k, v in node.items()}
            row = {}
            for field, aliases in FIELDS.items():
                for alias in aliases:
                    key = re.sub(r'[^a-z0-9]', '', alias)
                    if key in normalized and not isinstance(normalized[key], (dict, list)):
                        row[field] = normalized[key]
                        break
            if 'rnti' in row:
                for direction in ('dl', 'ul'):
                    ok, nok = number(row.get(direction+'_ok')), number(row.get(direction+'_nok'))
                    row[direction+'_bler'] = 100*nok/(ok+nok) if ok is not None and nok is not None and ok+nok > 0 else None
                rows[str(row['rnti'])] = row
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)
    visit(payload)
    return list(rows.values())


async def metrics():
    while True:
        try:
            async with websockets.connect('ws://10.53.1.3:8001', open_timeout=4, max_size=2**20) as ws:
                state['gnb_connected'] = True
                await ws.send(json.dumps({'cmd': 'metrics_subscribe'}))
                async for message in ws:
                    try:
                        payload = json.loads(message)
                        state['raw'] = payload
                        state['metrics_at'] = time.time()
                        metrics_history.append({'time': time.time(), 'message': payload})
                        cells = payload.get('cells', []) if isinstance(payload, dict) else []
                        if any(isinstance(c, dict) and 'ue_list' in c for c in cells):
                            state['radio_ues'] = extract([c.get('ue_list', []) for c in cells])
                            state['radio_at'] = time.time()
                            prune_evm(state['radio_at'])
                            for row in state['radio_ues']:
                                rnti = radio_rnti(row.get('rnti'))
                                if rnti is not None:
                                    dl_history.setdefault(rnti, deque(maxlen=120)).append({
                                        'time': state['radio_at'],
                                        **{k: number(row.get(k)) for k in ('cqi', 'dl_mcs', 'dl_bler')},
                                        'dl_mbps': number(row.get('dl_brate'))/1e6 if number(row.get('dl_brate')) is not None else None})
                        for cell in cells:
                            for item in cell.get('event_list', []):
                                event('metrics', private_text(json.dumps(item, ensure_ascii=False)))
                            if 'cell_metrics' in cell:
                                state['cell_metrics'] = cell['cell_metrics']
                        state['errors'].pop('metrics', None)
                    except (ValueError, TypeError) as exc:
                        state['errors']['metrics'] = str(exc)
        except Exception as exc:
            state['errors']['metrics'] = str(exc)[:300]
        finally:
            state['gnb_connected'] = False
        await asyncio.sleep(3)


def log_line(source, line, replay=False):
    line = ANSI.sub('', line)
    log_buffers[source].append(private_text(line[:16384]))
    stamp = log_time(line)
    if source == 'gnb':
        if not replay:
            try:
                iq_monitor.scs = int(state.get('cell', {}).get('scs') or 30)
                prb = state.get('cell', {}).get('prb')
                iq_monitor.n_sc = int(prb)*12 if prb else None
                iq_monitor.feed(line, stamp)
            except Exception as exc:
                iq_error(exc)
        created = re.search(r'(?:ue=(\d+) )?c-rnti=(0x[0-9a-f]+): UE created', line, re.I)
        if created and stamp is not None:
            creations.append((stamp, int(created[2], 16)))
            if created[1] is not None:
                ue_indexes.append((stamp, int(created[1]), int(created[2], 16)))
            associate()
        kind = next((k for k, pattern in (
            ('ul_busy', r'UL processor is busy'), ('underflow', 'underflow'),
            ('overflow', 'overflow'), ('late', r'\blate\b'),
            ('other', 'Real-time failure')) if re.search(pattern, line, re.I)), None)
        if kind and not replay:
            rt[kind] += 1
            rt['total'] += 1
            rt_total[kind] += 1
            rt_total['total'] += 1
        if re.search(r'UE created|RLF detected|rrcRelease|PRACH.*detect|detect.*PRACH', line, re.I):
            event(source, line)
        if 'gNB started' in line:
            state['gnb_since'] = stamp
        match = re.search(r'(?:config(?:uration)?[^\n]*?)([\w./-]+\.yml)', line, re.I)
        if match:
            state['config'] = match[1]
    else:
        nf = re.search(r'\[(amf|smf|upf|ausf|udm|udr|pcf|nssf|bsf|nrf|scp)\]', line, re.I)
        if nf:
            nf_seen[nf[1].upper()] = stamp if stamp is not None else (0 if replay else time.time())
        # SUCI con esquema nulo (suci-0-MCC-MNC-rutina-0-clave-MSIN): el IMSI es MCC+MNC+MSIN.
        suci = re.search(r'suci-0-(\d{3})-(\d{2,3})-\d+-0-\d+-(\d+)', line)
        if suci and stamp is not None:
            last_suci[:] = [stamp, suci[1]+suci[2]+suci[3]]
        ngap = re.search(r'RAN_UE_NGAP_ID\[(\d+)\].*TAC\[', line)
        if ngap and stamp is not None and last_suci[0] is not None and 0 <= stamp-last_suci[0] <= 1:
            ngap_ids.append((stamp, int(ngap[1]), last_suci[1]))
            associate()
        match = re.search(r'UE SUPI\[(?:imsi-)?(\d+)\].*DNN\[([^]]+)\].*IPv4\[([\d.]+)\]', line)
        imsi_match = re.search(r'(?:imsi-|IMSI[\s\[:=]*|SUPI\[|\[)(\d{14,15})(?!\d)', line, re.I)
        imsi = match[1] if match else imsi_match[1] if imsi_match else None
        if imsi:
            if imsi not in subscribers and len(subscribers) >= 128:
                subscribers.pop(next(iter(subscribers)))
            ue = subscribers.setdefault(imsi, {'imsi': imsi, 'ip': None, 'since': None, 'connected': False})
            if match:
                ue.update(ip=match[3], dnn=match[2])
            if 'Registration complete' in line and stamp is not None:
                registrations.append((stamp, imsi))
                associate()
            if match:
                ue['pdu'] = True
            if re.search(r'Session.*(?:Release|removed)|PDU.*Release', line, re.I):
                ue['pdu'] = False
            if 'Registration complete' in line or match:
                if not ue['connected']:
                    ue['since'] = stamp if stamp is not None else (None if replay else time.time())
                ue['connected'] = True
            if 'Deregistration' in line:
                ue['connected'] = False
                ue['pdu'] = False
                ue['seconds'] = time.time()-ue['since'] if ue['since'] else None
        if re.search(r'Registration complete|UE SUPI\[|Paging failed|Ue requested DNN.*Not Supported|Deregistration', line, re.I):
            event(source, line)


ASSOC_MARKS = {'gnb': (b': UE created',), 'core': (b'suci-', b'RAN_UE_NGAP_ID', b'Registration complete')}


def prescan(source, path, limit):
    """Busca en todo el log, hasta `limit`, solo las líneas que unen RNTI e IMSI.

    El arranque relee solo los últimos 256 KB; con el volcado IQ el log del gNB pesa cientos
    de MB y sin esto se pierden las asociaciones de los UE ya conectados al reiniciar el panel.
    """
    marks, found, rest = ASSOC_MARKS[source], [], b''
    with path.open('rb') as handle:
        while handle.tell() < limit:
            block = rest + handle.read(min(4*1024*1024, limit-handle.tell()))
            if not block:
                break
            lines = block.split(b'\n')
            rest = lines.pop()[-16384:]
            found += [line.decode(errors='replace') for line in lines if any(m in line for m in marks)]
            time.sleep(.005)  # ceder CPU al gNB en PCs chicas
    return found[-2048:]


def assoc_line(source, line):
    """Versión mínima de log_line: solo actualiza los datos de asociación, sin eventos."""
    stamp = log_time(line)
    if stamp is None:
        return
    if source == 'gnb':
        created = re.search(r'(?:ue=(\d+) )?c-rnti=(0x[0-9a-f]+): UE created', line, re.I)
        if created:
            creations.append((stamp, int(created[2], 16)))
            if created[1] is not None:
                ue_indexes.append((stamp, int(created[1]), int(created[2], 16)))
        return
    suci = re.search(r'suci-0-(\d{3})-(\d{2,3})-\d+-0-\d+-(\d+)', line)
    if suci:
        last_suci[:] = [stamp, suci[1]+suci[2]+suci[3]]
    ngap = re.search(r'RAN_UE_NGAP_ID\[(\d+)\].*TAC\[', line)
    if ngap and last_suci[0] is not None and 0 <= stamp-last_suci[0] <= 1:
        ngap_ids.append((stamp, int(ngap[1]), last_suci[1]))
    imsi = re.search(r'imsi-(\d{14,15})', line)
    if 'Registration complete' in line and imsi:
        registrations.append((stamp, imsi[1]))


async def tail(source, path):
    """Lectura acotada por vuelta; detecta inode, tamaño y prefijo tras truncado rápido."""
    handle = None
    identity = None
    prefix = b''
    pending = b''
    first = True
    history = []
    try:
        while True:
            try:
                stat = path.stat()
                with path.open('rb') as probe:
                    head = probe.read(128)
                reset = handle is None or identity != (stat.st_dev, stat.st_ino) or stat.st_size < handle.tell() or (prefix and head[:len(prefix)] != prefix)
                if reset:
                    if handle:
                        handle.close()
                        event(source, 'Log truncado o rotado; comienza una nueva lectura.')
                    handle = path.open('rb')
                    identity = (stat.st_dev, stat.st_ino)
                    pending = b''
                    # Bootstrap acotado; no contabiliza fallas históricas como nuevas.
                    replay = first
                    if first and stat.st_size > 256*1024:
                        start = stat.st_size-256*1024
                        try:
                            history = await asyncio.to_thread(prescan, source, path, start)
                        except OSError:
                            history = []
                        handle.seek(start)
                        handle.readline()  # descartar primera línea incompleta
                    first = False
                    log_buffers[source].clear()
                    if source == 'gnb':
                        iq_monitor.reset()
                        creations.clear()
                        ue_indexes.clear()
                        associations.clear()
                        state['gnb_since'] = None
                        state['config'] = None
                    else:
                        registrations.clear()
                        ngap_ids.clear()
                        last_suci[:] = [None, None]
                        associations.clear()
                        nf_seen.clear()
                        for ue in subscribers.values():
                            ue['connected'] = False
                            ue['pdu'] = False
                    for old in (history if replay else ()):
                        assoc_line(source, old)
                    history = []
                    associate()
                prefix = head
                chunk = handle.read(256*1024)
                pending += chunk
                lines = pending.split(b'\n')
                pending = lines.pop()[-16384:]
                for line in lines:
                    log_line(source, line.decode(errors='replace'), replay=replay)
                replay = False
                state['errors'].pop(source+'_log', None)
            except (OSError, ValueError) as exc:
                state['errors'][source+'_log'] = str(exc)[:300]
            await asyncio.sleep(.2)
    finally:
        if handle:
            handle.close()


def iq_error(exc):
    message = str(exc)[:300]
    state['errors']['iq'] = message
    iq_monitor.stats['ultimo_error'] = message


async def iq_worker():
    while True:
        try:
            jobs = iq_monitor.poll()
            for key, rx, allocations in jobs:
                generation = iq_monitor.generation
                try:
                    cell = state.get('cell', {})
                    results = await asyncio.to_thread(process_slot, iq_monitor.path, key, rx, allocations,
                                                    cell.get('waveform') == 'DFT-s-OFDM',
                                                    int(cell.get('pci') or 0), int(cell.get('scs') or 30))
                    if generation == iq_monitor.generation:
                        iq_monitor.accept(results)
                        prune_evm(time.time())
                        grouped = {}
                        for result in results:
                            rnti = radio_rnti(result.get('rnti'))
                            if rnti is not None:
                                grouped.setdefault(rnti, []).append(result)
                        for rnti, group in grouped.items():
                            ratio = sum(r['error'] for r in group)/sum(r['reference'] for r in group)
                            evm_history.setdefault(rnti, deque(maxlen=120)).append({
                                'time': max(r['time'] for r in group),
                                'evm_pct': 100*math.sqrt(ratio), 'sinr_db': None, 'ul_mcs': None})
                        state['errors'].pop('iq', None)
                except NoChannel as exc:
                    if generation == iq_monitor.generation:
                        iq_monitor.stats['sin_canal'] += 1
                        iq_error(exc)
        except Exception as exc:
            if isinstance(exc, FileNotFoundError):
                iq_monitor.reset()
            iq_error(exc)
        await asyncio.sleep(.05)


async def sample():
    previous = None
    cpu_prev = None
    while True:
        now = time.monotonic()
        try:
            counters = {k: int(Path('/sys/class/net/ogstun/statistics', k).read_text()) for k in ('rx_bytes', 'tx_bytes', 'rx_packets', 'tx_packets')}
            rates = {}
            if previous:
                dt = now-previous[0]
                rates = {k+'_per_s': max(0, v-previous[1][k])/dt for k, v in counters.items()}
            state['ogstun'] = {**counters, **rates}
            previous = now, counters
            state['errors'].pop('ogstun', None)
        except OSError as exc:
            state['ogstun'] = {}
            previous = None
            state['errors']['ogstun'] = str(exc)
        try:
            # guest/guest_nice ya están incluidos en user/nice.
            values = list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:9]))
            total, idle = sum(values), values[3]+values[4]
            usage = None
            if cpu_prev and total > cpu_prev[0]:
                usage = 100*(1-(idle-cpu_prev[1])/(total-cpu_prev[0]))
            cpu_prev = total, idle
            state['host'] = {'cpu_percent': usage, 'load': Path('/proc/loadavg').read_text().split()[:3]}
        except (OSError, ValueError, IndexError) as exc:
            state['errors']['host'] = str(exc)
        if not state['gnb_connected'] or not state['radio_at'] or time.time()-state['radio_at'] > 5:
            state['radio_ues'] = []
        state['host'].update(host_details())
        state['cell'] = read_cell()
        prune_evm(time.time())
        rt_window.append(dict(rt))
        state['rt'] = dict(rt)
        state['alarm'] = rt['ul_busy'] > state['busy_threshold']
        rt.clear()
        history.append({'time': time.time(), 'ogstun': dict(state['ogstun']), 'ues': state['radio_ues'], 'rt': state['rt']})
        await asyncio.sleep(1)


def destination(value):
    try:
        return str(ipaddress.IPv4Address(value))
    except ValueError:
        if len(value) <= 253 and re.fullmatch(r'(?=.{1,253}$)[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*', value) and not re.fullmatch(r'[\d.]+', value):
            return value
    raise HTTPException(422, 'Destino inválido: usá IPv4 o nombre de host sin opciones.')


class PingRequest(BaseModel):
    target: str = Field(max_length=253)
    interval: float = Field(default=1, ge=.2, le=2, allow_inf_nan=False)
    duration: int = Field(default=30, ge=1, le=600)


class IperfRequest(BaseModel):
    target: str = Field(max_length=253)
    duration: int = Field(default=10, ge=1, le=60)
    reverse: bool = False
    udp: bool = False
    bandwidth_mbps: int = Field(default=10, ge=1, le=100)


async def terminate(proc):
    if proc and proc.returncode is None:
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), 3)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
        except ProcessLookupError:
            pass


def launch(coro):
    task = asyncio.create_task(coro)
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return task


async def run_ping(key, request):
    item = pings[key]
    proc = None
    last = None
    jitter_sum = 0
    pairs = 0
    rtt_sum = 0
    try:
        proc = await asyncio.create_subprocess_exec('ping', '-n', '-O', '-i', str(request.interval), '-w', str(request.duration), '-W', '2', '--', request.target, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, env={'LC_ALL': 'C', 'PATH': '/usr/bin:/bin'})
        processes[key] = proc
        async with asyncio.timeout(request.duration+8):
            async for raw in proc.stdout:
                line = raw.decode(errors='replace').strip()
                item['last_line'] = line[:500]
                seq = re.search(r'icmp_seq[= ](\d+)', line)
                if seq:
                    item['sent'] = max(item['sent'], int(seq[1]))
                    # -O informa cada paquete sin respuesta: una línea por paquete, como en la consola.
                    if line.startswith('no answer yet'):
                        item['lines'].append({'time': time.time(), 'seq': int(seq[1]), 'rtt_ms': None})
                match = re.search(r'time[=<]([\d.]+)', line)
                if match and 'DUP!' not in line:
                    value = float(match[1])
                    item['received'] += 1
                    item['rtt_ms'] = value
                    rtt_sum += value
                    item['rtt_avg_ms'] = rtt_sum/item['received']
                    if seq:
                        item['lines'].append({'time': time.time(), 'seq': int(seq[1]), 'rtt_ms': value})
                    item['samples'].append({'time': time.time(), 'rtt_ms': value})
                    if last is not None:
                        jitter_sum += abs(value-last)
                        pairs += 1
                    last = value
                    item['jitter_ms'] = jitter_sum/pairs if pairs else 0
                summary = re.search(r'(\d+) packets transmitted, (\d+) received', line)
                if summary:
                    item['sent'], item['received'] = map(int, summary.groups())
                item['loss_percent'] = 100*(1-item['received']/item['sent']) if item['sent'] else None
            await proc.wait()
            item['exit_code'] = proc.returncode
            # ping -w corta sin informar el último paquete perdido: completar cada seq enviado.
            vistos = {l['seq'] for l in item['lines']}
            for faltante in range(1, item['sent']+1):
                if faltante not in vistos:
                    item['lines'].append({'time': time.time(), 'seq': faltante, 'rtt_ms': None})
    except Exception as exc:
        item['error'] = str(exc)
    finally:
        await terminate(proc)
        processes.pop(key, None)
        item['running'] = False


async def run_iperf(server, args):
    key = 'server' if server else 'client'
    proc = None
    try:
        while True:
            # --one-off permite un documento JSON completo por prueba y reinicia el servidor.
            proc = await asyncio.create_subprocess_exec('iperf3', *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            processes[key] = proc
            out, err = await asyncio.wait_for(proc.communicate(), None if server else 75)
            try:
                result = json.loads(out)
            except ValueError:
                result = {'error': (out+err).decode(errors='replace')[:2000]}
            iperf['results'].append({'time': time.time(), 'mode': key, 'result': result})
            if not server or proc.returncode != 0:
                break
            await asyncio.sleep(.1)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        iperf['results'].append({'time': time.time(), 'mode': key, 'result': {'error': str(exc)}})
    finally:
        await terminate(proc)
        processes.pop(key, None)
        iperf[key] = False


@asynccontextmanager
async def lifespan(app):
    background = [launch(iq_worker()), launch(metrics()), launch(tail('gnb', Path('/logs/gnb/gnb.log'))),
                  launch(tail('core', Path('/logs/core/core.log'))), launch(sample())]
    yield
    for task in list(tasks):
        task.cancel()
    await asyncio.gather(*list(tasks), return_exceptions=True)
    await asyncio.gather(*(terminate(p) for p in list(processes.values())))


app = FastAPI(lifespan=lifespan)


@app.middleware('http')
async def local_ui(request: Request, call_next):
    # Sin credenciales: las acciones sólo se aceptan del origen de la propia página.
    if request.method not in ('GET', 'HEAD'):
        origin = request.headers.get('origin')
        if origin != 'http://'+request.headers.get('host', ''):
            return JSONResponse({'detail': 'Origen no permitido'}, status_code=403)
    return await call_next(request)


@app.get('/')
async def index():
    return FileResponse(Path(__file__).with_name('index.html'))


@app.get('/evm')
async def evm_page():
    return FileResponse(Path(__file__).with_name('evm.html'))


def snapshot():
    now = time.time()
    return {**state, 'uptime': time.monotonic()-START, 'events': list(events), 'history': list(history),
            'metrics_history': list(metrics_history),
            'core_ues': [{**u, 'seconds': now-u['since'] if u['connected'] and u['since'] else u.get('seconds')} for u in subscribers.values()],
            'pings': {k: {**v, 'samples': list(v['samples']), 'lines': list(v.get('lines', []))} for k, v in pings.items()},
            'iperf': {**iperf, 'results': list(iperf['results'])}}


@app.get('/api/state')
async def get_state():
    return snapshot()


@app.post('/api/ping')
async def ping_start(request: PingRequest):
    request.target = destination(request.target)
    if sum(p['running'] for p in pings.values()) >= 3:
        raise HTTPException(409, 'Máximo de tres pings simultáneos.')
    for key in list(pings):
        if len(pings) >= 12 and not pings[key]['running']:
            del pings[key]
            ping_tasks.pop(key, None)
    key = uuid.uuid4().hex[:12]
    pings[key] = {'target': request.target, 'running': True, 'sent': 0, 'received': 0,
                  'samples': deque(maxlen=180), 'lines': deque(maxlen=200), 'loss_percent': None}
    ping_tasks[key] = launch(run_ping(key, request))
    return {'id': key}


ping_tasks = {}


@app.delete('/api/ping/{key}')
async def ping_stop(key: str):
    task = ping_tasks.get(key)
    if task and not task.done():
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    if key in pings:
        pings[key]['running'] = False
    return {'ok': True}


iperf_tasks = {}


@app.post('/api/iperf/server')
async def iperf_server():
    if iperf['server']:
        raise HTTPException(409, 'El servidor ya está activo.')
    iperf['server'] = True
    iperf_tasks['server'] = launch(run_iperf(True, ['-s', '-B', '10.45.0.1', '-p', '5201', '-1', '-J']))
    return {'ok': True}


@app.post('/api/iperf/client')
async def iperf_client(request: IperfRequest):
    target = destination(request.target)
    if iperf['client']:
        raise HTTPException(409, 'Ya hay una prueba cliente en curso.')
    args = ['-c', target, '-t', str(request.duration), '-i', '1', '-J', '--connect-timeout', '5000']
    if request.reverse:
        args += ['-R']
    if request.udp:
        args += ['-u', '-b', str(request.bandwidth_mbps)+'M']
    iperf['client'] = True
    iperf_tasks['client'] = launch(run_iperf(False, args))
    return {'ok': True}


@app.delete('/api/iperf/{mode}')
async def iperf_stop(mode: str):
    if mode not in ('server', 'client'):
        raise HTTPException(404, 'Modo desconocido.')
    task = iperf_tasks.get(mode)
    if task and not task.done():
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    iperf[mode] = False
    return {'ok': True}


@app.websocket('/ws')
async def browser(ws: WebSocket):
    if ws.headers.get('origin') != 'http://'+ws.headers.get('host', ''):
        await ws.close(code=1008)
        return
    await ws.accept()
    try:
        while True:
            await asyncio.wait_for(ws.send_json(snapshot()), 5)
            await asyncio.sleep(1)
    except (WebSocketDisconnect, RuntimeError, asyncio.TimeoutError):
        pass



def read_cell():
    try:
        cfg = yaml.safe_load(Path('/config/gnb.yml').read_text()) or {}
        c, rf = cfg.get('cell_cfg', {}), cfg.get('ru_sdr', {})
        n = number(c.get('dl_arfcn'))
        bw, scs = number(c.get('channel_bandwidth_MHz')), number(c.get('common_scs'))
        band = c.get('band')
        return {'file': os.environ.get('GNB_CONFIG'), 'band': 'n'+str(band) if band else None,
                'sinrMethod': (cfg.get('expert_phy') or {}).get('pusch_sinr_calc_method', 'post_equalization'),
                'waveform': 'DFT-s-OFDM' if (c.get('pusch') or {}).get('enable_transform_precoding', False) else 'CP-OFDM',
                'duplex': {78: 'TDD', 3: 'FDD'}.get(band), 'arfcn': n,
                'dlFreq': round(.005*n if n < 600000 else 3000+.015*(n-600000), 3) if n is not None and 0 <= n < 2016667 else None,
                'bw': bw, 'scs': scs, 'prb': {(10, 15): 52, (10, 30): 24, (20, 15): 106, (20, 30): 51}.get((bw, scs)),
                'pci': c.get('pci'), 'plmn': c.get('plmn'), 'tac': c.get('tac'),
                'txGain': rf.get('tx_gain'), 'rxGain': rf.get('rx_gain'), 'clockPpm': rf.get('clock_ppm')}
    except (OSError, ValueError, AttributeError, yaml.YAMLError):
        return {}


def host_details():
    def read(path):
        try:
            return Path(path).read_text().strip()
        except OSError:
            return None
    mem = {}
    for line in (read('/proc/meminfo') or '').splitlines():
        parts = line.split()
        if len(parts) >= 2:
            mem[parts[0].rstrip(':')] = number(parts[1])
    total, available = mem.get('MemTotal'), mem.get('MemAvailable')
    freq = number(read('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'))
    temps = []
    for path in Path('/sys/class/hwmon').glob('hwmon*/temp*_input'):
        v = number(read(path))
        if v is not None:
            temps.append(v/1000)
    return {'cpus': os.cpu_count(), 'ram_total_gib': total/1048576 if total else None,
            'ram_used_gib': (total-available)/1048576 if total and available is not None else None,
            'gov': read('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'),
            'ghz': freq/1e6 if freq is not None else None, 'temp': max(temps) if temps else None}


@app.get('/api/logs')
async def get_logs(svc: str = Query(pattern='^(gnb|core)$'), tail: int = Query(default=160, ge=20, le=400)):
    return {'log': '\n'.join(list(log_buffers[svc])[-tail:]), 'error': state['errors'].get(svc+'_log')}


@app.get('/api/metrics')
async def panel_metrics():
    now = time.time()
    fresh = bool(state['gnb_connected'] and state['radio_at'] and now-state['radio_at'] <= 5)
    rows = []
    prune_evm(now)
    method = 'iq_constellation'
    for row in state['radio_ues'] if fresh else []:
        rnti = radio_rnti(row.get('rnti'))
        if rnti is None:
            continue
        link = associations.get(rnti)
        imsi = link[0] if link else None
        ue = subscribers.get(imsi, {})
        rows.append({**row, 'rnti': f'0x{rnti:04x}', 'imsi': private_text(imsi) if imsi else None,
                     'name': UE_NAMES.get(imsi), 'estimated': bool(imsi), 'ip': ue.get('ip'),
                     'dnn': ue.get('dnn'), 'status': ('registrado (observado)' if ue.get('connected') else 'sin registro observado'),
                     'dl_mbps': number(row.get('dl_brate'))/1e6 if number(row.get('dl_brate')) is not None else None,
                     'ul_mbps': number(row.get('ul_brate'))/1e6 if number(row.get('ul_brate')) is not None else None})
    window = Counter()
    for point in rt_window:
        window.update(point)
    # Ventana parcial normalizada por el tiempo realmente observado.
    seconds = min(60, max(1, time.monotonic()-START))
    rates = {k: v*60/seconds for k, v in window.items()}
    core_rows = [{**u, 'imsi': private_text(u['imsi'])} for u in subscribers.values()]
    return {'cell': state.get('cell', {}), 'sys': state['host'],
            'core': {'ues': core_rows, 'reg': sum(u['connected'] for u in subscribers.values()) if subscribers else None,
                     'pdu': sum(bool(u.get('pdu')) for u in subscribers.values()) if subscribers else None,
                     'nf': {n: ('log reciente' if now-t < 10 else 'sin actividad reciente') for n, t in nf_seen.items()},
                     'ogstun': state['ogstun'], 'slice': {'sst': 1, 'sd': '0xffffff', 'dnn': 'Metodos1'}},
            'evm': {'method': method, 'measured': True,
                    'series': {f'0x{rnti:04x}': {'name': UE_NAMES.get(associations.get(rnti, (None,))[0]),
                                               'points': list(points)} for rnti, points in evm_history.items()}},
            'ues': rows, 'thr': [{'dl': h['ogstun'].get('tx_bytes_per_s', 0)*8/1e6 if 'tx_bytes_per_s' in h['ogstun'] else None,
                                   'ul': h['ogstun'].get('rx_bytes_per_s', 0)*8/1e6 if 'rx_bytes_per_s' in h['ogstun'] else None} for h in list(history)[-60:]],
            'rt': {'rates': rates, 'total': dict(rt_total), 'series': [p.get('total', 0)*60 for p in rt_window], 'alarm': state['alarm']},
            'events': list(events), 'running': state['gnb_connected'], 'mode': 'métricas reales' if fresh else 'sin datos de radio',
            'pings': {k: {**v, 'samples': list(v['samples']), 'lines': list(v.get('lines', []))} for k, v in pings.items()},
            'iperf': {**iperf, 'results': list(iperf['results'])}, 'errors': state['errors']}


@app.get('/api/evm')
async def monitor_evm():
    panel = await panel_metrics()
    return {'cell': {k: panel['cell'].get(k) for k in ('band', 'dlFreq', 'prb', 'plmn', 'file', 'waveform', 'duplex')},
            **panel['evm'], 'time': time.time(), 'fresh': any(time.time()-p['time'] < 5 for series in evm_history.values() for p in series),
            'dl': {f'0x{rnti:04x}': {'name': UE_NAMES.get(associations.get(rnti, (None,))[0]),
                                    'points': list(points)} for rnti, points in dl_history.items()},
            # Paso C: ul[modulación] = {points: [[i, q], ...], evm_pct, snr_db, n_slots}.
            'constellations': iq_monitor.snapshot()}
