# Sesión 2026-11-03 (tarde): causa de los cortes, n3 FDD y el corte de los 60 s

## Resultado
**El corte de cada ~60 s lo inicia el teléfono, y quedó mitigado poniendo el Redmi en `NR only`:** duró 5 min 39 s en n3 FDD y 5 min 45 s en n78 TDD. **La hipótesis principal sobre la causa es la voz:** Open5GS anuncia IMS, pero no tenemos; el teléfono esperaría la voz y, al no conseguirla, dejaría la celda para buscar LTE. Es la explicación más consistente, pero **no está demostrada** (revisión de Codex, `revisiones/2026-11-03_codex-conclusion-voz.md`). En el camino:
- `clock_ppm 0` llevó las conexiones de 3-10 s a ~60 s;
- el kos alto quitó las RLF por CSI;
- **n3 FDD funcionó por primera vez**.

Toda la tarde la celda corrió en la PC de Santi. `start.sh` y `stop.sh` los corrieron las personas; Claude solo leyó logs por SSH.

## Cadena de pruebas
Horas en UTC. Teléfono: Redmi Note 14 5G (SIM …003), salvo que se indique otra cosa.

| # | Configuración | Resultado |
| :--- | :--- | :--- |
| 1 | `_csiaper.yml` (`clock_ppm −1,87`) | Línea de base: el gNB pide TA positivos sin parar (+2,2 a +3,8 pasos/s). Conexiones de 3-10 s |
| 2 | `_csiaper_ppm0.yml` | TA ~0 pasos/s; conexiones de **~60 s** (D-012) |
| 3 | `_csiper_ppm0.yml` | El Redmi no manda CSI periódico (~0,4 % de F2 decodificados) |
| 4 | `_csiper_ppm0_kos.yml` | Sin RLF por CSI; **sigue el corte de ~60 s** (D-014). Queda como punto de retorno TDD, etiqueta `tdd-ppm0-2026-11-03` |
| 5 | `_n3_ppm0_kos.yml` (n3 FDD, ARFCN 368500) | **Primer acceso real en n3.** Cortes a 64,1 s y 61,3 s del UE creado: el corte no depende de banda, duplexación ni numerología |
| 6 | n3 + `adb logcat` en el Redmi | El módem pierde servicio a **60,004 / 59,991 / 60,016 s** de obtenerlo (`+CIEV: 3,0`), y la mayoría de las veces pasa a RRC idle (`+CSCON: 0`) 2-15 ms después; en el primer ciclo, 14,8 s después. En los extractos no hay `rrcRelease` previo ni eventos del núcleo. Después escanea LTE comercial (EARFCN 2450, 9360, 9485, 2225, 850, 950, 3050) y vuelve en 6-9 s con un Registration de movilidad |
| 7 | n3 + MDLog (DebugLoggerUI) + OnePlus | Redmi: **60,022 y 60,014 s**. En total, **5 ciclos en n3 entre 59,991 y 60,022 s**; otros dos pares completos (15,2 y 23,9 s) terminaron al parar la celda. OnePlus: pide la DNN `ims`, el núcleo la rechaza y se corta antes (~40 s) |
| 8 | n3 con VoLTE desactivado | Se registran, pero el Redmi tuvo RLF por CRC a 1,4 s del registro. El OnePlus siguió pidiendo `ims`. **Prueba confundida:** no está claro qué cambió efectivamente en cada teléfono |
| 9 | n3 + **Redmi en `NR only`** con VoLTE | **338,7 s (5 min 39 s) desde que se creó el UE.** Terminó por RLF "RLC max ReTxs" a las 20:40:22. El atasco masivo de UL se registra desde ~20:40:35, así que no está probado que lo haya causado |
| 10 | n78 TDD (`_csiper_ppm0_kos.yml`) + **Redmi en `NR only`** | **345,3 s (5 min 45 s) sin RLF** hasta parar el gNB (último PUSCH OK a las 20:51:48,7). Casi sin fallas de tiempo real (339). El OnePlus (sin `NR only`) tuvo RLF a 37,4 y 35,2 s del registro |

## Por qué la hipótesis principal es la voz (no demostrada)
- **El corte lo inicia el teléfono:** en los extractos del gNB y de Open5GS no hay `rrcRelease` previo ni un evento del núcleo que lo explique. Las liberaciones llegan después. Esto favorece una salida local del UE, pero no prueba que sea por la voz: una falla local de radio también podría producirla.
- **Parece un temporizador:** 5 ciclos entre 59,991 y 60,022 s, en n3 y medidos entre indicaciones AT. En n78 no hay logcat, así que la precisión solo está medida en n3.
- **Open5GS v2.8.0 anuncia "IMS voice over PS session supported" = 1 fijo en el código** (`src/amf/gmm-build.c`, líneas 113-118 del tag), sin opción en el YAML. Falta decodificar el Registration Accept real.
- **TS 24.501 V15.7.0 §4.3.2** (con §4.9.2) contempla que, aun anunciándose IMS, las capas superiores no indiquen voz en un plazo definido por el fabricante. Un UE *voice centric* en single-registration deshabilita entonces N1 y busca E-UTRA, con condiciones sobre las sesiones persistentes (verificado por Codex). No fija 60 s ni dice que todo teléfono sea *voice centric*. Encaja con el escaneo LTE observado.
- **La guía oficial de srsRAN para COTS UEs** (verificado con WebFetch) dice, para el Pixel 6: *"Requires disabled NR_TIMER_WAIT_IMS_REGISTRATION or SUPPORT_IMS_NR_REGISTRATION_TIMER"*. Para el iPhone 13 Pro: *"iPhones require IMS to be enable UE to stay connected."*
- Con `NR only` no tiene a dónde ir y se queda. Pero `NR only` también bloquea otras políticas de selección de RAT, así que su éxito no distingue la voz de otras causas. La prueba sin VoLTE no ayuda a decidir (ver la prueba 8).

