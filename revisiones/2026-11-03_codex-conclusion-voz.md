**D-015 sirve como procedimiento provisorio para el Redmi, pero exagera la certeza de la causa.** La hipótesis de voz/IMS es la mejor respaldada de las consideradas; la evidencia demuestra un patrón temporal y una mejora con `NR only`, pero no identifica directamente el temporizador interno ni prueba una causa común para ambos teléfonos. No modifiqué archivos.

Las referencias locales siguientes son relativas al directorio del proyecto.

**Bloqueante — se presenta una hipótesis como causa demostrada.**

En `PROYECTO.md:77,84,104-105`, `sesiones/2026-11-03_cortes-60s-volte.md:4,27-33` e `investigacion/2026-11-03_analisis-cortes-claude.md:67-68` se afirma que la causa está encontrada y resuelta.

- **Verificado:** el Redmi pierde servicio repetidamente unos 60 s después de anunciar servicio; después aparecen observaciones LTE. Con `NR only` supera ampliamente ese intervalo.
- **Inferido:** que espera registro IMS, que deshabilita N1 por falta de voz y que esa misma causa explica al OnePlus.
- **Problema causal:** `NR only` también restringe otras políticas de selección de RAT. Su éxito no distingue por sí solo una búsqueda motivada por voz de otra política propietaria de selección, ahorro o tratamiento del PLMN de prueba. Tampoco demuestra que desaparecieron los problemas de radio.
- **Corrección:** describir “hipótesis principal: recuperación de voz/IMS” y “mitigación observada en el Redmi”. P-003 debe ser una investigación pendiente, no una reparación de causa confirmada.

**Importante — “7 de 7” y “60,00 ± 0,02 s” no coinciden exactamente con el extracto.**

Referencias: `PROYECTO.md:77`; sesión `:21-22`; `2026-11-03_redmi_logcat_radio_extracto.log`, líneas indicadas abajo.

| Líneas `+CIEV: 3,1 → 3,0` | Intervalo calculado |
|---|---:|
| 33 → 34 | 60,004 s |
| 85 → 89 | 59,991 s |
| 95 → 99 | 60,016 s |
| 171 → 172 | 60,022 s |
| 233 → 234 | 60,014 s |

Hay **cinco ciclos cercanos a 60 s** documentados así. Los otros dos pares completos son de **15,194 s** —líneas 109→111— y **23,941 s** —244→246—, próximos al final de sus respectivas corridas; no corresponde contarlos como ciclos naturales de 60 s.

Además, 60,022 excede literalmente 60,00±0,02. Conviene informar **rango observado: 59,991–60,022 s; n=5**, medido entre indicaciones AT de servicio, no desde `Registration complete`. La precisión de las marcas no equivale a exactitud del temporizador del módem. Estos cinco ciclos son de **n3**: no sustentan esa precisión en n78.

**Importante — la ausencia de una liberación previa está respaldada, pero “sin ningún mensaje de la red” es demasiado absoluto.**

Referencias: sesión `:28`; README de evidencia `:21`; extractos `gnb_eventos_n3_volte_2_logcat.log:6-19`, `gnb_eventos_n3_volte_3_mdlog.log:6-18` y sus correspondientes logs del núcleo.

En los cinco instantes de pérdida de servicio **no aparece una orden previa `rrcRelease` ni un evento del núcleo que explique directamente el corte**. Las liberaciones registradas llegan después. Por ejemplo:

- Redmi: pérdida de servicio a **20:08:04,334** en el teléfono.
- gNB: `rrcRelease` del contexto anterior a **20:08:10,614**, durante la reconexión.

Esto favorece una salida o pérdida local del UE frente a una liberación ordenada por la red. **No prueba una decisión deliberada por voz:** una falla local de radio también puede producir silencio y recuperación posterior. Son extractos, con relojes distintos; tampoco permiten afirmar ausencia de toda señalización por aire.

Otro exceso: “`+CSCON: 0` 10 ms después” no es uniforme. En el primer ciclo la siguiente indicación disponible aparece **14,836 s** después (`logcat:34-35`); en los demás hay separaciones de 2–15 ms. Corrección: limitar la afirmación a lo observado en cada ciclo.

**Importante — `NR only` supera los 60 s, pero hay que informar los finales correctamente.**

Referencias: `PROYECTO.md:77,114`; sesión `:24-25`; `gnb_eventos_n3_nronly.log:4-26`; `gnb_eventos_tdd_nronly.log:4-16`.

La asociación `0x4601` con el Redmi está respaldada por el primer acceso y el registro de IMSI …003 en los núcleos de ambas corridas.

| Corrida | Resultado comprobable |
|---|---|
| n3 | Desde creación del UE hasta RLF: **338,736 s**, es decir **5 min 38,736 s**, superando 60 s por **278,736 s**. Termina por `RLC max ReTxs` a 20:40:22,401; `rrcRelease` a 20:40:22,927. |
| n78 | Desde creación hasta parada del CU-CP: **345,334 s**, aproximadamente **5 min 45 s**; margen sobre 60 s: **285,334 s**. No se observa RLF del Redmi antes de detener el gNB. |

Para n78 hay evidencia de actividad real: el log completo contiene un **PUSCH `crc=OK` de `0x4601` a 20:51:48,742**, línea descomprimida **542557**, y parada a 20:51:49,718, línea **542697**. No es solamente un contexto retenido.

