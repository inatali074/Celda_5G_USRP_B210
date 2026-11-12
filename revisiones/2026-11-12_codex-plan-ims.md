Recomiendo sumar **Kamailio IMS + PyHSS en Docker**, conservando el Open5GS v2.8.0 integrado. Primero validaría `PDU Session` para `ims` y `IMS registration`; después, llamadas con N5 y un `QoS Flow` de 5QI 1. **Sin N5 sirve como etapa de diagnóstico, pero no garantiza llamadas con el marcador nativo.**

No modifiqué archivos, no leí secretos y no ejecuté servicios.

Para las citas, **P** significa nuestro proyecto y **R** la referencia local, cuyo commit confirmé como `39029beeaca390cc05737593d143f09d1729cf2d`. Las propuestas e inferencias están identificadas; las citas `archivo:Lx–Ly` corresponden al contenido leído.

**1. Estado verificado y hallazgos**

Los dos teléfonos ya solicitan `ims`: el informe registra 15 intentos del Redmi y 351 del Motorola. Eso prueba intención de establecer la sesión, **no** compatibilidad completa de IMS/VoNR. Tampoco corresponde agregar manualmente `ims` a `default` ni seleccionarla como APN de datos. [P: `investigacion/2026-11-12_vonr-telefonos_verificacion.md:L13–L22`].

| Severidad | Archivo y línea | Qué falla y escenario | Corrección propuesta |
|---|---|---|---|
| **Bloqueante para IMS** | P: `config/open5gs/open5gs-5gc-zmq.yml:L41–L53,L106–L109`; `scripts/cargar_abonado.sh:L66–L77` | La configuración declarada sólo contempla `Metodos1`; el cargador sólo provisiona esa sesión. | Agregar `ims` en SMF, UPF, anuncio de SMF y suscripción. |
| **Importante** | P: `scripts/cargar_abonado.sh:L63–L79` | Una recarga reemplaza todo `slice`, eliminando una futura sesión `ims` y sus PCC rules. | Actualizar sesiones por nombre y preservar las restantes. |
| **Importante, condicional** | P: `config/open5gs/open5gs-5gc.yml:L64–L81`; `start.sh:L61` | El primer YAML usa 722/999; seleccionarlo con el gNB 00101 rompe la coherencia del PLMN. El predeterminado real es `open5gs-5gc-zmq.yml`, con 001/01. | Derivar el modo IMS del YAML 001/01 y validar el PLMN antes del arranque. |
| **Bloqueante para transportar IMS** | P: `docker/open5gs/entrypoint.sh:L4–L10` | Sólo crea `ogstun` y configura un pool. Agregar YAML no crea la segunda interfaz ni el retorno desde IMS. | Crear `ogstun2`, su gateway y rutas de retorno dentro de contenedores. |
| **Importante al adaptar la referencia** | R: `sa-vonr-deploy.yaml:L369–L370`; P: `docker-compose.yml:L19–L20` | PyHSS publica 8080, ya ocupado por nuestro dashboard. | No publicar su API o usar, por ejemplo, `127.0.0.1:8081:8080`. |
| **Importante al adaptar la referencia** | R: `pyhss/config.yaml:L78–L81,L95–L103` | Permite devolver material AUC y activa SQL echo, incompatible con el requisito de no exponer claves. | Desactivar ambos y revisar respuestas/logs del aprovisionamiento. |

El núcleo predeterminado y el gNB coinciden en **PLMN 001/01, TAC 7, SST 1 sin SD**, N2 en `10.53.1.2` y N3 entre `.2` y `.3`. La radio declara n78, ARFCN 635000, 20 MHz y SCS 30 kHz. **Propuesta:** conservarlos durante la incorporación de IMS. [P: `config/open5gs/open5gs-5gc-zmq.yml:L62–L82,L103–L105`; `config/gnb/gnb_b210_00101_n78_cpofdm.yml:L8–L23,L36–L42`].

**2. Contenedores mínimos**

Este es el mínimo práctico **manteniendo la arquitectura de la referencia**, no un mínimo teórico de procesos IMS:

