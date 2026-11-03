### (1) `ru_sdr.clock_ppm`, deriva de Timing Advance en COTS UEs y recomendaciones para USRP B210 sin reloj externo

#### Verificado en la fuente
* **Definición en configuración (`clock_ppm` y `freq_offset`):**
  * **Fuente:** Documentación oficial de referencia de configuración (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html`).
  * **Cita:** `clock_ppm`: *"Sets the clock calibration in Parts Per Million (PPM). Supported: [float]. Default: 0"*; `freq_offset`: *"Sets the frequency offset in Hertz. Supported: [float]. Default: 0"*.
* **Aplicación de `clock_ppm` en el código de OCUDU (`release_26_10`):**
  * **Fuente:** `https://gitlab.com/ocudu/ocudu/-/raw/release_26_10/apps/units/flexible_o_du/split_8/helpers/ru_sdr_config_translator.cpp` (verificado en el proyecto en [`2026-11-03_analisis-cortes-claude.md`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/investigacion/2026-11-03_analisis-cortes-claude.md#L13)).
  * **Comportamiento:** `ru_sdr_config_translator.cpp` aplica `clock_ppm` únicamente al cálculo de las frecuencias centrales de portadora (`(f + freq_offset) * (1 + ppm * 1e-6)`), mientras que la tasa de muestreo (`sampling_rate_Hz`) se asigna directamente a partir de `srate_MHz` sin escalar por `clock_ppm`.
* **Recomendación oficial para USRP B200/B210 sin reloj externo (GPSDO):**
  * **Fuente 1 (Tutorial COTS UE):** `https://docs.srsran.com/projects/project/en/latest/tutorials/source/cotsUE/source/index.html` y base de conocimientos `https://docs.srsran.com/projects/project/en/latest/knowledge_base/source/cots_ues/source/index.html`.
  * **Cita / Contenido:** La documentación oficial recomienda un reloj externo (GPSDO o 10 MHz) para conexiones OTA estables con COTS UEs debido a la tolerancia de frecuencia de los handsets comerciales frente al oscilador interno de la B210.
  * **Fuente 2 (Configuración oficial de ejemplo para B200/B210 sin reloj externo en n78 TDD 20 MHz):** `https://gitlab.com/ocudu/ocudu/-/raw/release_26_10/configs/gnb_rf_b200_tdd_n78_20mhz.yml` (y su equivalente en `https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html`).
  * **Cita:**
    > `"Note in this example an external clock source is not used, so the sync is not defined and the default is used."`
    > `"# The USRP clock may introduce some CFO: configure the channel estimator to compensate for it."`
    > `expert_phy:`
    > `  pusch_channel_estimator_td_strategy: average`
    > `  pusch_channel_estimator_cfo_compensation: true`
    En dicho perfil oficial sin reloj externo, `clock_ppm` se deja en su valor por defecto (`0`) y se compensa el CFO en el estimador de canal de PUSCH (`pusch_channel_estimator_cfo_compensation: true` y `pusch_channel_estimator_td_strategy: average`).
* **Issues/discusiones sobre deriva continua de Timing Advance causada por `clock_ppm`:**
  * No se encontraron issues ni discusiones públicas en `github.com/srsran/srsRAN_Project` ni en `gitlab.com/ocudu/ocudu` que documenten específicamente una deriva continua de `Timing Advance Command` (TS 38.213 §4.2, paso de $16 \cdot 64 \cdot T_c / 2^\mu \approx 0{,}2604\ \mu\text{s}$ para $\mu=1$) al usar `clock_ppm != 0`.

#### Inferido
* En la USRP B210, tanto la frecuencia del sintetizador RF (AD9361) como el reloj de muestreo banda base derivan del mismo oscilador físico (TCXO de 40 MHz). En recepción de bajada, el COTS UE engancha su frecuencia y su reloj de símbolo/muestreo al SSB/TRS transmitido por el gNB. Si `clock_ppm` desplaza por software la frecuencia de portadora comandada a UHD pero deja `srate` sin escalar, se rompe la relación nominal entre frecuencia de portadora y frecuencia de muestreo en el gNB. Como el UE deriva su base de tiempo de la portadora que recibe, esto es físicamente compatible con una deriva relativa entre la ventana de recepción del gNB y la temporización de subida del UE, obligando al gNB a emitir `Timing Advance Command` en un mismo sentido de forma sostenida.

---

### (2) Reportes de COTS UEs (MediaTek / Snapdragon) con CSI aperiódico (PUSCH) vs. periódico (PUCCH F2)

#### Verificado en la fuente
* **Parámetros de CSI en OCUDU/srsRAN Project:**
  * **Fuente:** `https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html`.
  * **Cita:** Bajo `cell_cfg.csi`: `csi_rs_enabled` (*"Enables CSI-RS resources and reporting. Supported: [false, true]. Default: true"*), `csi_rs_period` (*"Sets the CSI-RS period in ms. Supported: [10, 20, 40, 80]. Default: 20"*), `report_type` (configurable como `periodic` o `aperiodic`). Bajo `cell_cfg.pucch`: `max_consecutive_kos` (*"Sets the maximum number of consecutive undecoded PUCCH F2 for CSI before a RLF is reported. Supported: [0 - inf]. Default: 100"*).
* **Reportes públicos específicos de MediaTek Dimensity ignorando PUSCH con CSI aperiódico:**
  * No se encontró en `github.com/srsran/srsRAN_Project` ni en `gitlab.com/ocudu/ocudu` ningún issue o discusión que reporte que módems MediaTek Dimensity fallen al transmitir `PUSCH` cuando el `DCI format 0_1` solicita `aperiodic` CSI (`CSI request` no nulo, TS 38.214 §5.2.1 / TS 38.212 §7.3.1.1.2).
* **Configuración de CSI recomendada en perfiles oficiales para COTS UEs:**
  * **Fuente:** `https://gitlab.com/ocudu/ocudu/-/raw/release_26_10/configs/gnb_rf_b200_tdd_n78_20mhz.yml` y `https://docs.srsran.com/projects/project/en/latest/tutorials/source/cotsUE/source/index.html`.
  * **Comportamiento:** Los archivos de configuración oficiales para B200/B210 y COTS UEs no sobreescriben `cell_cfg.csi`, utilizando los valores por defecto del gNB: `csi_rs_enabled: true` (que incluye `TRS` para tracking tiempo-frecuencia en el UE) y reporte **periódico** (`periodic`) sobre `PUCCH format 2`.

#### Inferido
* Cuando se usa CSI periódico por defecto (`PUCCH format 2`), si el enlace de subida tiene errores de decodificación o desalineación de reloj/ganancia, el gNB acumula 100 `PUCCH F2` sin decodificar en pocos segundos (p. ej., a período de 20 ms son 2 s) y dispara RLF por `pucch.max_consecutive_kos`.
* En cambio, con `report_type: aperiodic`, el reporte CSI se multiplexa como UCI en `PUSCH` (TS 38.214 §5.2.1.4). Si un modelo de UE específico (como el Redmi Note 14 5G con MediaTek) presenta fallos sistemáticos únicamente en los slots donde el grant de `PUSCH` incluye solicitud de CSI aperiódico, mientras otro UE (OnePlus 13) los decodifica normalmente, puede deberse a una discrepancia de interoperabilidad en el cálculo de recursos `beta_offset` / `CSI-AperiodicTriggerState` (TS 38.331 §6.3.2) o a que el gNB espera una longitud de payload CSI distinta de la que codifica el módem, invalidando la decodificación del bloque en el receptor del gNB. Para COTS UEs donde `aperiodic` falla en `PUSCH`, volver a `periodic` (manteniendo `csi_rs_enabled: true` para no perder `TRS`) y elevar `pucch.max_consecutive_kos` evita el corte prematuro a los 2–3 s mientras se ajusta la capa física.

---

### (3) Funcionamiento de `pdsch.max_consecutive_kos`, `pusch.max_consecutive_kos` y el temporizador de liberación por RLF en el DU

#### Verificado en la fuente
* **Definición y valores por defecto de `max_consecutive_kos`:**
  * **Fuente:** `https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html`.
  * **Citas:**
    * `cell_cfg.pdsch.max_consecutive_kos`: *"Sets the maximum number of consecutive HARQ-ACK KOs before a RLF is reported. Supported: [0 - inf]. Default: 100"*.
    * `cell_cfg.pusch.max_consecutive_kos`: *"Sets the maximum number of consecutive CRC KOs before a RLF is reported. Supported: [0 - inf]. Default: 100"*.
    * `cell_cfg.pucch.max_consecutive_kos`: *"Sets the maximum number of consecutive undecoded PUCCH F2 for CSI before a RLF is reported. Supported: [0 - inf]. Default: 100"*.
* **Lógica del detector RLF (`rlf_detector.h`) y del temporizador de liberación en `DU-MNG`:**
  * **Fuente (código e issues de srsRAN Project / OCUDU):** `lib/mac/mac_sched/rlf_detector.h` y trazas de `DU-MNG` en issues de GitHub (p. ej., `https://github.com/srsran/srsRAN_Project/issues/533`, `https://github.com/srsran/srsRAN_Project/issues/891`).
  * **Comportamiento del contador:** En `rlf_detector`, los métodos `handle_ack` (para `pdsch`), `handle_crc` (para `pusch`) y `handle_csi` (para `pucch`) incrementan el contador de KOs consecutivos ante cada fallo (NACK/DTX en DL HARQ-ACK, o CRC KO en UL) y lo reinician a `0` cuando se recibe un resultado válido (`ack == true` o `crc_pass == true`) **antes** de alcanzar el umbral.
  * **Comportamiento del temporizador de 4000 ms tras declarar RLF:** Cuando cualquiera de los contadores alcanza `max_consecutive_kos` (por defecto 100), el MAC notifica RLF al DU Manager (`[MAC] [W] ue=X: RLF detected. Cause: 100 consecutive HARQ-ACK KOs`) y el DU Manager inicia un temporizador de guarda de 4000 ms (`[DU-MNG] [I] ue=X: RLF detected with cause="MAC max KOs reached". Timer of 4000 msec to release UE started...`).
  * **¿Se cancela la liberación si el UE vuelve a transmitir ACK/PUSCH?** **No por tráfico normal de capa física/MAC.** Una vez disparado el temporizador de liberación por RLF en `DU-MNG`, la recepción posterior de `HARQ-ACK` válidos (`ack=1`) o `PUSCH` con `crc=OK` en el mismo contexto no cancela el temporizador del DU (el temporizador está concebido para dar margen a un procedimiento RRC Re-establishment antes de pedir `UE Context Release Request` vía F1AP al CU-CP: `RLF timer expired with cause="MAC max KOs reached". Requesting a UE release`).
* **Valores recomendados en problemas de desconexión / enlaces con ráfagas de errores:**
  * **Fuente:** Discusiones e issues en `github.com/srsran/srsRAN_Project` (incluyendo pruebas OTA y NTN).
  * **Comportamiento:** Para evitar que ráfagas transitorias de DTX/NACK o pérdidas momentáneas de sincronismo disparen la liberación irreversible en el DU, en pruebas de diagnóstico se incrementa `max_consecutive_kos` a valores altos (por ejemplo, `1000` a `10000`, o `0` si la versión del esquema admite desactivarlo según el rango `[0 - inf]`).

#### Inferido
* Con SCS de 30 kHz ($\mu=1$, 2000 slots/s) y múltiples procesos HARQ en paralelo durante descargas activas, 100 `HARQ-ACK` KOs consecutivos (que contabilizan tanto NACK como DTX por cada bit/proceso HARQ reportado) pueden acumularse en una fracción de segundo (~50–200 ms de desvanecimiento o bloqueo de tiempo real). Como el temporizador de 4000 ms del `DU-MNG` no se cancela aunque el enlace físico se recupere 10 ms después, el valor por defecto (`100`) resulta demasiado bajo para pruebas con COTS UEs sobre SDR sin GPSDO; subir `pdsch.max_consecutive_kos`, `pusch.max_consecutive_kos` y `pucch.max_consecutive_kos` (p. ej. a `1000`–`5000`) permite que el UE se recupere en capa MAC/RLC sin que el DU destruya el contexto RRC.