“Más de 5 min 27 s” es un límite conservador válido, aunque el archivo completo permite precisar más. En n3, atribuir el final específicamente al bloqueo de UL requiere cautela: la sesión sitúa la acumulación masiva desde **~20:40:35** (`:39`), después de la RLF del Redmi. Los contadores globales prueban problemas de tiempo real, pero no esa secuencia causal exacta.

**Importante — el OnePlus no demuestra el mismo corte de 60 s.**

Referencias: `PROYECTO.md:86`; sesión `:22,25,66`; `gnb_eventos_tdd_nronly.log:7-16`; `nucleo_tdd_nronly.log:15-32`.

Desde `Registration complete` hasta detección de RLF transcurren:

- **37,418 s** en el primer acceso n78.
- **35,152 s** en el segundo.

Hasta `rrcRelease` serían **41,419 y 39,153 s**, respectivamente. Hay que indicar qué evento define “corte”.

Los rechazos de DNN `ims` prueban que el OnePlus intenta obtener conectividad IMS, pero **no prueban que esos rechazos causen su RLF**. Falta log del teléfono y una comparación controlada con `NR only`. Corrección: mantenerlo como fenómeno separado, posiblemente relacionado con voz.

**Importante — la prueba con VoLTE apagado está confundida por fallas de radio y no valida el mecanismo propuesto.**

Referencias: `PROYECTO.md:77,84`; sesión `:23,33`; `gnb_eventos_n3_sin_volte.log:4-12`; `nucleo_n3_sin_volte.log:20-25`.

En el primer acceso del Redmi:

- Registro completo: **20:26:52,664**.
- RLF por CRC: **20:26:54,053**, apenas **1,389 s después**.
- `rrcRelease`: **20:26:57,488**.

Los “~5 s” se parecen al tiempo hasta liberación, no al inicio de la falla. Además, el OnePlus **sigue solicitando `ims`** durante la corrida rotulada “sin VoLTE”. Esto no prueba que el interruptor no haya cambiado, pero impide asumir que desactivó efectivamente IMS en ambos equipos.

Corrección: registrar por teléfono qué ajuste cambió y su efecto efectivo. “Sin VoLTE sabe desde el principio que no tendrá voz” es una interpretación, no un resultado medido.

**Importante — la referencia normativa es pertinente, pero faltan condiciones esenciales.**

Referencias: `PROYECTO.md:77`; sesión `:31`; investigación Gemini `:36-37,74-77`.

La sección precisa es **TS 24.501 V15.7.0 §4.3.2**: contempla que, aun anunciándose soporte IMS, las capas superiores no indiquen disponibilidad de voz dentro de un plazo definido por el fabricante. Para un UE *voice centric*, en *single-registration*, prevé deshabilitar N1 y buscar E-UTRA/EPC, con condiciones sobre sesiones persistentes. §4.9.2 completa el procedimiento. **No fija 60 s ni establece que todo smartphone sea voice centric.** [Especificación oficial](https://www.etsi.org/deliver/etsi_ts/124500_124599/124501/15.07.00_60/ts_124501v150700p.pdf).

Falta verificar en este Redmi: *usage setting*, modalidad de registro, condición de sesión persistente y el evento interno de indisponibilidad IMS. La PDU activa por sí sola no resuelve esa última condición.

La [guía oficial COTS](https://docs.ocudu.org/knowledge_base/cots_ues/) confirma el ajuste del temporizador IMS para **Pixel 6**, y una mejora con `NR only` para **Xiaomi 12**. Son antecedentes útiles; no documentan el temporizador de este Redmi.

**Menor — el código de Open5GS está correctamente identificado; falta comprobar lo transmitido.**

Referencias: sesión `:30`; investigación Gemini `:129-130`.

En el tag v2.8.0, `gmm_build_registration_accept()` asigna efectivamente **1** al indicador de voz IMS sobre acceso 3GPP. Está en **líneas 113–118**, no 125–130. [Código oficial](https://github.com/open5gs/open5gs/blob/v2.8.0/src/amf/gmm-build.c#L113-L118).

Eso verifica el código del tag; falta vincularlo con la imagen ejecutada y decodificar el `Registration Accept` real. **Anunciar soporte no demuestra disponibilidad efectiva ni identifica la causa del abandono.** Cambiarlo a cero puede adelantar la búsqueda de otra RAT, por lo que tampoco sería una solución garantizada.

La prueba adicional más discriminante y barata sería **mantener NR/LTE permitido y cambiar únicamente el uso efectivo del Redmi de voice centric a data centric**, si el firmware lo permite y se puede verificar —no sustituirlo por apagar VoLTE—. Hacer una secuencia A/B/A, tres ciclos por condición, con el mismo tráfico y captura sincronizada de radio y red:

- Si desaparece el ciclo de 60 s en data centric y reaparece al restaurar voice centric, con LTE todavía permitido, la evidencia a favor de voz sería mucho más fuerte.
- Si persiste, habría que priorizar otras políticas del módem o una falla local.

Si ese ajuste no está disponible, una comparación A/B/A del indicador VoPS **1→0→1**, en una imagen Docker de prueba y verificando el NAS transmitido, es accesible aunque menos concluyente: un cambio reproducible del tiempo de salida apoyaría la intervención del subsistema de voz; no demostraría por sí solo que implementar IMS elimina todos los cortes.

La redacción defendible de D-015 sería: **“El Redmi muestra cinco pérdidas de servicio a 59,991–60,022 s. No se observa liberación previa de la red en los extractos. La recuperación de voz/IMS es la hipótesis principal. `NR only` evitó ese patrón durante corridas de unos 5–6 minutos; la causa interna y el comportamiento del OnePlus siguen pendientes de verificar.”**
