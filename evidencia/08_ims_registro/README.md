# Evidencia 08: registro IMS del Motorola sobre 5G SA (2026-11-12, etapa 1 de VoNR)

Celda n78 TDD (opción 1 del menú), núcleo Open5GS v2.8.0 con `open5gs-5gc-ims.yml` e IMS en contenedores (perfil `ims`, `docker/ims/README.md`): Kamailio P-CSCF `10.53.2.21`, I-CSCF `.19`, S-CSCF `.20`, PyHSS `.18`, DNS `.15`. Sin N5 ni flujo de voz dedicado (etapa 1).

| Teléfono | SIM | IMSI | MSISDN | Resultado |
| --- | --- | --- | --- | --- |
| Motorola Edge 30 | SIM 4 | 001010000000004 | 1004 | Sesión `ims` (10.46.0.2) y registro IMS completo |
| Redmi Note 14 5G | SIM 3 | 001010000000003 | 1003 | No pide la sesión `ims` (ver abajo) |

## Archivos
Extractos de logs. Se redactaron el IMEI del teléfono (`+sip.instance`), los parámetros de autenticación IMS-AKA (`nonce`, `ck`, `ik` y similares) y cualquier valor hexadecimal largo.
- `nucleo_sesion_ims.log`: AMF y SMF. Registro 5G (15:14:32) y sesiones PDU: `DNN[ims] IPv4[10.46.0.2]` a las 15:14:35 y `DNN[Metodos1] IPv4[10.45.0.2]` a las 15:14:37. El teléfono pide primero la sesión `ims`.
- `pcscf_register.log`: P-CSCF. `REGISTER` desde `10.46.0.2`, respuestas (`REGISTER_reply`), establecimiento de IPsec con el teléfono (`ipsec_forward`) y `SUBSCRIBE` al evento `reg`. Los avisos "Error cleaning IPSec ... during startup" son del arranque del contenedor y no afectan.
- `icscf_register.log`: I-CSCF. Consulta Cx `UAR`/`UAA` a PyHSS para el `REGISTER`.
- `scscf_identidades.log`: S-CSCF. Identidades públicas registradas.

## Cómo confirma la teoría
1. **Sesión PDU para IMS** (TS 23.501 §5.16.3): el AMF anuncia "IMS voice over PS supported over 3GPP access" en el `Registration Accept` (Open5GS `src/amf/gmm-build.c:129-130`). El teléfono abre una sesión a la DNN `ims` con su flujo por defecto 5QI 5 (señalización IMS, TS 23.501 tabla 5.7.4-1) y recibe la dirección del P-CSCF en el PCO/ePCO (TS 24.501).
2. **Registro IMS con USIM sin ISIM** (TS 24.229 §5.1.1.1A, TS 23.003 §13): el teléfono deriva su identidad privada y una pública temporal del IMSI (`001010000000004@ims.mnc001.mcc001.3gppnetwork.org`), el I-CSCF elige el S-CSCF con `UAR`/`UAA` y el S-CSCF autentica con IMS-AKA (TS 33.203) usando las mismas claves de la USIM, ahora cargadas en PyHSS. El P-CSCF y el teléfono establecen IPsec con las claves de esa autenticación.
3. **Conjunto de identidades registradas**: después del `200 OK` quedan registradas la derivada del IMSI, `sip:1004@…` y `tel:1004`. El teléfono va a usar el MSISDN para llamar, porque la identidad temporal derivada del IMSI está restringida al registro.
4. El `SUBSCRIBE`/`NOTIFY` al evento `reg` (RFC 3680) deja al teléfono informado del estado de su registro.

## Por qué el Redmi no se registra
En el Redmi (HyperOS 3, Android 16, MediaTek), la configuración de operadora de Android para la SIM 001/01 tiene `carrier_volte_available_bool = false` (leído con `adb shell dumpsys carrier_config`), aunque el módem soporta IMS, VoLTE y VoNR (`persist.vendor.ims_support=1`, `volte_support=1`, `vonr_setting_support=1`). Con eso, Android no activa IMS y el teléfono nunca pide la DNN `ims`: "Estado de IMS: No registrado", "Servicio de voz: Fuera de servicio".
- Los códigos de Xiaomi y los ajustes de VoLTE/VoNR no cambian esa configuración.
- `adb shell cmd phone cc set-value` responde "Permission denied" (requiere root).
- Pixel IMS 1.3.2 con Shizuku se cierra al aplicar el cambio en HyperOS 3: `NoSuchMethodError` en `IActivityManager$Stub.asInterface`, llamado desde `BrokerInstrumentation.applyConfig`.
- Quedan root (desbloquear el bootloader, que borra el teléfono) o CoIMS (permiso de operadora grabado en la SIM, que requiere sus claves de administración). No se probaron.
