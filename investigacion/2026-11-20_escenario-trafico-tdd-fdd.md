A continuación se presenta la investigación técnica sobre las especificaciones 3GPP, ITU-R e IETF aplicadas a las configuraciones **A (n78 TDD, 20 MHz, $\mu=1$, 51 PRB, `DDDDDDSUUU`)** y **B (n3 FDD, 20 MHz, $\mu=0$, 106 PRB)** con SISO ($1\text{ TX} / 1\text{ RX}$, 1 capa).

---

## 1. Fórmula de tasa pico aproximada (3GPP TS 38.306 §4.1.2) y cálculo para (A) y (B)

### 1.1. Ecuación y parámetros normativos
* **Fuente:** **3GPP TS 38.306 V15.8.0 (Release 15), §4.1.2** (*"Supported max data rate for DL/UL"*) **[Verificado en la fuente]**.

Para NR, la tasa de datos máxima aproximada (en $\text{Mbit/s}$) para $J$ portadoras componentes (*Component Carriers*, CC) agregadas se define como:

$$\text{Data rate (en Mbps)} = 10^{-6} \cdot \sum_{j=1}^{J} \left( v_{\text{Layers}}^{(j)} \cdot Q_m^{(j)} \cdot f^{(j)} \cdot R_{\max} \cdot \frac{N_{\text{PRB}}^{BW(j),\mu} \cdot 12}{T_s^\mu} \cdot \left(1 - OH^{(j)}\right) \right)$$

Donde cada parámetro corresponde a **[Verificado en la fuente: TS 38.306 §4.1.2]**:
* **$J$:** cantidad de portadoras componentes agregadas ($J = 1$ para operación *single carrier* SA).
* **$v_{\text{Layers}}^{(j)}$:** número máximo de capas MIMO soportadas en la $j$-ésima CC (`maxNumberMIMO-LayersPDSCH` en DL, `maxNumberMIMO-LayersCB-PUSCH` en UL). En el banco SISO con USRP B210 (1 antena TX y 1 RX), $v_{\text{Layers}}^{(1)} = 1$.
* **$Q_m^{(j)}$:** orden de modulación máximo (bits por símbolo de modulación: $Q_m = 6$ para **64QAM**, $Q_m = 8$ para **256QAM**; **TS 38.214 V15.8.0 §5.1.3.1 y §6.1.4.1**).
* **$f^{(j)}$:** factor de escala (*scaling factor*, señalizado en `scalingFactor` según **TS 38.306 §4.2.7.2**), que puede tomar valores $\{1;\, 0,8;\, 0,75;\, 0,4\}$. Si no se incluye, vale $f^{(1)} = 1$. *(Nota normativa en TS 38.306 §4.1.2: para operación NR SA de portadora única, el producto $v_{\text{Layers}}^{(j)} \cdot Q_m^{(j)} \cdot f^{(j)}$ no puede ser menor que $4$).*
* **$R_{\max} = \frac{948}{1024} = 0,92578125$:** tasa de código objetivo máxima (*maximum target code rate*) de LDPC, correspondiente al índice superior de la tabla MCS (**TS 38.214 §5.1.3.1, Tablas 5.1.3.1-1 y 5.1.3.1-2**).
* **$N_{\text{PRB}}^{BW(j),\mu}$:** asignación máxima de PRB en el ancho de banda $BW(j)$ con numerología $\mu$, definida en **3GPP TS 38.101-1 V15.17.0 §5.3.2, Tabla 5.3.2-1** **[Verificado en la fuente]**:
  * $BW = 20\text{ MHz}$, $\mu = 1$ ($\text{SCS} = 30\text{ kHz}$, banda n78): **$N_{\text{PRB}} = 51$** (ocupa $18,36\text{ MHz}$).
  * $BW = 20\text{ MHz}$, $\mu = 0$ ($\text{SCS} = 15\text{ kHz}$, banda n3): **$N_{\text{PRB}} = 106$** (ocupa $19,08\text{ MHz}$).
* **$T_s^\mu$:** duración promedio de un símbolo OFDM en una subtrama de $1\text{ ms}$ para numerología $\mu$ (asumiendo prefijo cíclico normal, 14 símbolos por slot, **TS 38.211 V15.10.0 §4.3.2**):
  $$T_s^\mu = \frac{10^{-3}}{14 \cdot 2^\mu}\text{ [s]} \implies \frac{12}{T_s^\mu} = 12 \cdot 14 \cdot 2^\mu \cdot 10^3 = 168\,000 \cdot 2^\mu\text{ [RE/s por PRB]}$$
* **$OH^{(j)}$:** *overhead* fijo de capa física (control L1/L2, DMRS, CSI-RS, SSB, PRACH) estipulado en **TS 38.306 §4.1.2** **[Verificado en la fuente]**:
  * **FR1 Downlink:** $OH_{\text{DL,FR1}} = \mathbf{0,14}$ ($1 - OH = 0,86$). *(En FR2 es $0,18$).*
  * **FR1 Uplink:** $OH_{\text{UL,FR1}} = \mathbf{0,08}$ ($1 - OH = 0,92$). *(En FR2 es $0,10$).*

---

### 1.2. Aclaración crítica sobre la nota de TS 38.306 §4.1.2 y el ciclo de trabajo TDD
* **[Verificado en la fuente: TS 38.306 V15.8.0 §4.1.2]:** La fórmula de TS 38.306 §4.1.2 define la **capacidad máxima de procesamiento de banda base del UE** (*UE capability*) en DL y en UL por separado, asumiendo que el $100\%$ del tiempo ($14 \cdot 2^\mu$ símbolos cada $1\text{ ms}$) está asignado a esa dirección. La única nota normativa (`NOTE 1`) al pie de la ecuación en TS 38.306 §4.1.2 establece literalmente:
  > *"NOTE 1: Only one of the UL or SUL carriers (the one with the higher data rate) is counted for a cell operating SUL."*
