No edité nada. **No encontré problemas bloqueantes**, pero sí errores de formato, de cronología y conclusiones más fuertes que la evidencia.

1. **Importante — Los tres CSV tienen las columnas corridas.**  
   Archivos: `evidencia/06_mediciones/2026-11-03_gnb_por_segundo_{A1,B,A2}.csv`, desde línea 1; cabeceras en líneas **575, 304 y 329**, respectivamente.  
   Cada fila tiene **12 campos**, pero la cabecera declara 11: `14,15` Mbit/s queda separado en dos columnas. Además, la cabecera está al final. Un lector CSV convencional interpreta mal modulaciones, PDSCH y fallas.  
   **Corrección:** cabecera al principio y punto decimal, o delimitador `;`. Reconstruyendo el decimal, **todos los registros publicados coinciden con los conteos y TBS de los logs**, incluidos los redondeos a dos decimales.

2. **Importante — “DFT-s-OFDM no mejora la subida” no queda demostrado.**  
   Archivos: [sesión, línea 18](</home/nacho/Escritorio/Universidad/5to 2do cuatrimestre/Comunicaciones Moviles/5G/sesiones/2026-11-03_dashboard-dfts.md:18>), [README, línea 24](</home/nacho/Escritorio/Universidad/5to 2do cuatrimestre/Comunicaciones Moviles/5G/evidencia/06_mediciones/README.md:24>) y `PROYECTO.md:79,122`.  
   B supera a A1 y queda debajo de A2. Hay **una corrida por tramo**, con 2/4/4 pruebas consecutivas: esas pruebas no equivalen a corridas independientes. No quedaron controlados posición/orientación, actividad del OnePlus, tiempo desde el arranque ni evolución del enlace. La asignación de PRB también difiere: observé asignaciones de 51 PRB en A y de 50 en B, entre otras.  
   **Corrección:** “En esta exploración no se obtuvo evidencia suficiente para adoptar DFT-s-OFDM por rendimiento; se mantiene CP-OFDM provisoriamente”. Repetir bloques con ambos órdenes, posición fija, un solo UE y tiempos equivalentes desde el arranque.

