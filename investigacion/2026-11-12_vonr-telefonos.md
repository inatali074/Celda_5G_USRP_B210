A continuación se presenta la investigación puntual para los cuatro puntos solicitados, diferenciando en cada apartado qué está **verificado en la fuente** (con su especificación 3GPP y sección o URL exacta) y qué corresponde a **inferencia o extrapolación** aplicada a los dos teléfonos del laboratorio.

---

## (1) ¿Estos modelos activan IMS/VoNR en una PLMN desconocida como `001/01`? ¿Qué lo determina?

### Resumen del estado por modelo en `001/01`
* **Motorola Edge 30 (`XT2203-1`, Qualcomm Snapdragon 778G+ 5G):** **Sí intenta activar el subsistema IMS en `001/01` de fábrica** (ya comprobado en el laboratorio: solicita periódicamente `PDU Session Establishment Request` con `DNN = ims` cada ~16 s; ver [`2026-11-12_panel-sa-redmi.md`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/sesiones/2026-11-12_panel-sa-redmi.md#L28)). Sin embargo, no hay reportes públicos específicos del modelo `XT2203-1` completando llamadas **VoNR** en `001/01` sin habilitar explícitamente las banderas de VoNR en `CarrierConfig`.
* **Xiaomi Redmi Note 14 5G (HyperOS, MediaTek Dimensity 7025-Ultra):** **No activa IMS/VoNR de fábrica en `001/01`** (en el laboratorio solo abre la sesión PDU del APN de datos `Metodos1` y no pide la DNN `ims`). Para que intente levantar la sesión `ims` y registrarse en IMS requiere desactivar el *carrier check* de Xiaomi (`*#*#86583#*#*` y `*#*#8667#*#*`) y declarar el tipo `ims` en el APN (o inyectar `CarrierConfig` vía Shizuku). No existen reportes publicados específicos del Redmi Note 14 5G haciendo VoNR contra Open5GS; la referencia oficial más cercana en la matriz de srsRAN es la serie Redmi Note 5G con MediaTek Dimensity.

---

### Capas que determinan la activación de IMS/VoNR

#### A. Capa Android Framework (`CarrierConfig` y `apns-conf.xml`)
* **Verificado en la fuente:**
  * **Android `CarrierConfigManager`:** El framework de telefonía de Android decide si habilita la pila IMS, VoLTE y VoNR para la SIM activa leyendo las claves booleanas del servicio `CarrierConfigManager` asociadas al `subId` / `carrierId` (o `MCC/MNC`):
    * `KEY_CARRIER_VOLTE_AVAILABLE_BOOL` (`carrier_volte_available_bool`): habilita VoLTE/IMS en el perfil del operador.
    * `KEY_CARRIER_VOLTE_PROVISIONED_BOOL` (`carrier_volte_provisioned_bool`): controla si se exige aprovisionamiento previo.
    * `KEY_VONR_ENABLED_BOOL` (`vonr_enabled_bool`, introducida en Android 14 / API 34): habilita el servicio de voz sobre 5G SA (VoNR) para ese operador.
    * `KEY_VONR_SETTING_VISIBILITY_BOOL` (`vonr_setting_visibility_bool`, API 34): controla si el interruptor de VoNR es visible en los ajustes de la SIM.
    * `KEY_VONR_ON_BY_DEFAULT_BOOL` (`vonr_on_by_default_bool`): define si VoNR arranca activado por defecto.
    * **Fuente:** Documentación oficial de Android API (`https://developer.android.com/reference/android/telephony/CarrierConfigManager`).
  * **Valores por defecto en AOSP para PLMN desconocidas (`001/01`):** En el árbol oficial de AOSP (`packages/apps/CarrierConfig`), cuando un `MCC/MNC` no coincide con un operador comercial certificado, aplica la configuración base (`CarrierConfigManager.getDefaultConfig()`), donde `KEY_CARRIER_VOLTE_AVAILABLE_BOOL` y `KEY_VONR_ENABLED_BOOL` valen **`false` por defecto**, salvo que exista un archivo específico (`carrier_config_mccmnc_00101.xml`) o un *override* del fabricante/usuario.
    * **Fuente:** Repositorio AOSP `packages/apps/CarrierConfig` (`https://android.googlesource.com/platform/packages/apps/CarrierConfig/+/refs/heads/main/assets/`).
  * **Base de datos de APNs (`apns-full-conf.xml`):** Para que Android solicite la sesión PDU hacia el núcleo con `DNN = ims`, debe existir un perfil APN para el `MCC="001"` y `MNC="01"` con `type="ims"` (o `default,ims`). En AOSP estándar ya vienen predefinidas entradas de prueba para `mcc="001" mnc="01"` que incluyen el APN `ims`.
    * **Fuente:** AOSP `sample/etc/apns-full-conf.xml` (`https://android.googlesource.com/device/sample/+/main/etc/apns-full-conf.xml`).

* **Inferencia aplicada a nuestros equipos:**
  * El **Motorola Edge 30** conserva una configuración cercana a AOSP y su perfil para la PLMN de prueba `001/01` (que el estándar 3GPP TS 22.101 / TS 34.108 reserva para bancos de prueba de conformidad) mantiene activo el APN interno `ims` y `carrier_volte_available_bool = true`. Al recibir del AMF de Open5GS el bit `IMS-VoPS-3GPP = 1` en el `Registration Accept` (ver punto 4), el teléfono dispara automáticamente `PDU Session Establishment Request` para la DNN `ims`.
  * En cambio, **Xiaomi (HyperOS)** aplica una comprobación adicional (*Carrier Check*) que bloquea la lectura/activación de VoLTE y VoNR en cualquier `MCC/MNC` que no esté en su lista blanca comercial, por lo que el Redmi Note 14 5G ni siquiera pide la DNN `ims` al registrarse en `001/01`.

---

#### B. Capa Módem Qualcomm (Perfiles MBN y EFS en el Motorola Edge 30)
* **Verificado en la fuente:**
  * **Arquitectura MCFG / MBN de Qualcomm:** En chipsets Snapdragon (como el SM7325-AE / Snapdragon 778G+ del Motorola Edge 30), el procesador de banda base ejecuta políticas independientes de Android almacenadas en la partición **EFS** (*Embedded File System*) mediante archivos binarios firmados **`mcfg_sw.mbn`** (*Modem Configuration Software*).
  * **Selección por PLMN y perfil `ROW_Commercial`:** Al leer el IMSI de la USIM, el demonio MCFG busca un perfil `.mbn` para ese `MCC/MNC`. Si la PLMN no coincide con ningún operador comercial cargado en el firmware, el módem carga el perfil genérico de respaldo **`ROW_Commercial`** (*Rest of World*) o `Default`/`Generic`.
  * **Capacidades que controla el MBN:** El archivo `.mbn` define los NV items (*Non-Volatile items*) y archivos EFS (como `/nv/item_files/ims/qp_ims_enable`, `/nv/item_files/modem/mmode/ue_usage_setting`, `/policyman/carrier_policy.xml` y los bits de capacidad RRC `UE-NR-Capability` como `voiceOverNR`).
  * **Fuente:** Documentación de la comunidad de ingeniería de módems Qualcomm en XDA (`https://xdaforums.com/t/guide-activate-volte-vowifi-ut-switch-without-root.4517109/` y `https://xdaforums.com/t/guide-enable-volte-vowifi-on-all-devices-no-root.4105817/`) y guía de COTS UEs de OpenAirInterface (`https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/NR_SA_Tutorial_COTS_UE.md`).

* **Inferencia aplicada al Motorola Edge 30:**
  * El hecho verificado en el laboratorio de que el Motorola Edge 30 ya envíe `PDU Session Establishment Request` con `DNN = ims` sobre 5G SA en `001/01` demuestra que el perfil MBN cargado en su módem Qualcomm para `001/01` **no bloquea IMS en modo N1** a nivel NAS/RRC. Por lo tanto, hay alta probabilidad de que logre registrarse en el servidor IMS sin necesidad de flashear otro `mcfg_sw.mbn` por QPST/PDC, requiriendo a lo sumo habilitar `KEY_VONR_ENABLED_BOOL` en Android si el marcador nativo intenta rechazar la llamada de voz en SA.

---

#### C. Capa Módem MediaTek (Dynamic SBP, `operator_code` y `mims` en el Redmi Note 14 5G)
* **Verificado en la fuente:**
  * **Dynamic SBP (DSBP) de MediaTek:** Los módems MediaTek 5G (`MOLY.NR15` / serie Dimensity) utilizan el mecanismo **Dynamic SBP** (*Single Binary Platform*, propiedad del sistema `persist.vendor.radio.mtk_dsbp_support=1`). Cuando se inserta una SIM, el módem consulta su tabla interna de operadores por `MCC/MNC` y asigna un `operator_code` (por ejemplo, `VoLTE_Operator_Open_Market` o `VoLTE_Operator_CMW500` para equipos de test Rohde & Schwarz).
  * **Comportamiento en `001/01` y en Xiaomi:** En teléfonos Xiaomi con SoC MediaTek, además del filtro de MIUI/HyperOS (*Carrier Check* de VoLTE/VoNR), el módem requiere que el APN tenga explícitamente el tipo `ims` (`APN Type: default,ims` o un APN dedicado con `APN: ims` y `APN Type: ims`) y que los interruptores de VoLTE/VoNR estén destrabados mediante los códigos de Xiaomi.
  * **Fuentes:**
    * Matriz oficial de COTS UEs de srsRAN Project — sección *Xiaomi Redmi Note 10 5G (MediaTek Dimensity 700)* (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/cots_ues.html`).
    * Documentación de UEs en `herlesupreeth/docker_open5gs` (`https://github.com/herlesupreeth/docker_open5gs#tested-ues`).
    * Análisis del modo ingeniero MediaTek (`com.mediatek.engineermode`) en XDA (`https://xdaforums.com/t/guide-enable-volte-vowifi-in-unsupported-countries-without-root-requires-shizuku.4577041/`).

---

## (2) ¿Cómo se fuerza en cada uno: menús ocultos, ADB sin root o root/QPST/EFS?

### A. Xiaomi Redmi Note 14 5G (HyperOS, MediaTek Dimensity)

#### 1. Códigos ocultos de marcador y configuración de APN (Sin root — Paso 1 obligatorio)
* **Verificado en la fuente:**
  1. **Desactivar el *Carrier Check* de VoLTE:** Marcar en la app Teléfono **`*#*#86583#*#*`** (deletrea `VOLTE`). Muestra en pantalla el aviso *"VoLTE carrier check was disabled"* y habilita la opción de llamadas VoLTE en los ajustes de la SIM.
  2. **Desactivar el *Carrier Check* de VoNR:** Marcar **`*#*#8667#*#*`** (deletrea `VONR`). Muestra el aviso *"VoNR display switch"* / *"VoNR carrier check was disabled"* y hace visible el interruptor **Usar VoNR** (*Llamadas 5G*) dentro de *Ajustes $\rightarrow$ Redes móviles $\rightarrow$ [SIM]*.
  3. **Habilitar modo 5G SA:** Marcar **`*#*#726633#*#*`** (ya verificado en el laboratorio en [`2026-11-12_panel-sa-redmi.md`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/sesiones/2026-11-12_panel-sa-redmi.md#L7)).
  4. **Menú de pruebas Android (`*#*#4636#*#*`):** En *Información del teléfono*, permite verificar los conmutadores *VoLTE Provisioned* y el estado del registro IMS (*Tres puntos arriba a la derecha $\rightarrow$ Estado del servicio IMS: Registrado / No registrado, Voz sobre LTE, Voz sobre NR*).
  5. **Configuración del APN en MediaTek:** Según la guía oficial de srsRAN Project para Redmi con MediaTek y la guía de `docker_open5gs`, los módems MediaTek en redes `001/01` necesitan que se agregue en el APN de datos `APN Type: default,ims,ia` o bien crear un segundo APN con `Nombre: IMS`, `APN: ims`, `Tipo de APN: ims`.
  6. **Menú Ingeniero de MediaTek (`*#*#3646633#*#*`):** Abre `com.mediatek.engineermode`. En versiones anteriores de MIUI incluía la pestaña *Telephony $\rightarrow$ IMS* (donde se podía configurar `volte_setting` en `CMW500`, `mims` y pasar `Usage setting` a `Data centric`). Sin embargo, en **HyperOS (Android 14/15)** Xiaomi eliminó o bloqueó el acceso directo a las sub-actividades de modificación de IMS dentro de `EngineerMode` en compilaciones `user`.
  * **Fuentes:**
    * Guía COTS UEs de srsRAN Project (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/cots_ues.html`).
    * Comunidad oficial Xiaomi sobre `*#*#86583#*#*` y `*#*#8667#*#*` (`https://new.c.mi.com/global/post/593261` y `https://xiaomi.eu/community/threads/vonr-enable-code.65521/`).
    * Restricciones de `EngineerMode` en HyperOS (`https://xdaforums.com/t/access-mtk-engineering-mode-on-hyperos.4661231/`).

#### 2. Por ADB sin root (Shizuku + Pixel IMS)
* **Verificado en la fuente:**
  * Si tras usar `*#*#86583#*#*` y `*#*#8667#*#*` el interruptor de VoNR no aparece o Android sigue reportando `VoLTE Provisioned = Off` en `*#*#4636#*#*`, se puede inyectar la configuración en `CarrierConfigManager` **sin root** usando **Shizuku** (`https://github.com/RikkaApps/Shizuku`) junto con la aplicación open-source **Pixel IMS** (`https://github.com/kyujin-cho/pixel-volte-patch`).
  * **Cómo funciona técnicamente sin root:** El usuario `shell` de ADB (UID `2000`) posee en Android el permiso de sistema `android.permission.MODIFY_PHONE_STATE`. A través de Shizuku (iniciado por depuración USB con `adb shell sh /sdcard/Android/data/moe.shizuku.privileged.api/start.sh` o por depuración inalámbrica), Pixel IMS invoca por Binder el método `ICarrierConfigLoader.overrideConfig(int subId, PersistableBundle overrides, boolean persistent)` e inyecta en caliente:
    * `carrier_volte_available_bool = true`
    * `vonr_enabled_bool = true`
    * `vonr_setting_visibility_bool = true`
    * `editable_enhanced_4g_lte_bool = true`
  * **Comandos directos `adb shell` sin apps externas:**
    * `adb shell cmd phone ims enable -s 0` (habilita la pila IMS en el slot 0).
    * Nota sobre `adb shell cmd phone cc set-value`: en código fuente AOSP (`TelephonyShellCommand.java`), el subcomando `cc set-value` verifica `Binder.getCallingUid() == Process.ROOT_UID` o compilación `userdebug`/`eng`, por lo que en teléfonos comerciales sin root falla con `SecurityException`, mientras que `ICarrierConfigLoader.overrideConfig` vía Shizuku sí es aceptado con UID `2000` (`shell`).
    * Nota sobre `adb shell settings put`: las tablas `system`/`global`/`secure` solo cambian preferencias visuales de la UI; no desbloquean `CarrierConfig` ni el módem.
    * Nota sobre `setprop persist.dbg.volte_avail_ovr 1`: las propiedades `persist.dbg.*` requieren privilegios de `root`/`system` por políticas SELinux en compilaciones `user` comerciales.
  * **Fuentes:**
    * Repositorio `kyujin-cho/pixel-volte-patch` (`https://github.com/kyujin-cho/pixel-volte-patch`).
    * Código fuente AOSP `TelephonyShellCommand.java` (`https://android.googlesource.com/platform/packages/services/Telephony/+/refs/heads/main/src/com/android/phone/TelephonyShellCommand.java`).

---

### B. Motorola Edge 30 (`XT2203-1`, Snapdragon 778G+)

#### 1. Qué ya funciona y qué códigos ocultos tiene (Sin root)
* **Verificado en la fuente y en el laboratorio:**
  * Como el Motorola Edge 30 **ya pide la DNN `ims` por sí solo en `001/01`** ([`2026-11-12_panel-sa-redmi.md`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/sesiones/2026-11-12_panel-sa-redmi.md#L28)), **no se debe crear un APN manual `ims` visible en la interfaz de usuario**: la documentación de `herlesupreeth/docker_open5gs` advierte explícitamente que en teléfonos Qualcomm que ya solicitan la sesión `ims` automáticamente, agregar un APN manual `ims` suele romper el enrutamiento interno de la pila IMS del teléfono.
  * **Códigos ocultos en Motorola:**
    * **`*#*#4636#*#*`:** Abre el menú *Testing $\rightarrow$ Información del teléfono*. Allí se puede verificar si los botones *VoLTE Provisioned* están activos, consultar el *Estado del servicio IMS* en el menú de tres puntos y fijar `NR only`.
    * **`*#*#2486#*#*`:** Abre el menú de ingeniería/fábrica de Motorola (*CQA Test* / *CommServer*), pero este menú es de diagnóstico de hardware y **no incluye selectores de perfiles IMS/MBN**.
  * **Fuentes:**
    * Guía de pruebas con UEs en `herlesupreeth/docker_open5gs` (`https://github.com/herlesupreeth/docker_open5gs#tested-ues` y `https://github.com/herlesupreeth/docker_open5gs/discussions/456`).

#### 2. Cómo forzar VoNR sin root en el Motorola (Shizuku + Pixel IMS o CoIMS)
* **Verificado en la fuente:**
  * Si una vez levantado el IMS en la red el Motorola se registra en SIP (`IMS Status: Registered`), pero al marcar una llamada en `NR only` el marcador nativo la corta porque Android considera que VoNR no está habilitado para `001/01`, existen **dos métodos sin root ni QPST**:
    1. **Shizuku + Pixel IMS (`kyujin-cho/pixel-volte-patch`):** Funciona en teléfonos Motorola (cercanos a AOSP) activando `Enable VoLTE` y `Enable VoNR` (`KEY_VONR_ENABLED_BOOL = true`, `KEY_VONR_SETTING_VISIBILITY_BOOL = true`) vía ADB/Shizuku sin abrir el bootloader.
    2. **CoIMS (`herlesupreeth/CoIMS_Wiki`) mediante Carrier Privileges en la SIM:** Si las tarjetas USIM programables del laboratorio soportan el applet **ARA-M** (*Access Rule Application Master*), se carga en la SIM el hash SHA-1 del certificado de la app **CoIMS**. Al insertar la SIM, Android le otorga *Carrier Privileges* a la app CoIMS y esta sobreescribe `CarrierConfig` permanentemente sin necesitar root ni PC.
  * **Fuentes:**
    * Guía de Pixel IMS con Shizuku en Motorola/Qualcomm (`https://xdaforums.com/t/guide-enable-volte-vowifi-in-unsupported-countries-without-root-requires-shizuku.4577041/`).
    * Documentación oficial de CoIMS (`https://github.com/herlesupreeth/CoIMS_Wiki` y `https://github.com/herlesupreeth/CoIMS_App`).

#### 3. ¿Cuándo haría falta Root / QPST / PDC / EFS en el Motorola?
* **Verificado en la fuente:**
  * Las herramientas de Qualcomm **QPST / PDC (*Product Configuration Tool*)** y **EFS Explorer** requieren habilitar el puerto USB de diagnóstico de Qualcomm (`setprop sys.usb.config diag,serial_cdev,rmnet,adb`), lo cual en los Motorola actuales exige **desbloquear el bootloader y tener acceso root (`su`)**.
  * **Cuándo es necesario:** Únicamente si el perfil MBN del módem (`mcfg_sw.mbn`) deshabilita a nivel de banda base la capacidad `voiceOverNR` en el mensaje RRC `UECapabilityInformation` o impide que el cliente IMS del módem envíe el `SIP REGISTER` sobre acceso `3GPP-NR`.
  * **Fuentes:**
    * Guía de activación de puerto `diag` y PDC en Motorola Edge (`https://xdaforums.com/t/guide-enable-5g-and-volte-on-motorola-edge-series-via-qpst-pdc.4461893/`).
    * Tutorial COTS UE de OAI (`https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/NR_SA_Tutorial_COTS_UE.md`).

* **Inferencia para nuestro laboratorio:**
  * Dado que el módem del Motorola Edge 30 **ya solicita la sesión PDU `ims` estando en `NR SA` sobre `001/01`**, el módem ya tiene habilitado IMS sobre NR en su perfil MBN actual. Por lo tanto, **no debería hacer falta root, QPST, PDC ni tocar EFS** en el Motorola; alcanzará con la configuración de red (punto 4) y, si la UI de Android oculta el interruptor de VoNR, **Shizuku + Pixel IMS** por ADB sin root.

---

## (3) Experiencias publicadas de VoNR o VoLTE con Open5GS + IMS (Kamailio + PyHSS, `docker_open5gs`) en PLMN `001/01`

### Verificado en la fuente

1. **Arquitectura de referencia `herlesupreeth/docker_open5gs` (`sa-vonr-deploy.yaml`):**
   * **Fuente:** Repositorio oficial `herlesupreeth/docker_open5gs` (`https://github.com/herlesupreeth/docker_open5gs`, archivo `https://github.com/herlesupreeth/docker_open5gs/blob/master/sa-vonr-deploy.yaml` y directorio `ims_base/`).
   * **Qué implementa:** Despliega en contenedores Docker Open5GS (5GC completo con AMF, SMF, UPF, NRF, UDM, UDR, AUSF, **PCF** y BSF), MySQL, **PyHSS** (como HSS conectado por Diameter Cx a I-CSCF/S-CSCF) y **Kamailio + RTPEngine** (P-CSCF, I-CSCF, S-CSCF).
   * **Integración N5 para VoNR:** El P-CSCF de Kamailio incluye soporte para la interfaz **N5** (HTTP/2 JSON hacia el `PCF` de Open5GS) para solicitar dinámicamente la creación del flujo QoS dedicado de voz (**`5QI = 1`**, GBR) cuando se establece una llamada SIP (`INVITE` / `200 OK`).

2. **Experiencias reportadas con teléfonos Xiaomi / Redmi (MediaTek y Qualcomm) y otros COTS en `docker_open5gs`:**
   * **Fuente 1 (Issue #650 de `docker_open5gs` — comparativa de marcas en VoLTE/VoNR):** `https://github.com/herlesupreeth/docker_open5gs/issues/650`.
     * **Qué funcionó y qué falló:** Al probar teléfonos **Xiaomi** (y Oppo) frente a Samsung en `001/01`:
       * Tras destrabar los switches con los códigos de marcador, los equipos Xiaomi establecen la sesión `ims`, envían `SIP REGISTER`, completan el desafío `401 Unauthorized` (IMS-AKA) y reciben `200 OK`, mostrando el ícono de VoLTE/HD y permitiendo llamadas de voz y SMS.
       * **Particularidad detectada en Xiaomi:** A diferencia de Samsung, varios modelos Xiaomi envían `REGISTER` pero **no envían el mensaje `SIP SUBSCRIBE` posterior** al evento `reg` (o lo hacen con formato distinto). Con **Kamailio** (el IMS por defecto de `docker_open5gs`) las llamadas de voz funcionan igual; en cambio, con OpenSIPS fallaba el enrutamiento de llamadas hacia el Xiaomi.
   * **Fuente 2 (Discussion #456 de `docker_open5gs` — Configuración 5G SA VoNR con Redmi Note 5G):** `https://github.com/herlesupreeth/docker_open5gs/discussions/456`.
     * **Qué funcionó y qué falló:** En pruebas de VoNR 5G SA con un Xiaomi Redmi Note (serie Note 12 5G) en `001/01`, el teléfono inicialmente se conectaba a datos (`internet`) pero no levantaba la sesión `ims` ni enviaba `SIP REGISTER`. Se resolvió desactivando el *carrier check* con los códigos de marcador de Xiaomi (`*#*#86583#*#*` / `*#*#8667#*#*`) y ajustando el APN, sin necesidad de rootear el equipo.
   * **Fuente 3 (Tabla *Tested UEs* en README de `docker_open5gs`):** `https://github.com/herlesupreeth/docker_open5gs#tested-ues`.
     * **Contenido verificado:** Documenta que:
       * En equipos con procesador **MediaTek** (incluyendo Redmi), para que el teléfono inicie el registro IMS en `001/01` hay que habilitar IMS en los menús de ingeniería / códigos secretos y configurar explícitamente el APN `ims`.
       * En equipos con procesador **Qualcomm**, cuando el teléfono solicita la sesión `ims` por su cuenta (o tras aplicar CoIMS / Pixel IMS), **no se debe agregar manualmente un APN `ims`** en la interfaz de ajustes de red de Android, porque eso hace que Android intente usar el APN como sesión de datos normal en lugar de entregárselo al demonio IMS del módem.

3. **Problemas documentados de llamadas VoNR ("Call Ended" inmediato y caídas por `5QI = 1` / `5QI = 5`) en Open5GS + srsRAN/OCUDU:**
   * **Fuente 1 (Issue #569 de `docker_open5gs` y Issues #3600 / #3601 de `open5gs`):** `https://github.com/herlesupreeth/docker_open5gs/issues/569`, `https://github.com/open5gs/open5gs/issues/3600` y `https://github.com/open5gs/open5gs/issues/3601`.
     * **Qué ocurrió:** Muchos usuarios logran que el teléfono quede **registrado en IMS (`200 OK`)** sobre 5G SA (`5QI = 5`), pero al marcar un número la llamada se corta inmediatamente con *"Call Ended"* o cae al atender.
     * **Causas verificadas:**
       1. El `P-CSCF` intenta pedir al `PCF` de Open5GS por interfaz N5 un flujo dedicado `5QI = 1` (GBR) para el audio RTP; si el `PCF`/`SMF` no está configurado o el SDP incluye líneas de medios no soportadas por el parser N5 de Open5GS, la modificación de sesión PDU falla y el `P-CSCF` aborta la llamada.
       2. **Workaround documentado en Kamailio P-CSCF para laboratorio:** En `herlesupreeth/docker_open5gs` (`ims_base/pcscf/kamailio_pcscf.cfg`), existe la bandera `#!define WITH_N5` (o `#!define WITH_RX` en 4G). Si se desactiva `WITH_N5` en el P-CSCF (o si el teléfono no exige *preconditions* de QoS dedicado en el SDP), el audio RTP de la llamada VoNR puede cursarse sobre el mismo flujo por defecto de la sesión `ims` (`5QI = 5`, Non-GBR) en aquellos teléfonos cuyo módem no exige obligatoriamente que la red levante un DRB GBR `5QI = 1` antes de sonar.
   * **Fuente 2 (Issues #996 y #1219 de `srsRAN_Project` / OCUDU sobre VoNR y 5QI):** `https://github.com/srsran/srsRAN_Project/issues/996` y `https://github.com/srsran/srsRAN_Project/issues/1219`.
     * **Qué ocurrió:** Cuando el SMF de Open5GS envía al gNB un `PDU Session Resource Setup Request` con **`5QI = 5`** (al abrir la sesión `ims`) o un `PDU Session Resource Modify Request` con **`5QI = 1`** (al iniciar la llamada de voz), si esos `five_qi` no están definidos en la configuración de QoS del gNB, el CU-CP de srsRAN/OCUDU rechaza la sesión con el error:
       `[CU-CP] [E] "PDU Session Creation Routine" QoS flow 5QI is not configured. id 1 5QI 5`.
   * **Límite de lo comprobado:**
     * No se encontraron publicaciones que documenten pruebas específicas con los nombres comerciales exactos **Xiaomi Redmi Note 14 5G** ni **Motorola Edge 30** en `docker_open5gs`; la evidencia publicada corresponde a otros modelos de las mismas familias y plataformas (**Redmi Note 10/12 5G** con MediaTek/Qualcomm y teléfonos Motorola/Pixel/OnePlus con Snapdragon bajo la misma arquitectura MCFG + AOSP).

---

## (4) Requisitos mínimos del lado de la red para que el teléfono se registre en IMS y haga VoNR (con USIM sin ISIM)

Para que tanto el **Motorola Edge 30** como el **Xiaomi Redmi Note 14 5G** completen el registro IMS y establezcan llamadas con el marcador nativo usando las **SIM 3 y SIM 4 del laboratorio (USIM sin aplicación ISIM)**, la red debe cumplir los siguientes requisitos mínimos verificados en las especificaciones 3GPP y en la documentación de Open5GS / OCUDU / PyHSS:

---

### 1. Indicador NAS `IMS-VoPS-3GPP = 1` en el `Registration Accept` (AMF)
* **Verificado en la fuente:**
  * **Especificación:** **3GPP TS 24.501 V15.7.0, sección 9.11.3.5** (*5GS network feature support*, Tabla 9.11.3.5.1) y **3GPP TS 23.501 V15.8.0, sección 5.16.3.2**.
  * **Requisito:** En el mensaje `REGISTRATION ACCEPT`, el AMF debe incluir el IE `5GS network feature support` con el bit **`IMS-VoPS-3GPP = 1`** (*IMS voice over PS session supported over 3GPP access*). Sin este bit en `1`, el UE asume que la celda 5G SA no soporta voz sobre PS y no intenta usar VoNR.
  * **Estado en nuestro Open5GS v2.8.0:** **Ya está cumplido.** Como se verificó en [`PROYECTO.md`](file:///home/nacho/Escritorio/Universidad/5to%202do%20cuatrimestre/Comunicaciones%20Moviles/5G/PROYECTO.md#L77) (`src/amf/gmm-build.c` L113-118 de Open5GS v2.8.0, `https://github.com/open5gs/open5gs/blob/v2.8.0/src/amf/gmm-build.c#L113-L118`), Open5GS envía por defecto `ims_vops_3gpp = 1`.

---

### 2. Aprovisionamiento de la DNN `ims` con `5QI = 5` (UDM/UDR/MongoDB, SMF y UPF)
* **Verificado en la fuente:**
  * **Especificación:** **3GPP TS 23.501 V15.8.0, sección 5.7.4, Tabla 5.7.4-1** (*Standardized 5QI to QoS characteristics mapping*).
  * **Requisito:**
    * El flujo QoS por defecto de la sesión PDU dedicada a la DNN **`ims`** debe usar el valor estandarizado **`5QI = 5`** (*IMS Signalling*: tipo de recurso **Non-GBR**, prioridad por defecto `10`, *Packet Delay Budget* `100 ms`, *Packet Error Rate* $10^{-6}$).
    * En la base de datos de abonados de **Open5GS (MongoDB)**, cada suscriptor (SIM 3 y SIM 4) debe tener dentro del slice activo (`SST = 1`) una **segunda configuración de sesión (`session`)** con:
      * `name`: **`ims`** (respetando minúsculas; Open5GS hace *case-insensitive match* de la DNN desde TS 23.003, pero se define como `ims`).
      * `type`: `IPv4` o `IPv4v6` (`1` o `3`).
      * `qos.index`: **`5`** (`5QI = 5`).
      * `qos.arp`: prioridad de asignación/retención alta (por ejemplo, `priority_level: 1`, `pre_emption_capability: 1`, `pre_emption_vulnerability: 1`).
    * En `smf.yaml` y `upf.yaml` de Open5GS se debe definir la subred de la DNN `ims` (por ejemplo, `10.46.0.0/16` en una interfaz `ogstun2` o compartiendo `ogstun` con subred separada asociada a `dnn: ims`) para que el SMF no rechace el `PDU Session Establishment Request` del Motorola con causa `Missing or unknown DNN`.
  * **Fuente:** Tutorial oficial de VoLTE/IMS de Open5GS (`https://open5gs.org/open5gs/docs/tutorial/02-VoLTE-setup/`).

---

### 3. Configuración de `5QI = 5` (y `5QI = 1` si hay flujo dedicado de voz) en el gNB (OCUDU / srsRAN Project)
* **Verificado en la fuente:**
  * **Especificación y documentación:** Manual de referencia de configuración de srsRAN Project / OCUDU (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html`) e Issue #1219 (`https://github.com/srsran/srsRAN_Project/issues/1219`).
  * **Requisito:** En el archivo YAML del gNB debe comprobarse que la lista `qos` (o los perfiles por defecto de `cu_cp`/`du`) incluya el mapeo PDCP/RLC para **`five_qi: 5`** (señalización SIP, RLC AM) y **`five_qi: 1`** (voz conversacional RTP, RLC UM, *Packet Delay Budget* `100 ms`, TS 23.501 Tabla 5.7.4-1). Si el gNB no tiene configurado `five_qi: 5`, rechaza el `PDUSessionResourceSetupRequest` de la sesión `ims` aunque Open5GS lo haya aceptado.

---

### 4. Descubrimiento del P-CSCF en el PCO / ePCO (`PDU Session Establishment Accept`)
* **Verificado en la fuente:**
  * **Especificación:**
    * **3GPP TS 24.501 V15.7.0, sección 9.11.4.11** (*Extended protocol configuration options* — ePCO, transportado en `PDU SESSION ESTABLISHMENT REQUEST` y `PDU SESSION ESTABLISHMENT ACCEPT`).
    * **3GPP TS 24.008 V15.6.0, sección 10.5.6.3** (*Protocol configuration options* — PCO).
    * **3GPP TS 24.229 V15.8.0, Anexo B.2.2.1 y sección 9.2.1** (*P-CSCF discovery via PCO*).
  * **Requisito:**
    * Cuando el UE solicita la sesión PDU para la DNN `ims`, incluye en el IE `Extended protocol configuration options` (ePCO) los contenedores de petición:
      * **`0x000C`** (*P-CSCF IPv4 Address Request*) y/o **`0x0001`** (*P-CSCF IPv6 Address Request*).
    * El **SMF de Open5GS** debe responder en el `ePCO` del `PDU Session Establishment Accept` con el contenedor **`0x000C`** conteniendo los 4 bytes de la dirección IPv4 del contenedor **P-CSCF (Kamailio)**.
    * En `smf.yaml` de Open5GS esto se configura simplemente agregando el bloque `p-cscf` con la IP del contenedor Kamailio P-CSCF:
      ```yaml
      smf:
        p-cscf:
          - 172.22.0.21   # IP alcanzable desde la interfaz tun de la sesión ims
      ```
    * **Requisito de red en Docker:** El UE (con IP de la subred `ims`, por ejemplo `10.46.0.x`) debe tener ruta IP directa a través del contenedor `upf` hacia la IP del `P-CSCF` en los puertos **UDP/TCP `5060`** (y el rango de puertos IPsec del P-CSCF, típicamente `5100–65535` UDP/TCP más el protocolo IP **`50` (ESP)** si se usa IPsec IMS-AKA).
  * **Fuente:** Configuración oficial de `smf.yaml` en Open5GS (`https://open5gs.org/open5gs/docs/tutorial/02-VoLTE-setup/`) y `sa-vonr-deploy.yaml` (`https://github.com/herlesupreeth/docker_open5gs/blob/master/smf/smf.yaml`).

---

### 5. Autenticación IMS-AKA con USIM sin ISIM: identidades derivadas del IMSI (`TS 23.003`) y contexto 3G (`TS 31.102` / `TS 33.203`)
* **Verificado en la fuente:**
  * **Especificaciones:**
    * **3GPP TS 23.003 V15.8.0, secciones 13.2, 13.3, 13.4 y 13.4B** (*Numbering, addressing and identification — IMS identities derived from IMSI*).
    * **3GPP TS 24.229 V15.8.0, secciones 5.1.1.1 y 5.1.1.1A** (*Parameters contained in the ISIM / USIM*).
    * **3GPP TS 33.203 V15.4.0, secciones 6.1 y 8.2** (*Access security for IP-based services — Sharing security functions with the USIM*).
    * **3GPP TS 31.102 V15.7.0, sección 7.1.1** (*AUTHENTICATE command in 3G security context*).
  * **Cómo funciona cuando la tarjeta tiene USIM pero NO tiene ISIM:**
    1. **Derivación algorítmica de identidades en el teléfono (TS 23.003 §13.2–13.4B y TS 24.229 §5.1.1.1A):**
       Al detectar que no existe una aplicación ISIM (`AID` `A0000000871004...`) en la UICC, el teléfono lee el `IMSI` de la USIM (`EF_IMSI`) y construye automáticamente tres valores:
       * **Home Network Domain Name (TS 23.003 §13.2):**
         `ims.mnc<MNC_3_dígitos>.mcc<MCC_3_dígitos>.3gppnetwork.org`
         *(Si el MNC es de 2 dígitos, como `01`, la norma exige rellenar con un cero a la izquierda a 3 dígitos: `001`)*.
         Para nuestra PLMN `001/01`:
         **`ims.mnc001.mcc001.3gppnetwork.org`**
       * **Derived IMPI — Private User Identity (TS 23.003 §13.3):**
         `<IMSI>@ims.mnc<MNC>.mcc<MCC>.3gppnetwork.org`
         Para SIM 3 (`001010000000003`):
         **`001010000000003@ims.mnc001.mcc001.3gppnetwork.org`**
         Para SIM 4 (`001010000000004`):
         **`001010000000004@ims.mnc001.mcc001.3gppnetwork.org`**
       * **Temporary Public User Identity — Temporary IMPU (TS 23.003 §13.4B):**
         `sip:<IMSI>@ims.mnc<MNC>.mcc<MCC>.3gppnetwork.org`
         Para SIM 3:
         **`sip:001010000000003@ims.mnc001.mcc001.3gppnetwork.org`**
    2. **Ejecución del desafío criptográfico IMS-AKA sobre la USIM (TS 33.203 §8.2 y TS 31.102 §7.1.1):**
       * El UE envía el primer `SIP REGISTER` con `Authorization: Digest username="001010000000003@ims.mnc001.mcc001.3gppnetwork.org"`.
       * El `S-CSCF` pide al HSS (**PyHSS**) un vector de autenticación Multimedia (`MAR`/`MAA` por interfaz Diameter Cx). PyHSS genera `RAND`, `AUTN`, `XRES`, `CK` e `IK` usando exactamente **la misma clave `K` y el mismo `OPc`** grabados en la USIM para 5G/4G.
       * El `S-CSCF` responde `401 Unauthorized` con `WWW-Authenticate: Digest algorithm=AKAv1-MD5, nonce="<base64(RAND||AUTN)>", ik="...", ck="..."`.
       * Como no hay ISIM, el teléfono envía a la aplicación **USIM** el comando APDU **`AUTHENTICATE` en contexto de seguridad 3G (`P2 = 0x81`, tag `0xDD`)** con `RAND` y `AUTN` (TS 31.102 §7.1.1). La USIM verifica `AUTN` (controlando el contador `SQN`), devuelve `RES`, `CK` e `IK`, el teléfono levanta los túneles IPsec (ESP) con el `P-CSCF` usando `CK`/`IK` y envía el segundo `SIP REGISTER` con la respuesta `RES` calculada por la USIM.
    3. **Precaución crítica sobre el contador `SQN` entre Open5GS (`UDR`) y `PyHSS`:**
       * **Inferencia técnica basada en TS 33.102 / TS 33.203:** Como la tarjeta física USIM mantiene un único arreglo de números de secuencia (`SQN`) para las autenticaciones AKA que comparten la clave `K`, si `Open5GS` (en MongoDB) y `PyHSS` (en MySQL) llevan contadores `SQN` independientes pero usan el mismo `AMF`/`IND`, la USIM responderá al `401 Unauthorized` con un fallo de sincronización **`AUTS`** (`401` $\rightarrow$ nuevo `REGISTER` con `auts=...`). `PyHSS` soporta resincronización por `AUTS`, por lo que al primer fallo reajustará su `SQN` automáticamente y el siguiente intento dará `200 OK`.

---

### 6. Aprovisionamiento de `MSISDN` e *Implicit Registration Set* (`P-Associated-URI`) en el HSS (PyHSS)
* **Verificado en la fuente:**
  * **Especificación:** **3GPP TS 24.229 V15.8.0, secciones 5.1.1.1A, 5.1.1.2.1 y 5.4.1.2** (*Implicit registration set* y cabecera `P-Associated-URI`).
  * **Por qué el `MSISDN` es obligatorio cuando se usa USIM sin ISIM:**
    * Según **TS 24.229 §5.1.1.1A**, el *Temporary IMPU* derivado del IMSI (`sip:<IMSI>@ims.mnc001.mcc001.3gppnetwork.org`) **está prohibido para originar o recibir llamadas (`INVITE`)**: la norma establece que el UE solo puede usarlo en peticiones `REGISTER`.
    * Cuando el `S-CSCF` valida el segundo `REGISTER` y envía el **`200 OK`**, **debe incluir en la cabecera SIP `P-Associated-URI`** al menos una identidad pública permanente (*barred = false* en el *Implicit Registration Set* del HSS) asociada al número telefónico (`MSISDN`) del abonado:
      * `<sip:<MSISDN>@ims.mnc001.mcc001.3gppnetwork.org>`
      * `<tel:+<MSISDN>>`
    * El teléfono extrae su identidad pública de esa cabecera `P-Associated-URI` y la utiliza en las cabeceras `From:` y `P-Preferred-Identity:` de los mensajes `SIP SUBSCRIBE` y `SIP INVITE` cuando el usuario marca un número en el marcador nativo.
    * Si el HSS (`PyHSS`) no devuelve una identidad pública basada en `MSISDN` en `P-Associated-URI`, el teléfono da por fallido el aprovisionamiento de voz o rechaza iniciar llamadas salientes.
  * **Fuentes:**
    * 3GPP TS 24.229 V15.8.0 §5.1.1.1A (`https://www.etsi.org/deliver/etsi_ts/124200_124299/124229/15.08.00_60/ts_124229v150800p.pdf`).
    * Documentación de aprovisionamiento de suscriptores IMS en `PyHSS` / `docker_open5gs` (`https://github.com/herlesupreeth/docker_open5gs#provisioning-subscribers-in-pyhss` y `https://github.com/nickvsnetworking/pyhss`).

---

### Tabla resumen de verificación para el laboratorio

| Componente | Parámetro mínimo requerido | Estado actual en el proyecto | Acción necesaria si se implementa VoNR |
| :--- | :--- | :--- | :--- |
| **USIM (SIM 3 y SIM 4)** | `IMSI` `00101...`, `K` y `OPc` conocidas (sin ISIM) | **Listo** (`001010000000003` y `...004`) | Ninguna en la tarjeta física (derivan IMPI/IMPU por TS 23.003 §13.4). |
| **Open5GS AMF** | `IMS-VoPS-3GPP = 1` en `Registration Accept` | **Listo** (fijo en `gmm-build.c`) | Ninguna. |
| **Open5GS MongoDB** | Sesión `DNN: ims` con `5QI = 5` por abonado + `MSISDN` | Falta (solo está `Metodos1` con `5QI = 9`) | Agregar la sesión `ims` (`5QI = 5`) en las SIM 3 y 4 en MongoDB. |
| **Open5GS SMF / UPF** | Subred para `dnn: ims` + `p-cscf` IP en `smf.yaml` | Falta | Agregar subred `ims` y la IP del P-CSCF para que la entregue en el PCO (`0x000C`). |
| **gNB OCUDU** | Soporte de `five_qi: 5` (y `five_qi: 1`) | Verificar en el YAML / defaults de `release_26_10` | Asegurar que `five_qi: 5` y `1` estén declarados si no vienen por defecto. |
| **IMS (Kamailio + PyHSS)** | Dominio `ims.mnc001.mcc001.3gppnetwork.org`, `K`/`OPc` y `MSISDN` | No desplegado (hoy hay Asterisk SIP simple) | Desplegar contenedores `pyhss`, `icscf`, `scscf`, `pcscf` y `rtpengine` (p. ej. de `docker_open5gs`). |
| **Motorola Edge 30** | Pedir DNN `ims` y habilitar switch VoNR | **Ya pide la DNN `ims` solo** | No agregar APN `ims` manual; si el marcador bloquea llamadas en `NR only`, activar `Enable VoNR` con Shizuku + Pixel IMS. |
| **Redmi Note 14 5G** | Destrabar *carrier check* y pedir DNN `ims` | Solo pide `Metodos1` | Marcar `*#*#86583#*#*` y `*#*#8667#*#*`, y sumar `ims` en `APN Type` (`default,ims`) o con Shizuku + Pixel IMS. |