* **[Aclaración sobre lo no presente en TS 38.306 §4.1.2]:** El texto normativo de TS 38.306 §4.1.2 **no incluye** un factor de ciclo de trabajo TDD ni una nota sobre el slot especial `S`, porque un mismo UE debe dimensionar su buffer de procesamiento para el peor caso permitido por su categoría.
* **Cómo se pondera TDD para obtener la tasa pico de la celda (TS 38.213 §11.1 y TS 38.331 §6.3.2 `TDD-UL-DL-ConfigCommon`):** En una celda TDD (*unpaired spectrum*), la tasa pico **efectiva del enlace** se obtiene escalando el resultado de TS 38.306 §4.1.2 por la fracción temporal de símbolos OFDM disponibles para DL ($\eta_{\text{DL}}$) o UL ($\eta_{\text{UL}}$) dentro del período $P$ (`dl-UL-TransmissionPeriodicity`), sumando los slots completos y los símbolos asignados dentro del slot especial/mixto (`S`):
  $$\eta_{\text{DL}} = \frac{14 \cdot n_{\text{slots,DL}} + n_{\text{symb,DL,S}}}{14 \cdot N_{\text{slots/período}}}, \qquad \eta_{\text{UL}} = \frac{14 \cdot n_{\text{slots,UL}} + n_{\text{symb,UL,S}}}{14 \cdot N_{\text{slots/período}}}$$

Para la configuración **A (`DDDDDDSUUU`, período $P = 5\text{ ms}$, $\mu = 1$):**
* En $P = 5\text{ ms}$ con $\mu = 1$ ($T_{\text{slot}} = 0,5\text{ ms}$) hay $N_{\text{slots/período}} = 10\text{ slots} = 140\text{ símbolos OFDM}$.
* En la configuración por defecto de OCUDU (`dl_ul_tx_period: 10`, `nof_dl_slots: 6`, `nof_dl_symbols: 8`, `nof_ul_slots: 3`, `nof_ul_symbols: 0`):
  * **Símbolos DL:** $6 \times 14 + 8 = 92\text{ símbolos}$ de $140 \implies \eta_{\text{DL}} = \frac{92}{140} = \frac{23}{35} \approx \mathbf{0,65714}$ ($65,71\%$).
  * **Símbolos de guarda/flexibles (`F` en slot `S`):** $14 - 8 - 0 = 6\text{ símbolos}$ de $140$ ($4,29\%$, equivalentes a $6 \times 35,71\ \mu\text{s} \approx 214,3\ \mu\text{s}$ de *guard period* GP para conmutación DL$\to$UL y propagación).
  * **Símbolos UL:** $3 \times 14 + 0 = 42\text{ símbolos}$ de $140 \implies \eta_{\text{UL}} = \frac{42}{140} = \frac{3}{10} = \mathbf{0,30000}$ ($30,00\%$).
  *(Nota: si no se contaran los 8 símbolos DL del slot `S`, la fracción DL por slots enteros sería $6/10 = 0,60$).*

---

### 1.3. Cálculo numérico paso a paso para (A) y (B) con $v_{\text{Layers}}=1$ y $f=1$

#### Configuración A: n78 TDD, 20 MHz, $\mu=1$ (30 kHz), $N_{\text{PRB}} = 51$
* Tasa bruta de REs ($100\%$ del tiempo):
  $$\frac{N_{\text{PRB}} \cdot 12}{T_s^1} = 51 \cdot 12 \cdot 14 \cdot 2^1 \cdot 10^3 = 17,136 \times 10^6\text{ RE/s}$$
* Multiplicando por $R_{\max} = \frac{948}{1024} = 0,92578125$:
  $$17,136 \times 0,92578125 = 15,8641875\text{ Mbit/s por bit de } Q_m \text{ (antes de } OH \text{ y TDD)}$$

#### Configuración B: n3 FDD, 20 MHz, $\mu=0$ (15 kHz), $N_{\text{PRB}} = 106$
* Tasa bruta de REs ($100\%$ del tiempo en DL y $100\%$ en UL simultáneamente por espectro pareado):
  $$\frac{N_{\text{PRB}} \cdot 12}{T_s^0} = 106 \cdot 12 \cdot 14 \cdot 2^0 \cdot 10^3 = 17,808 \times 10^6\text{ RE/s}$$
  *(Observación física: con $\mu=0$ entran $106\text{ PRB}$ frente a los $51\text{ PRB}$ de $\mu=1$, lo que otorga un $\frac{106}{2 \times 51} - 1 = +3,92\%$ más de subportadoras útiles por menor banda de guarda en TS 38.101-1 Tabla 5.3.2-1).*
* Multiplicando por $R_{\max} = \frac{948}{1024}$:
  $$17,808 \times 0,92578125 = 16,4863125\text{ Mbit/s por bit de } Q_m \text{ (antes de } OH\text{)}$$

#### Tabla comparativa de tasas pico (1 capa, $f=1$)

| Configuración y Dirección | $N_{\text{PRB}}$ | $\mu$ | $OH$ (FR1) | Fracción temporal ($\eta$) | Tasa pico $Q_m = 6$ (**64QAM**) | Tasa pico $Q_m = 8$ (**256QAM**) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **A (n78) — DL** *(TS 38.306 puro, 100%)* | 51 | 1 | 0,14 | $1,0000$ ($140/140$) | $81,86\text{ Mbit/s}$ | $109,15\text{ Mbit/s}$ |
| **A (n78) — DL TDD** *(6D + 8 símb. en S)* | 51 | 1 | 0,14 | **$0,6571$** ($92/140$) | **$53,79\text{ Mbit/s}$** | **$71,72\text{ Mbit/s}$** |
| **A (n78) — DL TDD** *(solo 6 slots D enteros)* | 51 | 1 | 0,14 | $0,6000$ ($84/140$) | $49,12\text{ Mbit/s}$ | $65,49\text{ Mbit/s}$ |
| **A (n78) — UL** *(TS 38.306 puro, 100%)* | 51 | 1 | 0,08 | $1,0000$ ($140/140$) | $87,57\text{ Mbit/s}$ | $116,76\text{ Mbit/s}$ |
| **A (n78) — UL TDD** *(3U + 0 símb. en S)* | 51 | 1 | 0,08 | **$0,3000$** ($42/140$) | **$26,27\text{ Mbit/s}$** | **$35,03\text{ Mbit/s}$** |
| **B (n3) — DL FDD** *(portadora DL continua)* | 106 | 0 | 0,14 | **$1,0000$** | **$85,07\text{ Mbit/s}$** | **$113,43\text{ Mbit/s}$** |
| **B (n3) — UL FDD** *(portadora UL continua)* | 106 | 0 | 0,08 | **$1,0000$** | **$91,00\text{ Mbit/s}$** | **$121,34\text{ Mbit/s}$** |

