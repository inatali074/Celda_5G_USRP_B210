# Sesión 2026-11-17 (tarde): revisión de Codex, normas verificadas, ping e IMS en el Redmi

Continúa `sesiones/2026-11-17_panel-grilla-dft-ulbusy.md`. Celda en tachoPC con la opción 1 del menú (`gnb_b210_00101_n78_cpofdm.yml`). Hubo dos corridas: la del ping (~18:47 UTC) y la del IMS (desde las 19:00:57 UTC).

## Diagrama DFT-s-OFDM: revisión de Codex (commit `fff5eba`)
- `revisiones/2026-11-17_revision-diagrama-dft.md`, 13 hallazgos.
  - Se aplicaron 12. Entre ellos:
    - "fuera de la grilla" en lugar de "guarda";
    - el CP largo en los símbolos 0 y 7 con μ=0;
    - las afirmaciones de PAPR más prudentes.
  - Se rechazó el 3: TS 38.331 V15.30.0 dice `msg3-transformPrecoder`.
- Se verificó en Brave con Claude in Chrome.
- Se agregó el link para bajar TS 38.211 Rel-15 (la norma no se sube a git, por decisión del usuario).

## Normas verificadas en la fuente (commits `dfc02b4` y `abeee8f`)
- **TS 38.214 V15.16.0 §6.1.2.2:**
  - el tipo 0 solo existe sin transform precoding;
  - el tipo 1 asigna VRB contiguos.
- **TS 38.101-1 V15.17.0:**
  - 106 PRB a 15 kHz y 51 a 30 kHz (tabla 5.3.2-1);
  - en n78 se permiten 15, 30 y 60 kHz (5.3.5-1);
  - la clase 3 es de 23 dBm (6.2.1-1).
- **E.212, anexo A:** los MCC que empiezan con 0 están "reservados para uso futuro", no para pruebas. La frase del informe se corrigió y ahora cita TS 38.508-1 V15.4.0, tabla 4.4.2-3, nota 3: la celda simulada usa el MCC/MNC de la USIM de prueba.
- **TS 23.501 V15.13.0, tabla 5.7.4-1:**
  - 5QI 1 es GBR, voz conversacional, 100 ms;
  - 5QI 5 es no GBR, señalización IMS;
  - 5QI 9 es no GBR.
- **TS 33.203 V15.3.0:**
  - §7.1: IPsec ESP con las claves de IMS-AKA;
  - §8.2: la USIM compartida para IMS.

## Informe (commits `2f06960` y `6382877`)
- Se agregaron la SIP, el IMS (etapa 1), el EVM, el menú y la causa de "UL processor is busy".
- **Por decisión del usuario, no se hace:**
  - **la comparación con EDGE/LTE:** "nos tenemos que centrar en 5G; 2G y 4G lo hicieron el año pasado";
  - **VoNR etapa 2.**
- Se quitaron del trabajo futuro EDGE/LTE, `zeroCorrelationZone` y el OnePlus.

## Ping con la celda recién arrancada (`evidencia/06_mediciones/2026-11-17_ping_*`)
- **Condiciones:** el Redmi en "NR only"; 3 corridas de 60 paquetes cada 0,5 s, lanzadas desde el contenedor `dashboard`.
- **RTT:**
  - mínimo, de 7,7 a 10,0 ms;
  - mediano, de 21,6 a 27,9 ms.
- **Pérdida:** 0 %, 0 % y 25 %.
- **Corrida 3:** un corte de ~7 s (18:49:11,7 a 17,4 UTC). En ese lapso no hubo PUSCH, los PUCCH llegaron con `sr=no` y no hubo RLF. La causa no se identificó.
- **"UL processor is busy" empieza en el primer acceso:**
  - la primera falla apareció 0,27 s después del primer PRACH del Redmi;
  - el 13/11 había aparecido 0,19 s después del primer PRACH;
  - durante las tres corridas se mantuvo en ~7 fallas por segundo, es decir, un procesador trabado.

  Es reproducible. Reiniciar el gNB no la evita, solo la deja en ese mínimo. El informe y `evidencia/09_ul_busy/README.md` se corrigieron.
- Se borró el volcado IQ de la corrida.

