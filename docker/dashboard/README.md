# Dashboard 5G SA

Disponible en http://localhost:8080, servido por FastAPI dentro del contenedor
`dashboard` del proyecto Compose `5g`. Conserva el diseño, CSS, tarjetas, consolas
y gráficos SVG del **Panel5G_SA de un compañero**, adaptados a nuestro backend.
No usa su `server.py`, CDN, modo demo, socket Docker ni comandos de control de red.
Levantar/Frenar muestran únicamente `./start.sh <config.yml>` y `./stop.sh`.

## Datos de cada panel

- **Conexiones:** `cells[].ue_list` del WebSocket del gNB, suscripción
  `metrics_subscribe`. RNTI hexadecimal, CQI, MCS DL/UL, SNR PUSCH (columna SINR),
  RSRP PUSCH, bitrates convertidos de bit/s a Mbit/s y BLER = 100×NOK/(OK+NOK).
  El detalle muestra SNR PUCCH, HARQ por dirección, RI DL/UL, PHR, BSR, buffer DL
  y TA explícitamente en ns. No se deducen unidades de aliases ambiguos.
  Un mensaje sin `ue_list` conserva la tabla; lista vacía la vacía. Después de
  5 s sin muestras de UEs o al perder el WebSocket, deja de mostrar radio vieja.
- **EVM de subida (PUSCH):** medido por decisión sobre las constelaciones IQ,
  historial por RNTI de hasta 120 puntos con timestamp del log PUSCH (recepción
  si falta). Se elimina tras 30 s sin resultados. No se deriva de SINR.
  Referencias TX: QPSK 17,5 %, 16QAM 12,5 %, 64QAM 8 %, 256QAM 3,5 %;
  no constituyen una prueba de conformidad del enlace recibido.
- **Identidad y núcleo:** registro, IP y DNN observados en `/logs/core/core.log`.
  La asociación es **estimada**, uno a uno: creación `c-rnti=0x…: UE created`
  y registro posterior dentro de 5 s, priorizando la creación más cercana.
  Se recalcula con timestamps, independientemente del orden de lectura de archivos;
  una nueva creación del mismo RNTI invalida la unión anterior. Sin timestamps
  reconocibles no hay asociación. Requiere relojes y zona horaria comunes entre logs;
  los registros simultáneos pueden resultar ambiguos. Nunca se une por fila.
  Apodos: Redmi Note 14, OnePlus 13 y srsUE (sim), según IMSI de laboratorio.
  Los IMSI ajenos a `00101…` se muestran como `****` más sus últimos cuatro dígitos,
  también en eventos y consolas. “srsUE (sim)” es un apodo, no datos simulados.
- **Celda/RF:** YAML `/config/gnb.yml`, montaje de sólo lectura del mismo
  `./config/gnb/${GNB_CONFIG:-gnb_b210.yml}` que usa `gnb-radio`. El nombre se
  transmite por `GNB_CONFIG` al dashboard. Lee banda, ARFCN, ancho, SCS, PCI,
  PLMN, TAC y ganancias/clock_ppm. Frecuencia DL: 0,005×N MHz debajo de 600000;
  3000+0,015×(N−600000) MHz hasta 2016666. Otras regiones: sin dato.
  Duplex identificado para n3/n78. Tabla PRB: 10 MHz/15 kHz=52,
  10/30=24, 20/15=106, 20/30=51. Otros casos: sin dato.
  Serie y velocidad USB no se consultan: “no disponible”. Las barras de uso PRB
  indican sin datos normalizados: los arrays por slot TDD no son un porcentaje
  comparable sin interpretar su ventana y denominador.
- **Sistema:** CPU host por diferencias de `/proc/stat` (100% = toda la máquina),
  cantidad de CPU lógicas por `os.cpu_count()`, RAM total y usada por
  `/proc/meminfo` (usada = total − disponible). Governor y frecuencia CPU0 desde
  sysfs; temperatura máxima entre sensores hwmon legibles. No es necesariamente
  temperatura de CPU. Sin acceso a sysfs: “–”. No mide CPU exclusiva del gNB.
- **Núcleo:** actividad reciente de log por NF, nunca supone procesos vivos.
  Después de 10 s sin líneas muestra “sin actividad reciente”; una NF silenciosa
  puede seguir funcionando. Cuenta registros/sesiones observados y liberaciones
  que contienen IMSI; no consulta MongoDB ni garantiza conectividad actual.
  Slice informado según el log aportado: SST 1, SD 0xffffff, DNN Metodos1.
- **N6:** bytes y tasas reales de ogstun, desde `/sys/class/net/ogstun/statistics`
  en el namespace de Open5GS. TX=DL hacia UE, RX=UL desde UE. Historial 60 puntos;
  no es el mismo contador que bitrate radio y puede incluir overhead.
