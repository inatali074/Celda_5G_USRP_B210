#!/usr/bin/env python3
"""Servicio de control de la celda para el panel web (lo arranca scripts/lanzador.sh).

Corre en el host, fuera de Docker, y escucha solo en 127.0.0.1:8090. Acepta órdenes
fijas: iniciar una de las 4 configuraciones del menú de start.sh (con o sin SIP e IMS)
o frenar la radio. No ejecuta texto que venga de la web: la opción es un número del 1
al 4 que se traduce a un archivo de una lista fija, y los comandos se arman sin shell.

Defensas:
- solo se aceptan pedidos con Host 127.0.0.1:8090 o localhost:8090 (DNS rebinding) y
  con Origin http://localhost:8080 o http://127.0.0.1:8080;
- las órdenes son POST con Content-Type application/json, lo que obliga al navegador a
  pedir permiso (preflight CORS), y ese permiso solo se da a esos dos orígenes;
- cuerpo de 1 KB como máximo, con plazo de lectura, y JSON con un esquema fijo.
No autentica al operador: cualquier proceso local de la PC puede mandar órdenes. Se
acepta porque la PC del laboratorio tiene un solo usuario (ver PROYECTO.md, D-022).

"Frenar" tiene prioridad: si llega durante un inicio, corta start.sh y después corre
stop.sh. Al terminar (SIGTERM/SIGINT/SIGHUP del lanzador), corta lo que esté corriendo;
el lanzador corre stop.sh después de que este proceso terminó.

Variable CONTROL_SIMULAR=1: no ejecuta nada, solo muestra los comandos (para probar).
"""
import collections
import json
import os
import pathlib
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PUERTO = 8090
HOSTS = {f'127.0.0.1:{PUERTO}', f'localhost:{PUERTO}'}
ORIGENES = {'http://localhost:8080', 'http://127.0.0.1:8080'}
OPCIONES = {
    1: ('gnb_b210_00101_n78_cpofdm.yml', 'n78 TDD · CP-OFDM'),
    2: ('gnb_b210_00101_n78_dfts.yml', 'n78 TDD · DFT-s-OFDM'),
    3: ('gnb_b210_00101_n3_cpofdm.yml', 'n3 FDD · CP-OFDM'),
    4: ('gnb_b210_00101_n3_dfts.yml', 'n3 FDD · DFT-s-OFDM'),
}
SECRETO_SIP = RAIZ / 'config/secretos/sip_credenciales.conf'
SECRETO_IMS = RAIZ / 'config/secretos/ims_mysql.env'
SIMULAR = os.environ.get('CONTROL_SIMULAR') == '1'

candado = threading.Lock()  # una acción por vez
salida = collections.deque(maxlen=200)
estado = {'accion': None, 'resultado': None, 'pedido': None, 'desde': None,
          'ultimo': None, 'cancelar': False}
proceso_actual = {'p': None}
cerrando = threading.Event()


def registrar(texto):
    for linea in texto.rstrip('\n').split('\n'):
        salida.append(time.strftime('%H:%M:%S ') + linea)
    try:
        print(texto, end='' if texto.endswith('\n') else '\n', flush=True)
    except OSError:
        pass  # la terminal del lanzador se cerró: la salida queda en el panel


def correr(comando):
    """Corre un comando del proyecto sin shell, en su propio grupo de procesos."""
    registrar('$ ' + ' '.join(comando))
    if SIMULAR:
        for _ in range(20):
            if estado['cancelar'] and comando[0] == './start.sh':
                registrar('(simulado: cortado)')
                return -15
            time.sleep(0.1)
        registrar('(simulado: no se ejecutó)')
        return 0
    proceso = subprocess.Popen(comando, cwd=RAIZ, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                               start_new_session=True)
    proceso_actual['p'] = proceso
    try:
        for linea in proceso.stdout:
            registrar(linea)
        return proceso.wait()
    finally:
        proceso_actual['p'] = None


