# Sesión 2026-11-03 (noche): dashboard, "UL processor is busy" y prueba A/B/A de DFT-s-OFDM

## Resultado
1. **Dashboard web funcionando**, con el diseño del panel de un compañero y datos reales:
   - métricas JSON del gNB, logs del gNB y del núcleo, la configuración montada, CPU y RAM del host;
   - ping e iperf3.

   Commits 50cc3e2 y 7755ae8. Se abre en `http://localhost:8080`.
2. **Primeras mediciones de tráfico** en tachoPC, n78 TDD, con el Redmi en `NR only`:

   | Medida | Resultado |
   | :--- | :--- |
   | Subida TCP | ~14,8 Mbit/s |
   | Bajada TCP | ~54 Mbit/s |
   | RTT mínimo y mediano | 17 y 28 ms, pero con la celda degradada |

   Los resultados de iperf3 y de ping son una transcripción: los JSON originales no se conservaron.

   Detalle: `evidencia/06_mediciones/`.
3. **DFT-s-OFDM funciona, pero no hay evidencia para adoptarlo por rendimiento.** Se mantiene CP-OFDM de forma provisoria.

   | Tramo | Promedio de subida |
   | :--- | :--- |
   | A1 (CP-OFDM) | 8,7 Mbit/s |
   | B (DFT-s-OFDM) | 12,7 Mbit/s |
   | A2 (CP-OFDM) | 14,8 Mbit/s |

   **Alcance limitado:** hay una sola corrida por tramo, y las pruebas fueron consecutivas.
   - **A1 tuvo otras condiciones de enlace:** SINR media del PUSCH de ~19 dB en sus ventanas de subida, contra ~27 dB en B y A2, y el MCS osciló. La causa está pendiente.
   - **Que el UE no esté limitado en potencia es una hipótesis:** no se midió el PHR.
   - **No se controlaron:** la posición del teléfono, el OnePlus y el tiempo desde el arranque.
4. **"UL processor is busy" también ocurre sin las métricas JSON.** En la PC de Santi se las había culpado. No son una condición necesaria; si aumentan la probabilidad o la frecuencia de la falla, no se determinó.

## Dashboard
- **Primera versión:** FastAPI más Chart.js. La escribió Codex y la revisó Claude.
  - Contenedor `dashboard` con `network_mode: service:open5gs`, `cap_drop: ALL` + `NET_RAW` y `no-new-privileges`.
  - Logs en volúmenes de solo lectura, puerto `127.0.0.1:8080`.
  - Se probó en la PC de Santi con la celda: las métricas JSON llegaron por `remote_control` (puerto 8001, `metrics_subscribe`).
- **Al usuario no le gustó el aspecto.** Se adoptó el `index.html` del Panel5G_SA del compañero.
  - **Su `server.py` se descartó**, porque:
    - arrancaba la radio desde la web saltándose `start.sh` y usaba la configuración vieja (`csiaper`, `clock_ppm −1,87`);
    - usaba `sudo -n docker`;
    - inyectaba el destino del test de tráfico en código Python que corría como root;
    - no verificaba de qué página venían los pedidos;
    - mostraba datos simulados con aspecto de reales;
    - asociaba las métricas de radio a cada IMSI por orden.
  - **Codex lo compatibilizó con nuestro backend.**
    - Agregó `/api/metrics` y `/api/logs`.
    - Asocia RNTI e IMSI por tiempo y enmascara los IMSI que no son de laboratorio.
    - Monta en solo lectura el YAML del gNB que se está usando.
    - Usa iperf3 real y escapa los textos.
  - **Claude corrigió:**
    - el rótulo del RSRP del PUSCH, que es relativo y no está en dBm;
    - los resultados de ping e iperf3, que salían como JSON crudo y ahora se ven resumidos.
- **Pendiente:** el servidor de iperf3 se apaga cuando `start.sh` recrea el dashboard; conviene que arranque solo. Además, los resultados quedan solo en memoria.