---

## 2. Diferencias esperables entre TDD y FDD en latencia y comportamiento de TCP

### 2.1. Estructura de trama y granularidad de slot
* **TS 38.211 V15.10.0 §4.3.2, Tablas 4.3.2-1 y 4.3.2-2** **[Verificado en la fuente]**:
  * En **Configuración A ($\mu=1$, $\text{SCS}=30\text{ kHz}$)**, cada slot dura $T_{\text{slot}} = \frac{1\text{ ms}}{2^1} = \mathbf{0,5\text{ ms}}$ ($20\text{ slots}$ por trama de $10\text{ ms}$).
  * En **Configuración B ($\mu=0$, $\text{SCS}=15\text{ kHz}$)**, cada slot dura $T_{\text{slot}} = \frac{1\text{ ms}}{2^0} = \mathbf{1,0\text{ ms}}$ ($10\text{ slots}$ por trama de $10\text{ ms}$).
* **Paradoja numerología vs. duplexación:** Aunque el slot de n78 ($\mu=1$, $0,5\text{ ms}$) dura la mitad que el de n3 ($\mu=0$, $1,0\text{ ms}$), en TDD una transmisión o realimentación solo puede ocurrir en un slot/símbolo cuya dirección coincida con `tdd-UL-DL-ConfigurationCommon` (**TS 38.213 V15.8.0 §11.1, Tabla 11.1.1-1**). En FDD hay oportunidades de DL y de UL en **todos** los slots de $1\text{ ms}$.

### 2.2. Temporización HARQ-ACK ($K_1$) y planificación UL ($K_2$)
1. **Retardo PDSCH $\to$ HARQ-ACK ($K_1$):**
   * **Fuente:** **3GPP TS 38.213 V15.8.0 §9.2.3** (*"UE procedure for reporting HARQ-ACK"*) y **TS 38.214 V15.8.0 §5.1.2.1** **[Verificado en la fuente]**.
   * Si el UE termina de recibir un PDSCH en el slot $n$, transmite el correspondiente HARQ-ACK en el PUCCH (o PUSCH) en el slot $n + k$, donde $k$ (denominado $K_1$) es indicado por el campo *PDSCH-to-HARQ_feedback timing indicator* de la DCI formato 1_0 o 1_1 (o fijado por `dl-DataToUL-ACK` en RRC). Para DCI 1_0, el conjunto por defecto de $K_1$ es $\{1, 2, 3, 4, 5, 6, 7, 8\}$ slots (**TS 38.213 §9.2.3**).
   * **Restricción de tiempo de procesamiento del UE ($N_1$):** Según **TS 38.214 §5.3, Tabla 5.3-1** (*UE processing time for Capability 1*), el UE requiere $N_1 = 8\text{ símbolos OFDM}$ (para $\mu=0$) o $N_1 = 10\text{ símbolos OFDM}$ (para $\mu=1$, con DMRS adicional: $13\text{ símbolos}$) entre el fin del PDSCH y el inicio del PUCCH.
   * **Efecto en FDD (n3, $\mu=0$):** Todo slot $n+K_1$ tiene UL activo. Con un $K_1$ típico de $2$ a $4$ slots en SDR (por latencia de procesamiento host/USB), el HARQ-ACK vuelve de manera **uniforme** en $2\text{ a }4\text{ ms}$, independientemente del slot en que cayó el PDSCH.
   * **Efecto en TDD (n78, $\mu=1$, patrón `D0 D1 D2 D3 D4 D5 S6 U7 U8 U9`):** El PUCCH con HARQ-ACK **solo puede transmitirse en `U7`, `U8` o `U9`**. Por lo tanto, un PDSCH transmitido en el primer slot de bajada (`D0`, $t=0\text{ ms}$) no puede ser confirmado hasta al menos `U7` ($t = 3,5\text{ ms}$, es decir, $K_1 = 7\text{ slots}$). Además, los HARQ-ACK de varios slots DL (`D0..S6`) deben multiplexarse en los pocos slots UL (`U7..U9`) mediante un *HARQ-ACK codebook* Tipo 1 (semi-estático, **TS 38.213 §9.1.2**) o Tipo 2 (dinámico, **TS 38.213 §9.1.3**). Si falla la decodificación de un PUCCH en `U7..U9`, se pierde la confirmación de múltiples bloques DL a la vez.

