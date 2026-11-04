La revisión encontró **errores técnicos y conclusiones que deben corregirse antes de entregar**. No encontré exposición de claves, IMSI completos, direcciones personales ni menciones a herramientas de IA en el informe. No modifiqué archivos ni accedí a las rutas excluidas.

No clasifiqué hallazgos como **CRÍTICO**: los problemas encontrados afectan la precisión técnica, la trazabilidad y la interpretación de los resultados.

Los números de línea corresponden a los archivos `.tex`.

**Hallazgos técnicos y de cálculo**

1. **IMPORTANTE — `informe/secciones/04_downlink.tex:83`: falta un bit en la explicación del PBCH.**  
   La suma escrita es \(23+8+24=55\), no 56. Falta distinguir los 23 bits del MIB del bloque de 24 bits entregado por capas superiores, que incluye el bit de selección del mensaje BCCH-BCH. Además, para el \(L_{\max}=8\) de esta celda, los bits adicionales no contienen los bits altos del índice SSB: incluyen el bit alto de \(k_{\mathrm{SSB}}\) y bits reservados.  
   **Corrección:** explicar \(24+8=32\) bits antes del CRC y \(32+24=56\) antes de la codificación polar; distinguir el caso FR1 del caso \(L_{\max}=64\). [TS 38.212, §7.1.1–7.1.4](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/15.02.00_60/ts_138212v150200p.pdf).

2. **MENOR — `informe/secciones/06_flujos.tex:55`: error aritmético en \(N_{\mathrm{info}}\).**  
   El resultado correcto es:
   \[
   7344\frac{948}{1024}\,8=54\,391{,}5\text{ bits},
   \]
   no \(54\,390{,}4\).  
   **Corrección:** actualizar también \(N_{\mathrm{info}}-24=54\,367{,}5\) y el cociente del paso siguiente. **El error no cambia el TBS final de 54 296 bits**, ni los siete CB.

3. **IMPORTANTE — `informe/secciones/06_flujos.tex:68`, `:82` y `informe/secciones/10_preguntas.tex:6`: se confunden tamaños de entrada, palabras codificadas y bits útiles.**  
   Los 8448 bits son la entrada LDPC después del relleno; no son el tamaño de la palabra codificada. Los 7784 incluyen el CRC del CB y una parte del bloque que ya contiene el CRC del TB: no son todos datos útiles. Tampoco el TBS solo se divide exactamente en siete: \(54\,296/7\) no es entero.  
   **Corrección:** presentar esta cadena:
   \[
   A=54\,296,\ B=54\,320,\ C=7,\ K'=7784,\ K=8448.
   \]
   Cada CB tiene 7760 bits antes de su CRC, 24 de CRC y 664 de relleno. Distinguir después la salida codificada y el rate matching. Los 58 752 bits transmitidos se reparten en cinco bloques de 8392 y dos de 8400 bits, para los supuestos del ejemplo. [TS 38.212, §5.2.2, §5.3.2 y §5.4.2](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/15.02.00_60/ts_138212v150200p.pdf).

