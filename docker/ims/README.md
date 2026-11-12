# IMS / VoNR — etapa 1

Objetivo: sesión PDU `ims` IPv4 y registro `REGISTER → 401 → REGISTER autenticado → 200 OK` para las dos SIM. No incluye llamadas, RTPengine, SMS, N5 ni Rx. IPsec permanece habilitado. La compatibilidad del firmware y del 5QI 5 en OCUDU debe verificarse con los teléfonos.

Adaptado de Supreeth Herle/docker_open5gs, commit `39029beeaca390cc05737593d143f09d1729cf2d`, BSD-2-Clause: [licencia](LICENSE-docker_open5gs). Kamailio se compila desde `9874599e41fa69cc3807676a7995a135a350a9ba`; PyHSS desde tag `1.0.2`. Las dependencias apt/pip no constituyen un lock completo. La [API de esa versión](https://github.com/nickvsnetworking/pyhss/blob/1.0.2/services/apiService.py) imprime JSON de aprovisionamiento; `silenciar_api.py` elimina sus instrucciones print en la imagen y el inicializador descarta stdout/stderr de la API. No activar SQL echo ni logging DEBUG al trabajar con claves.

## Arquitectura

Todos los servicios nuevos usan perfil `ims`; Asterisk conserva `voz`. No se publican puertos IMS al host; la API se consulta con `compose exec`. Open5GS conserva `ran` y suma `ims`:

| Componente | IP en `ims` | Función |
|---|---|---|
| Open5GS | 10.53.2.2 | SMF/UPF integrado, retorno UE |
| ims-dns | 10.53.2.15 | BIND autoritativo IMS |
| ims-mysql | 10.53.2.17 | Persistencia HSS y CSCF |
| ims-pyhss | 10.53.2.18 | AUC, Cx TCP 3868, API 8080 |
| ims-icscf | 10.53.2.19 | SIP 4060, selección S-CSCF |
| ims-scscf | 10.53.2.20 | SIP 6060, registro AKA |
| ims-pcscf | 10.53.2.21 | SIP 5060, IPsec, entrada UE |

Dominio `ims.mnc001.mcc001.3gppnetwork.org` (PLMN 001/01, TAC 7, SST 1 sin SD). Pool `10.46.0.0/24`, gateway `10.46.0.1/24` en `ogstun2`. El P-CSCF instala dentro de su namespace `10.46.0.0/24 via 10.53.2.2`. No hay NAT de ese pool. Los DNS entregados por el SMF a Metodos1 siguen siendo 8.8.8.8 y 8.8.4.4; el P-CSCF se entrega por PCO/ePCO. El DNS interno se usa para Cx y encaminamiento SIP.

`IMS_SUBNET` y `OGSTUN2_ADDRESS` habilitan la segunda TUN; sin ellas el entrypoint mantiene su comportamiento anterior. `start.sh` las exporta sólo al elegir IMS. `IMS_N5=0` mantiene N5 apagado; cambiarlo a 1 requiere primero integrar SCP/PCF y validar la etapa 2, no basta con activar el selector. Rx permanece apagado.

No se usa privileged ni modprobe. Sólo P-CSCF agrega NET_ADMIN para ruta/XFRM y configura ip_nonlocal_bind dentro de su namespace. MySQL retiene capacidades de su entrypoint para cambiar dueño y usuario; CSCF/PyHSS eliminan todas las restantes. IPsec necesita soporte XFRM del kernel compartido; si falta, el diagnóstico queda pendiente de intervención del usuario, sin cambios automáticos del host.

## Preparación manual (sin radio)

Requiere Docker Compose >= 2.24 (`env_file.required`) y soporte de `up --wait`. Antes de usar la red, comprobar que 10.53.2.0/24 y 10.46.0.0/24 no se superpongan con redes locales/VPN.

1. Copiar `config/ims/ims_mysql.ejemplo.env` a `config/secretos/ims_mysql.env`, con permisos 600. Reemplazar ambos CAMBIAR por contraseñas distintas; IMS_DB_PASSWORD admite 16 o más caracteres A-Z, a-z, 0-9 y `_` (restricción deliberada para SQL/URLs). No crear MYSQL_ROOT_HOST: root queda local. Los cuatro usuarios sólo tienen acceso a su propia base. El archivo real no se versiona. Las contraseñas SQL son variables del contenedor; las claves de SIM nunca lo son.
2. Construir las imágenes cuando el responsable lo autorice. **También hay que reconstruir Open5GS**, porque cambió su entrypoint. No se construyeron durante esta implementación:

   ```bash
   docker compose --profile ims build open5gs ims-dns ims-mysql ims-pyhss ims-icscf ims-scscf ims-pcscf
   ```

3. Levantar sólo núcleo e IMS, sin gNB ni USB:

   ```bash
   export OPEN5GS_CONFIG=open5gs-5gc-ims.yml
   export IMS_SUBNET=10.46.0.0/24 OGSTUN2_ADDRESS=10.46.0.1/24
   docker compose up -d --no-build mongodb open5gs
   docker compose --profile ims up -d --no-build --wait --wait-timeout 180 ims-dns ims-mysql ims-pyhss ims-icscf ims-scscf ims-pcscf
   scripts/verificar_ims.sh
   ```

MySQL persiste en `ims-mysql-data`. La creación de usuarios sólo ocurre con un volumen nuevo. Si un esquema CSCF quedó a medio inicializar, se aborta al reiniciar: revisar/restaurar la base afectada; no se continúa con tablas incompletas. Cambiar el env no rota contraseñas de un volumen existente: planificar una rotación SQL autenticada; no borrar volúmenes para resolver AKA/SQN. No ejecutar cargadores concurrentemente ni mientras se cambia la suscripción desde otra herramienta.

## Abonados

Primero debe existir el abonado 5G y su slice SST 1. Si todavía no existe, usar `scripts/cargar_abonado.sh <IMSI>` según el procedimiento del proyecto. Ese cargador ahora conserva otras sesiones y slices al recargar Metodos1.

```bash
scripts/cargar_ims.sh 001010000000003 1003
scripts/cargar_ims.sh 001010000000004 1004
```

El cargador parsea `config/secretos/usim.env` como datos, sin source. Ambas SIM usan USIM_K y USIM_OPC compartidas según la decisión local. JSON en memoria y stdin hacia Python dentro de PyHSS; nunca claves en argv, Compose o archivos temporales. La salida sólo informa IMSI, IDs y resultado. No imprimir respuestas AUC ni usar `set -x`.

Se crean APN Metodos1/ims, AUC, subscriber e ims_subscriber usando IDs devueltos. Un AUC existente se reutiliza **sin PATCH**, sin comparar ni resetear SQN; un cambio de claves debe seguir un procedimiento separado que informe sólo coincide/difiere. El cargador no demuestra que las claves existentes coincidan con la tarjeta. En MongoDB sólo cambia sesión ims y agrega MSISDN: IPv4, 5QI 5, ARP 1, pre-emption deshabilitada, AMBR DL 3850 / UL 1530 kbit/s. Preserva Metodos1, otras sesiones, security y SQN. PyHSS y MongoDB no forman una transacción conjunta: si una parte falla, corregir la causa y repetir. Primero se actualiza PyHSS; el mensaje de error identifica la posible carga parcial.

## Pruebas en orden

Sin radio:

1. `docker compose --profile ims config --quiet` (no imprimir config completa: incluye credenciales SQL). Verificar todos los healthchecks.
2. `scripts/verificar_ims.sh`: exige A correctos, API disponible y `cdp.list_peers` con peer HSS `I_Open` o `R_Open` en ambos CSCF. También se puede consultar cada peer con `docker compose --profile ims exec ims-scscf kamcmd -s unix:/var/run/kamailio/kamailio_ctl cdp.list_peers`.
3. En `ims-dns`, consultar `dig @127.0.0.1 _sip._udp.ims.mnc001.mcc001.3gppnetwork.org SRV` y NAPTR del dominio: deben seleccionar I-CSCF 4060. Las consultas A de pcscf/scscf/hss deben coincidir con la tabla.
4. Cargar ambos abonados y repetir la carga: mismos IDs AUC, sin duplicados, sin reinicio de SQN. Corroborar localmente que Metodos1 sigue presente; no volcar documentos con security.

Con radio, sólo bajo el procedimiento autorizado del laboratorio:

1. `./start.sh`, conservar el menú habitual y responder sí a IMS. Selecciona el YAML IMS y aborta antes del gNB si IMS no queda listo. Asterisk sigue siendo una opción independiente. Cargar abonados antes de conectar los teléfonos.
2. Un teléfono por vez: confirmar `PDU Session Establishment Accept` para DNN ims, IP 10.46.0.x, P-CSCF 10.53.2.21 y default QoS Flow 5QI 5. Confirmar también que Metodos1 sigue navegando.
3. Verificar `REGISTER → 401 → REGISTER con Authorization → 200 OK`, identidades IMSI/MSISDN del dominio e IPsec negociado. El 401 inicial es esperado. Con IPsec, parte del tráfico puede verse como ESP; corroborar el resultado en los CSCF y estado de registro de PyHSS, sin exportar claves ni vectores AKA. No elegir ims manualmente como APN de datos.
4. Repetir con ambos teléfonos simultáneamente (1003/1004) y tras reconexión. Un healthcheck verde no prueba este resultado.
5. `./stop.sh` frena primero radio, luego IMS y después núcleo; conserva MongoDB/MySQL. No copia automáticamente logs IMS que puedan contener material de autenticación.

Quedó pendiente la validación real de imágenes, BIND/Kamailio, SQL, capacidades/IPsec, peers Cx, PCO, radio y REGISTER 200 OK. Ningún contenedor fue ejecutado durante la implementación.