2. **Retardo UL Grant (DCI 0_0/0_1) $\to$ PUSCH ($K_2$) y solicitud de recursos (SR/BSR):**
   * **Fuente:** **3GPP TS 38.214 V15.8.0 §6.1.2.1** (*"Resource allocation in time domain"*, Tablas 6.1.2.1.1-2 y 6.1.2.1.1-3) y **§6.4** (*UE PUSCH preparation procedure time $N_2$*) **[Verificado en la fuente]**.
   * Si el UE recibe una DCI de *UL grant* en el slot $n$, transmite el PUSCH en el slot $n + K_2$.
   * **En TDD (`D0..D5 S6 U7..U9`):**
     * Los grants DCI solo pueden enviarse en slots con PDCCH (`D0..S6`) y el PUSCH solo puede salir en `U7..U9`.
     * **Peor caso de acceso UL (SR $\to$ Grant $\to$ PUSCH):** Si un paquete IP llega a la cola del UE (p. ej., un paquete `ping` o un `TCP ACK`) justo al terminar `U9` ($t = 5,0\text{ ms}$), el UE **no tiene canal de subida** durante los próximos $7\text{ slots}$ ($3,5\text{ ms}$, `D0..S6`). Recién puede enviar el *Scheduling Request* (SR en PUCCH, **TS 38.321 §5.4.4** y **TS 38.213 §9.2.4**) en el próximo slot UL configurado para SR (dentro de `U7..U9`, sumando de $0\text{ a }3,5\text{ ms}$ de espera de ventana UL, o múltiplos de $5\text{ ms}$ según la periodicidad `sr-ProhibitTimer` / `PeriodicityAndOffset`). Luego el gNB procesa el SR, envía el *UL Grant* en el siguiente bloque DL (`D0..S6`) y el UE espera otro offset $K_2$ hasta el siguiente bloque UL (`U7..U9`) para enviar el *Buffer Status Report* (BSR) o los datos.
     * **En FDD (n3):** Hay PDCCH (DL) y PUCCH/PUSCH (UL) en **todos los slots** de $1\text{ ms}$, eliminando el *TDD alignment delay* (espera de ventana UL/DL).

### 2.3. Impacto sobre el RTT, la asimetría DL/UL y la dinámica de TCP
1. **RTT base y jitter de alineación TDD:**
   * En **TDD (`DDDDDDSUUU`)**, el bloqueo de subida durante $3,5\text{ ms}$ de cada $5\text{ ms}$ introduce una variable aleatoria de espera de alineación (*alignment jitter*) en cada cruce de interfaz de aire. Sumando la cadena $\text{SR} \to \text{UL Grant} \to \text{BSR/PUSCH}$, el RTT de plano de usuario en TDD presenta un piso de $\sim 8\text{ a }15\text{ ms}$ y una dispersión (jitter) intrínseca de múltiplos del período TDD ($5\text{ ms}$).
   * En **FDD**, al no existir tiempos muertos de dirección, la latencia depende únicamente de $T_{\text{slot}} = 1\text{ ms}$, la periodicidad del SR y los tiempos de procesamiento $K_1, K_2$, logrando menor jitter de planificación (aunque un slot individual de $\mu=0$ sea de $1\text{ ms}$ frente a $0,5\text{ ms}$).
2. **Compresión y agrupamiento de ACKs de TCP (*ACK compression / clustering*) en TDD:**
   * Durante una descarga TCP (**DL**), el gNB transmite datos continuamente durante `D0..S6` ($3,29\text{ ms}$), pero el UE no puede devolver los `TCP ACK` de capa 4 hasta que llega la ventana `U7..U9` ($1,5\text{ ms}$), y solo después de haber obtenido un *UL Grant*.
   * Como consecuencia, los `TCP ACK` regresan en **ráfagas cada $5\text{ ms}$** en lugar de llegar espaciados al ritmo de los segmentos DL. Esto altera la estimación de tasa de entrega (*delivery rate*) en algoritmos como TCP CUBIC o BBR y exige que el transmisor soporte ráfagas de envío cuando la ventana se desliza de golpe.
3. **Asimetría de capacidad y *ACK starvation* en tráfico bidireccional:**
   * En TDD la razón de recursos es $\sim 2,2 : 1$ a favor del DL ($65,7\%$ vs. $30,0\%$), y el UL suele tener menor SINR/MCS por limitación de potencia del UE (**TS 38.213 §7.1.1**, $P_{\text{CMAX}} = 23\text{ dBm}$ en Power Class 3 según **TS 38.101-1 Tabla 6.2.1-1**). Si hay tráfico de subida simultáneo o un BLER alto en PUSCH, los `TCP ACK` del flujo de bajada se encolan detrás de los datos de subida o sufren retransmisiones HARQ/RLC AM, frenando el crecimiento de la ventana de congestión (`cwnd`) del flujo DL.
4. **Producto Ancho de Banda-Retardo (BDP) y tamaño de ventana TCP:**
   * Para alcanzar el pico de DL en TDD ($\sim 71,7\text{ Mbit/s}$) con un RTT bajo carga de, por ejemplo, $25\text{ ms}$:
     $$\text{BDP} = 71,7 \times 10^6\text{ bit/s} \times 0,025\text{ s} \approx 1,79\text{ Mbit} \approx \mathbf{224\text{ KB}}$$
   * En FDD ($\sim 113,4\text{ Mbit/s}$), para un mismo RTT de $25\text{ ms}$:
     $$\text{BDP} = 113,4 \times 10^6\text{ bit/s} \times 0,025\text{ s} \approx 2,84\text{ Mbit} \approx \mathbf{354\text{ KB}}$$
   * Si la ventana de recepción o congestión de TCP (`rwnd` / `cwnd`) cae por debajo del BDP (por ejemplo, tras una pérdida de paquete no recuperada a tiempo o un *timeout* por retransmisión RLC AM), el enlace de radio queda subutilizado (slots DL con PRBs vacíos aunque haya datos en el servidor `iperf3`).

---

## 3. Metodología recomendada para medir rendimiento

