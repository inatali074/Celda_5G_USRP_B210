# Prompt para generar el informe final

Sos un ingeniero en telecomunicaciones con experiencia docente en comunicaciones móviles. Tenés que redactar el **informe final académico** de un trabajo práctico de la materia Comunicaciones Móviles (UNRC): la implementación de una celda 5G NR Standalone con una USRP B210. Escribí en español rioplatense formal, con la terminología 3GPP en inglés (SSB, PRACH, PUSCH, etc.).

## Reglas de redacción
1. **Voz del grupo.** Todo se cuenta como trabajo del grupo: "el grupo detectó…", "se analizó…", "se resolvió…". No menciones herramientas de inteligencia artificial, asistentes, revisores automáticos ni quién hizo cada cosa. No uses nombres de personas.
2. **Tono académico.** Usá párrafos con argumentación, ecuaciones numeradas, tablas y figuras con epígrafe, y citas a las especificaciones (TS y sección). Cada cálculo va paso a paso, con unidades.
3. **Tus límites.** No inventes números de sección ni valores de tablas 3GPP. Si no estás seguro de una cita, marcala como **[verificar]**. Los datos experimentales son solo los de este prompt: no agregues mediciones.
4. **Prioridades.** La teoría de capa física y de **métodos de acceso** pesa más que los protocolos de señalización: mencioná NAS, RRC y NGAP solo cuando hagan falta.
5. **Confidencialidad.** No incluyas claves de SIM, IMSI completos ni direcciones de equipos personales.

## Indicaciones del profesor (obligatorias)
- La presentación y el informe **empiezan por la consigna** y después por **3GPP y los conceptos básicos**.
- **Primero el downlink, después el uplink.** El downlink arranca por la información piloto que se manda al iniciar la comunicación.
- Ver bien el ancho de banda: **1536 × 15 kHz** (la velocidad de muestreo con la que se busca la señal).
- Explicar las **propiedades de los códigos** (secuencias).
- Al hablar del **PAPR de OFDM clásico, hablar de probabilidad.**
- Preguntas que el informe tiene que responder explícitamente (podés juntarlas en una sección "Preguntas de la cátedra" con referencia a dónde se desarrollan):
  1. Cómo son los flujos, cuántos bits por segundo y cuál es el peso de las palabras (tamaño de bloque de transporte, code blocks).
  2. Cómo se asigna el presupuesto de potencia (downlink y uplink).
  3. Qué pasa apenas se prende el celular y en qué momento se engancha: escaneo de bandas, búsqueda de pilotos, sincronización con los pilotos.
  4. Por qué se hace el scrambling.
  5. Por qué hay diferencia entre CP-OFDM y DFT-s-OFDM.
  6. En OFDMA, cuál tiene mayor PAPR y por qué crece con N (no es que siempre haya más PAPR, sino que **aumenta la probabilidad** de picos altos).
  7. Cuál es el valor mínimo del prefijo cíclico: tiene que ser mayor que el ensanchamiento temporal del canal (delay spread).
  8. Cuánto vale la frecuencia de muestreo en 5G.
  9. Cómo se relaciona el timing advance con el radio de cobertura.
  10. Si en DFT-s-OFDM se ecualiza antes o después de la IDFT (respuesta esperada: en el receptor se ecualiza en frecuencia, después de la FFT y del demapeo de subportadoras, y **antes** de la IDFT de M puntos que deshace la precodificación; justificarlo).
