# Revisión de `Diagrama_Visual_DFT_Mapeo_IFFT1536.html`

- **Revisó:** Claude, 2026-11-13. Revisión cruzada de Codex el 2026-11-17 (`revisiones/2026-11-17_revision-diagrama-dft.md`), con sus correcciones incorporadas.
- **Versión corregida:** `Diagrama_Visual_DFT_Mapeo_IFFT_corregido.html`. El original no se modificó.
- **Norma de referencia:** 3GPP TS 38.211 V15.10.0 (2021-12), "NR; Physical channels and modulation (Release 15)". Es la última versión de la Release 15, que es la que fija la consigna. Se baja de [https://www.3gpp.org/ftp/Specs/2026-09/Rel-15/38_series/38211-fa0.zip](https://www.3gpp.org/ftp/Specs/2026-09/Rel-15/38_series/38211-fa0.zip) (un .zip con el .docx adentro). La copia local, `referencias/3GPP_TS_38.211_V15.10.0.docx`, no se sube a git.

## 0. Qué significa cada variable y cada sigla

### Variables de las fórmulas

| Símbolo | Nombre | Qué es | Valor en nuestro caso |
| --- | --- | --- | --- |
| **μ** | Numerología | Número entero que elige la separación entre subportadoras: Δf = 2<sup>μ</sup>·15 kHz. Cada vez que μ sube en 1, la SCS se duplica y la parte útil del símbolo, el CP corto y el slot duran la mitad (el extra de 16κ del CP largo no cambia). | 0 en n3, 1 en n78 |
| **Δf** (SCS) | Separación entre subportadoras (*subcarrier spacing*) | Distancia en frecuencia entre dos subportadoras OFDM vecinas. Su inversa (1/Δf) es la duración de la parte útil del símbolo. | 15 kHz (n3), 30 kHz (n78) |
| **T<sub>c</sub>** | Unidad básica de tiempo de NR | El "tick" más chico en el que la norma mide todos los tiempos. Se define como T<sub>c</sub> = 1/(Δf<sub>max</sub>·N<sub>f</sub>). | ≈ 0,509 ns |
| **Δf<sub>max</sub>** | SCS máxima de referencia | Constante de la norma que se usa para definir T<sub>c</sub>. | 480 kHz |
| **N<sub>f</sub>** | Tamaño de FFT de referencia de NR | Constante de la norma que se usa para definir T<sub>c</sub>. | 4096 |
| **T<sub>s</sub>** | Unidad básica de tiempo de LTE | La unidad equivalente de 4G: T<sub>s</sub> = 1/(Δf<sub>ref</sub>·N<sub>f,ref</sub>). Es la que corresponde a muestrear a 30,72 MHz. | ≈ 32,55 ns |
| **Δf<sub>ref</sub>** | SCS de referencia de LTE | SCS de referencia de LTE que usa la norma para definir T<sub>s</sub> (LTE tiene además otras, como 7,5 kHz para MBSFN). | 15 kHz |
| **N<sub>f,ref</sub>** | Tamaño de FFT de referencia de LTE | FFT de LTE con 20 MHz. | 2048 |
| **κ** (kappa) | Relación entre las unidades | κ = T<sub>s</sub>/T<sub>c</sub>. Sirve para escribir los tiempos de NR "en unidades de LTE". | 64 |
| **l** | Índice de símbolo OFDM | Número de símbolo dentro de la subtrama (empieza en 0). Los símbolos l = 0 y l = 7·2<sup>μ</sup> son los primeros de cada 0,5 ms y llevan un CP un poco más largo (CP largo). Con μ = 0 son los símbolos 0 y 7 de cada slot; con μ = 1, el símbolo 0 de cada slot. | 0 … 13 (n3), 0 … 27 (n78) |
| **N<sub>u</sub>** | Largo de la parte útil del símbolo | N<sub>u</sub> = 2048κ·2<sup>−μ</sup>, en unidades de T<sub>c</sub>. Multiplicado por T<sub>c</sub> da 1/Δf. | 131 072 (n3), 65 536 (n78); por T<sub>c</sub>: 66,67 y 33,33 µs |
| **N<sub>CP,l</sub>** | Largo del prefijo cíclico del símbolo l | En unidades de T<sub>c</sub>: 144κ·2<sup>−μ</sup>, más 16κ en los símbolos l = 0 y l = 7·2<sup>μ</sup>. | Corto: 9216 (n3), 4608 (n78); largo: 10 240 y 5632. Por T<sub>c</sub>: 4,69 y 2,34 µs (largo: 5,21 y 2,86 µs) |
| **T<sub>symb,l</sub>** | Duración total del símbolo l | T<sub>symb,l</sub> = (N<sub>u</sub> + N<sub>CP,l</sub>)·T<sub>c</sub>: parte útil más CP. | Con CP corto: 71,35 µs (n3), 35,68 µs (n78); con CP largo: 71,88 y 36,20 µs |
| **f<sub>s</sub>** | Frecuencia de muestreo | Cuántas muestras por segundo genera o lee la radio (la USRP). Se expresa en Msps (millones de muestras por segundo). | 23,04 Msps (`srate` del gNB) |
| **t<sub>s</sub>** | Tiempo de muestra | Duración de una muestra: t<sub>s</sub> = 1/f<sub>s</sub>. | 43,40 ns |
| **N<sub>FFT</sub>** | Tamaño de la FFT/IFFT | Cantidad de puntos (subportadoras) de la transformada. Cumple N<sub>FFT</sub> = f<sub>s</sub>/Δf. Las que no se usan van en cero. | 1536 (n3), 768 (n78) |
| **N<sub>CP</sub>** (en muestras) | Prefijo cíclico contado en muestras | El mismo CP pero contado en muestras de la radio: CP corto: 144·N<sub>FFT</sub>/2048; el CP largo suma 16κ·T<sub>c</sub>·f<sub>s</sub> (12 muestras a 23,04 Msps, 16 a 30,72). | 108 y 120 (n3), 54 y 66 (n78) |
| **N<sub>sc</sub><sup>RB</sup>** | Subportadoras por bloque de recursos | Fijo en NR. | 12 |
| **N<sub>RB</sub>** | Cantidad de PRB del canal | Cuántos bloques de 12 subportadoras entran en el ancho de banda (TS 38.101-1, tabla 5.3.2-1). | 106 (n3), 51 (n78) |
| **M<sub>RB</sub><sup>PUSCH</sup>** | PRB asignados al PUSCH | Cuántos PRB le da el gNB al teléfono para transmitir en un slot. Con DFT-s-OFDM tiene que ser 2<sup>α2</sup>·3<sup>α3</sup>·5<sup>α5</sup>. | Variable; máx. 100 (n3) o 50 (n78) |
| **α2, α3, α5** | Exponentes de la regla de PRB | Números enteros no negativos (0, 1, 2…). La regla pide que la cantidad de PRB se pueda escribir como producto de potencias de 2, 3 y 5. | Ej.: 100 = 2²·3⁰·5² |
| **M** (o M<sub>sc</sub><sup>PUSCH</sup>) | Tamaño de la DFT | Subportadoras asignadas al PUSCH: M = 12·M<sub>RB</sub><sup>PUSCH</sup>. Es la cantidad de símbolos modulados que entran a la DFT por cada símbolo OFDM. | Ej.: 10 PRB → M = 120 |
| **x(i)** | Símbolos modulados | Los símbolos QPSK/QAM que salen del modulador, antes de la DFT (dominio del tiempo). | — |
| **y(k)** | Salida de la DFT | Los mismos datos pasados al dominio de la frecuencia; son los que se colocan en las subportadoras asignadas. | — |
| **k** | Índice de subportadora | Posición en frecuencia dentro de la DFT o de la grilla. | — |
| **c** | Velocidad de la luz | Se usa para pasar el largo del CP a una distancia (diferencia de recorrido de los ecos que el CP cubre). | 3·10⁸ m/s |
| **RE** | Elemento de recurso | Una subportadora durante un símbolo OFDM: la unidad mínima de la grilla. | — |

### Siglas y términos

| Sigla o término | Significado |
| --- | --- |
| **CP** | Prefijo cíclico (*cyclic prefix*): copia del final del símbolo que se pega al principio. Si los ecos llegan con un retardo menor que el CP, no hay interferencia entre símbolos y la convolución con el canal se comporta como circular (cada subportadora se ecualiza con un solo coeficiente). **Normal** o **extendido** según su largo. |
| **SCS** | Separación entre subportadoras (*subcarrier spacing*), lo mismo que Δf. |
| **PRB** | Bloque de recursos físicos (*physical resource block*): 12 subportadoras contiguas. Es la unidad con la que el gNB asigna frecuencia. |
| **Slot** | Grupo de 14 símbolos OFDM (con CP normal). Dura 1 ms con μ = 0 y 0,5 ms con μ = 1. |
| **Subtrama / trama** | Subtrama: 1 ms (contiene 2<sup>μ</sup> slots). Trama: 10 ms (10 subtramas). |
| **OFDM** | Multiplexación por división de frecuencias ortogonales: los datos se reparten en muchas subportadoras angostas. |
| **CP-OFDM** | OFDM con prefijo cíclico. La forma de onda de bajada en NR y una opción de subida. |
| **DFT-s-OFDM** | OFDM con una DFT previa (*DFT-spread OFDM*, también llamado SC-FDMA en LTE). Solo en subida; baja el PAPR. |
| **Transform precoding** | El nombre que usa la norma para esa DFT previa. Se habilita con `transformPrecoder`. |
| **DFT / IFFT / FFT** | Transformada discreta de Fourier y sus versiones rápida e inversa. La IFFT pasa las subportadoras al dominio del tiempo para transmitir. |
| **PAPR** | Relación entre la potencia pico y la potencia media de la señal (*peak-to-average power ratio*). |
| **Back-off** | Margen que se deja por debajo de la saturación del amplificador para no distorsionar los picos. |
| **PUSCH / PDSCH** | Canal físico compartido de subida / de bajada: donde viajan los datos del usuario. |
| **Delay spread** | Dispersión de retardo: cuánto se extienden en el tiempo las copias de la señal que llegan por distintos caminos. Para dimensionar el CP importa el exceso de retardo máximo significativo respecto de la primera llegada (que no siempre es un camino directo); también se usa el valor RMS. |
| **Banda de guarda** | En la IFFT, los puntos fuera de la grilla de PRB, que van en cero. Ayudan a que la señal quede dentro del canal, pero no alcanzan solos: las guardas de RF las fija TS 38.101-1 §5.3.3. No hay que confundirlas con los PRB de la grilla que un PUSCH no usa, que pueden llevar otros canales. |
| **FDD / TDD** | Dúplex por frecuencia (subida y bajada en frecuencias distintas, como n3) o por tiempo (misma frecuencia, se turnan en el tiempo, como n78). |
| **n3 / n78** | Bandas de NR: n3 en 1800 MHz (FDD) y n78 en 3,5 GHz (TDD). |
| **ARFCN** | Número de canal que codifica la frecuencia de la portadora. |
| **Msps** | Millones de muestras por segundo. |
| **Clase 3** | Clase de potencia del teléfono: potencia máxima nominal de 23 dBm (≈ 200 mW), con las tolerancias y reducciones que fija TS 38.101-1 §6.2. |
| **Rel-15** | Release 15 de 3GPP: la primera versión de 5G NR, la que fija la consigna. |

## 1. Qué hacía el HTML original

Explicaba la cadena de transmisión de subida de un teléfono 5G con DFT-s-OFDM, en estas secciones:

| Sección | Contenido |
| --- | --- |
| Comparativa de PAPR | Compara CP-OFDM (bajada, PAPR de "8 a 12 dB") con DFT-s-OFDM (subida, "4 a 6 dB"), con dibujos de las formas de onda y del amplificador. |
| 0. Cálculos de timing (n3) | Para n3 FDD (15 kHz, 106 PRB): "delay spread" τ = 1/(4·SCS) = 16,67 µs, f<sub>s</sub> = 30,72 MHz, CP = 512 muestras, símbolo = 1536 + 512 = 2048 muestras = 66,67 µs y 14 símbolos = 0,9333 ms. |
| 1. Flujo del transmisor | Modulación → DFT de M puntos → mapeo contiguo → IFFT de 1536 → CP de 512. |
| 2. Transform precoding | Fórmula de la DFT y ejemplo de M = 12 × N<sub>PRB</sub>, incluido M = 1272 para los 106 PRB. |
| 3. Mapeo en la grilla | Bloque contiguo de M subportadoras con ceros a los costados, en una IFFT de 1536 puntos. |
| 4. Símbolo con CP | Barra con CP de 512 y parte útil de 1536 (50 µs), con una tabla de parámetros de n3. |
| 5. Cálculos para n78 | Lo mismo para 30 kHz y 51 PRB: 768 + 256 = 1024 muestras a 30,72 MHz, CP de 8,33 µs y 14 símbolos = 0,4667 ms. |

**Lo que estaba bien:**
- La estructura general del proceso.
- 106 PRB con 15 kHz y 51 PRB con 30 kHz (1272 y 612 subportadoras).
- 1536 = 3·2⁹ y 768 = 3·2⁸ como tamaños de FFT de base mixta.
- Las frecuencias de n3: DL 1842,5 MHz y UL 1747,5 MHz, iguales a nuestra configuración (ARFCN 368500).
- La asignación contigua de PRB en subida con DFT-s-OFDM.
- La potencia máxima nominal de 23 dBm (clase 3).

## 2. Errores, correcciones y fuentes

Por cada error: el valor original, el valor correcto y su fuente. La columna "Verificado" indica si esa fuente se leyó en esta revisión.

### 2.1 El prefijo cíclico no es 1/4 del símbolo (el error de fondo)

- **Original:** "τ = 1/(4·SCS)" y N<sub>CP</sub> = τ/t<sub>s</sub> = 512 muestras sobre 2048 (n3) y 256 sobre 1024 (n78).
- **Corrección:** en NR, el CP **normal** dura

  N<sub>CP,l</sub> = 144κ·2<sup>−μ</sup> (más 16κ en los símbolos l = 0 y l = 7·2<sup>μ</sup>), en unidades de T<sub>c</sub>

  - Con μ = 0 (15 kHz): 144 · 64 · T<sub>c</sub> = **4,69 µs**, y 5,21 µs en los símbolos 0 y 7 de cada slot.
  - Con μ = 1 (30 kHz): 144 · 64 · ½ · T<sub>c</sub> = **2,34 µs**, y 2,86 µs en el símbolo 0 de cada slot. El extra de 16κ (0,52 µs) no se divide por 2<sup>μ</sup>.
  - Es alrededor del 7 % de la parte útil del símbolo, no el 25 %.
  - El original tomó un CP de 1/(4·SCS) y además lo **restó** de la parte útil (512 + 1536 = 2048), así que su CP es 1/3 de la parte útil. Eso no corresponde a ninguna estructura de NR. El tiempo 1/(4·SCS) coincide con el del CP extendido (512κ·2<sup>−μ</sup>, ¼ de la parte útil), pero la norma solo lo permite con μ = 2 (60 kHz), y ahí la parte útil no se acorta. Un CP de ¼ aparece en otros sistemas, como WiFi o DVB-T.
- **Fuente:** TS 38.211 V15.10.0 §5.3.1 (fórmula de N<sub>CP,l</sub>) y §4.2, tabla 4.2-1 (CP extendido solo con μ = 2). **Verificado.**

Las constantes vienen de TS 38.211 §4.1 (**verificado**):
- T<sub>c</sub> = 1/(Δf<sub>max</sub>·N<sub>f</sub>), con Δf<sub>max</sub> = 480·10³ Hz y N<sub>f</sub> = 4096, así que T<sub>c</sub> ≈ 0,509 ns.
- κ = T<sub>s</sub>/T<sub>c</sub> = 64, con T<sub>s</sub> = 1/(Δf<sub>ref</sub>·N<sub>f,ref</sub>), Δf<sub>ref</sub> = 15·10³ Hz y N<sub>f,ref</sub> = 2048. T<sub>s</sub> es la unidad de tiempo de LTE.

### 2.2 La dispersión de retardo no se calcula a partir de la SCS

- **Original:** "Delay spread τ = 1/(4·SCS)".
- **Corrección:** la dispersión de retardo es una propiedad del **canal**, no de la SCS. El CP se dimensiona para que sea más largo que el exceso de retardo máximo significativo (respecto de la primera llegada), más un margen de sincronización.
  - Con 2,34 µs se toleran ecos con hasta unos 700 m más de recorrido (2,34 µs × c = 703 m).
  - Con 4,69 µs, hasta unos 1,4 km (1406 m).
  - Son diferencias de recorrido idealizadas, no radios de celda.
- **Fuente:** teoría de OFDM. No hace falta una norma.

### 2.3 Una IFFT de 1536 puntos con 30,72 MHz no da 15 kHz

- **Original:** IFFT de 1536 con f<sub>s</sub> = 30,72 MHz y SCS = 15 kHz.
- **Corrección:** la separación entre subportadoras es Δf = f<sub>s</sub>/N<sub>FFT</sub>, así que 30,72 MHz / 1536 = **20 kHz**. Para 15 kHz hay dos opciones:
  - **2048 puntos a 30,72 Msps.**
  - **1536 puntos a 23,04 Msps**, la que usa nuestro gNB (`srate: 23.04` en `config/gnb/gnb_b210_00101_n3_*.yml`).

  El original mezclaba el tamaño de FFT de una opción con la frecuencia de muestreo de la otra.
- **Fuente:** definición de la DFT y configuración del proyecto. **Verificado** en los YAML.

### 2.4 El símbolo completo no dura 1/SCS

- **Original:** "T<sub>simb</sub> = 2048 / 30,72 MHz = 1/15 kHz = 66,67 µs", con la IFFT "útil" en 50 µs y el CP adentro.
- **Corrección:** la **parte útil** dura 1/Δf y el CP se **suma**:

  T<sub>symb,l</sub> = (N<sub>u</sub> + N<sub>CP,l</sub>)·T<sub>c</sub>, con N<sub>u</sub> = 2048κ·2<sup>−μ</sup>

  - Con 15 kHz: 66,67 + 4,69 = **71,35 µs**.
  - Con 30 kHz: 33,33 + 2,34 = **35,68 µs**.
- **Fuente:** TS 38.211 V15.10.0 §5.3.1. **Verificado.**

### 2.5 Un slot dura 1 ms (μ = 0) o 0,5 ms (μ = 1), no 0,9333 ni 0,4667 ms

- **Original:** 14 símbolos = 0,9333 ms (n3) y 0,4667 ms (n78).
- **Corrección:** al sumar los CP, el slot cierra exacto. Por ejemplo, a 23,04 Msps:
  - n3: 12 × (1536 + 108) + 2 × (1536 + 120) = 23 040 muestras = **1 ms**.
  - n78: 13 × (768 + 54) + (768 + 66) = 11 520 muestras = **0,5 ms**.

  Lo que le faltaba al original (1 − 14/15 = 0,0667 ms con μ = 0 y 0,5 − 14/30 = 0,0333 ms con μ = 1) son los CP. El original sí tenía un CP, pero lo sacaba de la parte útil: al corregirlo, la parte útil vuelve a ser 1/SCS y el CP normativo se suma.
- **Fuente:** TS 38.211 V15.10.0 §4.3.1 (subtrama de 1 ms) y §4.3.2 (14 símbolos por slot con CP normal y 2<sup>μ</sup> slots por subtrama). **Verificado.**

### 2.6 Los valores de n78

- **Original:** 768 (IFFT) + 256 (CP) = 1024 muestras a 30,72 MHz, con parte útil de 25 µs y CP de 8,33 µs.
- **Corrección:**
  - A 30,72 Msps con 30 kHz: FFT de **1024** y CP de **72** muestras (88 en el símbolo 0 de cada slot).
  - A 23,04 Msps, en nuestro gNB: FFT de **768** y CP de **54** muestras (66).
  - En los dos casos: parte útil de 33,33 µs y CP de 2,34 µs (2,86 µs).
  - Es lo mismo que calcula el panel del proyecto para la tarjeta de la celda (`fft_details` en `docker/dashboard/app.py`).
- **Fuente:** TS 38.211 V15.10.0 §5.3.1. **Verificado.**

### 2.7 Con DFT-s-OFDM no se pueden asignar 106 PRB

- **Original:** "si le concede los 106 PRB completos del canal, M = 1272".
- **Corrección:** con transform precoding, la cantidad de PRB del PUSCH tiene que cumplir

  M<sub>RB</sub><sup>PUSCH</sup> = 2<sup>α2</sup> · 3<sup>α3</sup> · 5<sup>α5</sup>, con α no negativos

  - **n3:** 106 = 2·53 no cumple. El máximo es **100 PRB** (M = 1200).
  - **n78:** 51 = 3·17 tampoco cumple. El máximo es **50 PRB** (M = 600).
  - El original no mencionaba esta restricción.
- **Fuente:** TS 38.211 V15.10.0 §6.3.1.4 ("Transform precoding"). **Verificado:** la fórmula se leyó de la ecuación de la norma.

### 2.8 Afirmaciones exageradas o sin fuente

| Original | Corrección | Fuente |
| --- | --- | --- |
| PAPR de "8 a 12 dB" contra "4 a 6 dB", "ahorro de 3–4 dB" | La ventaja de DFT-s-OFDM existe, pero las cifras dependen de la modulación, la asignación, el sobremuestreo y la probabilidad de excedencia con que se mida el PAPR. Sin esas condiciones, ningún intervalo (ni el original ni otro) está justificado. | 3GPP no fija el PAPR. **Sin fuente concreta.** |
| "Duplica el alcance en borde de celda" | Con pérdida ∝ d<sup>n</sup>, G dB de mejora multiplican el alcance por 10<sup>G/(10n)</sup>. Con 3 dB: × 1,41 en espacio libre (n = 2) y menos en entornos reales (n > 2). No lo duplica. | Presupuesto de enlace. |
| "Banda media (> 3 GHz) usa μ = 1" | No es una regla. n78 admite varias SCS para datos, y μ = 1 es la elección habitual. | TS 38.101-1. **No verificado.** |
| "En la gNodeB no es crítico porque está enchufada a la red eléctrica trifásica" | Se quitó. No aporta a la explicación técnica. | — |

## 3. Tabla corregida (CP normal; entre paréntesis, el CP largo)

| | n3 FDD, μ = 0, 15 kHz | n78 TDD, μ = 1, 30 kHz |
| --- | --- | --- |
| PRB en 20 MHz | 106 (1272 subportadoras) | 51 (612 subportadoras) |
| Máximo de PRB de PUSCH con DFT-s-OFDM | 100 | 50 |
| **Nuestro gNB (23,04 Msps):** FFT / CP corto (largo) | 1536 / 108 (120) | 768 / 54 (66) |
| A 30,72 Msps: FFT / CP corto (largo) | 2048 / 144 (160) | 1024 / 72 (88) |
| Puntos de la IFFT fuera de la grilla, a 23,04 Msps | 264 | 156 |
| Parte útil del símbolo (1/Δf) | 66,67 µs | 33,33 µs |
| CP normal corto (largo) | 4,69 µs (5,21 µs) | 2,34 µs (2,86 µs) |
| Símbolos con CP largo | 0 y 7 de cada slot | 0 de cada slot |
| Símbolo con CP corto (largo) | 71,35 µs (71,88 µs) | 35,68 µs (36,20 µs) |
| Slot de 14 símbolos | 1 ms | 0,5 ms |

## 4. Fuentes

| Fuente | Qué se tomó | Verificado |
| --- | --- | --- |
| 3GPP TS 38.211 V15.10.0 §4.1 | T<sub>c</sub>, κ = 64, T<sub>s</sub> | Sí |
| 3GPP TS 38.211 V15.10.0 §4.2, tabla 4.2-1 | Numerologías; CP extendido solo con μ = 2 | Sí |
| 3GPP TS 38.211 V15.10.0 §4.3.1 y §4.3.2 | Subtrama de 1 ms, 14 símbolos por slot | Sí |
| 3GPP TS 38.211 V15.10.0 §5.3.1 | N<sub>u</sub>, N<sub>CP,l</sub>, T<sub>symb,l</sub> | Sí |
| 3GPP TS 38.211 V15.10.0 §6.3.1.4 | M<sub>RB</sub><sup>PUSCH</sup> = 2<sup>α2</sup>·3<sup>α3</sup>·5<sup>α5</sup> | Sí |
| 3GPP TS 38.214 §6.1.2.2 | Asignación contigua (tipo 1) del PUSCH con transform precoding | No por Claude. Codex informó que lo confirmó en la versión Rel-15 de ETSI; falta verificarlo |
| 3GPP TS 38.101-1, tabla 5.3.2-1 | 106 y 51 PRB en 20 MHz | No por Claude. Codex informó que lo confirmó en la Rel-15; falta verificarlo. Los YAML solo fijan el ancho de banda y la SCS |
| `config/gnb/gnb_b210_00101_n3_*.yml` y `..._n78_*.yml` | `srate` 23,04, ARFCN, SCS y ancho de banda | Sí |

La norma Rel-15 se bajó del archivo oficial de 3GPP ([https://www.3gpp.org/ftp/Specs/2026-09/Rel-15/38_series/38211-fa0.zip](https://www.3gpp.org/ftp/Specs/2026-09/Rel-15/38_series/38211-fa0.zip)). Claude la comparó el 2026-11-13 con la Rel-18 (V18.10.0), ya borrada: las fórmulas de §4.1 y §5.3.1 eran idénticas (no quedó registro aparte de esta nota).

## 5. Revisión de Codex (2026-11-17)
Codex revisó este archivo y el HTML corregido (`revisiones/2026-11-17_revision-diagrama-dft.md`). Confirmó todos los valores numéricos: FFT, CP, muestras por slot, máximos de 100 y 50 PRB, y las secciones citadas de TS 38.211. Se incorporaron 12 de sus 13 observaciones:
- el original no usa la estructura del CP extendido: resta el CP de la parte útil;
- el extra del CP largo no se divide por 2<sup>μ</sup>;
- en n3 el CP largo está en los símbolos 0 y 7 de cada slot;
- en el glosario, N<sub>u</sub> y N<sub>CP,l</sub> se dan como cantidades de T<sub>c</sub>;
- se ajustaron las definiciones de dispersión de retardo, CP, banda de guarda, clase 3 y SCS de LTE;
- se quitaron las cifras de PAPR sin fuente y se corrigió la cuenta del alcance;
- se aclaró la trazabilidad de lo verificado.

**Se rechazó la observación 3:** Codex dijo que el parámetro se llama `msg3-transformPrecoding`, pero TS 38.331 V15.30.0 (la copia del proyecto) lo llama `msg3-transformPrecoder`, como ya decía el HTML.