### 3.1. KPIs de ITU-R M.2410-0 y su aplicación al laboratorio
* **Fuente:** **Report ITU-R M.2410-0 (11/2017)**, *"Minimum requirements related to technical performance for IMT-2020 radio interface(s)"* **[Verificado en la fuente]**.
  1. **Peak data rate (ITU-R M.2410-0 §4.1):** Máxima tasa de datos alcanzable por una única estación móvil bajo condiciones ideales libres de error ($0\%$ BLER residual), cuando se le asignan todos los recursos de radio utilizables en la dirección del enlace (excluyendo *overhead* de señales de referencia y bandas de guarda).
     * *Requisito global IMT-2020:* $20\text{ Gbit/s}$ (DL) y $10\text{ Gbit/s}$ (UL) agregando máximo ancho de banda y capas MIMO.
     * *Aplicación en nuestro banco:* Normalizado a los recursos de nuestra celda SISO de $20\text{ MHz}$ (vía **ITU-R M.2410-0 §4.2 Peak spectral efficiency** y **TS 38.306 §4.1.2**), el techo teórico de referencia contra el que se contrasta `iperf3` es el calculado en la Tabla de la Sección 1.3 (p. ej., **$71,72\text{ Mbit/s}$ DL / $35,03\text{ Mbit/s}$ UL** en n78 TDD 256QAM; **$113,43\text{ Mbit/s}$ DL / $121,34\text{ Mbit/s}$ UL** en n3 FDD 256QAM).
  2. **User experienced data rate (ITU-R M.2410-0 §4.3):** Definido como el **percentil $5\%$ ($P_5$) de la CDF del throughput de usuario** (bits de SDUs entregados correctamente a Capa 3 divididos por el tiempo activo).
     * *Requisito IMT-2020 (Dense Urban eMBB):* $100\text{ Mbit/s}$ (DL) y $50\text{ Mbit/s}$ (UL).
     * *Aplicación en nuestro banco:* Como trabajamos con un único UE estático dentro de una jaula de Faraday (sin distribución espacial multicelda), el concepto de $P_5$ de la CDF se aplica a la **distribución temporal** de los intervalos de reporte de `iperf3` (p. ej., muestras de $1\text{ s}$ a lo largo de $60\text{ s}$ o múltiples corridas) o variando la ganancia de TX/RX (`tx_gain`/`rx_gain`) para emular usuarios desde el centro hasta el borde de celda.
  3. **User plane latency (ITU-R M.2410-0 §4.7.1):** Contribución de la red de radio al tiempo de tránsito **unidireccional** (*one-way*) desde que un paquete IP (SDU de L2/L3) ingresa a la capa 2 del transmisor hasta que sale hacia la capa 3 del receptor, en condiciones **sin carga** (*unloaded*, usuario único) para paquetes IP pequeños (p. ej., payload de 0 bytes + cabecera IP) con el UE en estado activo (`RRC_CONNECTED` sin DRX).
     * *Requisito IMT-2020:* **$4\text{ ms}$** para eMBB y **$1\text{ ms}$** para URLLC (en DL y en UL).
     * *Aplicación en nuestro banco:* Al medir con `ping` (ICMP Echo Request/Reply) sin tráfico de fondo y con el UE recién activo en `RRC_CONNECTED`, obtenemos el $\text{RTT}$. La latencia de plano de usuario unidireccional promedio se estima como $\approx \frac{\text{RTT}}{2}$ (descontando el tránsito en la red Docker del núcleo Open5GS, que es $< 0,2\text{ ms}$), aunque en TDD el retardo de bajada y el de subida no son simétricos (la subida sufre la espera de SR + $K_2$).

### 3.2. Metodologías IETF: RFC 2544 vs. RFC 6349
1. **RFC 2544** (*"Benchmarking Methodology for Network Interconnect Devices"*, **§26.1 Throughput, §26.2 Latency, §26.3 Frame Loss Rate**) **[Verificado en la fuente]**:
   * Diseñada para pruebas sin estado en capas 2/3 usando flujos **UDP** a tasa constante.
   * **Cómo aplicarla con `iperf3 -u -b <tasa>`:** Se realiza un **barrido escalonado de carga ofrecida (*offered load*)** desde el $20\%$ hasta el $120\%$ de la tasa pico teórica de TS 38.306, registrando en el receptor:
     * **Goodput (tasa entregada)** vs. **Offered load**,
     * **Porcentaje de datagramas perdidos** (*Frame/Packet Loss Rate*), y
     * **Jitter RFC 3550** (variación suavizada del retardo entre paquetes reportada por `iperf3` UDP).
   * Permite encontrar el **punto de saturación real de Capa 2/1** de la celda (el codo donde `goodput` deja de crecer igual que `offered load` y se disparan la pérdida de paquetes y el retardo de cola RLC/PDCP), sin que el algoritmo de control de congestión de TCP reduzca la tasa ante un error de radio.
2. **RFC 6349** (*"Framework for TCP Throughput Testing"*, **§3 y §4**) **[Verificado en la fuente]**:
   * Diseñada específicamente para evaluar el rendimiento de **Capa 4 (TCP)**, que depende del RTT, del BDP y de las pérdidas.
   * **Métricas clave definidas en RFC 6349:**
     * **Baseline RTT ($\text{RTT}_0$) y Bottleneck Bandwidth ($\text{BB}$):** medidos sin congestión para calcular el $\text{BDP} = \text{BB} \times \text{RTT}_0$ (**RFC 6349 §3.1**).
     * **TCP Transfer Time Ratio / Ideal vs. Actual TCP Throughput:** compara el throughput alcanzado contra el límite impuesto por la ventana `rwnd`/`cwnd`.
     * **TCP Efficiency (%):** porcentaje de bytes transmitidos que no fueron retransmisiones TCP (**RFC 6349 §4.2**):
       $$\text{TCP Efficiency} = \frac{\text{Transmitted Bytes} - \text{Retransmitted Bytes}}{\text{Transmitted Bytes}} \times 100$$
       *(En `iperf3` en modo emisor se observa directamente a través de la columna `Retr`).*
     * **Buffer Delay (%):** incremento porcentual del RTT medio durante la transferencia TCP ($\text{RTT}_{\text{load}}$) respecto del RTT base sin carga ($\text{RTT}_0$) (**RFC 6349 §4.3**):
       $$\text{Buffer Delay} = \frac{\text{RTT}_{\text{load}} - \text{RTT}_0}{\text{RTT}_0} \times 100$$
       *(Mide el *bufferbloat* en las colas RLC del gNB o del módem del UE).*