- **Ejercicio del prefijo cíclico (resolverlo tal como lo planteó el profesor y después compararlo con NR):**
  - Delay spread τ = 1/(4·SCS), con SCS = 15 kHz → τ = 16,67 µs.
  - Tiempo de muestreo T_s = 1/f_s, con f_s = 1536 × 15 kHz = 23,04 MHz → T_s = 43,40 ns.
  - Muestras de CP = τ/T_s = 384. Con las 1536 muestras de la IFFT, el símbolo tiene 1920 muestras.
  - Con una IFFT de 2048 puntos, f_s = 30,72 MHz (y el CP sería de 512 muestras): la duración del símbolo no cambia.
  - Duración del símbolo: 1920/23,04 MHz = 83,33 µs (66,67 µs útiles + 16,67 µs de CP). Con 14 símbolos: 1,167 ms.
  - **Comparación que el informe debe hacer:** con un CP de T/4 entran solo 12 símbolos en 1 ms. Ese es el caso del CP extendido (LTE, o NR con μ=2). El CP normal de NR (TS 38.211 §5.3.1) es de 144 muestras a 30,72 MHz, o 4,69 µs, y 160 en el primer símbolo de cada medio subframe: así entran 14 símbolos en 1 ms (2048·14 + 144·14 + 16·2 = 30720 muestras). En 5G, los 14 símbolos forman un **slot**, no una trama: la trama dura siempre 10 ms.

## Consigna del trabajo
Desplegar desde cero una celda 5G NR Standalone (opción 2, Release 15) en un entorno de RF controlado (jaula de Faraday). Lograr que un celular comercial con SIM de laboratorio se registre, obtenga IP y navegue. Medir throughput, latencia y jitter, para compararlos con 2G (EDGE) y 4G (LTE). Toda la implementación va dentro de contenedores Docker. Cada decisión se justifica con las especificaciones 3GPP, y cada etapa se cierra con evidencia.

## Estructura sugerida
1. Resumen (con los resultados principales).
2. Consigna y objetivos.
3. Marco teórico: 3GPP y conceptos básicos de 5G NR:
   - releases;
   - NSA contra SA;
   - arquitectura gNB y 5GC (AMF, SMF, UPF; interfaces N2, N3 y N6, solo lo justo);
   - FR1 y FR2; bandas n78 (TDD) y n3 (FDD).
4. Capa física: numerología y recursos:
   - μ, SCS, slots y símbolos;
   - unidad de tiempo T_c y frecuencia de muestreo;
   - grilla, RE y PRB;
   - **cálculo de PRB y de banda de guarda;**
   - prefijo cíclico (con el ejercicio);
   - estructura TDD.
5. **Downlink:**
   - qué pasa al prender el celular (escaneo y raster de sincronización, GSCN);
   - SSB: PSS, SSS y PBCH; cálculo del PCI;
   - MIB/SIB1;
   - señales piloto: DMRS, CSI-RS y TRS;
   - PDCCH (CORESET, search space) y PDSCH;
   - scrambling;
   - codificación: LDPC para datos, Polar para control;
   - propiedades de las secuencias: m-secuencias en PSS, Gold en SSS y scrambling, Zadoff-Chu;
   - OFDMA y su PAPR **con enfoque probabilístico**;
   - presupuesto de potencia en el DL (EPRE por RE).
6. **Uplink y métodos de acceso:**
   - acceso aleatorio por PRACH: preámbulos Zadoff-Chu, procedimiento de 4 pasos, **analogía con slotted ALOHA** (colisión de preámbulos, resolución de contienda), power ramping y timing advance;
   - acceso planificado (grant-based): SR por PUCCH, BSR, grant en DCI; mencionar configured grant;
   - qué pasa cuando el celular está callado: DRX en RRC_CONNECTED, inactivity timer, paso a RRC_INACTIVE y RRC_IDLE, paging, vencimiento del timer de TA y pérdida de sincronismo de subida (otra vez por RACH);
   - **CP-OFDM contra DFT-s-OFDM** (transform precoding, TS 38.211 §6.3.1.4): PAPR, cuándo conviene, dónde se ecualiza;
   - control de potencia del PUSCH (TS 38.213 §7.1, fórmula con P_CMAX, P_0, α·PL, 10·log10(2^μ·M_RB), Δ_TF y f) y PHR.
7. Flujos y tasas:
   - MCS, modulación y tasa de código;
   - TBS (TS 38.214 §5.1.3.2) con un ejemplo numérico para 51 PRB;
   - segmentación en code blocks;
   - throughput teórico máximo (TS 38.306 §4.1.2) contra el medido.
