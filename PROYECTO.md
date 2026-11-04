# Proyecto: celda 5G NR SA con USRP B210

*Memoria entre sesiones. Solo la edita Claude. Última actualización: 2026-11-04.*

## Objetivo
Desplegar desde cero una celda 5G NR Standalone (Opción 2, Release 15) en un entorno de RF autorizado o controlado, y lograr que un celular con SIM de laboratorio se registre, obtenga IP y navegue. Después, medir throughput, latencia y jitter y compararlos con 2G (EDGE) y 4G (LTE) del mismo grupo.

## Alcance
- Radio USRP B210 por USB 3.0, gNB OCUDU/srsRAN Project, núcleo Open5GS v2.8.0 + MongoDB, NAT del kernel Linux, PLMN 722/999.
- La implementación va dentro de Docker, por consigna de los docentes.
- Antes de implementar cualquier cosa se le pregunta al usuario.
- Cada decisión se justifica con teoría y especificaciones (TS 38.211, 38.213, 38.321, 38.331).
- Cada etapa se cierra con evidencia: sincronización, acceso, registro, sesión PDU, tráfico IP y mediciones.
- Nada de `~/red5g` se reutiliza: sus resultados son solo antecedente.

## Entorno (relevado 2026-10-30, `tachoPC`)
| Ítem | Valor |
| :--- | :--- |
| Sistema | Debian 13 (trixie), kernel 6.12.113 |
| CPU / RAM / disco | Intel i3-1005G1 (2C/4T, AVX2 y AVX-512) / 7,3 GiB / 86 GB libres |
| USRP B210 | Serie 31677B2, rev. 4, FW 8.0, FPGA 16.0, sin GPSDO. **USB 3.0 confirmado** (5000 Mb/s) tras cargar firmware con `uhd_usrp_probe`, sin transmitir. Aparece en USB 2.0 (`Cypress WestBridge`) hasta cargarlo; hay que repetirlo tras cada desconexión |
| UHD | 4.8.0 instalado (`uhd-host`, paquete Debian) |
| Instalados | docker, git, pcscd, pcsc-tools |
| No instalados | Open5GS, MongoDB, gNB, tmux, iperf3, tshark |
| Ajustes del host | governor `powersave`; `wmem_max` 1 MB y `rmem_max` 50 MB; `ip_forward` = 1 |
| Docker | Contenedores 4G detenidos (`srsran-4g`, `srsran_4g`) |
| `~/red5g` | **No existe en esta PC**: está en la PC de un compañero |

## Entorno 2: PC de Santi (desde 2026-11-03)
Acceso por SSH, con contraseña (usuario e IP en `CONTEXTO_ANTECEDENTES.local.md`, fuera del repo). **La contraseña no va en el repo: la da el usuario.** Ubuntu, kernel 6.14, 12 hilos con AVX2 y 60 GiB de RAM. Proyecto en `~/Descargas/Moviles/5G/red5g-docker`, con `screen` instalado. Claude puede leer por SSH, pero Claude Code le bloquea arrancar la celda allá: `start.sh` y `stop.sh` los corren las personas en esa PC. **Santi tiene su propio `srsran-5g`, con `restart: unless-stopped` y acceso al USB: si se levanta, compite por la B210.** Detalle en `sesiones/2026-11-03_pc-santi.md`.

## A definir (lo decide el usuario)
1. **Entorno de RF:** definido: jaula de Faraday (2026-10-30). Falta confirmar que la B210 esté adentro antes de cada transmisión.
2. **Celulares:** definidos: OnePlus 13, Motorola Edge 30, Xiaomi Redmi Note 14 5G. Falta confirmar sus bandas SA.
3. **Entregable:** informe final en LaTeX/PDF (`informe/informe_final.pdf`), redactado el 2026-11-04 a partir de `informe/prompt_informe_final.md`. Fecha de entrega sin definir.
4. **SIM:** se usan las que hay; falta leerlas (el usuario las conecta al lector). Ver Riesgos.
5. **Acceso a `~/red5g`:** copia de solo lectura, si se quiere consultar más allá del docx.