### 3.3. Mediciones de Capa 2 (3GPP TS 38.314) y contadores OAM (3GPP TS 28.552) frente a las métricas del gNB (OCUDU)
* **Fuentes:** **3GPP TS 38.314 V15.2.0** (*"NR; Layer 2 measurements"*, **§4**) y **3GPP TS 28.552 V15.5.0** (*"Management and orchestration; 5G performance measurements"*, **§5.1.1**) **[Verificado en la fuente]**.
* *(Nota: los nombres exactos de subsecciones $4.x$ de TS 38.314 y prefijos de familias `DRB.`/`TB.`/`RRU.`/`CARR.` de TS 28.552 §5.1.1 están verificados; cuando el nombre literal de un sub-contador varía entre revisiones de TS 28.552, se indica la familia normativa).*

| Métrica en gNB (OCUDU log / JSON) | Medición L2 en **TS 38.314** | Contadores / Familias en **TS 28.552 §5.1.1** | Relación física y de protocolo con la prueba `iperf3` |
| :--- | :--- | :--- | :--- |
| **`brate` (DL/UL bitrate)** | **§4.1 / §4.2** *Data Volume* y *Scheduled IP Throughput* (PDCP SDU bits / tiempo activo) | **§5.1.1.3** (*UE Throughput*: `DRB.UEThpDl`, `DRB.UEThpUl`) y **§5.1.1.8** (*Data Volume*: `DRB.PdcpSduVolumeDl/Ul`) | Tasa a nivel MAC/RLC/PDCP. Siempre es ligeramente superior al *goodput* de `iperf3` por las cabeceras IP (20 B), UDP (8 B) o TCP (20–32 B), PDCP, RLC y MAC. |
| **`prb` / Grilla de slots** | **§4.1 / §4.2** *PRB usage* (porcentaje de PRBs usados en DL/UL) | **§5.1.1.2** (*Radio Resource Utilization*: `RRU.PrbTotDl`, `RRU.PrbTotUl`, `RRU.PrbUsedDl`, `RRU.PrbUsedUl`) | Mide si `iperf3` logra **saturar la grilla** ($51\text{ PRB}$ en n78 o $106\text{ PRB}$ en n3 en cada slot disponible). Si `PRB used < PRB avail`, el cuello de botella está en la ventana TCP, en el SR/BSR o en el procesador del host (`UL busy`), no en la capacidad RF. |
| **`bler` (DL/UL)** y **`nok` / `ok`** | *(Métrica de capa MAC/PHY asociada a HARQ)* | **§5.1.1** Familia `TB.` (*Transport Block counters*: `TB.TotNbrDlInitial`, `TB.IntialErrNbrDl`, `TB.ErrTotalNbrDl` y equivalentes UL) | **BLER inicial** ($\approx 10\%$ objetivo típico de *Outer Loop Link Adaptation*, OLLA) vs. **BLER residual** (tras agotar las 4 transmisiones HARQ). Si hay BLER inicial del $10\%$ recuperado por HARQ, UDP no pierde paquetes pero sube la latencia; si hay BLER residual, actúa RLC AM o se pierden paquetes IP. |
| **`mcs` (DL/UL)** | *(Asignación del scheduler MAC)* | **§5.1.1** Distribución de MCS / modulación por TB (`TB.TotNbrDlInitial.Qpsk`, `.16Qam`, `.64Qam`, `.256Qam` / distribución MCS) | Índice $I_{\text{MCS}}$ elegido por el gNB (**TS 38.214 Tablas 5.1.3.1-1 / 5.1.3.1-2**). Define $Q_m$ y la tasa de código $R$, determinando el *Transport Block Size* (TBS, **TS 38.214 §5.1.3.2**) en cada slot. |
| **`cqi`** | *(Reporte CSI de L1/L2, **TS 38.214 §5.2.2.1**)* | **§5.1.1** Distribución de CQI reportado (`CARR.WBCqiDist.BinX` / *Wideband CQI distribution*) | Índice $0..15$ (**TS 38.214 Tablas 5.2.2.1-2 / 5.2.2.1-3**) con el que el UE informa qué modulación y tasa de código soporta en DL con $\text{BLER} \le 0,1$. *(En este proyecto, como el Redmi casi no reporta CSI en PUCCH F2, el gNB depende más del HARQ-ACK para adaptar el MCS DL).* |
| **`bsr`** | **§4.1 / §4.2** *Number of active UEs* (UEs con datos en buffer DL/UL) y **TS 38.321 §5.4.5 / §6.1.3.1** | **§5.1.1** Contadores de UEs activos con datos en cola (`DRB.MeanActiveUeDl`, `DRB.MeanActiveUeUl`) | *Buffer Status Report* enviado por el UE en MAC CE (**TS 38.321 Tablas 6.1.3.1-1 / 6.1.3.1-2**). Si durante un `iperf3` de subida el BSR es alto pero el throughput es bajo, el UE tiene datos listos y el cuello de botella está en los grants o errores de PUSCH. |
| **`phr`** | **TS 38.321 §5.4.6 / §6.1.3.8** y **TS 38.133 §10.1.17** (*Power Headroom Report*) | *[No verificado un contador estándar en TS 28.552 Rel-15 para histograma de PHR; suele ser métrica de trace/MDT o propietaria del vendedor]* | $\text{PHR} = P_{\text{CMAX,f,c}} - P_{\text{PUSCH\_estimada}}$ (**TS 38.213 §7.7.1**). Cuando al pedir los $51$ o $106\text{ PRB}$ el término $10\log_{10}(2^\mu \cdot M_{\text{RB}})$ lleva al UE a $\text{PHR} \le 0\text{ dB}$, el amplificador del celular entra en saturación ($P_{\text{CMAX}}$), haciendo caer la SINR del PUSCH al asignar toda la banda. |

---

## 4. Lista priorizada de experimentos para profundizar el escenario