8. Implementación: arquitectura, equipamiento, parámetros de la celda, decisiones de diseño justificadas.
9. **Desarrollo cronológico: problemas detectados y soluciones.**
10. Resultados y análisis frente a la teoría.
11. Conclusiones y trabajo futuro.
12. Referencias (TS 38.101-1, 38.104, 38.211, 38.212, 38.213, 38.214, 38.300, 38.306, 38.321, 38.331, 24.501, 31.102, 35.208).

Sugerí figuras donde ayuden: grilla tiempo-frecuencia con el SSB, patrón TDD, diagrama de bloques de CP-OFDM y DFT-s-OFDM (transmisor y receptor), procedimiento RACH de 4 pasos, CCDF del PAPR para varios N, y la arquitectura implementada.

## Datos de la implementación

### Equipamiento y software
- **Radio:** USRP B210 (sin GPSDO) por USB 3.0. Frecuencia de muestreo configurada: **23,04 MS/s** (= 1536 × 15 kHz = 768 × 30 kHz), formato sc12.
- **gNB:** OCUDU (ex srsRAN Project), versión `release_26_10`, en Docker.
- **Núcleo:** Open5GS v2.8.0 con MongoDB, en Docker.
- **Salida a Internet:** por NAT del kernel Linux.
- **PC principal:** Intel i3-1005G1 (2 núcleos y 4 hilos), 7,3 GiB de RAM, Debian 13. Se usó también una segunda PC del laboratorio, con 12 hilos y 60 GiB.
- **Celulares:** Xiaomi Redmi Note 14 5G (el que se midió), OnePlus 13 y Motorola Edge 30 Neo.
- **SIM:** programables de laboratorio, grabadas por el grupo desde Linux con comandos APDU (listas de tecnologías de acceso con NG-RAN y PLMN, TS 31.102). La autenticación se validó con los vectores de Milenage de TS 35.208.
- **Monitoreo:** un panel web de monitoreo, en otro contenedor, que muestra las métricas del gNB y los logs, y lanza ping e iperf3.

### Parámetros de la celda principal
| Parámetro | Valor |
| --- | --- |
| Banda | n78 (TDD), FR1 |
| ARFCN DL | 635000 → 3525 MHz |
| Ancho de banda de canal | 20 MHz |
| Numerología | μ = 1, SCS = 30 kHz |
| PRB | 51 |
| PLMN / TAC / PCI | 001/01 (PLMN de prueba) / 7 / 1 |
| Patrón TDD | período de 5 ms: 6 slots DL, 1 slot especial (8 símbolos DL, 0 UL, 6 de guarda), 3 slots UL |
| PRACH | `prach-ConfigurationIndex` 159, secuencia corta L = 139, SCS del PRACH 30 kHz, `msg1-FrequencyStart` 11, `preambleReceivedTargetPower` −100 dBm, `powerRampingStep` 4 dB, `preambleTransMax` 7, 64 preámbulos por SSB. Ver en TS 38.211 tabla 6.3.3.2-3 qué formato es el índice 159 **[verificar]** |
| Forma de onda | DL: CP-OFDM. UL: CP-OFDM (se probó DFT-s-OFDM) |
| Modulación usada en el DL | Hasta 256QAM. En una corrida: 44 882 PDSCH en 256QAM, 10 506 en 64QAM, 1530 en 16QAM y 4901 en QPSK |
| Antenas | 1 de TX y 1 de RX (1 capa) |
| Ganancias de la B210 | TX 80 dB, RX 40 dB |

También se probó una celda **n3 FDD**: ARFCN 368500 (DL 1842,5 MHz, UL 1747,5 MHz), 20 MHz, SCS 15 kHz (106 PRB).