## "UL processor is busy"
- **En la PC de Santi, con métricas:** 5093 fallas por corrida. En la corrida TDD anterior, sin métricas, hubo 0. Se pensó que las causaban las métricas.
- **En tachoPC, sin métricas, también aparecieron:**

  | Tramo | Primera falla | Fallas en la corrida |
  | :--- | :--- | :--- |
  | A1 | 22:41:21,35 | 5142 |
  | B | Ninguna en ~5 min | 0 (79 fallas de tiempo real en total) |
  | A2 | 22:56:58,59 | 1429 |

- **Patrón:**
  - **Cuándo empiezan:**
    - en A1, en el mismo segundo de una ráfaga de underflow y late;
    - en A2, en el mismo segundo de una ráfaga chica, unos 11 s después de una mayor.
  - **Una vez que empiezan, persisten hasta el final de la corrida**, y su tasa varía con el tráfico:
    - en A1: ~10, ~20 y 60 por segundo, y después vuelve a ~20;
    - en A2: hasta 30 por segundo, y después baja a ~12-14.
  - **B tuvo ráfagas de tiempo real y ninguna "UL busy"**, así que una ráfaga no alcanza para que aparezcan.
  - **Caen en los slots de subida 7, 8, 9, 17, 18 y 19**, la mayoría en el 19, el del PRACH.
  - La CPU no estaba saturada.
- **En el código de OCUDU `release_26_10`** (`lib/fapi_adaptor/phy/p7/fapi_to_phy_fastpath_translator.cpp`, alrededor de las líneas 480-513):
  - la falla aparece cuando `ul_pdu_repository.get_pdu_slot_repository(slot)` devuelve un repositorio inválido, o sea, el espacio de ese slot sigue ocupado;
  - en cada pedido de subida solo se libera el controlador del slot anterior (`release_controller(slot - 1)`).
- **Hipótesis, sin demostrar:** después de una perturbación de tiempo real, algún repositorio de slot de subida queda ocupado. Un repositorio inválido no prueba, por sí solo, que se pierda para siempre: falta leer su implementación.
- **Lectura del código:** la hizo Claude con el fuente bajado de GitLab. Codex no pudo acceder para confirmarla.
- **Consecuencias:**
  - la celda se degrada mientras dura la corrida;
  - la tercera bajada (42 Mbit/s, contra ~54) coincidió en parte con la aparición de las fallas, sin que eso pruebe causalidad;
  - el ping tuvo 22 % de pérdida con "UL busy" activo.
- **Hay que medir con la celda recién arrancada** y reducir las ráfagas: cerrar Brave y usar el governor `performance`.

## DFT-s-OFDM
- **Verificado en OCUDU** (`apps/units/flexible_o_du/o_du_high/du_high/du_high_config_translators.cpp`):
  - L784: `pusch: enable_transform_precoding` activa `rach_cfg.msg3_transform_precoder`;
  - L888: también activa `transform_precoding_enabled` en el PUSCH dedicado;
  - L894-898: fija el PUSCH en 1 capa.
- **La tabla de MCS no cambia** (`mcs_table`). No se verificó qué tabla de TS 38.214 §6.1.4.1 usa con transform precoding.
- **Los dos teléfonos entraron con Msg3 en DFT-s-OFDM.** El scheduler usó casi todo 256QAM.
- **La consulta a Gemini falló:** agy cortó a los 15 min sin salida y no se reintentó. Quedan sin verificar la restricción de PRB 2^a·3^b·5^c y los problemas conocidos con COTS.
- **Configuraciones:**

  | Rol | Archivo |
  | :--- | :--- |
  | A | `gnb_b210_00101_csiper_ppm0_kos_sinmetricas.yml` |
  | B | `gnb_b210_00101_csiper_ppm0_kos_sinmetricas_dfts.yml` |

  Las armó Codex y las verificó Claude: en `_dfts` solo cambia la línea de transform precoding. Las variantes sin métricas son idénticas a las de 981c456, salvo el comentario.