Los experimentos se ordenan de mayor a menor impacto didáctico y diagnóstico para el informe, indicando la hipótesis teórica y el resultado esperado. *(Precondición operativa del banco: iniciar cada bloque con el gNB recién reiniciado para evitar la degradación por procesadores de subida trabados `"UL processor is busy"` y con el teléfono en modo `NR only`).*

### Experimento 1 (Prioridad 1): Barrido escalonado de carga UDP (*Offered Load vs. Goodput*) en DL y UL — Comparación n78 TDD vs. n3 FDD
* **Procedimiento:** Ejecutar corridas de `iperf3 -u -l 1350 -t 10 -b <R>` incrementando la tasa ofrecida $R$:
  * En **DL:** $15, 30, 45, 55, 65, 75, 90, 115\text{ Mbit/s}$.
  * En **UL:** $5, 10, 15, 20, 25, 30, 40, 60, 90\text{ Mbit/s}$.
  * Graficar $\text{Goodput}$, $\text{Pérdida (\%)}$, $\text{Jitter (ms)}$ y ocupación de PRBs vs. $\text{Offered Load}$ para (A) n78 TDD y (B) n3 FDD.
* **Teoría que confirma:**
  * Ecuación de capacidad límite de **TS 38.306 §4.1.2** ponderada por el ciclo de trabajo TDD (**TS 38.213 §11.1**) frente al canal continuo de FDD, siguiendo la metodología **RFC 2544 §26.1 / §26.3**.
* **Resultado esperado:**
  * En **n78 TDD DL**, una recta de pendiente $1:1$ ($\text{Goodput} = \text{Offered Load}$, pérdida $\approx 0\%$) hasta el codo de saturación entre **$50\text{ y }68\text{ Mbit/s}$** (según si el MCS se estabiliza en 64QAM o 256QAM), donde los $51\text{ PRB}$ de los $6$ slots DL + slot `S` llegan al $100\%$ de ocupación y toda carga adicional se convierte en pérdida de paquetes.
  * En **n3 FDD DL**, el codo de saturación debe desplazarse hacia arriba en un factor $\approx \frac{106 \times 14}{51 \times 28 \times 0,6571} \approx \mathbf{1,58\times}$ (hasta **$80\text{–}105\text{ Mbit/s}$** a igual MCS).
  * En **UL**, el techo práctico en n78 TDD estará acotado por $\eta_{\text{UL}} = 0,30$ ($\le 26\text{–}35\text{ Mbit/s}$) y por la caída de SINR cuando el UE satura su potencia ($\text{PHR} \le 0\text{ dB}$ al ocupar los $51\text{ PRB}$), mientras que en n3 FDD ($\eta_{\text{UL}} = 1,0$) el techo temporal es $3,33\times$ mayor, por lo que el límite pasará a estar dominado por el presupuesto de potencia del UE repartido en $106\text{ PRB}$ ($10\log_{10}(2^0 \cdot 106) = 20,25\text{ dB}$, casi idéntico a $10\log_{10}(2^1 \cdot 51) = 20,09\text{ dB}$ en **TS 38.213 §7.1.1**).

### Experimento 2 (Prioridad 2): Distribución de latencia (CDF de RTT) y *Bufferbloat* bajo carga — n78 TDD vs. n3 FDD
* **Procedimiento:**
  1. Medir $200$ muestras de `ping -i 0.1` sin tráfico ($\text{RTT}_0$) con el UE activo en `RRC_CONNECTED` en n78 TDD y en n3 FDD.
  2. Repetir el `ping` en paralelo con una transferencia `iperf3` TCP en DL y luego en UL ($\text{RTT}_{\text{load}}$) para calcular el **Buffer Delay** de **RFC 6349 §4.3**.
* **Teoría que confirma:**
  * Temporización HARQ $K_1$ (**TS 38.213 §9.2.3**), preparación PUSCH $K_2$ (**TS 38.214 §6.1.2.1**), espera del slot UL para SR (**TS 38.213 §9.2.4**) y latencia de plano de usuario (**ITU-R M.2410-0 §4.7.1**).
* **Resultado esperado:**
  * Sin carga, n3 FDD mostrará una distribución de RTT más compacta (menor varianza/jitter entre el mínimo y el percentil 90) que n78 TDD, donde la espera de los slots `U7..U9` dentro del período de $5\text{ ms}$ ensancha la CDF del RTT en escalones de $\sim 3,5\text{ a }5\text{ ms}$.
  * Bajo carga TCP saturada, $\text{RTT}_{\text{load}}$ subirá a decenas o cientos de milisegundos (*Buffer Delay* $> 200\%$) debido al encolamiento en los buffers RLC AM del gNB (en DL) o del UE (en UL).

### Experimento 3 (Prioridad 3): Dinámica de TCP — 1 flujo vs. $N$ flujos paralelos (`-P 1`, `-P 4`, `-P 8`) y tráfico bidireccional (`--bidir`)
* **Procedimiento:** Comparar `iperf3 -t 15` en DL con `-P 1` vs. `-P 4`, y luego ejecutar `iperf3 --bidir -t 15` en n78 TDD y en n3 FDD, registrando throughput, retransmisiones TCP (`Retr`) y utilización de PRBs.
* **Teoría que confirma:**
  * **RFC 6349 §3/§4** (relación entre ventana de congestión, BDP, compresión de ACKs y pérdidas/retransmisiones) y el acoplamiento entre UL y DL en TDD.
* **Resultado esperado:**
  * Si un único flujo TCP (`-P 1`) no llena el $100\%$ de los PRBs porque las variaciones de RTT en TDD o una retransmisión reducen `cwnd` por debajo del BDP, pasar a `-P 4` acercará el *goodput* TCP total al máximo alcanzado con UDP en el Experimento 1.
  * Con `--bidir`, en **n78 TDD** se observará una caída pronunciada del throughput DL respecto de la prueba unidireccional: al saturarse el $30\%$ de recursos UL con datos de subida (y caer la SINR UL por $\text{PHR} \approx 0\text{ dB}$, elevando el BLER de PUSCH), los `TCP ACK` del flujo DL sufren retardo de cola y *ACK starvation*. En **n3 FDD**, al disponer del $100\%$ de los slots en UL, la degradación cruzada sobre el DL será significativamente menor.