## SIM leídas (solo lectura, con `scripts/leer_sim.py`)
| Fecha | ICCID | IMSI | MNC en EF_AD | AcT 722/999 | 5G |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-10-30 | …0010 | 722999000000001 | 3 dígitos | E-UTRAN, UTRAN, GSM; sin NG-RAN | Sin DF_5GS, EF_UST de 11 bytes |
| 2026-10-30 | <ICCID> | 722999000000003 | 3 dígitos | E-UTRAN, UTRAN, GSM; sin NG-RAN | Sin DF_5GS, EF_UST de 11 bytes. **Regrabada el 2026-11-02, ver abajo** |

Estado al 2026-11-02 (K/OPc confirmadas por AUTHENTICATE en SIM 3 y SIM 4; ADM en ref. `0x0C` aceptada en ambas; copias previas en `evidencia/sim/`):

| SIM | ICCID | IMSI | PLMN | AcT | Abonado | Uso |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| SIM 1 | …0010 | 722999000000001 | 722/999 | Sin NG-RAN | Cargado | Referencia, sin tocar |
| SIM 3 | …0374 | 001010000000003 | 001/01 | NG-RAN + E-UTRAN | Cargado | Redmi |
| SIM 4 | …0044 | 001010000000004 | 001/01 | NG-RAN + E-UTRAN | Cargado | OnePlus 13. Grabada con OYEI en Windows, luego por APDU |

## Versiones
| Componente | Versión | Estado |
| :--- | :--- | :--- |
| Open5GS | v2.8.0 | Fijada por el proyecto |
| UHD | 4.8.0 en el host; 4.9.0.1 en el Dockerfile oficial de OCUDU | Propuesta: usar la del contenedor. Probado en el host solo para cargar firmware |
| OCUDU (ex srsRAN Project) | `release_26_10` (`e0db566`) | Propuesta, sin decidir: tag oficial más reciente. "OCUDU 26.10" es este tag; "OCUDU 2.10" no existe. Ver `investigacion/2026-10-30_verificacion-claude.md` |

