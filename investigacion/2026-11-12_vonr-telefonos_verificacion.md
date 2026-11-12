# Verificación de `2026-11-12_vonr-telefonos.md` (Gemini), hecha por Claude el 2026-11-12

## Confirmado
- **Open5GS v2.8.0 anuncia IMS voice over PS en el `Registration Accept`:** `src/amf/gmm-build.c:129-130` pone `ims_voice_over_ps_session_over_3gpp_access_indicator = 1`, leído en la imagen `5g-open5gs`. Gemini citó bien el hecho, pero con líneas equivocadas (113-118) y con una referencia a `PROYECTO.md#L77` que no habla de eso (es D-015).
- **El gNB trae configurados por defecto los 5QI 1 y 5**, entre otros (`make_default_du_qos_config_list`, `include/srsran/du/du_high/du_qos_config_helpers.h`). Se verificó en una copia de srsRAN Project del 2025-11-11 (`d2f4b70`), no en el árbol exacto de OCUDU `e0db566`, así que conviene confirmarlo en la primera corrida. Sin una sección `qos` en el YAML, el gNB no debería rechazar la sesión `ims` (la advertencia de Gemini sobre el issue #1219 no aplica).
- Existen y tratan lo que dice Gemini:
  - `herlesupreeth/docker_open5gs`: `sa-vonr-deploy.yaml` y `smf/smf.yaml`;
  - issue #569 de docker_open5gs, "VoNR setup - Call ended issue";
  - issue #3600 de open5gs, "Issues with Open5GS with VoNR QoS over N5";
  - issue #996 de srsRAN_Project, llamadas VoNR que fallan por un commit;
  - `kyujin-cho/pixel-volte-patch` ("Pixel IMS: Rootless replacement for Tensor Pixel VoLTE patch", pensado para Pixel; no se verificó que funcione en Motorola);
  - `herlesupreeth/CoIMS_Wiki` (sobrescribir la configuración IMS con Carrier Privileges).
- **README de docker_open5gs** (sección "Troubleshooting"):
  - si no aparece el símbolo de VoLTE o el teléfono no pide la APN `ims`, en general VoLTE no está habilitado en el teléfono: "MediaTek: secret-code IMS menu; others: CoIMS";
  - **nunca elegir a mano la APN `ims` en el teléfono**, y mantener la PLMN de la red igual a la de la SIM (00101);
  - no soportado: VoLTE en Samsung sin root.
- **El código `*#*#726633#*#*`** para mostrar la opción de SA en Xiaomi lo recomienda el autor de docker_open5gs en el issue #650.

## Falso o mal descripto
- ~~"El Redmi no pide la DNN `ims`": falso~~. **Corrección del mismo día:** Gemini tenía razón. Los "15 pedidos" del …003 eran 5, del 2026-11-05, repetidos en tres logs guardados (cada uno incluye la historia completa del contenedor). En la prueba de la etapa 1 el Redmi no pidió `ims` ni con VoLTE y VoNR activados: su configuración de operadora para 001/01 tiene `carrier_volte_available_bool = false` (ver `evidencia/08_ims_registro/README.md`). El Motorola sí la pide.
- **"Para MediaTek, agregar `ims` al tipo de APN (`default,ims`)":** contradice el README de docker_open5gs, que dice no tocar la APN `ims` a mano. No hacerlo.
- **Issue #650:** dice que los Xiaomi y Oppo con Kamailio funcionan en VoLTE (llamadas y SMS) y, en 5G, "igual que en 4G". Lo de "no envían `SUBSCRIBE`" ocurre con OpenSIPS, no con Kamailio. Gemini mezcló los dos casos. Tampoco menciona los códigos `*#*#86583#*#*` ni `*#*#8667#*#*`.
- **"Discussion #456" de docker_open5gs:** no existe como issue; no se pudo verificar como discusión. Lo que se le atribuye (Redmi Note 12 resuelto con códigos de Xiaomi) queda sin fuente.
- **Issue #3601 de open5gs y `herlesupreeth/CoIMS_App`:** no existen.
- **Issue #1219 de srsRAN_Project:** existe, pero es una pregunta general ("How can I set the 5QI class for each UE?"), no el error de 5QI no configurado que describe Gemini.

## Sin verificar
- Los códigos de Xiaomi `*#*#86583#*#*` (VoLTE) y `*#*#8667#*#*` (VoNR) y su efecto en HyperOS.
- Las afirmaciones sobre `CarrierConfig` en AOSP para 001/01, los perfiles MBN de Qualcomm y los permisos de `cmd phone` desde `adb`.
- Las citas de especificaciones (TS 23.003 §13, TS 24.229 §5.1.1.1A, TS 33.203, TS 24.501 §9.11.3.5) coinciden con lo que se sabe de esas normas, pero no se revisaron las secciones exactas.