## Otras cosas
- **El proyecto volvió a tachoPC.**
  - Se copiaron los 36 logs del 2026-11-03 desde la PC de Santi, con el sha256 verificado.
  - Las imágenes `5g-gnb-radio` y `5g-open5gs` tienen el mismo ID en las dos PC.
  - `5g-dashboard` se construyó en las dos.
- **El governor de tachoPC estaba en `powersave`.** El usuario lo puso en `performance` con sudo antes de la corrida. Se pierde al reiniciar.
- **CP-OFDM o DFT-s-OFDM:** hasta hoy todas las configuraciones usaban CP-OFDM en la subida (`enable_transform_precoding: false`). La bajada es siempre CP-OFDM.

## Trabajo de las otras IAs
- **Codex:**
  - `revisiones/2026-11-03_codex-dashboard-entrega.md`;
  - `revisiones/2026-11-03_codex-panel-compat-entrega.md`;
  - `revisiones/2026-11-03_codex-sinmetricas-entrega.md`;
  - `revisiones/2026-11-03_codex-dfts-entrega.md`;
  - revisión de esta sesión: `revisiones/2026-11-03_codex-revision-dfts-ulbusy.md`.
- **Gemini:** la consulta sobre DFT-s-OFDM no devolvió nada (timeout de agy).

## Revisión de Codex
`revisiones/2026-11-03_codex-revision-dfts-ulbusy.md`. No encontró nada bloqueante. Las correcciones ya están incorporadas:
- **CSV:** usaban coma decimal y tenían la cabecera al final.
- **Conclusiones:** las de DFT-s-OFDM, A1 y "UL busy" estaban sobredimensionadas.
- **Horas de iperf3:** eran de fin de prueba, no de inicio.
- **Extractos del núcleo:** mezclaban corridas.
- **Desvío de A2:** era 1,18, no 1,19.

Verificó contra los logs completos los totales, las primeras "UL busy" y los promedios.

## Errores de esta sesión
- **Se culpó a las métricas** de "UL processor is busy" con una sola comparación entre corridas distintas. La corrida sin métricas en tachoPC mostró que no son necesarias.
- **Se sobredimensionaron las conclusiones** de DFT-s-OFDM y de "UL busy". Codex las corrigió.
- **El servidor de iperf3 se apagó** al recrear el dashboard, y la primera prueba del tramo B falló con "unable to connect".
- **La app de iperf3 usó 10 s en lugar de los 30 s pedidos.** No se hizo la bajada en A1 ni en B, así que no se pueden comparar las formas de onda en la bajada (por otra parte, la bajada es siempre CP-OFDM).
- **El ping del usuario no llegó al dashboard:** no hubo POST a `/api/ping`. Se hizo desde la API, cuando la celda ya estaba degradada.

## Para retomar
1. **Ping y latencia con la celda limpia:** 60 s cada 0,2-0,5 s, con la celda recién arrancada. Repetir la bajada con `-R`, 3 × 10 s.
2. **"UL processor is busy":**
   - leer en OCUDU cómo se liberan los repositorios de slot de subida (`uplink_pdu_slot_repository`, `slot_controller_mngr`) y qué se puede ajustar (`expert_phy`, hilos, `max_request_headroom_slots`);
   - cerrar Brave durante las corridas.
3. **DFT-s-OFDM, si se quiere una conclusión firme:** repetir en bloques con los dos órdenes (ABAB / BABA), con la posición fija, un solo UE, el mismo tiempo desde el arranque y el PHR registrado.
4. **Dashboard** (necesita ok):
   - que inicie el servidor de iperf3 al arrancar;
   - guardar en disco los resultados de iperf3 y de ping;
   - revisar por qué el botón de ping no envió el pedido.
5. **Siguen abiertos:** P-003 (voz IMS) y P-005 (OnePlus en `NR only`). P-004 (tiempo real) ahora vale para las dos PC.
