Las correcciones principales son válidas: **los valores de FFT, CP y muestras por slot están bien para μ=0 y μ=1**. Sin embargo, ambos documentos conservan errores de explicación y algunas afirmaciones sin respaldo suficiente.

Leí el original, ambos documentos corregidos, los cuatro YAML indicados y el XML y las ecuaciones WMF de TS 38.211 V15.10.0. No modifiqué archivos. En las referencias siguientes, **MD** significa `Correcciones_Diagrama_DFT_IFFT.md` y **HTML**, `Diagrama_Visual_DFT_Mapeo_IFFT_corregido.html`.

**Hallazgos, ordenados por gravedad**

1. **Error — MD:103; HTML:85–86. El original no usa realmente la proporción de CP extendido.**

   > «El valor de 512κ·2⁻μ que usaba el original es el CP extendido».

   El original usa **512 muestras de CP y 1536 útiles**, por lo que CP/parte útil = **1/3**. En NR con CP extendido, esa relación es 512/2048 = **1/4**, y CP/símbolo completo = **1/5**.

   Coincide el tiempo `1/(4·SCS)` con la expresión del CP extendido extrapolada a esas numerologías, pero **no coincide la estructura del símbolo original**. Además, el original no escribe la fórmula con κ.

   **Corrección propuesta:** «El original fija un CP igual a 1/(4·SCS), pero además descuenta ese CP de la parte útil. Eso produce una relación CP/útil de 1/3 y no corresponde a ninguna estructura NR válida para μ=0 o μ=1». Mantener por separado que el CP extendido de NR solo está admitido con μ=2. **Fuente:** TS 38.211 V15.10.0, §5.3.1 y tabla 4.2-1.

2. **Error — HTML:254; también generalización en MD:13. El CP largo y los símbolos completos no se reducen exactamente a la mitad.**

   > «Al duplicar la SCS, el símbolo útil y el CP se reducen a la mitad».

   Esto vale para la parte útil y para el **CP corto**. El extra del CP largo permanece constante: `16κTc = 0,520833… µs`.

   Por eso, al pasar de μ=0 a μ=1:

   - CP largo: **5,208333 → 2,864583 µs**, no 2,604167 µs.
   - Símbolo largo: **71,875 → 36,197917 µs**, no 35,9375 µs.

   **Corrección propuesta:** aclarar que se divide por dos la parte útil y el término base del CP; el extra de los símbolos especiales no cambia. **Fuente:** §5.3.1.