## IMS en el Redmi: es el teléfono, no la SIM
- **Sugerencia del profesor:** un campo "ARN" podría tener que ser de prueba. Lo más probable es que se refiriera al APN. No se aclaró.
- **Logs del núcleo de hoy:**
  - el Redmi con la SIM 3 pidió 62 veces la DNN `Metodos1` y ninguna vez `ims`;
  - el Motorola con la SIM 4 pidió `ims` 30 veces.
- **SIM 4 en el Redmi**, con la red levantada con el IMS:
  - registros a las 19:02:35, 19:03:46, 19:07:06 y 19:08:20 UTC;
  - **solo pidió `Metodos1`**, y el P-CSCF no recibió ningún `REGISTER`.

  Con la misma SIM, el Motorola sí abre `ims`. Entonces **la causa está en el teléfono**: Android tiene `carrier_volte_available_bool = false` para 001/01 (ver 12/11).
- **APN `ims` creado a mano en el Redmi:** tipo `ims`, IPv4. No cambió nada: siguió pidiendo solo `Metodos1`. Un APN de tipo `ims` no se selecciona a mano: el sistema lo usa solo si decide registrarse en IMS. `Metodos1` tiene que seguir siendo el APN de datos.
- **Pendiente sin confirmar:** el 05/11 hubo 5 pedidos de `ims` con la SIM 3, pero esos logs no se guardaron y no se sabe en qué teléfono estaba la SIM.
- **Para hacer "NR only" sin cortes de ~60 s** hay que activarlo cada vez que se cambia la SIM: se vio el corte cuando faltaba.
- **Al cierre:** la red quedó apagada y se borró el volcado IQ (382 MB).

## Consola del gNB y PHR (red levantada de nuevo, ~19:20 UTC)
- **Comandos de la consola:** se escriben en el panel `metricas` aunque la tabla no se frene. Otra opción es `docker attach --detach-keys=ctrl-c 5g-gnb-radio-1` en otra pestaña, con todo el ancho. Comandos útiles: `tx_gain`, `rx_gain`, `release`, `log` y `t`.
  - Se probó `tx_gain 0 70` y se volvió a `tx_gain 0 80`.
  - Con la línea vacía, la consola imprime la ayuda.
- **Sin teléfonos conectados, la tabla no imprime filas.**
- **iperf3 de subida, 19:54:42 a 19:54:58 UTC** (Redmi con SIM 3, CP-OFDM; `evidencia/06_mediciones/2026-11-17_iperf_ul_phr.txt`):
  - el PHR baja de 9–12 a 0–2 dB y la SINR de ~34 a ~21 dB;
  - la tasa es de 10–17,5 Mbit/s y la BLER de 21–43 %;
  - hubo solo 36 fallas de "UL processor is busy".
- **Se corrigió el informe:**
  - el resumen, las secciones 5.5 y 5.6, el párrafo 28 nuevo de la cronología, la sección 9.5 nueva y las conclusiones;
  - la MPR verificada en TS 38.101-1 V15.17.0, tabla 6.2.2-1;
  - la bibliografía citaba v15.31.0 y ahora dice V15.17.0, la versión leída.

## Para retomar
- **El Redmi tiene la SIM 4.** Hay que volver a ponerle la SIM 3 y la 4 al Motorola antes de la próxima prueba de IMS o SIP.
- **Opciones para el IMS del Redmi, sin elegir todavía:**
  - revisarlo por adb con USB (`dumpsys carrier_config`, la operadora asignada y los APN);
  - preguntarle al profesor qué era el "ARN" (puede ser el nombre de la operadora en la SIM, el SPN);
  - dejarlo documentado como está.
- **Decidir** si las pruebas del Redmi (cambio de SIM y APN `ims`) van al informe.
- **Opcional:** bajar TS 34.108 para confirmar el valor 001/01 de la USIM de prueba.
- **Descartado por el usuario:**
  - una configuración del gNB sin volcado IQ;
  - informarle la falla a OCUDU;
  - una excepción en `.gitignore` para la norma;
  - la prueba A/B/A con `nof_threads: 2`;
  - la comparación con EDGE/LTE;
  - VoNR etapa 2.