- **Tiempo real:** una categoría por línea, prioridad UL busy, underflow,
  overflow, late y otras “Real-time failure”. Acumulados desde inicio del
  dashboard, tasas por tipo en ventana de hasta 60 s, normalizada durante inicio.
  Gráfico: 60 muestras de la cuenta por segundo multiplicada por 60.
  Alarma UL busy >10 por segundo. Se cuenta por tiempo de lectura: un atraso del
  tailer puede desplazar los picos. No se cuentan fallas del bootstrap histórico.
- **Consolas/eventos:** tailers incrementales; bootstrap máximo 256 KiB por log,
  400 líneas por consola, sin ANSI, 150 eventos. El estado reconstruido desde ese
  fragmento puede estar incompleto. Truncado/rotación limpia asociaciones y estado
  observado del servicio. No relee logs completos por petición.

El navegador refresca cada 2 s sin solapar el ciclo de métricas. Los gráficos no
rellenan datos ausentes con muestras ficticias. Texto externo usa `textContent`
o escape HTML antes de insertarse en la página.

## Herramientas y API

Ping permite elegir IP conocida, 10.45.0.1, 8.8.8.8 o destino libre. Usa la validación
`destination()` y subprocess sin shell existentes. Duración 1–600 s, intervalo
0,2–2 s; máximo tres pings simultáneos. El resultado incluye RTT, pérdida y jitter
(media de diferencias absolutas entre RTT consecutivos).

iperf3: botón servidor enlaza 10.45.0.1:5201. En la app del teléfono:

```text
-c 10.45.0.1 -p 5201 -t 10
-c 10.45.0.1 -p 5201 -t 10 -R
```

El cliente web apunta al destino de ping, donde debe existir servidor iperf3.
Normal envía desde el núcleo; reverse recibe en el núcleo. TCP o UDP, duración
1–60 s, UDP 1–100 Mbit/s. Un cliente simultáneo. Muestra el resultado JSON real.
El servidor se relanza entre pruebas completas (`-1 -J`); detener puede perder
el resultado parcial. Estas herramientas agregan carga durante las mediciones.

- `GET /api/metrics`: cell, sys, core, ues, evm, thr, rt, events, running, mode y tests.
  `evm` contiene `method`, `measured` y `series` por RNTI hexadecimal; cada
  serie incluye `name` y `points` (`time`, `sinr_db`, `evm_pct`, `ul_mcs`).
  `running` significa conexión WebSocket al gNB, no estado Docker confirmado.
- `GET /api/logs?svc=gnb|core&tail=160`: buffer, tail entre 20 y 400.
- Se mantienen `/api/state`, `/ws`, `/api/ping`, `/api/iperf/*` y sus validaciones.
  Las rutas antiguas conservan sus datos de diagnóstico crudos: no son una API
  anonimizada. La página adaptada usa `/api/metrics` y `/api/logs`.
- Se mantiene el middleware Origin para acciones y la comprobación Origin de WS.
  No hay autenticación: usar en el laboratorio confiable. El namespace compartido
  permite acceso desde UEs aunque la publicación host sea 127.0.0.1:8080.

## Verificación y prueba manual

Verificado durante la adaptación: `python3 -m py_compile docker/dashboard/app.py`.
No se ejecutaron Docker, instalaciones, red, ping, iperf ni radio. Dockerfile sin
cambios; PyYAML 6.0.2 se agrega a requirements para la próxima construcción.

Los siguientes pasos los ejecutan las personas responsables:

1. Construir `docker compose build dashboard`. Al recrearlo, usar el mismo
   `GNB_CONFIG` que para `gnb-radio`; al recrear Open5GS, recrear dashboard también
   para compartir el namespace actual. No cambiar configuración durante una corrida.
2. Abrir localhost:8080. Sin gNB debe mostrar sin datos de radio, nunca demo.
   Levantar/Frenar sólo deben mostrar comandos y no hacer peticiones de control.
3. En una corrida autorizada, comprobar archivo/banda/ARFCN/SCS/PRB contra el YAML
   elegido; registrar un teléfono y contrastar timestamps, RNTI, IMSI/IP y unidades.
   Revisar que mensajes sin ue_list no vacíen la tabla, y una lista vacía sí.
4. Comprobar consolas, rotación/truncado, enmascarado de terceros y texto con signos
   HTML mostrado literalmente. `/api/logs?svc=otro` y `tail=401` deben dar 422.
5. Probar ping e iperf3 con el teléfono y revisar resultados. Destino `-R`, duración
   fuera de límites y acciones con Origin ajeno deben rechazarse.
6. Contrastar CPU/RAM con el host, contadores ogstun y fallas con logs. Tras detener
   la red mediante `./stop.sh`, la UI debe perder métricas sin inventar estados NF.

Pendiente: prueba integrada en contenedores, navegador y logs reales. Los parsers
son conservadores: formatos no reconocidos quedan sin asociación/dato; ausencia de
un evento de liberación puede dejar un registro o PDU observado antiguo.

## EVM medido (IQ) y constelaciones