def cortar_actual():
    """Corta el comando en curso (todo su grupo de procesos)."""
    p = proceso_actual['p']
    if p and p.poll() is None:
        try:
            os.killpg(p.pid, signal.SIGTERM)
            p.wait(timeout=20)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def gnb_activo():
    """Devuelve (estado, archivo): estado es True (corriendo), False (detenido o sin
    contenedor) o None (no se pudo saber, por ejemplo si Docker no responde)."""
    try:
        r = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=^5g-gnb-radio-1$', '--format',
                            '{{.State}}|{{.Mounts}}'], capture_output=True, text=True, timeout=8)
        if r.returncode != 0:
            return None, None
        if not r.stdout.strip():
            return False, None  # el contenedor no existe: confirmado por Docker
        corriendo = r.stdout.split('|', 1)[0].strip() == 'running'
        m = subprocess.run(['docker', 'inspect', '-f',
                            '{{range .Mounts}}{{.Source}}>{{.Destination}}|{{end}}', '5g-gnb-radio-1'],
                           capture_output=True, text=True, timeout=8)
    except (OSError, subprocess.TimeoutExpired):
        return None, None
    archivo = next((pathlib.Path(x.rsplit('>', 1)[0]).name for x in m.stdout.split('|')
                    if x.endswith('>/config/gnb.yml')), None) if m.returncode == 0 else None
    return corriendo, archivo


def trabajo(accion, pedido):
    try:
        codigo = 0
        if accion == 'iniciar':
            corriendo, _ = gnb_activo()
            if corriendo is None:
                raise RuntimeError('Docker no responde: no se sabe si el gNB está corriendo')
            if corriendo:
                codigo = correr(['./stop.sh', '--solo-radio'])
            if codigo == 0 and not estado['cancelar']:
                comando = ['./start.sh', OPCIONES[pedido['opcion']][0], '--sin-preguntas']
                comando += ['--sip'] if pedido['sip'] else []
                comando += ['--ims'] if pedido['ims'] else []
                codigo = correr(comando)
                if codigo == 0:
                    estado['ultimo'] = pedido
        if accion == 'frenar' or estado['cancelar']:
            if estado['cancelar']:
                registrar('--- se pidió frenar durante el inicio ---')
            codigo = correr(['./stop.sh', '--solo-radio'])
        corriendo, _ = gnb_activo()
        if (accion == 'frenar' or estado['cancelar']) and corriendo is not False:
            codigo = codigo or 1
            registrar('ATENCIÓN: no se pudo confirmar que el gNB esté detenido. Revisá con: docker ps')
        estado['resultado'] = 'ok' if codigo == 0 else f'falló (código {codigo})'
        registrar(f'--- {accion}: {estado["resultado"]} ---')
    except Exception as exc:  # se informa en el panel; el servicio sigue
        estado['resultado'] = f'error: {exc}'
        registrar(estado['resultado'])
    finally:
        estado.update(accion=None, cancelar=False)
        candado.release()