## Decisiones
| ID | Fecha | Decisión | Justificación | Aportó |
| :--- | :--- | :--- | :--- | :--- |
| D-001 | 2026-10-30 | El repo git es solo local y versiona lo nuevo más los documentos propios sin claves de la raíz (`Diagramas_UL_DL_Paging_5G.{md,html}`, `DFT-s-OFDM_explicacion.html`, `generar_html.py`). El resto del material previo, `.env` y `CONTEXTO_ANTECEDENTES.local.md` quedan excluidos | Varios contienen claves de SIM; también son pesados o de terceros. Sin referencia a TS: decisión de organización | Claude |
| D-002 | 2026-10-30 | Implementación en Docker | Consigna de los docentes. Sin referencia a TS | Usuario |
| D-003 | 2026-10-30 | Preguntar antes de implementar, siempre | Pedido del usuario. Sin referencia a TS | Usuario |
| D-004 | 2026-10-30 | La prueba sin radio usa n3 FDD, 20 MHz, 106 PRB, μ=0, CP-OFDM en UL. No fija la banda de radio | srsUE rechaza SCS común distinto de 15 kHz (`rrc_nr_procedures.cc:439`), así que n78 μ=1 no se puede probar por ZMQ. Numerología: TS 38.211 §4.2 | Codex, revisó Claude |
| D-006 | 2026-10-30 | Primera celda: n78 TDD, ARFCN 635000 (3525 MHz), 20 MHz, μ=1, CP-OFDM en UL, TX/RX 50/40 | Fuera del bloque atribuido a Personal; barrido sin portadoras visibles (no concluyente en señales débiles). CP-OFDM primero para cambiar una sola cosa. Numerología: TS 38.211 §4.2; SSB caso C: TS 38.213 §4.1 | Claude, Codex |
| D-005 | 2026-10-30 | Se abandona la prueba con srsUE; se pasa a la celda real con celulares. Los servicios `gnb-zmq` y `srsue` quedan en el compose, sin usar | Tres corridas bloqueadas antes de la búsqueda de celda, sin causa identificada. El objetivo son celulares reales. Sin referencia a TS | Usuario, a propuesta de Claude |
| D-007 | 2026-11-02 | NG-RAN y PLMN se graban por APDU desde Linux (`scripts/grabar_ng_ran.py`, `grabar_plmn.py`). K y OPc solo con OYEI en Windows | Los archivos usan UPDATE BINARY con ADM (TS 31.102 §4.2.5, §4.2.53, §4.2.54). El Ki LTE usa un comando propietario | Claude, revisó Codex |
| D-008 | 2026-11-02 | Para las pruebas con celulares se usa PLMN 001/01 en vez de 722/999. **Se aparta de lo fijado en Alcance; hay que justificarlo en el informe** | Con 722/999 el Redmi y el Motorola no generaron PRACH con NG-RAN grabado. Con 001/01 el Redmi registró al primer intento y el OnePlus también. No se identificó por qué el módem los trata distinto | Claude, aprobó usuario |
| D-009 | 2026-11-02 | Consola de control con `start.sh`, `stop.sh` y GNU screen, 4 paneles | Pedido del usuario. `screen` ya estaba instalado; `tmux` no. Sin referencia a TS | Usuario, revisó Codex |
| D-011 | 2026-11-03 | Se sigue en la PC de Santi. Prueba con log reducido: `gnb_b210_00101_csiaper_logw.yml` (`all_level: warning`; MAC, RRC y NGAP en `info`) | El i3 con 7 GiB tenía swap y fallas de tiempo real. El log en `info` escribía unos 3 MB por minuto, y la mitad era PHY. Sin referencia a TS | Usuario, Claude. Sin revisión de Codex |
| D-010 | 2026-11-02 | Configuración activa de prueba: `gnb_b210_00101_csiaper.yml` (CSI aperiódico, tx_gain 80, clock_ppm −1,87) | Con CSI periódico el gNB corta a los 3 s por CSI sin decodificar. Sin CSI-RS hubo más reconexiones. No es la configuración final | Claude, aprobó usuario |
| D-012 | 2026-11-03 | `clock_ppm: 0` en vez de −1,87 | En OCUDU `release_26_10`, `clock_ppm` corrige solo la portadora y no el muestreo (`ru_sdr_config_translator.cpp`). Con −1,87 el gNB pide TA positivos sin parar (+2,2 a +3,8 pasos/s, paso 0,26 µs, TS 38.213 §4.2) y las conexiones duran 3-10 s; con 0, ~0 pasos/s y ~60 s. El ejemplo oficial para B210 sin reloj externo usa 0. Ver `investigacion/2026-11-03_analisis-cortes-claude.md` | Claude, revisó Codex, aprobó usuario |
| D-013 | 2026-11-03 | `start.sh` recibe la configuración como argumento, verifica el montaje y ya no pide `si` | `GNB_CONFIG` no llegó en 5 arranques. El usuario pidió quitar la confirmación: quien lo ejecuta ya decidió transmitir. Sin referencia a TS | Usuario, Codex, Claude |
| D-014 | 2026-11-03 | Con el Redmi, CSI periódico con `pucch.max_consecutive_kos: 100000` | El Redmi no envía CSI ni aperiódico (0 PUSCH OK de ~10 000 con pedido de CSI) ni periódico (~0,4 % de F2 decodificados). El OnePlus sí. Con el umbral alto, el CSI faltante no dispara RLF | Claude, aprobó usuario |
| D-015 | 2026-11-03 | **Mitigación provisoria:** en las pruebas, el Redmi va con **VoLTE activado y tipo de red `NR only`** (`*#*#4636#*#*` → Información del teléfono). Es un arreglo del lado del teléfono, no de la red | **Lo observado:** en n3, el Redmi tuvo 5 pérdidas de servicio entre 59,991 y 60,022 s después de obtener servicio (`+CIEV: 3,1` → `3,0`). En los extractos no hay una liberación previa de la red, y después escanea LTE comercial. Con `NR only` superó ese patrón: 338,7 s en n3 (terminó por RLF "RLC max ReTxs") y 345,3 s en n78 (sin RLF hasta parar el gNB). **Hipótesis principal, sin demostrar:** recuperación de voz/IMS. Open5GS v2.8.0 anuncia IMS VoPS = 1 fijo (`src/amf/gmm-build.c` L113-118) y no hay IMS. TS 24.501 V15.7.0 §4.3.2 y §4.9.2 prevén que un UE *voice centric* sin voz en un plazo definido por el fabricante deshabilite N1 y busque E-UTRA. **Falta verificar:** el *usage setting* del Redmi, el temporizador interno y si el OnePlus (cortes a ~35-37 s del registro) responde a la misma causa. `NR only` también bloquea otras políticas de selección de RAT, así que su éxito no distingue entre ellas. Revisión: `revisiones/2026-11-03_codex-conclusion-voz.md` | Claude, propuesta de Gemini (`NR only`), revisó Codex, aprobó usuario |
| D-016 | 2026-11-03 | Dashboard web en el contenedor `dashboard` (`127.0.0.1:8080`): `index.html` del panel del compañero con backend propio (FastAPI). La web no arranca ni frena la red, no usa sudo ni el socket de Docker y no muestra datos simulados | Pedido del usuario. El `server.py` del compañero se descartó: salteaba `start.sh`, usaba `sudo -n docker`, permitía inyectar código y mezclaba los UEs. Sin referencia a TS | Usuario, Codex (código), Claude (revisión) |
| D-017 | 2026-11-03 | En la subida se mantiene **CP-OFDM de forma provisoria**. DFT-s-OFDM funciona con los dos teléfonos (`gnb_b210_00101_csiper_ppm0_kos_sinmetricas_dfts.yml`), pero no se usa por defecto | A/B/A en tachoPC (una corrida por tramo): 8,7 / 12,7 / 14,8 Mbit/s de subida TCP. **No hay evidencia suficiente para adoptarlo por rendimiento.** A1 tuvo otras condiciones de enlace: SINR media de ~19 dB, contra ~27 dB en B y A2. Que la reducción de PAPR (TS 38.211 §6.3.1.4) no aporte porque el UE no está limitado en potencia es una hipótesis: no se midió el PHR. En OCUDU, `enable_transform_precoding` también activa `msg3_transform_precoder` y fija 1 capa (`du_high_config_translators.cpp` L784 y L888-898). Detalle: `evidencia/06_mediciones/` | Claude, aprobó usuario |