### Cálculos ya verificados por el grupo (usalos y desarrollalos)
- **PRB y banda de guarda (TS 38.101-1, tabla 5.3.2-1 [verificar el número]):**
  - **n78:** 20 MHz con 30 kHz → 51 PRB; ocupados 51 × 12 × 30 kHz = 18,36 MHz (91,8 % del canal). Guarda mínima = (20 000 − 18 360)/2 − 30/2 = **805 kHz** por lado.
  - **n3:** 20 MHz con 15 kHz → 106 PRB; ocupados 19,08 MHz. Guarda = (20 000 − 19 080)/2 − 7,5 = **452,5 kHz**.
- **Tiempos con μ = 1:**
  - slot de 0,5 ms (20 slots por trama de 10 ms);
  - símbolo útil de 33,33 µs;
  - CP normal 144·κ·2^−μ·T_c = 2,344 µs, y 2,865 µs en el primer símbolo de cada medio subframe;
  - con T_c = 1/(480 kHz · 4096) ≈ 0,509 ns y κ = 64.
- **Muestreo de nuestra radio:** a 23,04 MS/s, la FFT es de 768 puntos.
  - CP = 54 muestras, o 66 en el símbolo largo.
  - Comprobación: 768·14 + 54·13 + 66 = 11 520 muestras = 0,5 ms × 23,04 MS/s.
  - Comparar con 30,72 MS/s (FFT de 2048 y 15 kHz), con la f_s básica de NR (1/T_c ≈ 1,966 GHz), y con 61,44 MS/s.
- **Delay spread tolerable:** un CP de 2,344 µs equivale a ~703 m de diferencia de camino entre trayectos.
- **Timing advance:**
  - paso con μ = 1: 16·64·T_c/2^μ ≈ 0,26 µs, o ~39 m de distancia por paso (ida y vuelta);
  - el TA máximo del RAR (T_A ≤ 3846) da ~1 ms con μ = 1;
  - el radio de cobertura real lo limitan el CP y el tiempo de guarda del formato del PRACH. Desarrollar esa relación.
- **PCI 1:** N_ID^(1) = 0 y N_ID^(2) = 1 (PCI = 3·N_ID^(1) + N_ID^(2)).
- **Throughput teórico (TS 38.306 §4.1.2), 1 capa, Q_m = 8, R_max = 948/1024, 51 PRB, T_s^μ = 10^−3/(14·2) s:**
  - **DL:** sin TDD, con OH = 0,14, da 109,2 Mbit/s. La fracción DL del patrón es (6·14 + 8)/140 = 0,657, así que el máximo es **≈ 71,7 Mbit/s**.
  - **UL:** sin TDD, con OH = 0,08, da 116,8 Mbit/s. La fracción UL es 42/140 = 0,30, así que el máximo es **≈ 35 Mbit/s** (≈ 26 Mbit/s con 64QAM).

### Desarrollo cronológico (redactarlo como trabajo del grupo, con la teoría que explica cada problema)
**Antecedente:** una prueba previa de otro grupo había funcionado con un UE simulado por software, pero por aire solo un celular comercial ajeno había llegado al núcleo. La atribuía a que las SIM no tenían el directorio 5G (DF_5GS).

**30/10: entorno, contenedores y primera celda**
1. La B210 aparecía como USB 2.0 hasta cargarle el firmware. Se resolvió cargándolo después de cada conexión, y quedó en USB 3.0 (5 Gb/s), necesario para 23,04 MS/s.
2. Se construyeron las imágenes Docker del gNB, el núcleo y un UE simulado. gNB y AMF completaron el NG Setup.
3. **La prueba sin radio, con UE simulado y enlace por software, no avanzó.** Además, el UE simulado solo admite SCS de 15 kHz, así que no servía para n78 a 30 kHz. El grupo la abandonó y pasó directamente a la celda real.
4. **Primera celda por aire en la jaula:** n78, 3525 MHz. Se eligió 3525 MHz porque 3489,42 MHz caía en el bloque de un operador comercial y atraía celulares ajenos.
   - El Redmi completó un registro una sola vez, sin sesión PDU.
   - El Motorola con SIM de laboratorio no generó ningún PRACH.
   - Con chip comercial, el Motorola llegó al núcleo y fue rechazado, como se esperaba.
