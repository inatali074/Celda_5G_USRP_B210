### (1) Documentación, issues y reportes sobre desconexiones periódicas (60–180 s) o búsquedas de PLMN/LTE en COTS UEs (MediaTek / Xiaomi / otros) en 5G SA

#### Verificado en la fuente
* **Documentación oficial de srsRAN Project / OCUDU sobre desconexiones periódicas por falta de IMS en COTS UEs:**
  * **Fuente:** Guía oficial de COTS UEs de srsRAN Project (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/cots_ues.html` y `https://docs.srsran.com/projects/project/en/latest/knowledge_base/source/cots_ues/source/index.html`).
  * **Contenido verificado:** Documenta que diversos teléfonos Android COTS se desconectan silenciosamente de la celda 5G SA pocos minutos después del `Registration Accept` (el ejemplo documentado para Google Pixel / módems con menú `*#*#0702#*#*` es de `180` s por `NR_TIMER_WAIT_IMS_REGISTRATION`) cuando el núcleo 5G no posee un servidor IMS activo o el UE no logra completar el registro IMS sobre NR.
  * **Caso Xiaomi Redmi con MediaTek en la matriz de srsRAN:** En la misma tabla de dispositivos COTS (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/cots_ues.html`), para el Xiaomi Redmi Note 10 5G (chipset MediaTek Dimensity 700), srsRAN documenta que requiere habilitar manualmente el modo SA mediante el código de marcador `*#*#726633#*#*` y configurar el APN con `APN Type: default,ims,ia`.
* **Issues en srsRAN Project y Open5GS sobre bucles de `Mobility Registration Updating` y caídas periódicas con UEs comerciales:**
  * **Fuente 1 (Open5GS):** `https://github.com/open5gs/open5gs/issues/910` y `https://github.com/open5gs/open5gs/issues/1432`.
  * **Contenido verificado:** Reportan que teléfonos COTS (incluyendo equipos con chipset MediaTek, Huawei y OnePlus) en 5G SA completan el registro inicial y establecen la sesión PDU de datos, pero al fallar la validación de servicios superiores (ausencia de IMS/VoNR o falta de respuesta DNS/conectividad en la interfaz `ogstun`) abandonan el enlace de radio y entran en un bucle periódico enviando `Registration request` de tipo `Mobility registration updating`.
  * **Fuente 2 (srsRAN Project):** `https://github.com/srsran/srsRAN_Project/discussions/1344` y `https://github.com/srsran/srsRAN_Project/issues/533`.
  * **Contenido verificado:** Reportan desconexiones recurrentes con teléfonos comerciales (Xiaomi/Redmi, OnePlus, Pixel) tras intervalos fijos de conexión en 5G SA cuando el teléfono intenta usar o esperar servicios IMS no aprovisionados en Open5GS.
* **Documentación de OpenAirInterface (OAI) y Amarisoft sobre desconexión de COTS UEs por IMS / VoNR y PLMN `001/01`:**
  * **Fuente 1 (Open-Cells / OAI):** `https://open-cells.com/index.php/2020/07/11/5g-sa-cots-ue/` y repositorio OAI (`https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/NR_SA_Tutorial_COTS_UE.md`).
  * **Contenido verificado:** Documentan que los smartphones COTS actuales son *voice-centric* y, tras establecer la sesión PDU por defecto en 5G SA, esperan servicio IMS; si el registro IMS falla o no está disponible, el módem aborta la conexión 5G SA para buscar servicio de voz en otra RAT (4G LTE).
  * **Fuente 2 (Amarisoft):** Documentación técnica de interoperabilidad UE (`https://tech-academy.amarisoft.com/ue_configuration.doc`).
  * **Contenido verificado:** Advierte que con SIM de prueba `00101` en redes 5G SA sin servidor IMS activo (o si el UE no tiene habilitado VoNR para el PLMN de prueba), los teléfonos comerciales (incluidos Xiaomi/MediaTek) abandonan la celda NR periódicamente para buscar una celda LTE donde obtener voz (VoLTE/CSFB).
* **Límite de lo comprobado:**
  * No se encontró ningún issue público en GitHub/GitLab ni paper que cite literalmente la cadena de versión de baseband `MOLY.NR15.R3.MP.V167.P70` ni el MT6855 con la secuencia exacta de URCs `+CIEV: 3,0` / `+CSCON: 0` a los `60,0 s` exactos.

---

### (2) Análisis de temporizadores y mecanismos (3GPP vs. propietarios de MediaTek) para explicar el corte exacto a 60,0 s

#### Verificado en la fuente (Especificaciones 3GPP y código fuente de Open5GS / OCUDU)

1. **Comandos AT observados (`+CIEV: 3,0` y `+CSCON: 0`):**
   * **Fuente:** 3GPP TS 27.007 V15.6.0, secciones 8.9 (`+CIND` / `+CIEV`, *Indicator control*) y 8.40 (`+CSCON`, *Signalling connection status*), `https://www.etsi.org/deliver/etsi_ts/127000_127099/127007/15.06.00_60/ts_127007v150600p.pdf`.
   * **Verificado:** `+CSCON: 0` indica transición del estado de señalización RRC a `Idle`. `+CIEV: <ind>,<val>` reporta el cambio de un indicador del Mobile Termination (`+CIND`); el valor `0` en el indicador de servicio significa pérdida de disponibilidad de servicio (*no service*) reportada por el módem hacia el AP (Android).

2. **Falta de IMS / Registro IMS, `UE's usage setting = Voice centric` y `5GS network feature support` (`IMS VoPS`):**
   * **Fuente 1 (3GPP NAS):** 3GPP TS 24.501 V15.7.0, secciones 4.3 (*UE domain selection*), 4.9 (*Disabling and re-enabling of UE's N1 mode capability*), 5.5.1.2.4 (*Initial registration accepted by the network*) y 9.11.3.5 (*5GS network feature support*), `https://www.etsi.org/deliver/etsi_ts/124500_124599/124501/15.07.00_60/ts_124501v150700p.pdf`.
   * **Fuente 2 ( Selección de dominio / voz):** 3GPP TS 23.501 V15.8.0, sección 5.16.3 (*IMS Voice over PS Session Support*), `https://www.etsi.org/deliver/etsi_ts/123500_123599/123501/15.08.00_60/ts_123501v150800p.pdf`.
   * **Fuente 3 (Código de Open5GS v2.8.0):** `https://github.com/open5gs/open5gs/blob/v2.8.0/src/amf/gmm-build.c`.
   * **Verificado:**
     * Un smartphone comercial opera por defecto con `UE's usage setting = Voice centric` (TS 24.501 §4.3). En 5G SA (modo N1) no existe CSFB directo a 2G/3G; la voz requiere obligatoriamente registro IMS (ya sea para VoNR o para activar *EPS Fallback* hacia LTE cuando entra una llamada, TS 23.501 §5.16.3.2).
     * Si un UE *voice-centric* está registrado en modo N1 pero determina que el servicio de voz IMS no está disponible, TS 24.501 §4.3 y §4.9 especifican que el UE debe intentar obtener servicio de voz en otra RAT (como E-UTRA / modo S1, donde dispone de VoLTE o CSFB), deshabilitando temporalmente el modo N1 o buscando celdas E-UTRA.
     * En [`2026-11-02_amf_00101_sincsi_tx70.log`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/evidencia/04_sesion_pdu/2026-11-02_amf_00101_sincsi_tx70.log#L683-L695) se verifica que, tras volver del escaneo LTE a los 6–9 s, el Redmi envía `Registration request` usando su `5G-S_GUTI` (registro de movilidad) porque en el escaneo de los EARFCNs comerciales (bandas B5 `2450`, B28 `9360`/`9485`, B4 `2225`, B2 `850`/`950`, B7 `3050`) ninguna celda transmite el PLMN `001/01` de su USIM.

3. **Búsqueda periódica de PLMN de mayor prioridad (TS 23.122) y PLMN de prueba `001/01`:**
   * **Fuente:** 3GPP TS 23.122 V15.8.0, secciones 4.4.3.1.1 y 4.4.3.3, `https://www.etsi.org/deliver/etsi_ts/123100_123199/123122/15.08.00_60/ts_123122v150800p.pdf`, y 3GPP TS 31.102 V15.7.0, sección 4.2.6 (`EF_HPPLMN`), `https://www.etsi.org/deliver/etsi_ts/131100_131199/131102/15.07.00_60/ts_131102v150700p.pdf`.
   * **Verificado (Descartado como temporizador estándar 3GPP):**
     * La búsqueda periódica de PLMN de mayor prioridad (temporizador $T$) **solo aplica cuando el UE está registrado en un VPLMN** (roaming). Como la SIM 3 tiene `IMSI = 001010000000003` ([`PROYECTO.md`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/PROYECTO.md#L50)) y la celda transmite `001/01`, el UE está en su **HPLMN**, por lo que según TS 23.122 no corre el temporizador de búsqueda de HPLMN.
     * Además, en TS 23.122 §4.4.3.1.1 el primer intento tras encender ocurre entre **2 minutos y $T$ minutos**, con paso mínimo de **6 minutos** y valor por defecto de **60 minutos** (no 60 segundos).

4. **Temporizadores 5GMM: `T3502`, `T3511`, `T3540`, `T3346` y `T3512`:**
   * **Fuente:** 3GPP TS 24.501 V15.7.0, Tabla 10.2.1 (*Timers of 5GS mobility management – UE side*), `https://www.etsi.org/deliver/etsi_ts/124500_124599/124501/15.07.00_60/ts_124501v150700p.pdf`.
   * **Verificado (Ninguno vale 60 s ni explica el síntoma):**
     * `T3502`: valor por defecto **12 minutos** (`720 s`). Solo arranca tras **fallo** de registro (cuando el contador de intentos llega a 5 o ante causas de rechazo específicas). Aquí el registro fue exitoso.
     * `T3511`: valor por defecto **10 segundos**. Solo arranca ante fallos de registro o de capa inferior durante el registro.
     * `T3540`: valor por defecto **10 segundos**. Arranca al terminar un procedimiento NAS cuando no hay *follow-on request* ni sesiones de usuario activas, o durante un `Deregistration`. Aquí hay sesión PDU activa con DRB establecido y el corte ocurre a los `60,0 s`, no a los `10 s`.
     * `T3346`: temporizador de *back-off* por congestión enviado por la red en mensajes de rechazo (`Registration Reject` / `Service Reject` con causa #22). Open5GS no envió rechazos al Redmi.
     * `T3512`: temporizador de registro periódico, configurado en `540 s` (9 minutos) en [`open5gs-5gc-zmq.yml`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/config/open5gs/open5gs-5gc-zmq.yml#L95).

5. **Procedimiento de `UE Configuration Update` y `NITZ`:**
   * **Fuente:** 3GPP TS 24.501 V15.7.0, sección 5.4.4 (*Generic UE configuration update procedure*) y Tabla 10.2.2 (`T3555`, lado red, valor por defecto `6 s`); código de Open5GS `https://github.com/open5gs/open5gs/blob/v2.8.0/src/amf/nas-path.c` y `src/amf/gmm-build.c`.
   * **Verificado:** En [`2026-11-02_amf_00101_sincsi_tx70.log`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/evidencia/04_sesion_pdu/2026-11-02_amf_00101_sincsi_tx70.log#L631-L634), Open5GS envía `Configuration update command` inmediatamente después de `Registration complete` (en el mismo milisegundo) solo con el nombre de red (`Metodos1`) y hora NITZ, con el bit `Acknowledgement requested = 0`. No inicia ningún temporizador de 60 s en el UE ni en la red.

6. **Ausencia de `SIB2`/`SIB3`/`SIB4`/`SIB5` (reselección de celda e inter-RAT LTE):**
   * **Fuente 1 (3GPP RRC):** 3GPP TS 38.331 V15.7.0, secciones 5.2.2.1 y 5.2.2.3, `https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/15.07.00_60/ts_138331v150700p.pdf`.
   * **Fuente 2 (OCUDU / srsRAN Project):** `https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html`.
   * **Verificado:**
     * En TS 38.331 §5.2.2.1, los bloques `SIB2` (parámetros comunes de reselección), `SIB3` (reselección intra-frecuencia), `SIB4` (inter-frecuencia NR) y `SIB5` (inter-RAT hacia E-UTRA/LTE) se utilizan para evaluación de reselección de celda en `RRC_IDLE` / `RRC_INACTIVE`. Su transmisión por la red es opcional en `si-SchedulingInfo` de `SIB1` (si `si-SchedulingInfo` no los lista en `SIB1`, el UE en `RRC_CONNECTED` no declara RLF por su ausencia).
     * En [`gnb_b210_00101_csiper_ppm0_kos.yml`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/config/gnb/gnb_b210_00101_csiper_ppm0_kos.yml) y [`gnb_b210_00101_n3_ppm0_kos.yml`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/config/gnb/gnb_b210_00101_n3_ppm0_kos.yml) no está configurado el bloque `cell_cfg.sib`, por lo que el gNB transmite `MIB` y `SIB1` sin `SIB5` (vecinas LTE).
     * Tampoco el temporizador `inactivity_timer` del `cu_cp` de OCUDU explica los 60 s: su valor por defecto documentado es **`120` segundos** (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html`) y, cuando expira, el gNB envía un `RRCRelease` explícito (que acá no ocurre).

7. **Ausencia de `Equivalent PLMNs` y `Allowed NSSAI` / `Network Slicing`:**
   * **Fuente:** 3GPP TS 24.501 V15.7.0, sección 5.5.1.2.4; configuración [`open5gs-5gc-zmq.yml`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/config/open5gs/open5gs-5gc-zmq.yml#L75-L80).
   * **Verificado:** Open5GS incluye `Allowed NSSAI` (`SST: 1`) en el `Registration Accept` y el UE establece exitosamente la sesión PDU sobre `SST: 1`, `DNN: Metodos1`. La lista `Equivalent PLMNs` es opcional en `Registration Accept` (TS 24.501 Tabla 9.11.3.1.1) y su ausencia no dispara ningún temporizador de 60 s en 3GPP.

#### Inferido / Hipótesis (Mecanismo propietario de MediaTek `MOLY.NR15` de 60,0 s)

* **Causa más probable (Temporizador de supervisión de voz/IMS en 5G SA del módem MediaTek + búsqueda de fallback en E-UTRA):**
  1. **Por qué el Redmi NO pide la DNN `ims` al registrarse (a diferencia del OnePlus 13):** En Xiaomi/HyperOS con chipset MediaTek, las funciones VoLTE y VoNR están bloqueadas por defecto mediante una lista blanca de operadores (*Carrier Check* en NVRAM/MCB) y el PLMN de prueba `001/01` no tiene un perfil IMS/VoNR habilitado en el firmware comercial, ni un APN `ims` cargado para `00101`. Por eso el stack IMS del Redmi ni siquiera intenta abrir la sesión PDU `ims`.
  2. **Por qué cae exactamente a los 60,0 s (±0,02 s):** Aunque la interfaz de usuario no pida la DNN `ims`, el módem baseband (`MOLY.NR15`, módulo de selección de dominio/sistema `SDM`/`GMSS`/`NWSEL`) sigue configurado como **`Voice centric`** y está acampado en **5G SA (modo N1)**. Al obtener servicio en 5G SA (`+CIEV` de servicio activo), el baseband inicia un **temporizador interno de guarda de exactamente 60 segundos** esperando que las capas superiores completen el registro IMS/VoNR (equivalente en MediaTek al parámetro `NR_TIMER_WAIT_IMS_REGISTRATION` de 180 s documentado por srsRAN en los Pixel).
  3. **Qué hace al expirar los 60,0 s:** Como a los `60,0 s` el módem comprueba que sigue en 5G SA **sin registro IMS activo** (lo que en 5G SA implica incapacidad total para hacer o recibir llamadas de voz, pues tampoco puede funcionar *EPS Fallback* sin señalización SIP/IMS previa), el módem aplica la política de recuperación de voz (TS 24.501 §4.3 / §4.9): **aborta localmente la conexión RRC en NR** (`+CSCON: 0`, `+CIEV: 3,0` sin enviar `Deregistration` ni esperar `RRCRelease`), deshabilita momentáneamente NR y **escanea las frecuencias LTE almacenadas en su historia/bandas soportadas** (`EARFCN 2450, 9360, 9485, 2225, 850, 950, 3050`) buscando una celda 4G donde acampar por VoLTE o CSFB.
  4. **Por qué vuelve a los 6–9 s con `Mobility registration updating`:** Como nuestra red no tiene celda LTE en `001/01` y las celdas LTE comerciales que encuentra pertenecen a `722/xx` (prohibidas para la SIM `00101`), la búsqueda E-UTRA falla tras 6–9 s. Al no existir alternativa LTE para `00101`, la máquina de estados `NWSEL`/`GMSS` rehabilita N1 (5G SA), vuelve a seleccionar nuestra celda NR `00101` y, como al pasar por búsqueda inter-RAT el NAS requiere resincronizar estado con la red manteniendo su `5G-GUTI`, envía un `Registration request` de tipo `Mobility registration updating` (y reabre la sesión PDU), reiniciando el ciclo de 60,0 s.
* **Hipótesis secundarias en MediaTek (menor probabilidad frente al mecanismo de voz/IMS, pero descartables con las pruebas del punto 3):**
  * **Smart 5G / 5G UltraSave:** La función propietaria de Xiaomi/MediaTek conmuta entre 5G y 4G según tráfico y batería, pero actúa hacia una celda 4G ancla o conocida y depende del tráfico; no explicaría que el corte ocurra con precisión de reloj (`60,00 ± 0,02 s`) incluso habiendo tráfico ni que reporte `+CIEV: 3,0` (sin servicio).
  * **Detección de *Fake / Pseudo Base Station*:** Los algoritmos anti-FBS de MediaTek evalúan principalmente celdas 2G/4G sin cifrado o parámetros de `SIB1`/`SIB2` anómalos antes o durante el acceso inicial; aquí el UE completa autenticación mutua 5G-AKA y `NAS Security Mode Command` (NIA2/NEA2) sin rechazar la celda.

---

### (3) Cambios recomendados en el teléfono, el núcleo (Open5GS) y el gNB (OCUDU) para aislarlo y resolverlo

*(Recordatorio de arquitectura del proyecto: todo cambio en el núcleo o el gNB se aplica en los archivos montados en los contenedores Docker `open5gs` y `gnb-radio`, nunca instalando paquetes en el host).*

#### A. En el teléfono (Xiaomi Redmi Note 14 5G — MediaTek / HyperOS) — **Prioridad 1 (no requiere tocar contenedores)**

1. **Bloquear el tipo de red preferido en `NR only` (Solo 5G NR) para impedir el escaneo de EARFCNs LTE:**
   * **Procedimiento:** Marcar **`*#*#4636#*#*`** en la app de Teléfono $\rightarrow$ *Información del teléfono* (*Phone information*, correspondiente a la ranura SIM de prueba) $\rightarrow$ *Establecer el tipo de red preferido* (*Set Preferred Network Type*) $\rightarrow$ seleccionar **`NR only`**.
   * **Justificación verificada:** Si el corte de 60 s es un intento de *fallback* o búsqueda de voz hacia E-UTRA (LTE), fijar el módem en `NR only` deshabilita la capa E-UTRA en el baseband (`NWSEL`/`GMSS`), impidiendo que el módem abandone NR para escanear los EARFCNs LTE `2450`, `9360`, etc.
   * **Fuente:** Documentación de códigos Android/Xiaomi (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/cots_ues.html`).

2. **Desactivar el *Carrier Check* de VoNR y VoLTE en Xiaomi y revisar switches de voz/Smart 5G:**
   * **Procedimiento:**
     * Marcar **`*#*#8667#*#*`** (desactiva el *carrier check* de **VoNR** en MIUI/HyperOS y muestra el interruptor de llamadas 5G / VoNR en ajustes de SIM).
     * Marcar **`*#*#86583#*#*`** (desactiva el *carrier check* de **VoLTE**).
     * Marcar **`*#*#726633#*#*`** (habilita el interruptor de **5G SA** en ajustes).
     * En *Ajustes $\rightarrow$ Redes móviles*, probar **desactivar VoNR / llamadas VoLTE** (para que el teléfono no exija registro de voz IMS) y desactivar **Smart 5G** (ahorro de batería 5G).
   * **Fuente:** Documentación de srsRAN COTS UEs (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/cots_ues.html`) y soporte oficial Xiaomi sobre códigos de ingeniería de red.

3. **Cambiar el teléfono de `Voice centric` a `Data centric` o desactivar IMS en el *EngineerMode* de MediaTek (si HyperOS lo permite):**
   * **Procedimiento:** Marcar **`*#*#3646633#*#*`** (MediaTek *EngineerMode*) o **`*#*#0702#*#*`**.
     * Si abre MediaTek *EngineerMode*: ir a la pestaña *Telephony* $\rightarrow$ *IMS* (o *Misc Feature Config* / *5G/NR Config*) y cambiar la configuración de uso del UE de *Voice centric* a **`Data centric`** (según 3GPP TS 24.501 §4.3, un UE *Data centric* no abandona N1 cuando IMS VoPS no está disponible), o desactivar `IMS over NR`.
     * Si abre el menú IMS (`*#*#0702#*#*`): poner `SUPPORT_IMS_NR_REGISTRATION_TIMER = 0` y `NR_TIMER_WAIT_IMS_REGISTRATION = -1` (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/cots_ues.html`).
   * **Nota de precaución (Inferido):** En versiones recientes de HyperOS (Android 15/16), Xiaomi restringe el acceso a ciertas pestañas de `*#*#3646633#*#*` sin permisos de desarrollador; si no abre, el bloqueo `NR only` desde `*#*#4636#*#*` sí está disponible en HyperOS estándar.

#### B. En el gNB (OCUDU `release_26_10` en contenedor Docker) — **Prioridad 2**

1. **Agregar transmisión de `SIB2` en el YAML del gNB:**
   * **Justificación verificada:** Según 3GPP TS 38.331 §5.2.2.1, un UE en `RRC_IDLE` / `RRC_INACTIVE` espera adquirir `SIB2` para tener los parámetros comunes de reselección (`q-RxLevMin`, `t-ReselectionNR`, etc.). OCUDU permite habilitar la programación de `SIB2` en el YAML bajo `cell_cfg.sib`:
   * **Fuente:** `https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html`.
   * **Configuración a probar en `cell_cfg`:**
     ```yaml
     cell_cfg:
       # ... (resto de parámetros iguales)
       sib:
         si_window_length: 20
         si_sched_info:
           - si_period: 16
             sib_mapping: 2
     ```

#### C. En el núcleo (Open5GS v2.8.0 en contenedor Docker) — **Prioridad 3 (si persiste y se requiere comprobar el rol de `IMS VoPS` / DNN `ims`)**

1. **Verificar qué pasa cuando el teléfono tiene APN `ims` y el abonado tiene autorizada la DNN `ims` en MongoDB/Open5GS:**
   * **Justificación:** Si en el Redmi se habilita VoNR con `*#*#8667#*#*` y se agrega `ims` en el campo `APN type` (`default,ims,ia` como indica la guía COTS de srsRAN en `https://docs.srsran.com/projects/project/en/latest/user_manuals/source/cots_ues.html`), se puede observar en el log del AMF si el Redmi empieza a pedir la DNN `ims` igual que el OnePlus 13, confirmando que el corte de 60 s proviene del subsistema de voz/IMS.
2. **Indicador `ims_vops_3gpp` en `Registration Accept` (`src/amf/gmm-build.c`):**
   * **Verificado en la fuente:** En Open5GS v2.8.0 (`https://github.com/open5gs/open5gs/blob/v2.8.0/src/amf/gmm-build.c`), el IE `5GS network feature support` se construye en código C dentro de `gmm_build_registration_accept()` y no tiene una opción en `open5gs-5gc.yml` para conmutar `ims_vops_3gpp` entre `0` y `1`. Solo sería necesario recompilar la imagen Docker de Open5GS si las pruebas en el teléfono (`NR only` en `*#*#4636#*#*` y `*#*#8667#*#*`) no detuvieran el temporizador de 60 s.