| Agregar | Función y fundamento |
|---|---|
| `ims-dns` | Resolución del dominio IMS y ENUM. R: `sa-vonr-deploy.yaml:L296–L309`; `dns/named.conf:L35–L52`. |
| `ims-mysql` | Persistencia de PyHSS y bases de Kamailio. R: `sa-vonr-deploy.yaml:L337–L350`; `pcscf/pcscf_init.sh:L51–L66`; `pyhss/config.yaml:L108–L114`. |
| `ims-pyhss` | AUC e identidades IMS; Diameter Cx hacia I-CSCF/S-CSCF. R: `sa-vonr-deploy.yaml:L351–L419`; `README.md:L509–L558`. |
| `ims-icscf` | Entrada al dominio IMS y selección del S-CSCF. R: `sa-vonr-deploy.yaml:L374–L396`. |
| `ims-scscf` | Registro y encaminamiento IMS. R: `sa-vonr-deploy.yaml:L397–L419`. |
| `ims-pcscf` | Entrada desde el UE, IPsec y AF para N5. R: `sa-vonr-deploy.yaml:L420–L452`; `pcscf/pcscf.cfg:L140–L149`. |
| `ims-rtpengine` | Relay de RTP usado por este P-CSCF. R: `sa-vonr-deploy.yaml:L310–L336`; `pcscf/pcscf_init.sh:L93–L94`. |

`ims_base` es **una imagen común** para los tres CSCF, no otro servicio. PyHSS ya instala y arranca Redis dentro de su contenedor: no hace falta uno separado para reproducir esta referencia. [R: `ims_base/Dockerfile:L39–L53`; `pyhss/Dockerfile:L50–L57`; `pyhss/pyhss_init.sh:L67–L76`].

**Propuesta de exclusiones:** IBCF, SMSC, OsmoMSC/OsmoHLR, ePDG, OCS, Grafana/metrics y WebUI no son necesarios para dos llamadas internas de audio. Tampoco duplicaría MongoDB ni los NFs del 5GC. El README distingue el despliegue VoNR del que agrega IBCF; el troubleshooting vincula IBCF con trunking. [R: `README.md:L400,L414`; `TROUBLESHOOTING.md:L258`; P: `docker-compose.yml:L5–L57`].

Al omitir SMSC, quitaría del perfil mínimo el iFC activo que deriva `MESSAGE` hacia él. No afecta el objetivo de audio, pero evita referencias a servicios ausentes. [R: `pyhss/default_ifc.xml:L76–L105`].

**3. Cambios concretos propuestos en Compose y red**

Propongo conservar `ran` y agregar una bridge `ims`:

| Elemento | Dirección propuesta |
|---|---|
| Red IMS | `10.53.2.0/24` |
| `open5gs`, segunda interfaz | `10.53.2.2` |
| `ims-dns` | `10.53.2.15` |
| `ims-rtpengine` | `10.53.2.16` |
| `ims-mysql` | `10.53.2.17` |
| `ims-pyhss` | `10.53.2.18` |
| `ims-icscf` | `10.53.2.19` |
| `ims-scscf` | `10.53.2.20` |
| `ims-pcscf` | `10.53.2.21` |
| Pool de UE para `ims` | `10.46.0.0/24`, gateway `10.46.0.1` |

**Son asignaciones de diseño propuestas:** no se superponen con las dos redes indicadas, `10.53.1.0/24` y `10.45.0.0/16`; falta comprobar otras redes del host/VPN antes de implementarlas. Las redes actuales están declaradas en P: `docker-compose.yml:L254–L261` y `config/open5gs/network.env:L1–L2`. La referencia también separa red de servicios y pool IMS. [R: `.env:L10,L160–L161`].

Cambios propuestos:

- Los siete servicios nuevos con `profiles: [voz]`; mover Asterisk a `profiles: [sip]` para que activar IMS no lo arranque automáticamente. Hoy `voz` pertenece a Asterisk. [P: `docker-compose.yml:L195–L198`].
- Volumen persistente propio para MySQL; configuraciones montadas `read_only`; archivos generados en el filesystem del contenedor. La referencia persiste `/var/lib/mysql` y genera configuraciones desde `/mnt/...`. [R: `sa-vonr-deploy.yaml:L343–L345`; `pcscf/pcscf_init.sh:L35–L42`].
- `dns: 10.53.2.15` para PyHSS y CSCF. No publicar SIP, Diameter, MySQL ni RTP al host. La referencia comunica esos servicios mediante su bridge. [R: `sa-vonr-deploy.yaml:L351–L452`].
- Mantener RTPengine en `2223/UDP` para control y `49000–50000/UDP` para media; SIP: P-CSCF 5060, I-CSCF 4060, S-CSCF 6060. [R: `sa-vonr-deploy.yaml:L325–L333,L392–L393,L415–L416,L444–L445`].
- Fijar versiones/digests de imágenes. Para Kamailio, conservar inicialmente el commit de `ims_base`; PyHSS usa tag `1.0.2`. No elegir `master` mutable para una prueba reproducible. [R: `ims_base/Dockerfile:L39–L42`; `pyhss/Dockerfile:L55–L57`].

**Retorno sin NAT, imprescindible:** P-CSCF y RTPengine necesitan `10.46.0.0/24 via 10.53.2.2`. DNS también necesita retorno si recibe consultas desde ese pool sin traducción. La referencia instala explícitamente las rutas en P-CSCF/RTPengine y no aplica NAT al pool IMS. [R: `pcscf/pcscf_init.sh:L96–L99`; `rtpengine/rtpengine_init.sh:L62–L65`; `upf/upf_init.sh:L58–L59`]. La ruta adicional en DNS es una **inferencia del diseño propuesto**.

Las rutas y TUN quedarían en namespaces de contenedores. No propongo NAT ni rutas del host. Revisaría aparte las capacidades: la referencia usa `privileged` y RTPengine intenta `modprobe`, que afecta al kernel compartido. **Propuesta:** evaluar RTPengine en userspace y evitar ese intento; cualquier módulo requerido en el host queda pendiente de aprobación. [R: `sa-vonr-deploy.yaml:L314,L424–L426`; `rtpengine/rtpengine_init.sh:L32–L35`].

**4. Open5GS y MongoDB**

Propongo una configuración opcional `open5gs-5gc-ims.yml`, derivada de la actual **001/01**, con:

```yaml
# Fragmentos propuestos; no constituyen el YAML completo.
smf:
  session:
    - subnet: 10.45.0.0/16
      gateway: 10.45.0.1
      dnn: Metodos1
    - subnet: 10.46.0.0/24
      gateway: 10.46.0.1
      dnn: ims
  dns:
    - 10.53.2.15
  p-cscf:
    - 10.53.2.21
  info:
    - s_nssai:
        - sst: 1
          dnn:
            - Metodos1
            - ims

upf:
  session:
    - subnet: 10.45.0.0/16
      gateway: 10.45.0.1
      dnn: Metodos1
      dev: ogstun
    - subnet: 10.46.0.0/24
      gateway: 10.46.0.1
      dnn: ims
      dev: ogstun2
```

El patrón de pools, `p-cscf` y dispositivos está en R: `smf/smf.yaml:L40–L59` y `upf/upf.yaml:L20–L36`; la lista de DNN anunciadas debe ampliar la actual de P: `config/open5gs/open5gs-5gc-zmq.yml:L49–L53`.

El DNS de SMF es global en este esquema: cambiarlo también alcanza a `Metodos1`. Por eso BIND debe resolver IMS y reenviar consultas externas; la referencia configura forwarders. [R: `smf/smf.yaml:L53–L59`; `dns/named.conf:L13–L15`].

El entrypoint necesitaría crear `ogstun2` con `10.46.0.1/24`, sólo en modo IMS. El MASQUERADE existente puede seguir limitado al pool de datos; no extenderlo al pool IMS. [P: `docker/open5gs/entrypoint.sh:L4–L10`; R: `upf/upf_init.sh:L58–L59`].

Para **cada IMSI …003 y …004**, propuesta de suscripción:

| Campo | Valor propuesto |
|---|---|
| Slice | SST 1, sin agregar SD |
| Sesión existente | Preservar `Metodos1`, IPv4, 5QI 9 |
| Nueva sesión | `name: "ims"`, IPv4, `qos.index: 5` |
| ARP de señalización | Priority level 1; pre-emption deshabilitada |
| Session-AMBR inicial | DL 3850 kbit/s / UL 1530 kbit/s, como referencia |
| MSISDN | Uno distinto por SIM, **todavía a definir**, igual en MongoDB y PyHSS |
| PCC de audio, etapa N5 | 5QI 1, GBR/MBR finitos; referencia: 128/128 kbit/s y ARP 2 |