3. **Importante — La explicación de A1 y el argumento de potencia están sobredimensionados.**  
   Archivos: `sesiones/2026-11-03_dashboard-dfts.md:26`, `evidencia/06_mediciones/README.md:23–25` y `PROYECTO.md:79`.  
   A1 efectivamente tiene más fallas y cambios de modulación, pero **no encontré fallas de tiempo real dentro de las dos ventanas de subida publicadas**. Además, el PUSCH del Redmi durante esas ventanas tiene SINR promedio aproximada de **19,2 dB**, frente a **27,4 dB en B** y **26,8 dB en A2**. “27–31 dB” no representa las tres mediciones. La diferencia de condiciones es real; su causa no está identificada.  
   Una SINR alta tampoco demuestra por sí sola que el UE tenga margen de potencia: faltan PHR o mediciones equivalentes. **TS 38.211 §6.3.1.4 define la transformada; no demuestra que su beneficio sea exclusivamente estar limitado en potencia ni predice este resultado TCP.**  
   **Corrección:** describir A1 como “corrida de menor rendimiento y condiciones de enlace diferentes, causa pendiente”, conservarla en el análisis y presentar la explicación por PAPR como hipótesis. [TS 38.211 V15.8.0, §6.3.1.4](https://www.etsi.org/deliver/etsi_ts/138200_138299/138211/15.08.00_60/ts_138211v150800p.pdf).

4. **Importante — Las horas corresponden al final de las pruebas; la superposición de las bajadas con “UL busy” está mal ubicada.**  
   Archivo: [resultados, líneas 44–46](</home/nacho/Escritorio/Universidad/5to 2do cuatrimestre/Comunicaciones Moviles/5G/evidencia/06_mediciones/2026-11-03_iperf_ping_resultados.md:44>).  
   El backend guarda `time.time()` después de terminar iperf. Los logs lo corroboran: las ráfagas PDSCH de las tres bajadas ocurren aproximadamente a **22:56:27–38, 22:56:41–51 y 22:56:54–22:57:04**. Por lo tanto:
   - La segunda bajada terminó **antes** del primer “UL busy”.
   - La tercera **cruzó su aparición**, a las 22:56:58,586650.
   - Los aproximadamente 16 eventos/s corresponden a después de terminar esa tercera bajada; durante parte de ella hubo **30/s**.

   **Corrección:** rotular las horas como finalización, agregar inicio/fin y corregir los estados. La caída a 42,18 Mbit/s coincide parcialmente con la aparición de fallas; no demuestra por sí sola causalidad.

5. **Importante — La persistencia está respaldada; el crecimiento irreversible en escalones y su mecanismo, no.**  
   Archivos: `sesiones/2026-11-03_dashboard-dfts.md:62–68` y `PROYECTO.md:87,94`.  
   A1 comienza inmediatamente después de underflow/late; A2 comienza después de underflow/overflow, unos 11 segundos después de una ráfaga mayor. Pero:
   - **B tiene ráfagas de tiempo real y ningún “UL busy”.**
   - En A1 hay tramos de aproximadamente 10, 20 y 60/s, pero el salto a 60 coincide con tráfico intenso, sin una nueva ráfaga late allí; luego vuelve a aproximadamente 20/s.
   - En A2 sube a 30/s y **baja** hasta aproximadamente 12–14/s.
   - También hay fallas en slots **17 y 18**, omitidos en la enumeración de la sesión.

   **Corrección:** “En A1 y A2 aparece después de perturbaciones de tiempo real y persiste hasta finalizar; su tasa varía con el tráfico. La causa y la relación con repositorios pendientes no están demostradas”.

   **No pude acceder al código de `release_26_10`**, ni encontré ese fuente en el proyecto. La interpretación del repositorio ocupado es plausible si el código citado es correcto, pero no pude validar las líneas ni la semántica de liberación. Un repositorio inválido no prueba, sin revisar su implementación, que un controlador quede perdido permanentemente.

6. **Importante — Aparecer sin métricas no descarta que las métricas contribuyan.**  
   Archivos: `sesiones/2026-11-03_dashboard-dfts.md:27,110` y `PROYECTO.md:123`.  
   Lo demostrado es que **las métricas JSON no son una condición necesaria** para que aparezca “UL busy”. No se evaluó si aumentan su probabilidad o frecuencia.  
   **Corrección:** reemplazar “no lo causan las métricas” por “también ocurre sin métricas; su contribución al problema sigue sin determinarse”.

7. **Importante — No se pueden verificar independientemente todos los resultados TCP y de ping.**  
   Archivo: `evidencia/06_mediciones/2026-11-03_iperf_ping_resultados.md:12,20–29,44–58`.  
   No están conservados los JSON originales ni la salida cruda del ping. Los logs PHY permiten verificar tráfico y fallas, pero **TBS decodificados no equivalen a goodput TCP**. Tampoco permiten reconstruir mediana, p90 o jitter ICMP. Las listas “por segundo” incluyen 11–12 valores pese a describir pruebas de 10 segundos, sin duraciones individuales para ponderarlos.  
   **Corrección:** marcar estos valores como transcripción sin original conservado. En próximas pruebas guardar JSON completo, salida del ping y tiempos de inicio/fin. Para bajada, identificar expresamente el valor actual como **tasa del emisor**, porque se tomó `sum_sent`.

8. **Menor — Los extractos del núcleo B y A2 incluyen corridas anteriores.**  
   Archivos: `2026-11-03_nucleo_eventos_B.log:1` y `2026-11-03_nucleo_eventos_A2.log:1`.  
   B empieza con eventos de A1; A2 contiene A1 y B antes de sus propios eventos. Esto puede confundir registros, sesiones y presencia del OnePlus al comparar tramos.  
   **Corrección:** filtrar cada extracto por su ventana temporal o declarar explícitamente que es acumulativo.

9. **Menor — El desvío de A2 no reproduce exactamente el cálculo publicado.**  
   Archivo: `evidencia/06_mediciones/2026-11-03_iperf_ping_resultados.md:37`.  
   Desde los cuatro valores mostrados, el desvío muestral es **1,18448 → 1,18**, no 1,19 Mbit/s. Podría explicarse por precisión original no conservada.  
   **Corrección:** publicar 1,18 o conservar los valores completos que justifican 1,19; indicar que son desvíos muestrales.

Los siguientes números sí quedaron verificados contra los logs completos:

| Tramo | PUSCH OK / KO | PDSCH | Fallas RT, incluyendo busy | UL busy | Primera UL busy, UTC |
|---|---:|---:|---:|---:|---|
| A1 | 27.249 / 13.187 | 55.013 | 7.289 | 5.142 | 22:41:21,347029 |
| B | 21.028 / 13.920 | 35.584 | 79 | 0 | Ninguna |
| A2 | 21.601 / 10.667 | 61.819 | 1.541 | 1.429 | 22:56:58,586650 |

Los promedios TCP calculados desde la transcripción son **8,66 / 12,7025 / 14,84 Mbit/s**; los desvíos de A1 y B coinciden. Ninguna subida publicada se superpone con “UL busy”.

Las referencias TDD son pertinentes: el SIB1 muestra **5 ms, 6 slots DL completos, 8 símbolos DL adicionales y 3 slots UL completos**, coherente con [TS 38.213 §11.1](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/15.11.00_60/ts_138213v151100p.pdf) y [TS 38.331, TDD-UL-DL-ConfigCommon](https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/15.03.00_60/ts_138331v150300p.pdf). Ese patrón explica parte de la asimetría, sin predecir una relación fija entre tasas TCP.

También confirmé que **256QAM es compatible con transform precoding**: [TS 38.214 §6.1.4.1](https://www.etsi.org/deliver/etsi_TS/138200_138299/138214/15.02.00_60/ts_138214v150200p.pdf) contempla `mcs-TableTransformPrecoder=qam256`. La restricción de PRB **2ᵃ·3ᵇ·5ᶜ** figura en TS 38.211 §6.3.1.4 y se refiere a la asignación PUSCH, no al ancho total de la celda.

**Privacidad:** no detecté claves Ki, OPc o ADM ni IMSI de terceros en los archivos nuevos. Los identificadores completos encontrados corresponden a las SIM de laboratorio …003 y …004. No leí archivos `*.local.*` ni `config/secretos/`. No encontré inconsistencias en D-016 dentro del alcance documental revisado.