3. **Error — HTML:137. Nombre incorrecto de un parámetro normativo.**

   > «`msg3-transformPrecoder` para el Msg3».

   El nombre es **`msg3-transformPrecoding`**. `transformPrecoder` sí es el otro parámetro.

   **Corrección propuesta:** reemplazar el identificador. **Fuente:** [TS 38.214 Release 15, §6.1.3](https://www.etsi.org/deliver/etsi_TS/138200_138299/138214/15.02.00_60/ts_138214v150200p.pdf).

4. **Error — MD:19. LTE no tiene una única SCS.**

   > «La única SCS de LTE».

   Los 15 kHz son la **SCS de referencia** utilizada para definir `Ts`; LTE también contempla otras separaciones, por ejemplo 7,5 y 1,25 kHz en determinados modos de bajada.

   **Corrección propuesta:** «SCS de referencia de LTE usada en esta definición». **Fuente:** TS 38.211 §4.1 para la constante; [TS 36.211 V15.5.0, §6.12](https://www.etsi.org/deliver/etsi_ts/136200_136299/136211/15.05.00_60/ts_136211v150500p.pdf) para las otras SCS.

5. **Impreciso — MD:175–176; HTML:107 y 134. Se reemplazan cifras de PAPR sin justificar por otras igualmente sin justificar.**

   > «La ventaja […] es del orden de 2 a 3 dB».

   Sin una referencia concreta y condiciones de comparación —modulación, asignación, sobremuestreo y probabilidad de excedencia— no queda demostrado que **2–3 dB** sea una corrección de **3–4 dB**. El MD reconoce «No verificado», pero el HTML presenta el nuevo intervalo como una conclusión establecida.

   También es demasiado general:

   > «La pérdida de propagación crece más rápido que con el cuadrado de la distancia».

   En espacio libre crece con el cuadrado. Para un modelo `Pr ∝ d⁻ⁿ`, una mejora de `G` dB multiplica el alcance por `10^(G/(10n))`: con 3 dB y `n=2`, resulta **1,413**, no dos.

   **Corrección propuesta:** conservar el diagnóstico de que «duplica el alcance» no está sustentado, pero retirar el nuevo intervalo universal. Si se incorpora un ejemplo numérico, declarar sus supuestos. **Fuente:** definición de PAPR y ecuación del presupuesto de enlace; las fuentes actuales de los documentos no respaldan un intervalo concreto.

6. **Impreciso — HTML:174–193 y 245; MD:59 y 188. Se confunden ceros de la FFT, recursos no asignados y guarda RF.**

   > «Las demás entradas de la IFFT valen cero: forman las bandas de guarda que mantienen la señal dentro del canal de 20 MHz».

   Las restas **1536−1272=264** y **768−612=156** son correctas: cuentan bins fuera de la grilla considerada. Pero los recursos de esa grilla que no usa un PUSCH **no se convierten por eso en bandas de guarda**; pueden estar libres o transportar otros canales/señales. Tampoco los ceros eliminan los lóbulos espectrales fuera del canal.

   Los repartos **132/132** y **78/78** requieren asumir una grilla centrada y una convención de índices. Además, mostrar el centro en la mitad del dibujo corresponde a un orden de frecuencias centrado, no al orden habitual de entrada de una IFFT sin reordenamiento.

   **Corrección propuesta:** rotular «bins fuera de la grilla, bajo el supuesto de centrado» y distinguirlos de los RE no usados por ese PUSCH. Aclarar el orden de índices del dibujo. **Fuente:** TS 38.211 §4.4 y §5.3.1; las guardas RF se especifican separadamente en TS 38.101-1 §5.3.3.

7. **Impreciso — MD:22, 29, 186–191; HTML:246 y 268–271. El glosario y algunas tablas omiten las excepciones del CP largo.**

   > «FFT / CP (1.º símbolo)»  
   > «NCP = 144·NFFT/2048».

   Para μ=0, el CP largo está en **l=0 y l=7**, no solamente en el primer símbolo del slot. Para μ=1 está en **l=0 y l=14**, que sí son los primeros símbolos de sus respectivos slots.

   La fórmula en muestras citada describe solo el CP corto. Los valores de duración de símbolo **71,35 / 35,68 µs** también corresponden solo a símbolos con CP corto.

   **Corrección propuesta:** usar «CP corto; entre paréntesis, CP largo» y explicitar los índices. Completar la fórmula con el extra `16κTc·fs`, que vale **12 muestras a 23,04 Msps** y **16 a 30,72 Msps**. **Fuente:** §5.3.1.

8. **Impreciso — MD:23–24; HTML:269–270. Unidades incorrectas en las columnas de valores de Nu y NCP,l.**

   > «Nu […] en unidades de Tc» → «66,67 / 33,33 µs».

   Esas duraciones son **NuTc**, no Nu. Lo mismo ocurre con NCP,l.

   **Corrección propuesta:** mostrar los conteos normativos:

   - `Nu`: **131072 / 65536**.
   - `NCP,l` corto: **9216 / 4608**.
   - `NCP,l` largo: **10240 / 5632**.

   Alternativamente, cambiar el símbolo de la fila a `Tu` o `TCP,l` cuando se expresan microsegundos. **Fuente:** §5.3.1.

9. **Impreciso — MD:58 y 113; HTML:89 y 278. Definición de delay spread y efecto del CP demasiado absolutos.**

   > «Diferencia de tiempo entre el camino directo y los ecos».

   Puede no existir un camino directo observable. Además, *delay spread* puede referirse a la dispersión RMS; esta no es simplemente el retardo del último eco.

   **Corrección propuesta:** para explicar la condición del CP, hablar de **máximo exceso de retardo significativo respecto de la primera llegada**, junto con el margen de sincronización. El CP permite evitar interferencia entre símbolos y conservar la estructura circular bajo esas condiciones; no «absorbe» físicamente los ecos. Las distancias calculadas siguen siendo válidas como diferencias de recorrido idealizadas. **Fuente:** modelo de convolución y extensión cíclica de OFDM; §5.3.1 describe la construcción de la señal, no una garantía de cobertura.

10. **Impreciso — MD:146. Falta distinguir cuánto tiempo falta en cada caso.**

    > «Los 0,0667 ms que faltaban en el original eran justamente los CP».

    Es correcto para μ=0:

    `1 − 14/15 = 0,066666… ms`.

    Para μ=1 faltan **0,033333… ms**:

    `0,5 − 14/30 = 0,033333… ms`.

    **Corrección propuesta:** dar ambos valores. Aclarar que el original ya incluía un CP ficticio: al corregirlo se restituye la duración útil `1/SCS` y se añade el CP normativo. **Fuente:** §5.3.1 y cuentas anteriores.

11. **Impreciso — MD:64 y 87; HTML:134. Los 23 dBm no son un techo absoluto sin condiciones.**

    > «23 dBm (200 mW) como máximo».

    **23 dBm ≈ 199,526 mW** es el valor nominal de clase 3. La especificación contempla tolerancias y reducciones de potencia según las condiciones de transmisión.

    **Corrección propuesta:** «Potencia máxima nominal de clase 3: 23 dBm, aproximadamente 200 mW, sujeta a tolerancias y reducciones aplicables». **Fuente:** [TS 38.101-1 V15.17.0, §6.2](https://www.etsi.org/deliver/etsi_ts/138100_138199/13810101/15.17.00_60/ts_13810101v151700p.pdf).

12. **Impreciso — HTML:204. La duración exacta del slot se generaliza más allá de los dos casos estudiados.**

    > «Hace que un slot dure exactamente 1 ms / 2^μ».

    Para **μ=0 y μ=1**, las sumas que presenta el documento son exactas. Para numerologías mayores con CP normal, la distribución del extra cada 0,5 ms implica que no todos los slots tienen idéntica duración física.

    **Corrección propuesta:** restringir esa frase a μ=0 y μ=1; para el caso general, indicar `2^μ` slots por subtrama y duración nominal/media `1 ms/2^μ`. **Fuente:** §4.3.2 y §5.3.1.

13. **Sugerencia — MD:156, 207; HTML:108 y 286. Mejorar la trazabilidad de lo «verificado».**

    > «Es lo mismo que muestra el panel del proyecto».  
    > «Se comparó con la Rel-18 […] las fórmulas […] son idénticas».

    Estas afirmaciones no incluyen una ubicación verificable del panel ni un registro de la comparación. **No las doy por falsas**, pero esta revisión no las confirmó. Tampoco la coincidencia con los YAML demuestra por sí sola la tabla normativa de PRB: los YAML configuran ancho de banda y SCS.

    **Corrección propuesta:** identificar archivo/línea o evidencia de esas comprobaciones. Mantener la distinción entre «fuente consultada», «cálculo derivado» y «dato configurado». En HTML:108, separar la fuente de PAPR de la fuente sobre SCS admitidas por banda.

    Sí pude confirmar ahora los **106/51 PRB** en TS 38.101-1 Release 15, tabla 5.3.2-1, y la asignación tipo 1 con transform precoding en [TS 38.214 Release 15, §6.1.2.2](https://www.etsi.org/deliver/etsi_ts/138200_138299/138214/15.13.00_60/ts_138214v151300p.pdf). El rótulo histórico «no verificado en esta revisión» de los documentos es transparente, no un error.

**Lo que comprobé y está bien**

Las siguientes cuentas salen de la copia local de **TS 38.211 V15.10.0, §4.1 y §5.3.1**:

`Tc = 1/(480000·4096) = 0,508626302083… ns`  
`Ts = 32,552083333… ns`; `κ = 64`.

| Magnitud | μ=0 | μ=1 |
|---|---:|---:|
| Parte útil | 66,666667 µs | 33,333333 µs |
| CP corto | 4,687500 µs | 2,343750 µs |
| CP largo | 5,208333 µs | 2,864583 µs |
| Símbolo con CP corto | 71,354167 µs | 35,677083 µs |
| Símbolo con CP largo | 71,875000 µs | 36,197917 µs |
| FFT a 23,04 Msps | 1536 | 768 |
| CP corto/largo a 23,04 Msps | 108 / 120 | 54 / 66 |
| FFT a 30,72 Msps | 2048 | 1024 |
| CP corto/largo a 30,72 Msps | 144 / 160 | 72 / 88 |
| Muestras por slot a 23,04 Msps | 23040 | 11520 |
| Muestras por slot a 30,72 Msps | 30720 | 15360 |

En particular:

- **Sumas exactas:** `12·1644 + 2·1656 = 23040`; `13·822 + 834 = 11520`. A 30,72 Msps: `12·2192 + 2·2208 = 30720` y `13·1096 + 1112 = 15360`.
- **CP especiales:** `l=0,7` para μ=0 y `l=0,14` para μ=1, con índice dentro de la subtrama.
- **CP extendido:** únicamente μ=2 en tabla 4.2-1. La fórmula es `512κ·2⁻μ`; a μ=2 dura **4,166667 µs**.
- **Transform precoding:** la regla `MRB=2^α2·3^α3·5^α5` está efectivamente en §6.3.1.4. Los máximos bajo los límites de 106 y 51 PRB son **100 y 50**, con DFT de **1200 y 600 puntos**. Los ejemplos 96, 90 y 10 PRB también cumplen.
- **FFT y grillas:** las factorizaciones 1536=`3·2⁹` y 768=`3·2⁸`, los productos 106·12=1272 y 51·12=612, y las restas de bins **264/156** y **776/412** son correctos, con las salvedades del hallazgo 6.
- **Ecos:** usando `c=3·10⁸ m/s`, los CP cortos corresponden a **1406,25 m** y **703,125 m** de exceso de recorrido. Las aproximaciones 1,4 km y 700 m están bien; no representan radios de celda.
- **Configuraciones:** los cuatro YAML tienen `srate: 23.04`; n3 usa 15 kHz y n78, 30 kHz. Las frecuencias citadas coinciden con las configuraciones.
- **Otros números:** 19,08/18,36 MHz de extensión de grilla y 17808/17136 RE por milisegundo están bien como recursos brutos; estos últimos no equivalen a RE disponibles para datos, especialmente al considerar TDD y señales de referencia.
- **Coherencia MD/HTML:** no encontré discrepancias entre sus valores numéricos centrales de FFT, CP, tiempos, PRB o muestras. Comparten principalmente las imprecisiones señaladas.
- **Justicia del diagnóstico al original:** son reales los errores de muestreo/SCS, duración útil, CP, duración de slot y asignación de los 106 PRB con DFT-s-OFDM. **1536 y 768 no son tamaños de FFT erróneos por sí mismos**, y los documentos corregidos los reconocen correctamente. La acusación sobre PAPR debe limitarse a falta de sustento, y la identificación con CP extendido requiere la corrección del hallazgo 1.
