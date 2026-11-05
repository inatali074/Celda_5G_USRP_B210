### 1) Aparición del campo `evm` en el log de `PUSCH`, unidades, cálculo, otros canales y métricas JSON

#### Verificado en la fuente
* **Condición para que `evm` y `epre` aparezcan en el log de `PUSCH`:**
  * **Fuente:** Documentación oficial de configuración (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html`, secciones `log` y `expert_phy`) y documentación de análisis con MATLAB (`https://github.com/srsran/srsRAN-matlab`).
  * **Comportamiento según el nivel de log (`phy_level`):**
    * Con `phy_level: info` (o `all_level: info`), el logger de `PHY` emite únicamente la línea resumida de una sola estimación de SINR (`sinr=`):
      ```text
      [PHY] [I] [ 580.17] PUSCH: rnti=0x4601 harq_id=0 prb=[8, 11) symb=[0, 14) mod=QPSK rv=0 tbs=11 crc=OK iter=1.0 sinr=32.9dB t=155.5us uci_t=0.0us ret_t=6.0us
      ```
      *(Verificado también en los logs locales del proyecto, p. ej., [`2026-11-03_gnb_tdd_nronly_completo.log.gz`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/evidencia/04_sesion_pdu/2026-11-03_gnb_tdd_nronly_completo.log.gz)).*
    * Con **`log: phy_level: debug`**, el decorador de logging del procesador `PUSCH` imprime las métricas extendidas de estimación de canal y demodulación, incluyendo las tres variantes de SINR (`sinr_ch_est`, `sinr_eq`, `sinr_evm`), la etiqueta `[sel]` sobre el método activo, y los campos **`evm={:.2f}`**, **`epre={:+.1f}dB`**, `rsrp=` y `t_align=`:
      ```text
      sinr_ch_est=26.9dB sinr_eq=23.9dB sinr_evm[sel]=20.1dB evm=0.06 epre=+22.7dB rsrp=+22.7dB t_align=-0.2us
      ```
  * **Relación con `expert_phy.pusch_sinr_calc_method`:**
    * **Fuente:** `https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html` (sección `expert_phy`).
    * **Cita:** `pusch_sinr_calc_method` acepta `[channel_estimator, post_equalization, evm]`. Define cuál de los tres estimadores se selecciona (`[sel]`) como el `sinr` principal reportado por la capa física hacia las capas superiores (y mostrado como `sinr=` cuando `phy_level: info`).
* **Unidad del campo `evm`:**
  * **Fuente:** Trazas de `UL-PHY` en `github.com/srsran/srsRAN_Project` y `github.com/srsran/srsRAN-matlab`.
  * Está expresado en **fracción lineal adimensional** (magnitud RMS relativa, **no** en porcentaje `%` ni en dB), formateado con `evm={:.2f}` (por ejemplo, `evm=0.04` corresponde a un $4\,\%$ de EVM; `evm=0.06` corresponde a un $6\,\%$). Su equivalente en decibeles se imprime inmediatamente al lado bajo el nombre `sinr_evm` ($\text{SINR}_{\text{EVM}} = -20 \log_{10}(\text{EVM})$).
* **Método de cálculo:**
  * **Fuente:** Documentación de `pusch_sinr_calc_method` en `config_ref.html` y arquitectura de `lib/phy/upper/channel_processors/pusch/` (`pusch_processor_impl` / `pusch_demodulator`).
  * Se calcula en recepción luego de la etapa de ecualización de canal (`channel_equalizer`), comparando los símbolos de datos ecualizados con los puntos ideales de la constelación reconstruidos a partir de la decisión dura (*hard decision* / *slicing*) de los bits blandos (LLR) producidos por el `demodulation_mapper`.
* **¿Existe para `PUCCH` o `PDSCH`?**
  * **`PDSCH`:** **No.** En el gNB, `PDSCH` es un canal de bajada (transmisión): el gNB mapea símbolos ideales sin distorsión de canal y su línea de log (`[PHY] [I/D] PDSCH: rnti=... prb=... symb=... mod=... rv=... bg=... tbs=... t=...`) solo informa los parámetros de codificación y el tiempo de procesamiento.
  * **`PUCCH`:** En los logs de `PUCCH` (`format=0/1/2/3/4`), el gNB reporta `sinr=` (y en `debug`, `epre=`, `rsrp=`, `t_align=`, además de `metric=` en Formato 1), pero no imprime `evm=` en las trazas documentadas.
* **¿Aparece el EVM en las métricas JSON (`metrics: enable_json`)?**
  * **Fuente:** `https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html` (sección `metrics`) y esquema de salida JSON del DU (verificado también en [`docker/dashboard/app.py`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/docker/dashboard/app.py#L22-L34)).
  * **No existe ningún campo llamado `evm` (ni `pusch_evm`) en el JSON de métricas.** En la lista `ue_list` del reporte periódico del scheduler (`enable_sched: true`), las métricas de calidad de señal de subida por UE son únicamente:
    * `pusch_snr_db`
    * `pusch_rsrp_db`
    * `pucch_snr_db`
  * Si en el YAML se configura `expert_phy: pusch_sinr_calc_method: evm`, el valor `sinr_evm` calculado a partir del EVM pasa a ser el SINR reportado por el receptor de `PUSCH` y se publica en el campo JSON **`pusch_snr_db`** (en dB).

#### NO VERIFICADO
* **Líneas exactas en el código fuente de `release_26_10` (`gitlab.com/ocudu/ocudu`):** No se pudo inspeccionar directamente el árbol de código fuente de `release_26_10` en este entorno para citar el número de línea exacto dentro de `lib/phy/upper/channel_processors/pusch/` (`pusch_processor_impl.cpp`, el decorador de logging de `pusch_processor` y `evm_calculator_generic_impl`), ni verificar si el cálculo de `evm_calculator` se omite por completo en tiempo de ejecución cuando `phy_level != debug` y `pusch_sinr_calc_method != evm`.
* **EVM interno en `PUCCH` Formato 2/3/4 y en `enable_du_low`:** Queda **NO VERIFICADO** en el código fuente de `release_26_10` si los procesadores de `PUCCH` (F2/F3/F4) invocan internamente `evm_calculator` o si el bloque opcional `metrics.layers.enable_du_low: true` expone algún campo adicional relacionado con EVM en el JSON de `du_low`.

---

### 2) Opciones `phy_rx_symbols_*`: sección YAML, formato binario, etapa de captura, lectura con scripts y costo

#### Verificado en la fuente
* **Sección del YAML donde se configuran:**
  * **Fuente:** `https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html` (sección `log`).
  * Van dentro de la sección **`log:`** del archivo de configuración del gNB:
    ```yaml
    log:
      filename: /tmp/gnb.log
      phy_level: debug
      phy_rx_symbols_filename: /tmp/iq.bin
      phy_rx_symbols_port: 0        # [0 - inf, all], default: 0
      phy_rx_symbols_prach: false   # [false, true], default: false
    ```
* **Formato exacto del archivo binario (`phy_rx_symbols_filename`):**
  * **Fuente:** Documentación oficial de `config_ref.html` y código/ayuda de `srsRAN-matlab` / `OCUDU MATLAB` (`https://github.com/srsran/srsRAN-matlab`, funciones `srsResourceGridAnalyzer.m`, `srsPUSCHAnalyzer.m` y `srsParseLogs.m`).
  * **Tipo de muestra:** Binario crudo (*raw binary*) de muestras complejas en punto flotante de precisión simple de 32 bits (**`complex float32` / `single` intercalado**: 4 bytes para la parte real $I$ y 4 bytes para la parte imaginaria $Q$, totalizando **8 bytes por Resource Element**).
  * **Encabezado o metadatos en el archivo:** **Ninguno.** El archivo binario contiene exclusivamente los complejos `float32` concatenados sin cabeceras ni separadores.
  * **Cómo se identifica cada slot (`RX_SYMBOL`):** Cada vez que el gNB vuelca un slot al archivo binario, escribe una línea de índice en el **log de texto (`gnb.log`)** con el formato:
    ```text
    [Upper PHY] [I] [ 690.17] RX_SYMBOL: sector=0 offset=79705 size=8568
    ```
    donde `[ 690.17]` es `SFN.slot`, `sector` es el índice de celda/sector, y tanto `offset` (`RGOFFSET`) como `size` (`RGSIZE`) están medidos en **número de muestras complejas `float32`** (para obtener el desplazamiento y tamaño en bytes dentro del archivo `.bin` se multiplica por $8$).
  * **¿Grilla completa del slot o solo los PRB del PUSCH?** Vuelca la **grilla de recursos completa del slot de subida** ($N_{\text{RB}}^{\text{UL}} \times 12\text{ subportadoras} \times 14\text{ símbolos OFDM}$ por cada puerto capturado), no solo los PRB asignados al `PUSCH`. Por ejemplo, para una celda de 20 MHz con $\text{SCS} = 30\text{ kHz}$ ($51\text{ PRB}$) y 1 puerto Rx, el tamaño volcado por slot es siempre $51 \times 12 \times 14 = 8568$ muestras complejas (coincidente con `size=8568` en la documentación de `srsRAN-matlab`).
  * **Orden de recorrido:** Primero **subportadora** ($k$, índice más rápido), segundo **símbolo OFDM** ($l \in [0, 13]$), y tercero **puerto de recepción** ($p$, cuando `phy_rx_symbols_port: all`).
* **¿Antes o después de la ecualización?**
  * **Fuente:** `srsPUSCHAnalyzer.m` y `srsResourceGridAnalyzer.m` (`https://github.com/srsran/srsRAN-matlab`).
  * Los símbolos están **antes de la ecualización** (y antes de la estimación de canal): corresponden a la grilla tiempo-frecuencia de recepción a la salida de la FFT del *Lower PHY* cuando ingresa al *Upper PHY*, conteniendo aún los símbolos DMRS y la distorsión del canal inalámbrico.
* **Scripts oficiales para leerlo:**
  * **Fuente:** Repositorio oficial `https://github.com/srsran/srsRAN-matlab` (continuado como **OCUDU MATLAB**).
  * Incluye las herramientas en MATLAB (requieren *5G Toolbox*):
    1. `srsParseLogs`: parsea del archivo `gnb.log` (requiere `phy_level: debug`) la línea `RX_SYMBOL` y la configuración de la PDU `PUSCH`/`PUCCH`, devolviendo los objetos `[carrier, pusch, extra]`.
    2. `srsPUSCHAnalyzer(carrier, pusch, extra, RGFILENAME, RGOFFSET, RGSIZE)`: lee el bloque del archivo binario, ejecuta la estimación de canal y ecualización en MATLAB y grafica la **constelación ecualizada**, el perfil del canal estimado (magnitud y fase), la energía en la grilla del slot y el histograma de LLR.
    3. `srsResourceGridAnalyzer(NRBS, RGFILENAME, RGOFFSET, RGSIZE)`: devuelve la matriz compleja `RG` (subportadoras $\times$ símbolos) y grafica el mapa de calor de amplitud del slot.
    4. `srsPUCCHAnalyzer` y `srsPRACHAnalyzer`.
* **Costo de disco y procesamiento si se vuelca continuamente:**
  * **Fuente:** Advertencia en `https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html` (*"The file size grows very fast... only recommended for short debugging sessions"*).
  * **Cálculo sobre los parámetros de la celda del proyecto ($51\text{ PRB}$, $\text{SCS}=30\text{ kHz}$, 1 puerto):**
    * $1\text{ slot} = 8568\text{ complejos} \times 8\text{ B} = 68\,544\text{ B} \approx 66{,}94\text{ KiB}$.
    * Si se vuelcan todos los slots con `PUSCH` durante una prueba de tráfico continuo de subida (~400 a 600 slots UL/s en TDD), la escritura sostenida en disco es de **$\approx 27\text{ a }41\text{ MB/s}$** ($\approx 1{,}6\text{ a }2{,}5\text{ GB/min}$).
    * Además de llenar rápidamente el volumen montado en `/tmp`, realizar llamadas de escritura de ~68 KiB dentro del camino crítico de recepción de cada slot junto con `phy_level: debug` incrementa la latencia de los hilos de `upper_phy` y el riesgo de agotamiento de repositorios de subida (`UL processor is busy` / `late`).

#### NO VERIFICADO / Inferido
* **Opciones `phy_rx_symbols_pusch_on_ko`, `phy_rx_symbols_pusch_threshold_sinr_dB`, `phy_rx_symbols_pusch_threshold_iter`, `phy_rx_symbols_prach_threshold_rssi_dB`:**
  * **NO VERIFICADO en fuente:** Estas cuatro opciones no figuran en la tabla pública de `config_ref.html` de srsRAN Project y no se pudo inspeccionar el archivo del código fuente de `release_26_10` donde se registran en CLI11 (en `apps/`).
  * **Inferido:** Por compartir el prefijo `phy_rx_symbols_*` con `phy_rx_symbols_filename`, se ubican bajo la misma sección **`log:`** del YAML y actúan como filtros de disparo (*triggers*) en el `symbol_tracer` para volcar al archivo binario únicamente los slots de interés diagnóstico (p. ej., volcar el slot solo cuando el `PUSCH` falla con `crc=KO`, cuando la SINR cae por debajo de un umbral en dB, o cuando el decodificador LDPC supera cierto número de iteraciones), evitando así el costo de escribir decenas de MB/s en disco durante toda la corrida. El tipo exacto y sentido de comparación (`<` o `>=`) de cada umbral en C++ queda como **NO VERIFICADO**.

---

### 3) Otras formas oficiales de obtener constelaciones o EVM en tiempo real

#### Verificado en la fuente
* **Constelaciones IQ en tiempo real:**
  * **Fuente:** Documentación oficial de srsRAN Project / OCUDU (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html` y `https://docs.ocudu.org`).
  * **No existe en el gNB de OCUDU / srsRAN Project ningún mecanismo oficial para transmitir constelaciones en tiempo real** (ni por el WebSocket de `remote_control`, ni por UDP JSON, ni mediante una GUI como el antiguo `srsGUI` de `srsRAN 4G`). El único flujo oficial para obtener constelaciones del receptor del gNB es la captura en archivo con `phy_rx_symbols_filename` (o el uso de los umbrales de captura para volcar slots puntuales) y su reconstrucción posterior.
* **EVM en tiempo real:**
  * **Vía métricas JSON en vivo (`metrics: enable_json: true` + `remote_control` WebSocket `metrics_subscribe`):** Configurando en el YAML:
    ```yaml
    expert_phy:
      pusch_sinr_calc_method: evm
    ```
    el gNB calcula la SINR de `PUSCH` a partir del EVM de la constelación y la reporta periódicamente en tiempo real en el campo **`pusch_snr_db`** del JSON de cada UE (sin requerir `phy_level: debug`). A partir de ese valor en dB, cualquier cliente (como el dashboard) puede obtener en tiempo real el EVM RMS mediante:
    $$\text{EVM}_{\text{RMS}} = 10^{-\frac{\text{pusch\_snr\_db}}{20}}, \quad \text{EVM}\,[\%] = 100 \times 10^{-\frac{\text{pusch\_snr\_db}}{20}}$$
  * **Vía cola de logs (`log: phy_level: debug`):** Leyendo en vivo `/tmp/gnb.log`, donde cada recepción de `PUSCH` imprime explícitamente `evm={:.2f}` y `sinr_evm={:.1f}dB`, aunque con el costo de verbosidad de habilitar `debug` en `PHY`.

---

## Verificación de Claude contra el binario `release_26_10` (2026-11-05)
Con `strings /usr/local/bin/gnb` en el contenedor `gnb-radio`:
- **Confirmado:** existen `--pusch_sinr_calc_method` (valores `channel_estimator`, `post_equalization`, `evm`), `--phy_rx_symbols_filename`, `--phy_rx_symbols_port`, `--phy_rx_symbols_pusch_on_ko`, `--phy_rx_symbols_pusch_threshold_sinr_dB`, `--phy_rx_symbols_pusch_threshold_iter` y `--phy_rx_symbols_prach_threshold_rssi_dB`, con ayudas que dicen "Only works if phy_rx_symbols_filename is set". El umbral de SINR vuelca "when the PUSCH SINR is below this value".
- **Confirmado:** los formatos `RX_SYMBOL: sector={} offset={} size={}`, `evm={:.2f}` y `[sel]`.
- **Corrige a Gemini:** en esta versión no hay `phy_rx_symbols_prach` booleano; el PRACH se vuelca con `phy_rx_symbols_prach_threshold_rssi_dB`.
- **Matiza a Gemini:** la escritura del volcado pasa por una cola de un *task worker* (mensajes "RX_SYMBOL: Failed to write UL samples. Cause: task worker queue is full"): no escribe en disco dentro del camino crítico, pero puede perder slots si la cola se llena.
- **Sin verificar:** el formato float32 intercalado, el orden subportadora-símbolo-puerto, que la grilla esté antes de ecualizar, la sección `log:` del YAML y que `pusch_snr_db` del JSON use el método elegido. Se comprueban en una prueba corta.
