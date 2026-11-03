"""Monitoreo pasivo y herramientas de diagnóstico; nunca controla el gNB."""
import asyncio
from collections import Counter, deque
from contextlib import asynccontextmanager
import ipaddress
import json
import math
from pathlib import Path
import re
import time
import uuid

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import websockets

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
    'phr': ('phr', 'power_headroom'),
}
START = time.monotonic()
START_WALL = time.time()
state = {'gnb_connected': False, 'metrics_at': None, 'raw': None, 'radio_ues': [],
         'config': None, 'errors': {}, 'ogstun': {}, 'host': {}, 'rt': {},
         'radio_at': None, 'alarm': False, 'busy_threshold': 10, 'gnb_since': None}
metrics_history = deque(maxlen=30)
events = deque(maxlen=150)
history = deque(maxlen=180)
subscribers = {}  # IMSI -> estado observado en el núcleo, sin unión especulativa con RNTI.
pings = {}
iperf = {'server': False, 'client': False, 'results': deque(maxlen=10)}
processes = {}
tasks = set()
rt = Counter()


def event(source, text):
    events.append({'time': time.time(), 'source': source, 'text': text[:1000]})


def number(value):
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (ValueError, TypeError):
        return None


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
                        rows = extract(payload)
                        # Respuestas de control no borran el último conjunto de métricas.
                        if not isinstance(payload, dict) or payload.get('cmd') != 'metrics_subscribe' or rows:
                            state['radio_ues'] = rows
                            state['radio_at'] = time.time()
                        state['errors'].pop('metrics', None)
                    except (ValueError, TypeError) as exc:
                        state['errors']['metrics'] = str(exc)
        except Exception as exc:
            state['errors']['metrics'] = str(exc)[:300]
        finally:
            state['gnb_connected'] = False
        await asyncio.sleep(3)


def log_line(source, line):
    line = re.sub(r'\x1b\[[0-9;]*m', '', line)
    if source == 'gnb':
        for key, pattern in {'late': r'\blate\b', 'underflow': 'underflow', 'overflow': 'overflow',
                             'ul_busy': 'UL processor is busy', 'received_late': 'Received late'}.items():
            if re.search(pattern, line, re.I):
                rt[key] += 1
        if 'Real-time failure' in line:
            rt['total'] += 1
        if re.search(r'UE created|RLF detected|rrcRelease|PRACH.*detect|detect.*PRACH', line, re.I):
            event(source, line)
        if 'gNB started' in line:
            state['gnb_since'] = time.time()
        match = re.search(r'(?:config(?:uration)?[^\n]*?)([\w./-]+\.yml)', line, re.I)
        if match:
            state['config'] = match[1]
    else:
        match = re.search(r'UE SUPI\[(?:imsi-)?(\d+)\].*DNN\[([^]]+)\].*IPv4\[([\d.]+)\]', line)
        imsi_match = re.search(r'(?:imsi-|IMSI[\s\[:=]*|SUPI\[|\[)(\d{14,15})(?!\d)', line, re.I)
        imsi = match[1] if match else imsi_match[1] if imsi_match else None
        if imsi:
            if imsi not in subscribers and len(subscribers) >= 128:
                subscribers.pop(next(iter(subscribers)))
            ue = subscribers.setdefault(imsi, {'imsi': imsi, 'ip': None, 'since': None, 'connected': False})
            if match:
                ue.update(ip=match[3], dnn=match[2])
            if 'Registration complete' in line or match:
                if not ue['connected']:
                    ue['since'] = time.time()
                ue['connected'] = True
            if 'Deregistration' in line:
                ue['connected'] = False
                ue['seconds'] = time.time()-ue['since'] if ue['since'] else None
        if re.search(r'Registration complete|UE SUPI\[|Paging failed|Ue requested DNN.*Not Supported|Deregistration', line, re.I):
            event(source, line)


async def tail(source, path):
    """Lectura acotada por vuelta; detecta inode, tamaño y prefijo tras truncado rápido."""
    handle = None
    identity = None
    prefix = b''
    pending = b''
    first = True
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
                    # Al abrir el dashboard no se simulan registros viejos como conexiones nuevas.
                    if first:
                        if stat.st_mtime < START_WALL:
                            handle.seek(0, 2)
                        first = False
                    if source == 'gnb':
                        state['gnb_since'] = None
                        state['config'] = None
                    else:
                        for ue in subscribers.values():
                            ue['connected'] = False
                prefix = head
                chunk = handle.read(256*1024)
                pending += chunk
                lines = pending.split(b'\n')
                pending = lines.pop()[-16384:]
                for line in lines:
                    log_line(source, line.decode(errors='replace'))
                state['errors'].pop(source+'_log', None)
            except (OSError, ValueError) as exc:
                state['errors'][source+'_log'] = str(exc)[:300]
            await asyncio.sleep(.2)
    finally:
        if handle:
            handle.close()


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
                match = re.search(r'time[=<]([\d.]+)', line)
                if match and 'DUP!' not in line:
                    value = float(match[1])
                    item['received'] += 1
                    item['rtt_ms'] = value
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
    background = [launch(metrics()), launch(tail('gnb', Path('/logs/gnb/gnb.log'))),
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


def snapshot():
    now = time.time()
    return {**state, 'uptime': time.monotonic()-START, 'events': list(events), 'history': list(history),
            'metrics_history': list(metrics_history),
            'core_ues': [{**u, 'seconds': now-u['since'] if u['connected'] and u['since'] else u.get('seconds')} for u in subscribers.values()],
            'pings': {k: {**v, 'samples': list(v['samples'])} for k, v in pings.items()},
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
                  'samples': deque(maxlen=180), 'loss_percent': None}
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