4. **IMPORTANTE — `informe/secciones/06_flujos.tex:103`: la “verificación cruzada” por TBS trata el slot especial como una fracción de un slot completo.**  
   El TBS depende de los símbolos asignados, DM-RS y cuantización. Multiplicar el TBS del slot completo por la fracción de símbolos DL no reproduce ese procedimiento.  
   **Corrección:** llamarlo aproximación o calcular por separado ambos tipos de asignación. Por ejemplo, manteniendo los supuestos y usando siete símbolos de PDSCH en el especial, resulta un TBS de 27 144 bits:
   \[
   \frac{6(54\,296)+27\,144}{5\text{ ms}}=70{,}584\text{ Mbit/s}.
   \]
   Es un ejemplo condicionado, no el throughput exacto de la celda. [TS 38.214, §5.1.3.2](https://www.etsi.org/deliver/etsi_ts/138200_138299/138214/15.10.00_60/ts_138214v151000p.pdf).

5. **IMPORTANTE — `informe/secciones/06_flujos.tex:113`, `informe/secciones/09_resultados.tex:33` y `informe/secciones/11_conclusiones.tex:14`: se presenta una estimación como máximo exacto validado experimentalmente.**  
   TS 38.306 proporciona una tasa **aproximada** de capacidad. La multiplicación por la fracción TDD es una adaptación adicional; no determina el goodput TCP ni toda la planificación real. Alcanzar el 75 % no “confirma los máximos teóricos”.  
   **Corrección:** usar “referencia aproximada de capacidad PHY adaptada al patrón TDD” y “resultado compatible con esa referencia”. Los cálculos de ≈71,7 y ≈35 Mbit/s son numéricamente razonables. [TS 38.306, §4.1.2](https://www.etsi.org/deliver/etsi_ts/138300_138399/138306/15.10.00_60/ts_138306v151000p.pdf).

6. **MENOR — `informe/secciones/09_resultados.tex:16`: la referencia de DFT-s-OFDM usa 51 PRB pese al límite de 50 explicado en el informe.**  
   **Corrección:** conservar 35 Mbit/s como referencia común del canal, identificándola así, o agregar la referencia ajustada a 50 PRB: aproximadamente 34,3 Mbit/s.

7. **IMPORTANTE — `informe/secciones/04_downlink.tex:181`: una secuencia generada por registros de 31 etapas no tiene longitud 31.**  
   **Corrección:** escribir “generador Gold con registros de 31 etapas y período nominal \(2^{31}-1\); se utiliza el segmento requerido por cada canal”. [TS 38.211, §5.2.1](https://www.etsi.org/deliver/etsi_ts/138200_138299/138211/15.10.00_60/ts_138211v151000p.pdf).

8. **IMPORTANTE — `informe/secciones/04_downlink.tex:219` y `:226`: las afirmaciones sobre PAPR omiten las condiciones del modelo.**  
   El límite \(N\) requiere precisar la normalización; con el denominador de potencia media de conjunto escrito allí, una constelación QAM de amplitud variable requiere considerar también sus amplitudes máximas. Las muestras OFDM tampoco son exactamente gaussianas e independientes para cualquier \(N\).  
   **Corrección:** expresar la CCDF como aproximación gaussiana y distinguir la PAPR normalizada por energía de cada símbolo de la normalizada por potencia media de conjunto. Reservar el ejemplo de máximo \(N\) para símbolos de igual módulo.

9. **IMPORTANTE — `informe/secciones/05_uplink.tex:241`: “la PAPR no crece con \(M\)” es demasiado absoluto.**  
   La interpolación genera picos entre los símbolos originales; las estadísticas de máximos pueden depender del tamaño del bloque.  
   **Corrección:** “DFT-s-OFDM conserva una estructura de portadora única y suele presentar menor PAPR; su dependencia con la asignación difiere de CP-OFDM”. Evitar una independencia universal respecto de \(M\).

10. **IMPORTANTE — `informe/secciones/04_downlink.tex:250` y `informe/secciones/05_uplink.tex:243`: la simulación se presenta como equivalente a la configuración real, pero usa una asignación DFT de 51 PRB que el propio informe declara inadmisible.**  
    **Corrección:** identificarla como simulación matemática ilustrativa con 612 subportadoras, o rehacer la comparación con una asignación NR válida, manteniendo iguales recursos entre formas de onda. Los 2,5–3,7 dB deben quedar como resultados de esa simulación, no como ventaja universal ni medición del teléfono.

11. **IMPORTANTE — `informe/secciones/05_uplink.tex:253`, `:262`, `informe/secciones/08_cronologia.tex:108` y `informe/secciones/10_preguntas.tex:18`: se atribuye la diferencia medida a la IDFT sin evidencia suficiente.**  
    CP-OFDM también usa un MCS común para una asignación; el bit loading independiente por subportadora no describe el PUSCH NR de esta comparación. La selectividad, el ecualizador y el receptor influyen, pero no se midieron como para explicar los ≈2,1 Mbit/s de diferencia.  
    **Corrección:** retirar esa atribución causal. Indicar que la prueba no permite separar forma de onda, recursos, implementación y variación entre corridas. **La ubicación del ecualizador antes de la IDFT está correctamente explicada.**

12. **IMPORTANTE — `informe/secciones/05_uplink.tex:169` y `informe/secciones/07_implementacion.tex:94`: los ≈2 km se denominan radio de cobertura real.**  
    El cálculo es una cota temporal bajo supuestos sobre guarda, ventana de recepción y multitrayecto. No incorpora presupuesto de enlace, sensibilidad ni interferencia.  
    **Corrección:** “alcance geométrico orientativo impuesto por las restricciones temporales del PRACH, bajo los supuestos indicados”. Mantener separado el alcance radioeléctrico, que no se midió.

13. **MENOR — `informe/secciones/05_uplink.tex:156`: el intervalo del comando relativo de TA es asimétrico.**  
    Con \(T_A\in[0,63]\), \(T_A-31\in[-31,32]\).  
    **Corrección:** reemplazar “±31 pasos” por “−31 a +32 pasos”.

14. **IMPORTANTE — `informe/secciones/04_downlink.tex:260`, `:265`, `:269` y `informe/secciones/10_preguntas.tex:9`: el modelo de potencia DL se presenta como una regla general de NR.**  
    Potencia total fija repartida entre RE activas y EPRE constante frente a cambios de ocupación son supuestos diferentes. Tampoco está sustentado que esta implementación nunca ajuste potencia por usuario o que n3 tenga efectivamente 3,1 dB menos de EPRE.  
    **Corrección:** declarar un modelo simplificado de carga completa, distribución uniforme e igual potencia total. Presentar la diferencia n3/n78 como resultado de ese modelo. [TS 38.214, §4.1](https://www.etsi.org/deliver/etsi_ts/138200_138299/138214/15.10.00_60/ts_138214v151000p.pdf).

15. **IMPORTANTE — `informe/secciones/05_uplink.tex:297` y `informe/secciones/11_conclusiones.tex:15`: el ejemplo hipotético de potencia se utiliza como diagnóstico del UE real.**  
    \(PL=60\) dB y \(\alpha=1\) son supuestos. La SINR alta tampoco demuestra por sí sola que el UE tenga margen de potencia.  
    **Corrección:** escribir “en este ejemplo hipotético tendría ≈19 dB de margen”. En resumen y conclusiones, mantener explícito que la ausencia de limitación de potencia es una hipótesis pendiente de PHR.

16. **IMPORTANTE — `informe/secciones/09_resultados.tex:40`, `:46` y `:56`: la explicación de latencia y planificación contiene generalizaciones incorrectas.**  
    No toda ráfaga exige un nuevo SR si ya existen grants; una retransmisión no necesariamente espera el próximo período de 5 ms. Además, 2,5 ms no es automáticamente la espera media hasta un recurso UL: depende de las ocasiones de SR y de los slots habilitados.  
    **Corrección:** separar tráfico que reactiva un UE sin grant de tráfico sostenido. Identificar el período y offset reales de SR; presentar las esperas como ejemplos condicionados, no como deducción cuantitativa del RTT.

**Datos experimentales, trazabilidad y conclusiones**

17. **IMPORTANTE — `informe/secciones/09_resultados.tex:14` y `informe/secciones/08_cronologia.tex:113`: falta identificar qué mide la bajada TCP.**  
    La evidencia aclara que se tomó `sum_sent` del servidor: **tasa del emisor**, no goodput recibido. También informa que no se conservaron los originales de iperf3 ni ping.  
    **Corrección:** incorporar ambas limitaciones y describir el procedimiento de medición, dirección, duración y extremo observado. Sustento: `evidencia/06_mediciones/2026-11-03_iperf_ping_resultados.md:12–16`.

18. **IMPORTANTE — `informe/secciones/08_cronologia.tex:67`: n3 no terminó sin RLF por parada voluntaria.**  
    La evidencia indica 338,7 s en n3 **hasta RLF**; n78 sí llegó a 345,3 s sin RLF hasta detener el gNB. El informe reproduce aquí un error del prompt, línea 171.  
    **Corrección:** distinguir los desenlaces. Sustento: `evidencia/04_sesion_pdu/README.md:22` y `evidencia/04_sesion_pdu/2026-11-03_gnb_eventos_n3_nronly.log:23`.

19. **IMPORTANTE — `informe/secciones/04_downlink.tex:30`, `:32`, `:34`, `:96`, `:121`; `informe/secciones/05_uplink.tex:31`, `:37`, `:177`, `:191`; `informe/secciones/07_implementacion.tex:81`: aparecen parámetros observados que no están en el prompt.**  
    Entre ellos: ARFCN del SSB, `offsetToPointA`, \(k_{\mathrm{SSB}}\), periodicidad SSB, potencias nominales, paging, raíz PRACH, response window, configuración de search space, lista de \(k_2\) y timer de TA. No los califico como inventados: el problema es que se presentan como observaciones sin su procedencia y exceden la fuente experimental admitida.  
    **Corrección:** retirarlos, convertirlos en ejemplos explícitos o incorporarlos primero a la fuente de datos autorizada con referencia al SIB1/log correspondiente. El YAML permitido no explicita todos esos valores.

20. **IMPORTANTE — `informe/secciones/07_implementacion.tex:101`: el procedimiento de programación y validación de SIM está sobregeneralizado.**  
    `PROYECTO.md:69` distingue programación de NG-RAN/PLMN mediante APDU desde Linux de K/OPc mediante otra herramienta. Además, pasar vectores Milenage verifica el algoritmo o procedimiento probado; no demuestra por sí solo que las credenciales del abonado coincidan entre tarjeta y núcleo.  
    **Corrección:** describir por separado ambos procedimientos. Informar únicamente el resultado de la comparación local autorizada —“coinciden/difieren”— y el resultado de autenticación, sin revelar valores.

21. **IMPORTANTE — `informe/secciones/08_cronologia.tex:25`, `:34`, `:60`, `:65` y `informe/secciones/11_conclusiones.tex:13`: las conclusiones exceden lo observado.**  
    “No hay PRACH” no excluye por sí solo problemas de detección; poca CPU agregada no excluye un hilo crítico saturado; CSI no decodificado no prueba ausencia de transmisión; que otro UE funcione no demuestra compatibilidad completa con el Redmi; periodicidad exacta no descarta toda causa radio. Tampoco se demuestra que el UE haya dejado de corregir su deriva al quitar TRS.  
    **Corrección:** usar “apoya la hipótesis”, “no se decodificó” y “no se identificó”. Conservar como hechos los contadores, cambios aplicados y resultados reproducidos.

22. **IMPORTANTE — `informe/secciones/08_cronologia.tex:48–56`: se presenta un modelo del módem como mecanismo demostrado.**  
    No se verificó cómo el Redmi acopla CFO y seguimiento temporal. La predicción de ≈7 pasos/s difiere de los 2,2–3,8 observados, y el reparto atribuido al módem es especulativo. Los 6,6 kHz calculados tampoco son una medición del error absoluto del oscilador.  
    **Corrección:** separar el efecto verificado de `clock_ppm` en el código y la mejora experimental del modelo explicativo propuesto. No inferir exactitud del oscilador a partir del valor de corrección configurado.

23. **IMPORTANTE — `informe/secciones/11_conclusiones.tex:16`: la hipótesis IMS se vuelve una atribución causal en las conclusiones.**  
    **Corrección:** “el corte periódico se mitigó con NR only; su relación con voz/IMS continúa como hipótesis”. La referencia §4.3.2 es pertinente para selección de dominio, pero no establece un temporizador universal de 60 s ni demuestra qué política ejecutó este módem.

24. **MENOR — `informe/secciones/08_cronologia.tex:115` y `informe/secciones/09_resultados.tex:19`: faltan definición de jitter y alcance estadístico.**  
    La evidencia define el jitter mediante diferencias entre RTT sucesivos; no es automáticamente jitter unidireccional ni jitter UDP de iperf. Una corrida degradada tampoco constituye una cota pesimista garantizada.  
    **Corrección:** explicitar estimador, 60 paquetes enviados/47 recibidos e intervalo de 0,5 s. Reemplazar “cota pesimista” por “resultado de una corrida degradada”.

**Citas, redacción e indicaciones obligatorias**

25. **IMPORTANTE — `informe/informe_final.tex:51–55`: no empieza por la consigna.**  
    El resumen y el índice aparecen antes. Aunque la estructura sugerida pone primero el resumen, la indicación obligatoria del profesor exige consigna y después conceptos básicos.  
    **Corrección:** mover la consigna al comienzo del contenido y ubicar después el marco 3GPP; reubicar el resumen de manera compatible con esa prioridad.

26. **IMPORTANTE — `informe/secciones/01_consigna.tex:8` y `informe/secciones/08_cronologia.tex:11–115`: se exige cerrar etapas con evidencia, pero el informe no permite localizarla.**  
    Hay resultados narrados sin identificador de corrida, archivo o intervalo que los respalde.  
    **Corrección:** agregar una tabla breve de etapa, configuración, evidencia y conclusión admitida, usando extractos anonimizados. Para TCP/ping, declarar la falta de originales señalada en el hallazgo 17.

27. **MENOR — `informe/secciones/04_downlink.tex:6` y `:113`: las citas son incompletas para el alcance de las afirmaciones.**  
    TS 38.213 §4.1 respalda búsqueda/sincronización, pero no todo el procedimiento de selección PLMN, selección de celda y lectura de información de sistema. La cita del TRS tampoco precisa sección.  
    **Corrección:** distribuir referencias entre TS 23.122, TS 38.304 y TS 38.331 según el procedimiento; para CSI-RS de seguimiento, citar TS 38.214 §5.1.6.1.1. [TS 38.214](https://www.etsi.org/deliver/etsi_ts/138200_138299/138214/15.10.00_60/ts_138214v151000p.pdf).

28. **MENOR — `informe/secciones/12_referencias.tex:2–15`: falta versión concreta en varias especificaciones.**  
    “Release 15” no identifica de forma suficiente la edición usada para verificar tablas y secciones.  
    **Corrección:** consignar versión y fecha, especialmente para TS 38.101-1, 38.212, 38.214, 38.306 y 24.501. No asumir que un número de sección es incorrecto solo porque lleva `[verificar]`: **§7.2.2 de TS 38.212 y §4.1 de TS 38.214 sí son pertinentes**.

29. **MENOR — `informe/secciones/03_numerologia.tex:4`, `:48` y `informe/secciones/07_implementacion.tex:92`: hay afirmaciones universales innecesarias.**  
    LTE tiene excepciones a la SCS de 15 kHz; que entren las subportadoras no es la única condición práctica de muestreo; 23,04 MS/s no es un mínimo matemático universal ni garantiza reducir exactamente a 3/4 la carga de CPU.  
    **Corrección:** acotar la comparación al LTE convencional de datos y describir 23,04 MS/s como elección compatible y eficiente de esta implementación. La reducción de caudal de muestras sí es del 25 %; la de CPU requeriría medición.

**Verificado sin errores relevantes:** \(T_c\), \(\kappa\), FFT de 768 a 23,04 MS/s, CP de 54/66 muestras para \(\mu=1\), ejercicio de CP de la cátedra, conversiones ARFCN principales, cuentas GSCN dadas, 51/106 PRB, guardas de 805/452,5 kHz, fracciones TDD, paso de TA y TBS final. El índice PRACH 159 **sí corresponde a B4**; sus duraciones calculadas son coherentes con las tablas citadas. [TS 38.211, tablas 6.3.3.1-2 y 6.3.3.2-3](https://www.etsi.org/deliver/etsi_ts/138200_138299/138211/15.10.00_60/ts_138211v151000p.pdf).

Las diez preguntas obligatorias están respondidas explícitamente. Se respeta downlink antes de uplink y se desarrollan propiedades de secuencias, enfoque probabilístico del PAPR y ecualización antes de la IDFT. La comparación EDGE/LTE vacía está pedida por el prompt; no corresponde completarla con valores inventados.