5. **Conclusión:** la radio funcionaba y el problema era cómo trataba el teléfono a la SIM. La hipótesis del antecedente (falta de DF_5GS) quedó refutada, porque una SIM sin DF_5GS se registró.

**02/11: SIM, PLMN y primera navegación**
6. **Con PLMN 722/999, aun con NG-RAN grabado en la SIM, los teléfonos no generaban PRACH:** 0 en 2 minutos. Se cambió al PLMN de prueba 001/01 y el Redmi se registró al primer intento; el OnePlus también. No se identificó la causa dentro del módem.
7. **Con CSI periódico, el gNB declaraba falla de enlace (RLF) a los 3 s:** había 100 reportes de CSI sin decodificar. Se pasó a CSI aperiódico. Sin CSI-RS se perdía también el TRS (seguimiento de tiempo y frecuencia) y empeoraba.
8. **Primera navegación:** el Redmi descargó ~27 MB por NAT, y el OnePlus obtuvo IP.
9. **La conexión se cortaba cada 18-65 s.** Entre el 73 % y el 92 % de los PUSCH tenían error. Al abrir un navegador en la PC aparecían fallas de tiempo real (~900 por minuto), y una vez la B210 perdió el USB. Quedó abierto.

**03/11, mañana: una PC más potente**
10. En la segunda PC (12 hilos), el patrón fue el mismo, con el gNB usando ~110 % de 1200 %. Por minuto hubo ~130 transmisiones DL que agotaron los 4 reintentos HARQ, ~80 fallas de tiempo real (late, underflow) y ~2 RLF. **La CPU no era la causa principal:** el DL fallaba más de lo que explicaba el tiempo real, así que el problema apuntaba a la radio o a la sincronización.
11. Problema operativo: el script de arranque cargaba una configuración vieja. Se corrigió pasando la configuración como argumento y verificando qué archivo quedaba montado.

**03/11, tarde: las tres causas de los cortes**
12. **Corrección de reloj (`clock_ppm`):**
    - **Síntoma:** el gNB enviaba comandos de TA positivos sin parar (+2,2 a +3,8 pasos de 0,26 µs por segundo) y las conexiones duraban 3-10 s.
    - **Causa, verificada en el código del gNB:** el parámetro corregía en −1,87 ppm la frecuencia de portadora, pero no la de muestreo. El teléfono se sincronizaba a la portadora corregida y la temporización de muestreo derivaba.
    - **Solución:** `clock_ppm = 0`. El TA quedó estable y las conexiones pasaron a ~60 s.
    - **Para el informe:** explicarlo con la teoría de sincronización, el TA (TS 38.213 §4.2) y la relación entre el oscilador común, la portadora y el muestreo.
13. **El Redmi no envía CSI:** de ~10 000 pedidos aperiódicos, 0 se decodificaron, y del CSI periódico por PUCCH formato 2, solo ~0,4 %. El OnePlus sí lo enviaba. Solución: CSI periódico y umbral de KO consecutivos del PUCCH muy alto, para que el CSI faltante no dispare RLF.
14. **Corte casi exacto cada 60 s,** igual en n78 TDD y en n3 FDD. **n3 FDD funcionó por primera vez.**
    - Con los registros del módem (adb logcat) se vio que el Redmi perdía el servicio entre 59,99 y 60,02 s después de obtenerlo, en 5 ciclos, sin liberación previa de la red. Después escaneaba LTE comercial.
    - **Hipótesis principal, no demostrada:** el núcleo anuncia soporte de voz sobre IMS ("IMS voice over PS" = 1) sin tener IMS. Un UE *voice centric* sin voz abandona 5G y busca E-UTRA (TS 24.501 §4.3.2 [verificar]).
    - **Mitigación:** VoLTE activado y tipo de red "NR only" en el teléfono. Con eso, el Redmi duró 5 min 39 s en n3 y 5 min 45 s en n78, sin RLF.
