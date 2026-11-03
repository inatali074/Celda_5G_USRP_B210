# Sesión 2026-11-03 (tarde): causa de los cortes, n3 FDD y el corte de los 60 s

## Resultado
**Se encontró la causa del corte de cada ~60 s, y es la voz, no la radio.** Los teléfonos con VoLTE activado se registran, esperan voz por IMS (Open5GS les anuncia que hay, pero no tenemos IMS) y a los 60 s dejan solos la celda para buscar LTE. **Con el teléfono en `NR only`, el Redmi quedó estable más de 5 minutos en n3 FDD y en n78 TDD.** En el camino:
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
| 6 | n3 + `adb logcat` en el Redmi | El módem deja la celda a **60,004 / 59,991 / 60,016 s** de obtener servicio: `+CIEV: 3,0` y, 10 ms después, `+CSCON: 0` (RRC idle local, sin RRCRelease ni nada en Open5GS). Después escanea LTE comercial (EARFCN 2450, 9360, 9485, 2225, 850, 950, 3050) y vuelve en 6-9 s con un Registration de movilidad |
| 7 | n3 + MDLog (DebugLoggerUI) + OnePlus | Redmi: **60,022 y 60,014 s** (7 de 7 conexiones completas entre 59,99 y 60,02 s). OnePlus: pide la DNN `ims` y el núcleo la rechaza; se corta antes (~40 s) |
| 8 | n3 con VoLTE desactivado | Los dos teléfonos se registran pero se van en ~5-20 s |
| 9 | n3 + **Redmi en `NR only`** con VoLTE | **5 min 38 s sin corte.** Terminó por "RLC max ReTxs" cuando el procesador de UL del gNB se trabó por tiempo real (ver abajo) |
| 10 | n78 TDD (`_csiper_ppm0_kos.yml`) + **Redmi en `NR only`** | **Más de 5 min 27 s sin corte**, casi sin fallas de tiempo real (339). El OnePlus (sin `NR only`) se cortó a ~38 y ~35 s del registro |

## Por qué es la voz
- **El corte lo inicia el teléfono:** en el gNB y en Open5GS no hay ningún mensaje alrededor del corte (se verificó en los logs RRC/NGAP de la prueba 7).
- **Es un temporizador exacto:** 60,00 ± 0,02 s desde el registro, en n3 y en n78.
- **Open5GS v2.8.0 anuncia "IMS voice over PS session supported" = 1 fijo en el código** (`src/amf/gmm-build.c`, líneas 125-130). No hay opción en el YAML.
- **Un UE "voice centric" sin voz en 5GS deshabilita N1 y busca E-UTRA** (TS 24.501 §4.3 / §4.9, según Gemini; la sección exacta falta verificarla). Es lo que se ve: escaneo de bandas LTE.
- **La guía oficial de srsRAN para COTS UEs** (verificado con WebFetch) dice, para el Pixel 6: *"Requires disabled NR_TIMER_WAIT_IMS_REGISTRATION or SUPPORT_IMS_NR_REGISTRATION_TIMER"*. Para el iPhone 13 Pro: *"iPhones require IMS to be enable UE to stay connected."*
- Sin VoLTE, el teléfono sabe desde el principio que no tendrá voz y se va enseguida. Con `NR only` no tiene a dónde ir y se queda.

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
- **Falta revisión cruzada:** la conclusión de la voz (D-015) todavía no la revisó Codex.

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
6. Que Codex revise D-015 y la evidencia de hoy (revisión cruzada pendiente).
7. Verificar en TS 24.501 la sección exacta del comportamiento "voice centric" (§4.3) y el cambio a E-UTRA.