La referencia publica esos valores bajo nomenclatura QCI; en este proyecto SA corresponde comprobar su resultado como **5QI/QoS Flow**. No agregaría video 5QI 2 para esta primera prueba. [R: `README.md:L438–L448`].

El script usa `qos.index` y actualmente inicializa `msisdn: []`: hay que agregar el MSISDN como cadena, preservar seguridad/SQN y no reemplazar todo `slice`. [P: `scripts/cargar_abonado.sh:L63–L89`]. Los 128 kbit/s son **un punto inicial de la referencia**, no un bitrate demostrado para nuestros teléfonos.

**PCF/N5:** PCF ya existe dentro del contenedor; no hace falta agregar otro. Hoy escucha en `127.0.0.13:7777`, y SCP en `127.0.0.22:7777`. [P: `config/open5gs/open5gs-5gc-zmq.yml:L119–L126,L143–L154`].

Para N5, **propuesta de integración**:

- Exponer SCP dentro de `ims`, por ejemplo en `10.53.2.2:7777`, manteniendo el acceso interno.
- Agregar una dirección alcanzable de PCF, por ejemplo `10.53.2.2:7778`, preservando su listener interno y verificando lo anunciado en NRF.
- Configurar `SCP_IP=10.53.2.2` en P-CSCF; callback AF en `10.53.2.21:7777`.
- Verificar que ningún perfil de NF entregado al AF le exija alcanzar un `127.0.0.x` de otro contenedor.

Son **adaptaciones propuestas al 5GC integrado**, no valores copiados y probados. La referencia envía las operaciones N5 a través del SCP y mantiene PCF en una IP alcanzable. [R: `pcscf/pcscf.cfg:L40–L46`; `pcscf/route/mo.cfg:L589–L633`; `pcf/pcf.yaml:L17–L26`].

**5. PyHSS sin exponer Ki/OPc**

Seguiría la secuencia de la referencia: crear APN/DNN lógicas una vez, luego AUC, `subscriber` e `ims_subscriber` por SIM. Usaría `Metodos1` donde el ejemplo dice `internet`, tomando los IDs devueltos por la API; no asumiría IDs `1,2`. [R: `README.md:L480–L558`].

**Procedimiento propuesto para un futuro provisionador Docker:**

1. Montar únicamente el archivo secreto correspondiente a cada SIM como `read_only` bajo `/run/secretos/`.
2. Parsearlo como datos, sin `source`; validar IMSI y hexadecimales, siguiendo el criterio del cargador actual. No asumir que ambas SIM comparten claves. [P: `scripts/cargar_abonado.sh:L17–L39`].
3. Construir el JSON en memoria y enviarlo por HTTP interno a PyHSS; nunca en argv, variables Compose, historial o archivos versionados.
4. Redactar errores y respuestas: mostrar sólo IMSI, IDs y resultado. Desactivar `enable_insecure_auc` y `sqlalchemy_sql_echo` antes de cargar las claves. [R: `pyhss/config.yaml:L78–L81,L95–L103`].
5. Hacer operaciones idempotentes sin reiniciar el SQN de un AUC existente. El ejemplo comienza con `sqn: 0`, pero eso no justifica resetearlo en cada ejecución. [R: `README.md:L509–L521`].

El formato y la ubicación exacta de secretos **por SIM** quedan pendientes: no los inspeccioné. La comparación local debe devolver solamente **coincide/difiere** entre tarjeta, Open5GS y PyHSS. La exclusión Git ya cubre `config/secretos/` y `*.local.*`. [P: `.gitignore:L1–L4`].

También hay que adaptar las credenciales SQL: la referencia habilita root remoto sin contraseña y PyHSS con permisos globales. Propongo usuarios con permisos acotados y credenciales locales no versionadas; MySQL no publicado. [R: `mysql/mysql_init.sh:L48–L55`; `pyhss/pyhss_init.sh:L37–L43`].

Para USIM sin ISIM, **hipótesis inicial a validar en el REGISTER**:

- IMPI: `001010000000003@ims.mnc001.mcc001.3gppnetwork.org`, y equivalente …004.
- IMPU derivado de IMSI, IMPU SIP de MSISDN y `tel:MSISDN`.
- S-CSCF: `sip:scscf.ims.mnc001.mcc001.3gppnetwork.org:6060`.

La plantilla ya incluye esas tres identidades; eso permite iniciar la prueba sin reprogramar la SIM, pero no demuestra qué identidad enviará cada firmware. [R: `pyhss/default_ifc.xml:L3–L25`; `README.md:L546–L558`].

**6. DNS y dominio**

Dominio: **`ims.mnc001.mcc001.3gppnetwork.org`**. El MNC del PLMN sigue siendo `01`; se rellena a tres dígitos para el dominio. La referencia lo genera explícitamente. [R: `dns/dns_init.sh:L35–L37`].

Propuesta de registros:

- `pcscf` → `.21`, SRV UDP/TCP 5060.
- `icscf` → `.19`, SRV del dominio UDP/TCP 4060.
- `scscf` → `.20`, SRV UDP/TCP 6060.
- `hss` → `.18`.
- NAPTR SIP y ENUM hacia el dominio IMS.

[R: `dns/ims_zone:L13–L25,L39–L40`; `dns/e164.arpa:L12–L15`].

Quitar referencias a SMSC, IBCF y voicemail del diseño mínimo, incluyendo la excepción ENUM `+49` hacia IBCF. Ofrecer DNS por UDP y TCP 53 dentro de Docker; entregar P-CSCF mediante PCO/ePCO desde SMF. [R: `dns/ims_zone:L27–L37`; `dns/e164.arpa:L14–L17`; `smf/smf.yaml:L58–L59`].

**7. ¿Arrancar sin N5?**

**Sí para aislar `IMS registration`; no como objetivo final de voz.** Sin N5, la sesión `ims` puede tener su default QoS Flow 5QI 5, pero no habrá autorización dinámica de audio mediante este AF. Algunos COTS UE requieren QoS para completar llamadas, según la propia referencia. [R: `TROUBLESHOOTING.md:L94–L105`].

Desactivar N5 requiere modificar el comportamiento del inicializador: con `DEPLOY_MODE=5G` deshabilita Rx y habilita N5 automáticamente. Propongo un selector explícito que deje **ambos deshabilitados** durante la primera etapa, conservando IPsec. [R: `pcscf/pcscf_init.sh:L70–L74`; `pcscf/pcscf.cfg:L140–L149`].

Los issues justifican pruebas separadas, pero no abandonar N5:

- [Open5GS #3600](https://github.com/open5gs/open5gs/issues/3600): reporta en **2.7.2** problemas de GBR durante modificación de sesión y limitaciones de media types. No prueba que nuestro v2.8.0 tenga el mismo defecto.
- [docker_open5gs #569](https://github.com/herlesupreeth/docker_open5gs/issues/569): había registro IMS pero ningún INVITE; se resolvió actualizando el firmware y habilitando Vo5G. No era evidencia de una falla N5.
- [srsRAN_Project #996](https://github.com/srsran/srsRAN_Project/issues/996): documenta una regresión histórica durante modificación de sesión. No demuestra que afecte OCUDU `e0db566`.

**8. Cambios propuestos en `start.sh` y `stop.sh`**

`start.sh`:

- Separar opciones `--ims` y `--sip`; hoy sólo pregunta por la central SIP. [P: `start.sh:L118–L127`].
- Seleccionar el YAML IMS y activar sus servicios explícitamente antes del gNB.
- Esperar readiness de MySQL, DNS, PyHSS, CSCF y RTPengine; el healthcheck actual sólo comprueba un listener 7777 y no prueba IMS. [P: `docker-compose.yml:L41–L46`].
- Mantener el inicio de radio al final y la verificación del montaje. [P: `start.sh:L153–L164`].
- Si se pidió IMS y falla, detener el arranque antes de transmitir, dejando diagnóstico concreto.
- Separar el ajuste del governor como tarea del host para aprobación; hoy está dentro del arranque. [P: `start.sh:L106–L115`].

`stop.sh`:

- Mantener primero la detención y comprobación del gNB. [P: `stop.sh:L10–L29`].
- Guardar logs IMS con redacción de autenticación/identificadores; no exportar cuerpos AUC.
- Detener CSCF/RTPengine, luego PyHSS, DNS y MySQL; después el núcleo/MongoDB.
- Detener también Asterisk si estaba activo y conservar todos los volúmenes. Hoy sólo contempla `sip` y los servicios originales. [P: `stop.sh:L31–L52,L65–L66`].

**9. Pruebas incrementales y riesgos**

Este orden es una **propuesta de validación**, con criterios observables:

| Etapa | Condición para avanzar |
|---|---|
| Sin radio | Compose válido, IPs sin conflicto, DNS A/SRV/NAPTR/ENUM correctos, API sana y Diameter peers conectados. |
| Un UE, datos | `Metodos1` sigue funcionando. |
| Un UE, IMS | `PDU Session Establishment Accept` para `ims`, IP `10.46.0.x`, P-CSCF correcto y default QoS Flow 5QI 5. |
| IMS registration | `REGISTER → 401 → REGISTER autenticado → 200 OK`; identidades y seguridad negociada coherentes. |
| Dos UE | Ambos registrados simultáneamente y con MSISDN distintos. |
| N5 | AF alcanza SCP/PCF; callbacks llegan; autorización de audio crea QoS Flow 5QI 1 con GFBR/MFBR y filtros correctos. |
| Llamada | INVITE llega al segundo UE; negociación SDP completa; audio bidireccional y liberación limpia. |
| Repetición | Llamadas en ambos sentidos, tras idle y tras reiniciar; `Metodos1` sigue funcionando. |

Riesgos concretos:

- **Firmware:** pedir `ims` no garantiza enviar INVITE ni aceptar las preconditions. Si no aparece INVITE, investigar primero el UE, como ocurrió en #569.
- **IPsec/NAT:** evitar NAT hacia P-CSCF; la referencia documenta que su implementación IPsec no tiene NAT traversal. [R: `TROUBLESHOOTING.md:L102`].
- **Radio/QoS:** la disponibilidad de 5QI 1/5 no fue verificada en el commit exacto de OCUDU. Confirmarla antes de introducir un YAML `qos` propio. [P: `investigacion/2026-11-12_vonr-telefonos_verificacion.md:L5`].
- **Recursos:** sumar IMS puede afectar el tiempo real; el proyecto ya documenta limitaciones de CPU/RAM en tachoPC. Medir carga y pérdidas durante la llamada. [P: `PROYECTO.md:L19,L72`].
- **SQN:** tratar resincronización AKA sin resetear bases como solución rutinaria. Es una precaución del procedimiento propuesto, no una falla observada.

**10. Convivencia con Asterisk**

**No hay choque por 5060 mientras cada servicio tenga su propia IP y namespace, sin publicar el mismo puerto del host.** Asterisk está en `10.53.1.10:5060`; propongo P-CSCF en `10.53.2.21:5060`. [P: `docker-compose.yml:L195–L247`; `config/sip/pjsip.conf:L5–L8`; R: `sa-vonr-deploy.yaml:L444–L452`].

Los puntos a separar son:

- **Perfil:** `voz` actualmente activa Asterisk; cambiar esa asignación como indiqué.
- **Códecs:** Asterisk sólo ofrece `alaw,ulaw`. No asumir interoperabilidad con los códecs negociados por IMS sin revisar SDP. [P: `config/sip/pjsip.conf:L15–L16,L36–L37`].
- **Numeración/autenticación:** los internos 1001/1002 y sus credenciales SIP no reemplazan MSISDN, IMPI ni IMS AKA. [P: `config/sip/pjsip.conf:L11–L18,L32–L39`; R: `README.md:L509–L558`].
- **RTP:** Asterisk usa `10000–10100`; la propuesta de RTPengine usa `49000–50000`, además en otra IP. [P: `config/sip/rtp.conf:L1–L3`; R: `sa-vonr-deploy.yaml:L327–L328`].

Para la primera llamada nativa dejaría Asterisk fuera del camino. Integrarlo mediante trunk sería una etapa posterior, con numeración, routing y códecs definidos.

Quedan por definir **los dos MSISDN**, el archivo secreto correspondiente a cada SIM y la validación de redes del host. La viabilidad final en Redmi/Motorola se determina con `REGISTER`, INVITE y audio observados; el informe actual todavía no verifica esas tres condiciones.