**Descartados:** el `timeAlignmentTimer` (en OCUDU va de 500 ms a 10,24 s o infinito; no hay 60 s), T3512 (540 s), T3502, T3511, T3540 y T3346 (análisis de Gemini, coherente con TS 24.501 Tabla 10.2.1), y la búsqueda de HPLMN (TS 23.122: solo en VPLMN y en minutos).

## Tiempo real en la PC de Santi
- Con Brave y Spotify abiertos: de 1300 a 36 000 fallas de tiempo real por corrida.
- En la prueba 9, desde ~20:40:35, se acumularon miles de **`Real-time failure in FAPI: UL processor is busy`**: el gNB detectaba PRACH y mandaba RAR, pero procesó **0 PUSCH y 0 PUCCH en 2 minutos**; todo Msg3 se descartó por timeout y ningún teléfono pudo entrar. Se recupera reiniciando la celda.
- En la prueba 10 (TDD), casi sin fallas. Ver P-004.

## Herramientas en el Redmi
- **`adb`:** se instaló en tachoPC (`sudo apt install adb`, lo corrió el usuario). Búferes de logcat en 16 MiB. El enlace USB fue inestable: el dispositivo se reenumeró unas 90 veces y alternaba entre `unauthorized` y `closed`. Con cambio de cable y otro reinicio del servidor de `adb` volvió a andar.
- **EngineerMode de MediaTek (`*#*#3646633#*#*`)** → Log and Debugging → DebugLoggerUI → Modem Log. El registro queda en **`/data/debuglogger/mdlog1/`**, no en la memoria de usuario. Se bajó solo el MDLog (139 MB `.muxz` + MDDB); `netlog` y `mobilelog` no se tocaron, porque pueden tener datos personales. **El `.muxz` no se puede decodificar sin ELT de MediaTek**: solo se leen fragmentos. Quedó en el scratchpad, fuera del repo.
- `*#*#4636#*#*` sí funciona en el Redmi (HyperOS); en el OnePlus (OxygenOS) no.

## Evidencia
En `evidencia/04_sesion_pdu/`, archivos `2026-11-03_*`:
- extractos de eventos del gNB (UE, RRC, RLF, conteo de PRACH y de fallas de tiempo real) y del núcleo, por corrida;
- extracto del logcat de radio del Redmi (`+CIEV`, `+CSCON`, `+EPHYCONFIG`, `+EIMSESS`);
- log completo del gNB de la corrida TDD con `NR only`.

En los logs solo aparecen las SIM de laboratorio (…003 y …004): no hubo identificadores de terceros.

## Trabajo de las otras IAs
- **Codex:**
  - revisó el análisis de los cortes (`revisiones/2026-11-03_codex-analisis-cortes.md`);
  - generó las configuraciones `ppm0`, `csiper`, `kos` y n3 y el cambio de `start.sh` (`revisiones/2026-11-03_codex-*-entrega.md`).
- **Gemini:**
  - `investigacion/2026-11-03_gemini-clock-csi-rlf.md`;
  - `investigacion/2026-11-03_gemini-redmi-60s.md`. Propuso `NR only`, que resultó clave. Su cita principal (guía COTS de srsRAN) se verificó. **Las citas de issues de GitHub, Amarisoft y OAI no se verificaron.** Tampoco se verificaron sus códigos `*#*#8667#*#*` y `*#*#86583#*#*` ni el bloque `sib` propuesto para OCUDU.
- **Codex revisó D-015** (`revisiones/2026-11-03_codex-conclusion-voz.md`). Cuestionó que se presentara como causa demostrada, el "7 de 7", los tiempos del OnePlus y la prueba sin VoLTE, y precisó la sección de TS 24.501 y las líneas de Open5GS. Las correcciones están incorporadas.

## Errores de esta sesión
- Se lanzó tres veces la configuración equivocada por correr `./start.sh` sin argumento. Ahora el argumento existe, y `start.sh` verifica el montaje.
- Al principio se atribuyó el corte al módem MediaTek. El dato del usuario de que el OnePlus también se cortaba llevó a la causa común (la voz).
- La captura en vivo de `logcat` se cortó a las 19:56 por el USB inestable. El tercer corte se recuperó después desde el búfer.

## Para retomar
1. **Celda:** n78 TDD de referencia, `./start.sh gnb_b210_00101_csiper_ppm0_kos.yml`, con el Redmi en **VoLTE activado + `NR only`**. Al terminar, devolver el teléfono a su tipo de red original.
2. **Tiempo real (P-004):** pedirle a Santi cerrar Brave y Spotify durante las corridas; proponer governor `performance` (se pierde al reiniciar).
3. **OnePlus en `NR only` (P-005)** con `adb shell am start -n com.android.phone/.settings.RadioInfo`.
4. **Mediciones:** throughput (`iperf3` contra `ogstun`), latencia y jitter, ahora que la conexión dura minutos.
5. **Decidir P-003** (IMS en Docker o parche de Open5GS), para explicarlo en el informe o eliminar la dependencia de `NR only`.
6. **Prueba que más ayudaría a decidir (Codex):** A/B/A cambiando solo el Redmi a *data centric*, con LTE permitido, si el firmware lo deja. Si no, A/B/A con IMS VoPS 1→0→1 en una imagen de prueba de Open5GS (P-003).
7. Decodificar el Registration Accept real (VoPS) y ver el *usage setting* del Redmi.