15. **Quedaron abiertos:**
    - el OnePlus no permite forzar "NR only" desde el menú y se corta a los ~35-37 s (pide la DNN `ims`);
    - una falla de tiempo real del gNB ("UL processor is busy").

**03/11, noche: monitoreo, DFT-s-OFDM y mediciones**
16. El grupo armó un panel web de monitoreo en un contenedor sin privilegios. Lee las métricas del gNB y los logs, y lanza ping e iperf3.
17. **"UL processor is busy":**
    - aparece después de ráfagas de fallas de tiempo real y persiste hasta parar la celda, a 10-60 por segundo;
    - cae en los slots de UL (7, 8, 9, 17, 18 y 19), sobre todo en el 19, el del PRACH;
    - ocurrió en 2 de 3 corridas y degrada la celda.
    - Mitigación: medir con la celda recién arrancada, governor de CPU en `performance` y sin aplicaciones pesadas. La causa de fondo quedó abierta.
18. **Prueba A/B/A de la forma de onda UL:** subida TCP de 10 s, con el Redmi.

| Tramo | UL | Promedio | Desvío | Pruebas | SINR PUSCH media |
| --- | --- | --- | --- | --- | --- |
| A1 | CP-OFDM | 8,66 Mbit/s | 0,40 | 2 | ~19 dB |
| B | DFT-s-OFDM | 12,70 Mbit/s | 1,35 | 4 | ~27 dB |
| A2 | CP-OFDM | 14,84 Mbit/s | 1,18 | 4 | ~27 dB |

   - **Conclusión:** DFT-s-OFDM funciona (los dos teléfonos entraron y se usó 256QAM), pero **no mejoró**. Con SINR alta y un UE sin limitación de potencia, la menor PAPR no aporta: su beneficio aparece en el borde de celda, cuando el amplificador del UE trabaja cerca de saturación. Esto es una hipótesis, porque no se midió el PHR. Por eso se mantuvo CP-OFDM.
   - A1 tuvo peor enlace, por una causa no identificada. Hubo una sola corrida por tramo.
19. **Bajada TCP de 10 s (tramo A2):** 55,2, 52,7 y 42,2 Mbit/s. La tercera coincidió con la aparición de "UL processor is busy". Con la celda limpia, ~54 Mbit/s, ≈ 75 % del máximo teórico de 71,7 Mbit/s.
20. **Ping al teléfono, con la celda ya degradada:** RTT mínimo 16,7 ms, mediano 27,7 ms, p90 44,9 ms y máximo 1052 ms; 21,7 % de pérdida; jitter 52,3 ms. Hay que repetirlo con la celda limpia.

### Análisis que el informe debe hacer con los resultados
- **Asimetría DL/UL:** explicarla con el patrón TDD (65,7 % de símbolos DL contra 30 % UL), las diferencias de potencia y la latencia del acceso planificado en UL (SR → grant → PUSCH; k2 ≥ 4 slots).
- **UL medido contra teórico:** 14,8 Mbit/s contra ~35 Mbit/s. Atribuirlo a errores de PUSCH, BLER y la dinámica de TCP, y a la planificación por SR/BSR.
- **Latencia y TDD:** relacionarla con la estructura TDD (esperar un slot UL) y con DRX y SR.
- **Comparación con 2G y 4G:** la tienen que completar los alumnos, así que dejá una tabla con columnas para EDGE, LTE y NR (completada solo la de NR).

### Pendientes (para "trabajo futuro")
- Repetir ping y bajada con la celda recién arrancada.
- Identificar la causa de "UL processor is busy".
- Confirmar la hipótesis de voz cambiando solo el anuncio de IMS, o montar un IMS.
- Forzar "NR only" en el OnePlus.
- Repetir DFT-s-OFDM en bloques alternados (ABAB/BABA) registrando el PHR.
- Justificar formalmente el uso del PLMN de prueba 001/01.
