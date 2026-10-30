Respuesta conforme a [GEMINI.md](file:///home/nacho/Escritorio/Comunicaciones%20Moviles/5G/GEMINI.md):

---

### 1) Registro en 5G SA sin `DF_5GS` ni servicios 5G en `EF_UST`, cálculo de SUCI y restricciones normativas

#### Verificado en la fuente
* **¿Puede un UE registrarse en 5G SA con una USIM sin `DF_5GS` (`5FC0`) ni servicios 5G (122+) en `EF_UST` (`6F38`)?**
  * **Sí.** El estándar 3GPP mantiene retrocompatibilidad con tarjetas USIM pre-Release 15 (LTE/UMTS) para el acceso a 5G SA.
  * **Fuente:** **3GPP TS 31.102 (V15.9.0 / V16.6.0, Sección 4.2.8 `EF_UST` y Sección 4.4.11 `Contents of files at the DF_5GS level`)**. Los servicios n°122 (`5GS Mobility Management Information`), n°123 (`5G Security Parameters`), n°124 (`Subscription identifier privacy support`) y n°125 (`SUCI calculation by the USIM`) son opcionales. La existencia del directorio `DF_5GS` (`5FC0`) y sus archivos elementales es condicional a que dichos servicios estén presentes y marcados como *available* en `EF_UST`.
  * **Fuente:** **3GPP TS 33.501 (V15.8.0 / V16.7.0, Sección 6.1.2 y 6.2)** y **3GPP TS 24.501 (V15.7.0 / V16.9.0, Secciones 4.4.2 y 5.1.3.2.2)**. La autenticación mutua (5G-AKA / EAP-AKA') emplea el comando estándar `AUTHENTICATE` de la USIM en contexto 3G/UMTS con Milenage (`Ki` / `OPc`), y el ME deriva $K_{\text{AUSF}}$, $K_{\text{SEAF}}$ y $K_{\text{AMF}}$ a partir de $CK$ e $IK$. Cuando la USIM no soporta los servicios n°122 y n°123 (como en un `EF_UST` de 11 bytes, que llega solo hasta el servicio n°88), **el ME almacena los parámetros de movilidad 5GS (`5G-GUTI`, `LAST VISITED REGISTERED TAI`, `5GS update status`) y el contexto de seguridad 5G NAS ($K_{\text{AMF}}$, `ngKSI`) en su propia memoria no volátil (*ME non-volatile memory*)**.

* **¿Quién calcula el SUCI y con qué esquema en ese caso?**
  * **Lo calcula el ME (Mobile Equipment) utilizando el `null-scheme` (`Protection Scheme Identifier = 0`).**
  * **Fuente:** **3GPP TS 33.501 (V15.8.0 / V16.7.0, Sección 6.12.2 `Subscription concealed identifier` y Anexo C.2 `Null-scheme`)** y **3GPP TS 31.102 (V15.9.0 / V16.6.0, Sección 4.2.8 y Sección 4.4.11.8 `EF_SUCI_Calc_Info`)**.
    * Si el servicio n°124 (`Subscription identifier privacy support`) o el n°125 (`SUCI calculation by the USIM`) no están disponibles en `EF_UST`, el cálculo del SUCI corresponde al **ME**.
    * El soporte del `null-scheme` es obligatorio en el ME (*"The ME shall support the null-scheme"*, TS 33.501 Sección 6.12.2). Al no estar disponible el servicio n°124 (ni existir `EF_SUCI_Calc_Info` con una `Home Network Public Key`), el ME debe construir el SUCI con el **`null-scheme`**, enviando el `MSIN` sin cifrar dentro del campo `Scheme Output` y asignando el `Routing Indicator` por defecto (`0000`) ante la ausencia de `EF_Routing_Indicator`.

* **¿Algo normativo obliga al UE a no intentar NR?**
  * **No por carecer de `DF_5GS` o de los servicios 122+ en `EF_UST`.**
  * **Fuente:** **3GPP TS 31.102 (V15.9.0 / V16.6.0, Sección 4.2.5 `EF_PLMNwAcT` / Sección 4.2.8)** y **3GPP TS 23.122 (V15.8.0 / V16.7.0, Sección 4.4)**. Ninguna cláusula prohíbe el acceso a `NG-RAN` por ausencia de `DF_5GS`.

#### Inferido / Recordado
* La única vía por la cual una USIM pre-Rel-15 podría desincentivar la búsqueda automática de NR desde archivos estándar es si los archivos de selección de tecnología de acceso (`EF_HPLMNwAcT`, `EF_PLMNwAcT`, `EF_OPLMNwAcT`, TS 31.102 Sección 4.2.5) estuvieran programados con el bitmap `Access Technology Identifier` forzando únicamente `E-UTRAN` (`0x4000`) y con el bit de `NG-RAN` (`0x0800` en el segundo byte) en `0`. Aun así, eso afecta la prioridad de selección automática de RAT y no impide el escaneo cuando se fuerza `NR only` o búsqueda manual.

---

### 2) Evidencia pública en celulares comerciales (COTS UEs), bloqueo por `CarrierConfig` / módem y uso de PLMN `001/01`

#### Verificado en la fuente
* **Evidencia de celulares comerciales en 5G SA con USIM de LTE (sin `DF_5GS`):**
  * **Fuente:** Documentación de **sysmocom / Osmocom** (`https://www.sysmocom.de/products/sim/sysmousim-sjs1/index.html`, `https://osmocom.org/projects/pysim/wiki`) y **srsRAN Project - COTS UEs** (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/cots_ues.html`).
  * Tarjetas programables de generación LTE/3G sin `DF_5GS` (como `sysmoUSIM-SJS1` o perfiles USIM en `sysmoISIM-SJA2` sin servicios 5G activados) funcionan en 5G SA con **srsRAN Project** y **Open5GS** en teléfonos COTS. De hecho, la documentación de srsRAN indica que cuando se usan tarjetas nuevas con soporte 5G pero sin claves ECIES cargadas, varios módems comerciales fallan al leer `EF_SUCI_Calc_Info` vacío, por lo que **se recomienda desactivar los servicios 124 y 125 en `EF_UST`** (operando exactamente igual que una USIM LTE sin `DF_5GS`).

* **Bloqueo por perfil de módem (`Carrier Policy`) y `CarrierConfig` con un PLMN desconocido (`722/999`):**
  * **Fuente:** Código fuente de Android AOSP `CarrierConfigManager` (`https://android.googlesource.com/platform/packages/apps/CarrierConfig/`, clave `KEY_CARRIER_NR_AVAILABILITIES_INT_ARRAY`), guía oficial de **srsRAN COTS UEs** (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/cots_ues.html`) y documentación de políticas de banda base Qualcomm (`mcfg` / `carrier_policy.xml` documentada en comunidades técnicas como `https://cacombos.com/` y discusiones de Open5GS `https://github.com/open5gs/open5gs/discussions`).
  * Los celulares comerciales aplican un doble filtro basado en el **MCC/MNC del IMSI de la SIM insertada**:
    1. **Android `CarrierConfig`:** Si el PLMN de la SIM (`722/999`, que no corresponde a ningún operador comercial registrado en Argentina) no tiene una configuración específica en el paquete `CarrierConfig` del teléfono que incluya el valor `2` (`CARRIER_NR_AVAILABILITY_SA`) en `carrier_nr_availabilities_int_array`, Android deshabilita 5G SA hacia el módem.
    2. **Política de banda base (Qualcomm MCFG / Exynos / MediaTek):** El firmware del módem carga un perfil (`mcfg_sw.mbn` / `carrier_policy.xml`) según el MCC/MNC de la SIM. Si el PLMN es desconocido (`722/999`), cae en el perfil *default/ROW* del fabricante, que en la mayoría de los teléfonos comerciales **deshabilita NR SA (o poda las bandas SA en `UE Capability`) y apaga el escaneo de portadoras SA**.
  * Esto explica el comportamiento observado: con la SIM de operadora comercial, el MCC/MNC de esa tarjeta cargó un perfil válido en el módem que habilitó el escaneo RF en n3/n78 (permitiendo ver la celda y llegar al AMF), mientras que con la USIM `722/999` el módem bloqueó la pila NR SA antes de escanear el aire.

* **¿Sirve usar el PLMN `001/01`?**
  * **Fuente:** **srsRAN Project - COTS UEs** (`https://docs.srsran.com/projects/project/en/latest/user_manuals/source/cots_ues.html`) y tutoriales oficiales de **Open5GS** (`https://open5gs.org/open5gs/docs/tutorial/01-your-first-lte/`).
  * **Sí, en muchos equipos es mucho más efectivo que un PLMN desconocido como `722/999`, aunque con matices según el fabricante:**
    * `001/01` es el *Test PLMN* estándar de 3GPP TS 23.003 / ITU-T E.212. Tanto srsRAN como Open5GS lo usan por defecto porque muchos módems Qualcomm y teléfonos Android (OnePlus, varios Motorola/Xiaomi/Pixel y módulos Quectel) reconocen `001/01` como entorno de prueba (*test/lab SIM*) y cargan un perfil de módem genérico de laboratorio que **no restringe bandas ni capacidades 5G SA**.
    * Aun usando `001/01`, la documentación de srsRAN señala que en smartphones Android suele ser necesario:
      1. Marcar `*#*#4636#*#*` (*Información del teléfono*) y fijar el tipo de red preferido en **`NR only`** (lo que obliga al módem a buscar celdas SA e ignorar la preferencia de anclaje LTE/NSA).
      2. Si el teléfono bloquea SA por `CarrierConfig` incluso en `001/01` (frecuente en Samsung, Google Pixel o iPhone recientes), en Android se puede habilitar `CARRIER_NR_AVAILABILITY_SA` sin root mediante herramientas que usan la API de `CarrierConfigLoader` a través de ADB/Shizuku (como *Pixel IMS*), o bien (únicamente dentro de jaula de Faraday / conexión cableada atenuada) usar en la SIM y en la celda un MCC/MNC que esté en la *whitelist* 5G SA del teléfono.