### Experimento 4 (Prioridad 4): Efecto de las ganancias de RF (`tx_gain` / `rx_gain`) sobre SINR, EVM, CQI, MCS, BLER y PHR (Adaptación de Enlace)
* **Procedimiento:** Manteniendo una transferencia constante en n78 TDD, variar por pasos la ganancia de recepción o transmisión de la B210 (p. ej., `rx_gain` en $\{40, 30, 20, 15\}\text{ dB}$ para UL, o `tx_gain` en $\{80, 65, 50, 40\}\text{ dB}$ para DL) y registrar SINR, EVM (de las constelaciones IQ), MCS medio, BLER y goodput.
* **Teoría que confirma:**
  * *Link Adaptation* (**TS 38.214 §5.1.3.1, §5.2.2.1 y §6.1.4.1**) y control de potencia de lazo cerrado/abierto de PUSCH (**TS 38.213 §7.1.1**).
* **Resultado esperado:**
  * En **DL**, al bajar `tx_gain` disminuye la SNR en el UE y el MCS desciende escalonadamente ($256\text{QAM} \to 64\text{QAM} \to 16\text{QAM} \to \text{QPSK}$), manteniendo el BLER inicial cerca del objetivo del lazo externo ($\sim 10\%$) a costa de reducir el TBS (**TS 38.214 §5.1.3.2**) y el throughput.
  * En **UL**, también se verificará si un exceso de ganancia/nivel de señal dentro de la jaula de Faraday a corta distancia provoca compresión del front-end receptor de la B210, encontrando el punto óptimo de menor EVM y mayor SINR.

### Experimento 5 (Prioridad 5): Comparación de tabla MCS `qam64` (Tabla 5.1.3.1-1) vs. `qam256` (Tabla 5.1.3.1-2)
* **Procedimiento:** En condiciones de alta SNR dentro de la jaula, forzar en la configuración del gNB la tabla MCS de hasta 64QAM ($Q_m \le 6$) frente a la de 256QAM ($Q_m \le 8$) y medir el pico de throughput UDP/TCP y el BLER.
* **Teoría que confirma:**
  * **TS 38.214 §5.1.3.1 (Tablas 5.1.3.1-1 y 5.1.3.1-2)** y la proporción lineal con $Q_m$ en la fórmula de **TS 38.306 §4.1.2**.
* **Resultado esperado:**
  * A máxima eficiencia espectral ($R_{\max} = 948/1024$), pasar de $Q_m = 6$ a $Q_m = 8$ incrementa el TBS máximo y la tasa pico teórica exactamente en un $+\mathbf{33,3\%}$ ($\frac{8}{6} = 1,333$: en n78 TDD DL, de $53,79$ a $71,72\text{ Mbit/s}$). Sin embargo, 256QAM exige una SINR $\sim 5\text{ a }6\text{ dB}$ mayor y un EVM del transmisor $< 3,5\%$ (**TS 38.101-1 §6.4.2.1, Tabla 6.4.2.1-1**); si el EVM de la cadena RF está cerca de ese umbral, 256QAM presentará mayor BLER y retransmisiones HARQ que 64QAM.

### Experimento 6 (Prioridad 6): Variación del patrón TDD (`tdd_ul_dl_cfg`) y del ancho de banda ($10\text{ MHz}$ vs. $20\text{ MHz}$)
* **Procedimiento:**
  1. Cambiar en n78 el patrón de `6D:1S:3U` ($\eta_{\text{DL}} = 65,7\%, \eta_{\text{UL}} = 30,0\%$) a un patrón más simétrico como `5D:1S:4U` ($\eta_{\text{DL}} = 55,7\%, \eta_{\text{UL}} = 40,0\%$) o de menor período ($2,5\text{ ms}$, $5\text{ slots}$, p. ej., `3D:1S:1U`, $\eta_{\text{DL}} \approx 71,4\%, \eta_{\text{UL}} = 20,0\%$).
  2. Reducir `channel_bandwidth_MHz` de $20\text{ MHz}$ ($51\text{ PRB}$ en $\mu=1$) a $10\text{ MHz}$ ($24\text{ PRB}$ en $\mu=1$, **TS 38.101-1 Tabla 5.3.2-1**).
* **Teoría que confirma:**
  * Dependencia lineal de la tasa pico con las fracciones temporales $\eta_{\text{DL}}, \eta_{\text{UL}}$ (**TS 38.213 §11.1**), dependencia de la latencia de plano de usuario con el período de conmutación TDD, y escalamiento con $N_{\text{PRB}}$ (**TS 38.101-1 Tabla 5.3.2-1** y **TS 38.306 §4.1.2**).
* **Resultado esperado:**
  * Con `5D:1S:4U`, la tasa pico de subida crece en $+\mathbf{33,3\%}$ ($\frac{0,40}{0,30}$, de $35,03$ a $46,70\text{ Mbit/s}$ en 256QAM) mientras la de bajada disminuye un $-\mathbf{15,2\%}$ ($\frac{78}{92}$). Con un período de $2,5\text{ ms}$ (`3D:1S:1U`), el tiempo máximo de bloqueo de subida cae a la mitad ($\sim 1,75\text{ ms}$), reduciendo el RTT y el jitter del `ping`.
  * Al bajar de $20\text{ MHz}$ ($51\text{ PRB}$) a $10\text{ MHz}$ ($24\text{ PRB}$), la tasa pico DL/UL cae en proporción exacta a $\frac{24}{51} = \mathbf{0,4706}$ ($47,1\%$), mientras que en subida el UE dispone de $10\log_{10}(51/24) = \mathbf{+3,27\text{ dB}}$ más de densidad espectral de potencia por PRB (**TS 38.213 §7.1.1**), mejorando el PHR y la SINR del PUSCH.