## Propuestas pendientes de decisión
| ID | Propuesta | Justificación | Falta verificar |
| :--- | :--- | :--- | :--- |
| P-001 | Empezar por **n78 TDD, 20 MHz, μ=1, 51 PRB**, con UL DFT-s-OFDM como objetivo a validar | Es la única configuración con la que un celular comercial llegó al AMF. Numerología: TS 38.211 §4.2-4.3; SSB: TS 38.213 §4.1; precodificación: TS 38.211 §6.3.1.4 | Bandas SA de los celulares. Contradice el diseño n3 FDD del diagrama: cambia lo que se defiende ante el profesor |
| P-002 | Definir la **frecuencia** recién con el entorno de RF elegido | 3489,42 MHz cae en el bloque de Personal y atrajo celulares ajenos | Bloques adjudicados, barrido en recepción |
| P-003 | Confirmar la hipótesis de la voz y, si se confirma, resolverla del lado de la red: (0) prueba A/B/A cambiando solo el Redmi a *data centric* con LTE permitido, si el firmware lo deja; (b) A/B/A con IMS VoPS 1→0→1 en una imagen de prueba de Open5GS, verificando el NAS transmitido; (a) IMS en Docker (Kamailio + PyHSS) más la DNN `ims` | La hipótesis principal de D-015 no está demostrada (revisión de Codex). Una salida que se adelanta o se atrasa de forma reproducible apoyaría la intervención del subsistema de voz | Si existe el ajuste *data centric*; esfuerzo de (a); (b) requiere reconstruir la imagen |
| P-004 | Tiempo real, en las dos PC: cerrar Brave y Spotify durante las corridas, governor `performance` (en tachoPC ya se puso con sudo el 2026-11-03; se pierde al reiniciar) y revisar buffers USB y de red. Investigar en OCUDU por qué **"UL processor is busy"**, una vez que aparece, persiste hasta el final de la corrida | Ese mismo día: en la PC de Santi, a las 20:40, la subida quedó trabada (0 PUSCH y 0 PUCCH en 2 min). Por la noche, en tachoPC y **sin métricas**, "UL busy" apareció en 2 de 3 corridas después de perturbaciones de tiempo real, persistió hasta el final y su tasa varió con el tráfico (10-60 por segundo). En B hubo ráfagas y no apareció. En `fapi_to_phy_fastpath_translator.cpp`, la falla aparece cuando el repositorio de PDU del slot sigue ocupado. Con "UL busy" activo, el ping tuvo 22 % de pérdida. La aparición coincidió en parte con una bajada de 42 Mbit/s, contra ~54 en las anteriores | En la PC de Santi, sudo requiere el permiso de Santi |
| P-005 | `NR only` en el OnePlus por `adb shell am start -n com.android.phone/.settings.RadioInfo` | OxygenOS bloquea `*#*#4636#*#*`. En n78, el OnePlus tuvo RLF a los 37,4 y 35,2 s del registro. Pide la DNN `ims` y se la rechazan, pero no está probado que esa sea la causa | Depuración USB en el OnePlus |

