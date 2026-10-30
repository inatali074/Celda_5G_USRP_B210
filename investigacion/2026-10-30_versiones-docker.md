A continuación se presenta el relevamiento documental sobre los cuatro puntos consultados, siguiendo el formato de [GEMINI.md](file:///home/nacho/Escritorio/Comunicaciones%20Moviles/5G/GEMINI.md).

---

### 1) Relación entre OCUDU y srsRAN Project, repositorios y versiones

#### Verificado en la fuente
* **Transición e identidad:** **srsRAN Project** (el stack 5G NR CU/DU desarrollado por Software Radio Systems) fue transferido a la **OCUDU Ecosystem Foundation** bajo la órbita de la **Linux Foundation** y renombrado a **OCUDU** (*Open Centralized Unit / Distributed Unit*). El cambio incluyó la migración de licencia de AGPLv3 a **BSD 3-Clause (Open MPI variant)**.
  * *Fuentes:* [ocudu.org](https://ocudu.org/), [docs.ocudu.org](https://docs.ocudu.org/), [github.com/srsran/srsRAN_Project](https://github.com/srsran/srsRAN_Project).
* **Repositorios oficiales:**
  * **Fuente activa (Source of Truth):** [https://gitlab.com/ocudu/ocudu](https://gitlab.com/ocudu/ocudu) (con mirror de solo lectura en [https://github.com/ocudu/ocudu](https://github.com/ocudu/ocudu)).
  * **Repositorio histórico (archivado / read-only):** [https://github.com/srsran/srsRAN_Project](https://github.com/srsran/srsRAN_Project).
* **Esquema de versionado y aclaración de nombres:** El proyecto mantiene la convención semestral `YY.MM` (tags `release_YY_MM` en abril y octubre):
  * **`release_25_10` (octubre 2025):** Último release mayor publicado bajo el nombre original *srsRAN Project* antes del cambio de marca (disponible como tag tanto en GitHub como en el historial de GitLab). Introduce separación opcional de ejecutables CU-CP/CU-UP, E1AP Rel-18.5 y mejoras en el modelo de *threading* ([OCUDU Release Notes](https://docs.ocudu.org/)).
  * **`release_26_04` (abril 2026):** Primer release oficial publicado bajo el nombre **OCUDU** ([gitlab.com/ocudu/ocudu/-/tags/release_26_04](https://gitlab.com/ocudu/ocudu/-/tags/release_26_04)).
  * **`release_26_10` / "OCUDU 26.10" (8 de octubre de 2026):** Release estable más reciente de OCUDU (agrega 3GPP Rel-17 NTN, O-RAN Split 7.2b, 2-step RACH, 8T8R MIMO) ([gitlab.com/ocudu/ocudu/-/tags/release_26_10](https://gitlab.com/ocudu/ocudu/-/tags/release_26_10), [Linux Foundation Announcement](https://www.linuxfoundation.org/)).
  * **"OCUDU 2.10":** **No existe** ningún tag `2.10` ni `release_2_10` en `gitlab.com/ocudu/ocudu` ni en `github.com/srsran/srsRAN_Project`.

#### Inferido / Recomendación técnica
* **Sobre "OCUDU 2.10":** Se infiere que es una errata tipográfica en el material secundario por omisión de un dígito sobre `25.10` o `26.10` (o confusión con la numeración `2.x` de Open5GS).
* **Tag recomendado para fijar:**
  * Si se prioriza estabilidad actual y soporte upstream: fijar **`release_26_10`** de `https://gitlab.com/ocudu/ocudu.git`.
  * Si se requiere compatibilidad directa con nombres de binarios (`gnb`), rutas y plantillas de configuración heredadas de fines de 2025: fijar **`release_25_10`**.

---

### 2) Imágenes Docker, Dockerfiles oficiales y MongoDB para Open5GS v2.8.0

#### Verificado en la fuente
* **OCUDU / srsRAN Project (gNB):**
  * **Dockerfile oficial:** Se provee en el árbol fuente bajo `docker/Dockerfile` ([gitlab.com/ocudu/ocudu/-/tree/main/docker](https://gitlab.com/ocudu/ocudu/-/tree/main/docker)). Utiliza un build *multi-stage* sobre **Ubuntu 24.04 LTS (`ubuntu:24.04`)** parametrizado con `ARG OS_VERSION=24.04`, `ARG UHD_VERSION` y `ARG MARCH=native`.
* **Open5GS v2.8.0:**
  * **Imágenes oficiales:** El proyecto [open5gs/open5gs](https://github.com/open5gs/open5gs) **no publica imágenes precompiladas oficiales** en Docker Hub ni en GHCR.
  * **Dockerfiles oficiales para pruebas:** Tanto el repositorio de OCUDU/srsRAN (`docker/open5gs/Dockerfile` y `docker/docker-compose.yml`, que levantan un contenedor *all-in-one* `5gc` + MongoDB + WebUI) como el repositorio de Open5GS (`docker/`) incluyen Dockerfiles oficiales basados en **Ubuntu 22.04 LTS (`jammy`)** o **Ubuntu 24.04 LTS (`noble`)** compilando el tag deseado (`v2.8.0` alinea protocolos con 3GPP Release 19; [Open5GS v2.8.0 Release](https://github.com/open5gs/open5gs/releases/tag/v2.8.0)). En la comunidad también se emplea `gradiant/open5gs:2.8.0` ([Docker Hub](https://hub.docker.com/r/gradiant/open5gs)), aunque es de terceros.
* **MongoDB compatible con Open5GS v2.8.0 y requisitos:**
  * **Versión compatible:** La documentación oficial de instalación de Open5GS actual utiliza **MongoDB 8.0** por defecto, manteniendo compatibilidad hacia atrás con **MongoDB 6.0 y 7.0** mediante `mongoc` ([Open5GS Quickstart](https://open5gs.org/open5gs/docs/guide/01-quickstart/)). En Docker Hub corresponde a las imágenes oficiales `mongo:8.0` (o `mongo:7.0` / `mongo:6.0`).
  * **Requisitos de hardware de MongoDB (5.0 a 8.0):** En arquitectura `x86_64`, MongoDB >= 5.0 exige obligatoriamente soporte de instrucciones **AVX** en el CPU (microarquitectura Intel Haswell o posterior); sin AVX el contenedor aborta con `Illegal instruction` (código 132) ([MongoDB Production Notes](https://www.mongodb.com/docs/manual/administration/production-notes/)).
  * **Compatibilidad con el host (`tachoPC`):** El **Intel Core i3-1005G1** (Ice Lake, 10.ª Gen) soporta **AVX2 y AVX-512**, por lo que cumple el requisito de `mongo:8.0` sin restricciones.

#### Inferido / Recomendación técnica
* **Imagen base recomendada para el gNB:** Si se monta o compila UHD dentro del contenedor, conviene usar **`ubuntu:24.04`** (soportada oficialmente por los scripts de OCUDU) o **`debian:trixie`** si se busca igualar exactamente la versión de `libuhd` (4.8.0) del host para reutilizar `/usr/share/uhd/images` por bind-mount sin discrepancia de versión FPGA.

---

### 3) Acceso a la USRP B210, tiempo real y red en Docker

#### Verificado en la fuente
* **Dispositivos USB y re-enumeración de la B210:**
  * La USRP B210 utiliza un controlador Cypress FX3 (`VID:PID 2500:0020`, que en frío enumera en USB 2.0 como *Cypress WestBridge* hasta que UHD carga `usrp_b200_fw.hex` en RAM) ([Ettus UHD USRP B200/B210 Manual](https://files.ettus.com/manual/page_usrp_b200.html)).
  * Al cargarse el firmware FX3, el dispositivo **se desconecta y re-enumera en el bus USB 3.0 con un nuevo número de dispositivo (`/dev/bus/usb/BBB/DDD`)**. Si el contenedor se inicia solo con `--device /dev/bus/usb/BBB/DDD` estático, pierde acceso tras la re-enumeración.
  * **Permisos mínimos en contenedor (sin `--privileged` completo):**
    * Bind-mount del árbol USB: `-v /dev/bus/usb:/dev/bus/usb`
    * Regla de cgroup para dispositivos de caracteres USB (major `189`): `--device-cgroup-rule='c 189:* rwm'` (en Compose: `device_cgroup_rules: ['c 189:* rwm']`) ([Docker Runtime Privilege and Linux Capabilities](https://docs.docker.com/engine/containers/run/)).
* **Imágenes UHD (`UHD_IMAGES_DIR`):**
  * UHD busca `usrp_b200_fw.hex` y `usrp_b210_fpga.bin` en la ruta definida por la variable de entorno `UHD_IMAGES_DIR` (por defecto `/usr/share/uhd/images`).
  * **Importante:** La versión de `libuhd` dentro del contenedor debe coincidir en compatibilidad de FPGA con las imágenes montadas (en UHD 4.8.0 de Debian 13, B210 usa FPGA compat number 16.0). Si se monta `-v /usr/share/uhd/images:/usr/share/uhd/images:ro` desde el host, el contenedor debe compilarse contra una versión de UHD que espere el mismo *FPGA compatibility number* ([Ettus UHD Firmware/FPGA Images](https://files.ettus.com/manual/page_images.html)).
* **Tiempo real en Docker (`CAP_SYS_NICE` y `rtprio`):**
  * OCUDU/srsRAN utiliza planificación `SCHED_FIFO` para los hilos de L1/PHY y UHD. Para permitirlo sin `--privileged`:
    * `cap_add: [SYS_NICE]` (`--cap-add=SYS_NICE`)
    * `ulimits`: `rtprio: 99` y `memlock: -1` (`--ulimit rtprio=99 --ulimit memlock=-1`) ([srsRAN/OCUDU Docker Documentation](https://gitlab.com/ocudu/ocudu/-/blob/main/docker/docker-compose.yml)).
* **Red (`host` vs `bridge`), SCTP, TUN (`ogstun`) y NAT:**
  * **SCTP (N2 / NGAP, puerto 38412, TS 38.412):** Con una red `bridge` definida por el usuario en Docker Compose, la comunicación SCTP directa entre las IP privadas de los contenedores (`gnb` $\leftrightarrow$ `amf`) funciona nativamente porque el tráfico no pasa por `docker-proxy` sino por el bridge del kernel Linux (siempre que el módulo `sctp` esté cargado en el kernel del host). En cambio, publicar puertos SCTP hacia afuera vía `-p 38412:38412/sctp` suele presentar limitaciones con el proxy de usuario de Docker; por ello, las plantillas oficiales de OCUDU usan una **red bridge dedicada con IPs fijas** (ej. `10.53.1.0/24`) o `network_mode: host` para el gNB ([gitlab.com/ocudu/ocudu/-/blob/main/docker/docker-compose.yml](https://gitlab.com/ocudu/ocudu/-/blob/main/docker/docker-compose.yml)).
  * **Dispositivo TUN (`ogstun`) y NAT en el contenedor UPF:**
    * El contenedor que ejecuta `open5gs-upfd` requiere crear y administrar la interfaz `ogstun` y reglas de `iptables`/`nftables` internas a su *network namespace*:
      * `cap_add: [NET_ADMIN]`
      * `devices: ["/dev/net/tun:/dev/net/tun"]`
      * `sysctls: ["net.ipv4.ip_forward=1"]` (o heredado del host).
    * Si el UPF corre en red `bridge`, el script de entrypoint del contenedor UPF aplica `iptables -t nat -A POSTROUTING -s <SUBRED_UE> ! -o ogstun -j MASQUERADE` hacia la interfaz `eth0` del contenedor, y Docker a su vez hace NAT de la red `bridge` hacia la salida del host ([docker/open5gs en OCUDU](https://gitlab.com/ocudu/ocudu/-/tree/main/docker/open5gs)).

---

### 4) Viabilidad de 20 MHz (TDD $\mu=1$ y FDD $\mu=0$) en Intel i3-1005G1 (2C/4T)

#### Verificado en la fuente
* **Requisitos oficiales publicados por OCUDU / srsRAN Project:**
  * La documentación oficial establece como **mínimo 4 núcleos físicos (4 cores)** con soporte AVX2 (y recomienda 6 a 8 núcleos físicos a $\ge$ 3,0 GHz con gobernador `performance` y kernel *low-latency* o *real-time*) para operar una celda OTA en tiempo real (Split 8 con USRP).
  * Incluso para entornos mínimos o pruebas con núcleos ligeros, la guía especifica **4 cores mínimo** y 8 GB de RAM ([docs.ocudu.org — Hardware Requirements](https://docs.ocudu.org/)).
* **Demanda de procesamiento según numerología (3GPP TS 38.211 §4.2 y §4.3.2, TS 38.104 Tabla 5.3.2-1):**
  * **TDD 20 MHz con $\mu=1$ (SCS = 30 kHz, p. ej. n78):** Ocupa **51 PRBs** y la duración de slot es $T_{\text{slot}} = 0{,}5\text{ ms}$ (2000 slots/s). La tasa de muestreo típica en UHD para 20 MHz es **23,04 MS/s** (o 30,72 MS/s).
  * **FDD 20 MHz con $\mu=0$ (SCS = 15 kHz, p. ej. n3):** Ocupa **106 PRBs** y la duración de slot es $T_{\text{slot}} = 1{,}0\text{ ms}$ (1000 slots/s), pero procesa **DL y UL simultáneamente en todos los slots** (100 % ciclo de actividad DL + 100 % UL), manteniendo la misma tasa de símbolos OFDM por segundo ($14 \times 1000 = 14\,000\text{ símbolos/s}$ en cada dirección) que $\mu=1$ con el doble de subportadoras por símbolo ($106 \times 12 = 1272$ vs $51 \times 12 = 612$).
* **Mediciones oficiales en CPUs de 2 núcleos:** **No existen** mediciones ni benchmarks oficiales publicados por srsRAN/OCUDU sobre procesadores de 2 núcleos físicos (como el i3-1005G1).

#### Inferido a partir de las especificaciones y arquitectura del CPU
* **Viabilidad en el i3-1005G1 (2C/4T, base 1,20 GHz / turbo 3,40 GHz, Ice Lake con AVX-512):**
  * **Punto a favor:** A pesar de ser un i3 móvil, la microarquitectura Ice Lake del i3-1005G1 posee **AVX-512** (confirmado en `PROYECTO.md`), que OCUDU aprovecha en su capa física (LDPC, FFT, estimación de canal) compilando con `-DMARCH=native`, reduciendo sustancialmente el tiempo de cómputo de L1 respecto a AVX2.
  * **Cuello de botella crítico (2 núcleos físicos):** Con solo 2 núcleos físicos (4 hilos SMT) compartidos entre el kernel, interrupciones USB 3.0 de UHD, el gNB y los contenedores de Open5GS + MongoDB, el sistema está **por debajo del mínimo oficial (4 núcleos)**.
  * **TDD ($\mu=1$, 51 PRB) vs FDD ($\mu=0$, 106 PRB):**
    * **TDD 20 MHz ($\mu=1$, 51 PRB)** tiene **mayor probabilidad de sostenerse** en control/registro y tráfico moderado porque no procesa DL y UL simultáneamente (p. ej., patrón DDDSU procesa UL completo en 1 de cada 5 slots), aunque el presupuesto de tiempo por slot es más estricto ($0{,}5\text{ ms}$).
    * **FDD 20 MHz ($\mu=0$, 106 PRB)** exige codificación DL y decodificación UL continuas y simultáneas en cada milisegundo; con 2 núcleos es altamente probable sufrir *lates* (`L`), *underflows* (`U`) u *overflows* (`O`) bajo carga de datos si no se reduce el ancho de banda a **10 MHz (52 PRB en $\mu=0$)**.
  * **Condición indispensable en el host:** Con el gobernador actual en `powersave` (frecuencia base de 1,2 GHz), el i3-1005G1 no cumplirá las cotas de tiempo de 0,5 ms / 1 ms; requerirá pasar el gobernador a `performance` y compilar OCUDU habilitando instrucciones nativas (`AVX-512`).
