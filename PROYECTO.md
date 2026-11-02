# Proyecto: celda 5G NR SA con USRP B210

*Memoria entre sesiones. Solo la edita Claude. Última actualización: 2026-11-02.*

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

## A definir (lo decide el usuario)
1. **Entorno de RF:** definido: jaula de Faraday (2026-10-30). Falta confirmar que la B210 esté adentro antes de cada transmisión.
2. **Celulares:** definidos: OnePlus 13, Motorola Edge 30, Xiaomi Redmi Note 14 5G. Falta confirmar sus bandas SA.
3. **Entregable:** por ahora sin formato ni fecha.
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
| D-010 | 2026-11-02 | Configuración activa de prueba: `gnb_b210_00101_csiaper.yml` (CSI aperiódico, tx_gain 80, clock_ppm −1,87) | Con CSI periódico el gNB corta a los 3 s por CSI sin decodificar. Sin CSI-RS hubo más reconexiones. No es la configuración final | Claude, aprobó usuario |

## Propuestas pendientes de decisión
| ID | Propuesta | Justificación | Falta verificar |
| :--- | :--- | :--- | :--- |
| P-001 | Empezar por **n78 TDD, 20 MHz, μ=1, 51 PRB**, con UL DFT-s-OFDM como objetivo a validar | Es la única configuración con la que un celular comercial llegó al AMF. Numerología: TS 38.211 §4.2-4.3; SSB: TS 38.213 §4.1; precodificación: TS 38.211 §6.3.1.4 | Bandas SA de los celulares. Contradice el diseño n3 FDD del diagrama: cambia lo que se defiende ante el profesor |
| P-002 | Definir la **frecuencia** recién con el entorno de RF elegido | 3489,42 MHz cae en el bloque de Personal y atrajo celulares ajenos | Bloques adjudicados, barrido en recepción |

## Riesgos
- **RF, criterio de los docentes (informado por el usuario, 2026-10-30):** la jaula puede dejar pasar señales de una torre cercana, y consideran que no llegaría a la población por la jaula, la lejanía del laboratorio de zonas urbanas, la baja potencia de la SDR y la poca ganancia de las antenas. Por eso ver señal comercial no prueba que la jaula esté abierta. No se puede comparar adentro y afuera: la jaula es del laboratorio y no se pueden abrir las puertas para probar, así que su atenuación queda sin medir y el barrido de hoy es solo la línea de base dentro de la jaula.
- **RF:** ambas bandas están licenciadas. En pruebas previas, celulares de Personal intentaron registrarse en la celda, así que la señal salía del laboratorio. No se transmite hasta definir el entorno.
- **SIM:** **una LY14 sin DF_5GS se registró en SA el 2026-10-30 en el Redmi, lo que refuta la causa raíz del docx. El Motorola la ignora con esa SIM, lo que apoya la hipótesis del perfil de módem.** Antes, las tarjetas LY14 sin DF_5GS ni servicios 5G en EF_UST no habían buscado la celda. El docx de antecedente lo da por causa raíz, pero también sigue abierto el perfil del módem para un PLMN desconocido. Hay que verificar en TS 31.102 y TS 33.501 si esos servicios son realmente obligatorios.
- **CPU:** 2 núcleos a 20 MHz pueden no alcanzar. El host tiene el governor en `powersave` y buffers bajos, y cambiarlos requiere aprobación.

## Antecedentes (no reutilizados, a reverificar)
Según `Prueba_configuracion_Drive_5G.docx` (29/10): ZMQ + srsUE funcionó de punta a punta; por aire en n78 un celular de Personal llegó al AMF; n3 no tuvo ningún PRACH real; DFT-s-OFDM y NEA2 quedaron sin validar con celular; B210 serie 31677B2 con `clock_ppm` −1,87 medido.

## Estado actual
**Camino completo logrado el 2026-11-02 con PLMN 001/01:** registro, sesión PDU, IP y navegación por NAT en un Redmi Note 14 5G y sesión con IP en un OnePlus 13, con la celda n78 TDD en Docker. **La conexión no es estable todavía:** se corta cada pocos segundos o decenas de segundos, por lo que aún no se puede medir throughput, latencia ni jitter.

Lo que se sabe de los cortes: el teléfono deja de usar los permisos de PUSCH (SINR cerca de ruido) aunque sus SR llegan, y los PDSCH quedan sin ACK; hay errores de bajada aun en MCS bajos. Eso apunta a la bajada, sin causa confirmada. Saturación por `tx_gain` bastante descartada (60 no mejoró). Pendientes: reloj (`clock_ppm` 0 quedó sin concluir: corrida de 2 min con poco tráfico). También hubo fallas de tiempo real sostenidas que no se recuperan sin reiniciar el gNB, coincidentes con abrir un navegador en la PC, y una caída USB de la B210 sin causa conocida. La celda queda apagada.

## Próximos pasos
Ver la sección "Para retomar" de `sesiones/2026-11-02_sim-001-01-y-datos.md`.