## Riesgos
- **RF, criterio de los docentes (informado por el usuario, 2026-10-30):** la jaula puede dejar pasar señales de una torre cercana, y consideran que no llegaría a la población por la jaula, la lejanía del laboratorio de zonas urbanas, la baja potencia de la SDR y la poca ganancia de las antenas. Por eso ver señal comercial no prueba que la jaula esté abierta. No se puede comparar adentro y afuera: la jaula es del laboratorio y no se pueden abrir las puertas para probar, así que su atenuación queda sin medir y el barrido de hoy es solo la línea de base dentro de la jaula.
- **RF:** ambas bandas están licenciadas. En pruebas previas, celulares de Personal intentaron registrarse en la celda, así que la señal salía del laboratorio. No se transmite hasta definir el entorno.
- **SIM:** **una LY14 sin DF_5GS se registró en SA el 2026-10-30 en el Redmi, lo que refuta la causa raíz del docx. El Motorola la ignora con esa SIM, lo que apoya la hipótesis del perfil de módem.** Antes, las tarjetas LY14 sin DF_5GS ni servicios 5G en EF_UST no habían buscado la celda. El docx de antecedente lo da por causa raíz, pero también sigue abierto el perfil del módem para un PLMN desconocido. Hay que verificar en TS 31.102 y TS 33.501 si esos servicios son realmente obligatorios.
- **CPU:** ~~2 núcleos a 20 MHz pueden no alcanzar~~. **Descartada como causa principal el 2026-11-03:** en la PC de Santi (12 hilos) el gNB usa ~110 % sobre 1200 % y los cortes son iguales. **Pero el tiempo real sigue siendo un riesgo:** en una corrida n3 el procesador de UL se trabó y la celda dejó de aceptar UEs (P-004). Con Brave y Spotify abiertos hubo de 1300 a 36 000 fallas por corrida. En tachoPC, con 4 hilos y sin métricas, "UL processor is busy" apareció después de perturbaciones de tiempo real y persistió (P-004).
- **Jaula:** desde adentro, el Redmi ve celdas LTE comerciales (B2, B4, B5, B7 y B28; PLMN 722-310 en el MDLog) y la PC mantiene el WiFi. Confirma que la atenuación es limitada.

## Antecedentes (no reutilizados, a reverificar)
Según `Prueba_configuracion_Drive_5G.docx` (29/10): ZMQ + srsUE funcionó de punta a punta; por aire en n78 un celular de Personal llegó al AMF; n3 no tuvo ningún PRACH real; DFT-s-OFDM y NEA2 quedaron sin validar con celular; B210 serie 31677B2 con `clock_ppm` −1,87 medido.

## Estado actual
**Camino completo logrado el 2026-11-02 con PLMN 001/01:** registro, sesión PDU, IP y navegación por NAT en un Redmi Note 14 5G y sesión con IP en un OnePlus 13, con la celda n78 TDD en Docker. **La conexión no es estable todavía:** se corta cada pocos segundos o decenas de segundos, por lo que aún no se puede medir throughput, latencia ni jitter.

**2026-11-03:** el proyecto quedó instalado en la PC de Santi, con la B210 en USB 3. Con la misma configuración, **el patrón de cortes es igual:** unas 130 transmisiones de bajada por minuto agotan los 4 reintentos HARQ, hay unas 80 fallas de tiempo real (`late` y `underflow`) por minuto y unas 2 RLF por minuto, por CRC o HARQ-ACK. Todo eso con la CPU casi libre. La bajada falla más seguido que lo que explica el tiempo real, y eso apunta a la radio o a la sincronización. **La prueba con log reducido sigue pendiente:** en 3 intentos el gNB arrancó con la configuración vieja, porque `GNB_CONFIG` no llegó a `start.sh`. La celda quedó apagada al cerrar la sesión: `stop.sh` corrió a las 18:43 UTC y se verificó por SSH.

