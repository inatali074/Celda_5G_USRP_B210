# Dashboard de la celda 5G

Abrí **http://localhost:8080** en la PC de la celda. No controla ni inicia el gNB.
Muestra conexión WebSocket de métricas, UEs de radio y núcleo, eventos, fallas de
tiempo real, tráfico de ogstun, CPU y carga **del host completo**, ping e iperf3.
El uptime del dashboard es propio; el del gNB sólo aparece si se observó `gNB started`.
La configuración sólo se informa si el log permite deducirla (puede mostrar únicamente
`/config/gnb.yml`, que no identifica el archivo elegido en el host).

## Construcción y prueba (los ejecuta el usuario)

Desde la raíz del proyecto, construí únicamente la nueva imagen:

```bash
docker compose build dashboard
```

Para probar sin radio (requiere las imágenes del núcleo y MongoDB ya disponibles):

```bash
OPEN5GS_CONFIG=open5gs-5gc-zmq.yml docker compose up -d --no-build mongodb open5gs dashboard
```

Esto aplica el puerto y el volumen nuevos recreando Open5GS si hace falta: interrumpe
sesiones previas del núcleo. No debe hacerse con una prueba RF en curso.
Abrí la página: debe indicar gNB desconectado, sin caerse. Comprobá CPU/carga y
ping a 10.45.0.1 y 8.8.8.8; un destino como `-R` debe rechazarse.

Para una prueba de radio ya autorizada y con la B210 dentro de la jaula, elegí
explícitamente una de las dos configuraciones instrumentadas:

```bash
./start.sh gnb_b210_00101_csiper_ppm0_kos.yml
# Alternativa en otra corrida: ./start.sh gnb_b210_00101_n3_ppm0_kos.yml
```

**start.sh transmite apenas se ejecuta** y conserva sus pasos previos, incluido el
ofrecimiento existente de cambiar el governor en el host. No ejecutar ese cambio
sin aprobación. La configuración por defecto de start.sh no se modificó: no tiene
estas métricas habilitadas. Verificá registro, mapa IMSI/IP, JSON crudo, gráficos y
`ogstun`; ejecutá ping a la IP real del UE. Al terminar:

```bash
./stop.sh
```

Confirmá logs guardados como antes en `logs/`. En otra corrida, el log del gNB debe
empezar vacío y no repetir eventos anteriores. El núcleo conserva su archivo entre
arranques; el dashboard omite contenido anterior a su inicio si el archivo ya existía.
No borres volúmenes para detener la red: contienen logs y datos de MongoDB.

## Medir con el teléfono

En la página, iniciá el servidor iperf3. Desde una app compatible con **iperf3**, por
ejemplo Magic iPerf, usá servidor `10.45.0.1`, puerto `5201`:

```text
-c 10.45.0.1 -p 5201 -t 10       (subida desde el teléfono)
-c 10.45.0.1 -p 5201 -t 10 -R    (bajada hacia el teléfono)
```

Cada prueba completa aparece como JSON y gráfico por intervalo. El servidor usa
`-1 -J`: termina y se relanza entre pruebas; esperá un instante antes de la siguiente.
Durante una prueba, el gráfico ogstun sigue en vivo. Si usás el cliente de la página,
el destino debe ejecutar un servidor iperf3: normal envía desde el núcleo; `-R` recibe
en el núcleo. UDP: entre 1 y 100 Mbit/s; duración hasta 60 s; un cliente simultáneo.
Detener el servidor cancela la prueba y puede perder el resultado parcial.
Ping: intervalo 0,2–2 s, hasta 600 s, tres destinos simultáneos; detener puede dejar
una pérdida provisoria. Jitter es la media de |RTT actual − RTT anterior|, no el jitter UDP.
El ping entre **dos teléfonos** debe hacerse desde una app en uno de ellos.

## Métricas, logs y límites

- `app.py`, diccionario **FIELDS** y función **extract**, centralizan el mapeo tolerante.
  Con una captura real del visor JSON, agregá aliases en FIELDS y, si el esquema tiene
  campos anidados por dirección, ajustá extract. No se confirma el esquema real todavía.
  Los bitrates se grafican crudos: no se asumen unidades de aliases desconocidos.
  BLER = NOK/(OK+NOK): no se asume que los contadores sean del último segundo.
  SINR/SNR y BLER gráficos son promedios simples de los UEs; bitrate es la suma.