class Manejador(BaseHTTPRequestHandler):
    server_version = 'control-celda'
    timeout = 5  # plazo para leer el pedido

    def _origen(self):
        origen = self.headers.get('Origin')
        return origen if origen in ORIGENES else None

    def _permitido(self):
        return self.headers.get('Host') in HOSTS and self._origen() is not None

    def _responder(self, codigo, datos):
        cuerpo = json.dumps(datos).encode()
        self.send_response(codigo)
        origen = self._origen()
        if origen:
            self.send_header('Access-Control-Allow-Origin', origen)
            self.send_header('Vary', 'Origin')
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_OPTIONS(self):
        if not self._permitido():
            self.send_response(403)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', self._origen())
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '600')
        self.send_header('Vary', 'Origin')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        if not self._permitido():
            return self._responder(403, {'error': 'origen no permitido'})
        if self.path != '/estado':
            return self._responder(404, {'error': 'no existe'})
        corriendo, archivo = gnb_activo()
        opcion = next((n for n, (a, _) in OPCIONES.items() if a == archivo), None)
        self._responder(200, {
            'gnb': corriendo, 'config': archivo, 'opcion': opcion,
            'ultimo': estado['ultimo'] if corriendo else None,
            'accion': estado['accion'], 'resultado': estado['resultado'],
            'pedido': estado['pedido'], 'desde': estado['desde'],
            'opciones': {n: e for n, (_, e) in OPCIONES.items()},
            'salida': list(salida)[-40:], 'simulado': SIMULAR, 'hora': time.time()})

    def _leer_json(self):
        try:
            largo = int(self.headers.get('Content-Length', ''))
        except ValueError:
            return None
        if not 0 <= largo <= 1024:
            return None
        try:
            datos = json.loads(self.rfile.read(largo) or b'{}')
        except (ValueError, OSError):
            return None
        return datos if isinstance(datos, dict) else None

    def do_POST(self):
        if not self._permitido():
            return self._responder(403, {'error': 'origen no permitido'})
        if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
            return self._responder(415, {'error': 'se espera JSON'})
        datos = self._leer_json()
        if datos is None:
            return self._responder(400, {'error': 'pedido inválido'})
        if cerrando.is_set():
            return self._responder(503, {'error': 'el lanzador se está cerrando'})
        if self.path == '/frenar':
            if estado['accion'] == 'iniciar':
                estado['cancelar'] = True  # el trabajador corta start.sh y corre stop.sh
                cortar_actual()
                return self._responder(202, {'aceptado': 'frenar (cortando el inicio)'})
            pedido, accion = None, 'frenar'
        elif self.path == '/iniciar':
            opcion = datos.get('opcion')
            sip, ims = datos.get('sip', False), datos.get('ims', False)
            if type(opcion) is not int or opcion not in OPCIONES or type(sip) is not bool or type(ims) is not bool:
                return self._responder(400, {'error': 'opción inválida (1 a 4; sip e ims, true o false)'})
            # Prerrequisitos antes de cortar la celda que está andando.
            if sip and not SECRETO_SIP.is_file():
                return self._responder(400, {'error': 'falta config/secretos/sip_credenciales.conf: no se puede levantar SIP'})
            if ims and not SECRETO_IMS.is_file():
                return self._responder(400, {'error': 'falta config/secretos/ims_mysql.env: no se puede levantar IMS'})
            pedido, accion = {'opcion': opcion, 'sip': sip, 'ims': ims}, 'iniciar'
        else:
            return self._responder(404, {'error': 'no existe'})
        if not candado.acquire(blocking=False):
            return self._responder(409, {'error': f'ya hay una acción en curso: {estado["accion"]}'})
        estado.update(accion=accion, resultado=None, pedido=pedido, desde=time.time(), cancelar=False)
        threading.Thread(target=trabajo, args=(accion, pedido), daemon=True).start()
        self._responder(202, {'aceptado': accion})

    def log_message(self, formato, *args):
        pass


def main():
    servidor = ThreadingHTTPServer(('127.0.0.1', PUERTO), Manejador)
    servidor.daemon_threads = True

    def terminar(*_):
        # Cierra la admisión, corta lo que esté corriendo y espera al trabajador.
        cerrando.set()
        if estado['accion'] == 'iniciar':  # un stop.sh en curso no se corta: se lo deja terminar
            estado['cancelar'] = True
            cortar_actual()
        if candado.acquire(timeout=60):
            candado.release()
        threading.Thread(target=servidor.shutdown, daemon=True).start()

    for senal in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(senal, terminar)
    registrar(f'Control de la celda en http://127.0.0.1:{PUERTO}' + (' (SIMULADO)' if SIMULAR else ''))
    servidor.serve_forever()
    servidor.server_close()


if __name__ == '__main__':
    main()