**2026-11-03, tarde:**
- **El corte de los ~60 s quedó mitigado del lado del teléfono (D-015).** `clock_ppm 0` (D-012) llevó las conexiones de 3-10 s a ~60 s, y el kos alto (D-014) quitó las RLF por CSI.
- Lo que quedaba lo inicia el teléfono: con `adb logcat` se vio que el módem del Redmi pierde servicio a los 59,99-60,02 s (5 ciclos en n3), sin una liberación previa de la red, y después busca LTE. **La hipótesis principal es la voz IMS** (anunciada, pero inexistente); falta confirmarla (P-003).
- Con `NR only`, el Redmi duró 5 min 39 s en n3 y 5 min 45 s en n78.
- **n3 FDD funciona por primera vez** (`gnb_b210_00101_n3_ppm0_kos.yml`).
- Pendientes:
  - el OnePlus sin `NR only` (P-005);
  - el tiempo real en la PC de Santi (P-004);
  - la solución de red (P-003);
  - las mediciones de throughput, latencia y jitter, que ya se pueden intentar.

**2026-11-03, noche (tachoPC):**
- **Dashboard en `http://localhost:8080`** (D-016).
- **Primeras mediciones** (n78 TDD, Redmi en `NR only`; configuración `..._sinmetricas.yml`):
  - subida TCP de ~14,8 Mbit/s;
  - bajada TCP de ~54 Mbit/s;
  - RTT mínimo y mediano de 17 y 28 ms, medidos con la celda ya degradada.
- **DFT-s-OFDM funciona con los dos teléfonos.** La prueba A/B/A no da evidencia para adoptarlo por rendimiento (D-017).
- **"UL processor is busy" también aparece sin las métricas JSON:** no son una condición necesaria, y su contribución no se determinó. Aparece después de perturbaciones de tiempo real y persiste (P-004). Hay que medir con la celda recién arrancada. Revisión: `revisiones/2026-11-03_codex-revision-dfts-ulbusy.md`.

**2026-11-04: informe final.**
- `informe/informe_final.pdf` (45 páginas, LaTeX en `informe/secciones/`, figuras con `informe/figuras/generar_figuras.py`).
- Revisado por Codex (`revisiones/2026-11-04_codex-revision-informe.md`, 29 hallazgos, ninguno crítico). Se integraron casi todos. Codex se equivocó en el reparto del rate matching: son 6 CB de 8392 bits y 1 de 8400.
- **Errores del prompt corregidos con la evidencia:**
  - en n3 con `NR only`, la sesión terminó por RLF a los 338,7 s, no al detener el gNB;
  - la bajada TCP es la tasa del emisor;
  - K/OPc se grabaron con OYEI, no por APDU.
- **Verificado en TS 38.211:** `prach-ConfigurationIndex` 159 = formato B4, subtrama 9 (slot 19). El alcance geométrico del PRACH es de ~2 km.
- **Hipótesis nueva para P-004:** con `zeroCorrelationZoneConfig` 0, los 64 preámbulos salen de 64 raíces ZC, y eso podría cargar el slot 19. Se prueba subiendo ese parámetro.
- Quedan 13 citas marcadas [verificar], de TS que no están en el proyecto, y la tabla EDGE/LTE para completar.

## Punto de retorno TDD (2026-11-03)
Mejor configuración n78 TDD hasta hoy: **`config/gnb/gnb_b210_00101_csiper_ppm0_kos.yml`** (n78, ARFCN 635000, 20 MHz, μ=1, PLMN 00101, tx 80, `clock_ppm 0`, CSI periódico con `pucch.max_consecutive_kos 100000`). El corte de cada ~60 s se evita con el teléfono en `NR only` (D-015): el Redmi duró 5 min 45 s el 2026-11-03, sin RLF hasta parar el gNB. Variantes: `_csiaper_ppm0.yml` (CSI aperiódico, el valor por defecto de `start.sh`) y `_csiper_ppm0.yml`. Etiqueta git: **`tdd-ppm0-2026-11-03`**. Para volver: `./start.sh gnb_b210_00101_csiper_ppm0_kos.yml`. Las pruebas en n3 FDD van en archivos aparte y no tocan estos.

## Próximos pasos
Ver la sección "Para retomar" de `sesiones/2026-11-04_informe-final.md` y de `sesiones/2026-11-03_dashboard-dfts.md`. Siguen vigentes los puntos abiertos de `sesiones/2026-11-03_cortes-60s-volte.md` (voz IMS, OnePlus).