- Radio (RNTI) y núcleo (IMSI/IP) sólo se unen con un IMSI explícito en las métricas.
  El tiempo conectado es desde el registro o sesión observado por el dashboard,
  no una garantía de conectividad RF; puede quedar activo si no hay Deregistration.
- Conserva en RAM 180 muestras, 150 eventos, 30 mensajes crudos y 10 pruebas iperf.
  Reiniciar pierde esas historias. No interpreta los logs viejos como registros nuevos.
  Los fallos de tiempo real se cuentan por segundo **de lectura**, no por timestamp
  del log; si hay atraso, un pico puede corresponder a eventos anteriores.
  Alarma UL busy: más de 10/s (ajustable en `state['busy_threshold']`).
- Chart.js **4.4.1** se carga desde cdn.jsdelivr.net: requiere Internet en el navegador;
  sin CDN siguen disponibles tablas, JSON y herramientas. No hay build del frontend.
- Compartir `/tmp` del gNB conserva `/tmp/gnb.log` para stop.sh. Un wrapper `sh -ec`
  trunca sólo ese archivo y hace `exec` del binario con los argumentos originales;
  preserva señales, stdin y command. También quedan pcaps de /tmp en ese volumen.
  Logs montados sólo lectura en el dashboard. Open5GS agrega archivo sin desactivar
  el logger de consola; no se cambió su comando ni su entrypoint de red.
- NET_RAW es la única capacidad del dashboard: respaldo para ping cuando el kernel no
  permite sockets ICMP de datagrama. No tiene Docker socket ni acceso a USB.
- HTTP escucha en todas las interfaces del namespace compartido; aunque la publicación
  al host es sólo `127.0.0.1:8080`, **los UE pueden alcanzar 10.45.0.1:8080 y la red ran
  puede alcanzar 10.53.1.2:8080**. No hay autenticación: contiene IMSI, IP y herramientas.
  La comprobación de Origin evita acciones desde páginas de otro origen, no sustituye
  autenticación ni impide acceso directo de participantes del laboratorio.
  También comparte el loopback del núcleo: usar sólo en la red de laboratorio confiable.
- Ping, iperf, JSON, logs y el navegador agregan CPU/tráfico y pueden alterar mediciones
  y tiempo real. Los archivos de log crecen sin límite durante una corrida; el del
  núcleo también entre corridas. Revisá espacio y conservá/anónimizá según el proyecto.
- Si se recrea Open5GS, recreá también dashboard para compartir el namespace actual:
  `docker compose up -d --no-build --force-recreate dashboard` (sin radio).

## Verificación de fuentes y validación pendiente

Verificados en Open5GS **v2.8.0**:
[ejemplo amf.yaml.in](https://github.com/open5gs/open5gs/blob/v2.8.0/configs/open5gs/amf.yaml.in)
y [ogs-init.c](https://github.com/open5gs/open5gs/blob/v2.8.0/lib/app/ogs-init.c):
`logger.file.path`, parseo de path y agregado del archivo mediante `ogs_log_add_file`
(sin quitar el logger predeterminado). Falta validar la salida de todas las NF del
binario monolítico `5gc` en ejecución con este volumen.

Los raw de GitLab release_26_10 no se pudieron obtener (cache miss y DNS restringido).
La sección raíz `remote_control` y `metrics.enable_json`, `metrics.periodicity.du_report_period`
y `metrics.layers.enable_sched/enable_sched_ue` siguen el relevamiento de Claude del
pedido. **La registración/anidación raíz no quedó verificada independientemente**.
Antes de transmitir, con la imagen gNB existente, se puede validar parseo y ayuda sin
iniciar la radio (no ejecutado por Codex):

```bash
GNB_CONFIG=gnb_b210_00101_csiper_ppm0_kos.yml docker compose --profile radio run --rm --no-deps --entrypoint /usr/local/bin/gnb gnb-radio -c /config/gnb.yml --help
GNB_CONFIG=gnb_b210_00101_n3_ppm0_kos.yml docker compose --profile radio run --rm --no-deps --entrypoint /usr/local/bin/gnb gnb-radio -c /config/gnb.yml --help
```

Si esa versión procesa `--help` antes del YAML, ese comando sólo confirma la ayuda;
revisá en el código que las secciones se registren en la raíz antes del arranque real.
No se construyeron imágenes ni se iniciaron contenedores durante la implementación.