`/evm` consulta `/api/evm` cada segundo, con canvas local, sin CDN ni datos
simulados. El contenedor lee `/logs/gnb/gnb_rx_symbols.bin` y `gnb.log`,
montados en solo lectura desde `gnb-logs`. No controla la radio.

Las cuatro configuraciones del menú de `./start.sh` incluyen JSON,
`remote_control`, log `info` y `phy_rx_symbols_*`. Se conserva el método SINR
predeterminado `post_equalization`, usado por el scheduler. El volcado IQ
crece sin límite mientras haya subida: al terminar, borrar
`/tmp/gnb_rx_symbols.bin` del volumen `gnb-logs`.

`iq.py` deduce N_sc de `RX_SYMBOL size=14*N_sc`, valida el rango PRB y coteja
con la configuración: n78 tiene 612 subportadoras, SCS 30 kHz y 20 slots/trama;
n3 tiene 1272, SCS 15 kHz y 10 slots/trama. Un puerto, sector 0, 14 símbolos,
complex64 little endian, offset/size en muestras, orden símbolo/subportadora.
El emparejador SFN.slot espera 2 s, limita la cola a 4096 y procesa como máximo
un slot cada 250 ms. La CLI usa dos pasadas y el RX_SYMBOL más cercano.

La forma de onda y PCI se leen de `/config/gnb.yml`:

- CP-OFDM: DMRS Gold (TS 38.211 §5.2.1 y §6.4.1.1.1.1), longitud según grilla.
  Si coherencia <0,5, prueba PCI/1/0, slot/slot+1 y delta 0/1.
- DFT-s-OFDM: DMRS de baja PAPR (§6.4.1.1.1.2 y §5.2.2), M_ZC=6*n_PRB,
  mayor primo estrictamente menor que M_ZC, Zadoff-Chu y extensión cíclica.
  Sin hopping: u=PCI%30, v=0. Si coherencia <0,5 busca u=0..29 y delta 0/1.
  Para M_ZC<36 declara `NoChannel`; no implementa las tablas cortas.
  Aplica IDFT unitaria por símbolo después de ecualizar, antes de decidir QAM.

Detecta DMRS por energía de peine par/impar (relación >5); respaldo {2,7,11}.
Estima LS, suaviza módulo/fase sobre 15 pilotos, interpola y ecualiza ZF.
Excluye símbolos DMRS completos. QPSK, 16/64/256QAM; pi/2-BPSK no está
implementado y se rechaza explícitamente si aparece. Supone DMRS tipo 1,
puerto único y dos grupos CDM sin datos. Hopping, multicapas, PTRS/UCI y errores
de decisión pueden sesgar la medición. No equivale a EVM de conformidad TX.
Pendiente contrastar con capturas reales, especialmente n3 DFT-s-OFDM.

Contrato `/api/evm`:

- `cell`: band, dlFreq, prb, plmn, file, waveform y duplex.
- `method="iq_constellation"`, `measured=true`: identifica el método, incluso
  sin datos. `series` contiene puntos por RNTI con tiempo Unix y evm_pct;
  sinr_db y ul_mcs quedan null, no se inventan ni se asocian por cercanía.
- `time`: reloj Unix del servidor; `fresh`: hay medición IQ de menos de 5 s.
- `dl`: CQI, MCS, BLER y bitrate de métricas JSON, historial independiente.
- `constellations`: source, ul y stats. `ul[mod]` incluye hasta 3000 puntos,
  EVM/SNR por suma de energías de hasta 50 slots y dmrs_check (convención,
  coherencia, u/v para DFT-s-OFDM). Solo muestra modulaciones actualizadas en
  los últimos 5 s y con archivo en crecimiento. stats informa procesados,
  descartados_por_tasa, sin_canal y ultimo_error.

Ausencia/rotación/truncado del archivo limpia estado IQ. Errores se informan
sin detener el servidor. Una reescritura con igual inode/tamaño/prefijo puede
no detectarse. La coherencia DMRS valida operativamente el formato, sin
reemplazar la comparación con el productor.

Prueba local, sin Docker ni radio:

```sh
python3 -I docker/dashboard/iq.py --probar
python3 -I docker/dashboard/iq.py --bin /ruta/gnb_rx_symbols.bin --log /ruta/gnb.log --scs 15 --dfts --nid 1
```

`--probar` cubre las cuatro combinaciones con 16QAM, canal de fase lineal y
AWGN de 25 dB, EVM esperado 5,62 % ±0,5 puntos porcentuales, asignación al borde
de la grilla, búsqueda alternativa u=17/delta=1 y límites de slots.
OCUDU release_26_10 confirma `enable_transform_precoding`, `phy_rx_symbols_*`,
SINR por defecto y DMRS u=n_rs_id%30/v=0. El scheduler llena pusch_dmrs_id con
PCI; la búsqueda alternativa queda informada en dmrs_check y no modifica radio.
