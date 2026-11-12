# Sesión 2026-11-12: modo SA del Redmi, arreglos del panel y apagado de Open5GS

Celda en tachoPC con la opción 1 del menú (`gnb_b210_00101_n78_cpofdm.yml`), arrancada a las 12:40 UTC.

## Qué se hizo
- **Modo SA en el Redmi Note 14 5G (HyperOS).** El usuario lo había desactivado el día anterior y la opción desapareció de los ajustes. Para recuperarla:
  1. En el marcador, `*#*#726633#*#*`. El aviso "Show 5G network mode selection" confirma que la opción quedó visible.
  2. **El código alterna:** cada vez que se marca cambia entre mostrar y ocultar la opción, y en la tercera vuelve al estado original. Si no aparece, repetirlo hasta que el aviso diga "Show", forzar la detención de Ajustes y reiniciar.
  3. Elegir SA en la opción de modo de red 5G. Esta versión no tiene la pantalla de "Configuración avanzada" que mencionan las guías para otros Xiaomi. El usuario la hizo aparecer, pero no quedó anotada la pantalla exacta.
  4. Además, `NR only` en `*#*#4636#*#*` → Información del teléfono (D-015).
  - Con eso el Redmi se registró a las 13:07:53 UTC: …003, `10.45.0.3`.
- **Panel** (commit `254e8b8`), revisado en el navegador del usuario con Claude in Chrome:
  - encabezado opaco y tarjetas reordenadas: la tabla de conexiones ocupa todo el ancho y los gráficos usan el alto de su tarjeta;
  - eje Y con decimales según la escala, CQI inválido (−1) como "—", y funciones del núcleo en gris cuando no hay log reciente;
  - **asociación RNTI ↔ IMSI por índice NGAP:** el gNB escribe `ue=N c-rnti=X: UE created` y el AMF, después del SUCI del `InitialUEMessage`, `RAN_UE_NGAP_ID[N]`. Antes solo se usaba `Registration complete`, que no aparece en un Service Request, y por eso el OnePlus figuraba sin IMSI. La igualdad se comprobó en cinco conexiones de esta corrida;
  - al arrancar, el panel recorre el log completo buscando solo esas líneas. Antes releía 256 KB, y el log del gNB pesa cientos de MB con el volcado IQ.
- **Governor en `performance`.** Lo corrió el usuario, porque `sudo` pide contraseña.
- **Etiqueta `antes-menu-2026-11-06` subida a GitHub.**
- **Teléfonos (D-020):** desde ahora se usan el Redmi y el Motorola Edge 30, y el OnePlus 13 se deja de usar. La SIM 4 (…004) pasa al Motorola.

## Hallazgos
- **El Redmi no aparecía en el núcleo:** no hubo ningún intento del …003 hasta que se reactivó SA. Mientras tanto, el OnePlus (…004) se conectaba cada ~16 s, con el rechazo de la DNN `ims` de siempre (P-005).
- **Con los dos teléfonos conectados**, el EVM medido de las constelaciones fue de 4–6 %, con una SINR del PUSCH de 24–30 dB.
- **Tiempo real en tachoPC:** 500–4500 fallas por minuto, con "UL busy" en alarma y la CPU al 85–90 %. Siguieron altas después de pasar a `performance`, como se esperaba de P-004 (persiste una vez que aparece). Pesan el log en `info` que requiere el volcado IQ (334 MB en ~1 h), el volcado mismo (6 GB en ~1 h, con tráfico de los dos teléfonos), Chrome y el panel. **Recrear el panel con la celda corriendo produjo un pico de fallas "late"**, probablemente por leer el log entero.
- **La salida con código 139 de Open5GS ocurre siempre al apagar** (12 veces desde el 2026-11-03): ante el SIGTERM de `stop.sh`, un hilo no termina en 3 s y `ogs_thread_destroy` aborta (`ogs-thread.c:129-130`). No afecta el funcionamiento ni los datos, que están en MongoDB. No se tomó ninguna acción.

## Tarde: Motorola y llamadas SIP
- Segunda corrida (13:43 UTC, opción 1). **El Motorola Edge 30 se registró con la SIM 4 y PLMN 001/01.** Primero no pidió sesión PDU; con el APN `Metodos1` cargado recibió `10.45.0.4`. También pide la DNN `ims` cada ~16 s y el AMF la rechaza, como hacía el OnePlus.
- **Central SIP:** el Motorola usa el interno 1001 y el Redmi el 1002 (al revés de lo que decían los comentarios de `pjsip.conf`, ya corregidos).
  - El registro del Motorola fallaba con `401` aun pegando la contraseña: el Digest recalculado no coincidía con ninguna contraseña del archivo. Se cambiaron por contraseñas cortas sin caracteres ambiguos y, con la cuenta creada de nuevo, se registró.
  - Un `REGISTER` armado a mano dentro de la red interna, con la contraseña del archivo, recibió `200 OK`: así se descartó un problema de la central.
  - **Llamadas:** eco (600) desde el Redmi; el Motorola llamó al Redmi y el Redmi al Motorola. Las dos fueron atendidas, con RTP en los dos sentidos y G.711. Evidencia y explicación en `evidencia/07_voz_sip/`.
  - Cuando Android suspende Linphone, el teléfono deja de contestar los `OPTIONS` y Asterisk responde `404` a las llamadas hacia él.
  - **Después de reiniciar la red, Linphone no se vuelve a registrar solo:** los teléfonos reciben IP nueva y tienen datos, pero a la central no llega ningún `REGISTER`. Se resuelve con "Forzar detención" de Linphone y abrirlo de nuevo en los dos teléfonos. `start.sh` lo recuerda al levantar la central.

## Para retomar
- ~~Borrar el volcado IQ~~: hecho después de cada corrida, con la red apagada (7,9 GB de la mañana y 222 MB de la última; el disco quedó con 59 GB libres).
- **Conviene limitar el volumen del volcado y del log para corridas largas:** es la principal carga nueva sobre una PC de 4 hilos.
- ~~Probar el Motorola con 001/01~~: hecho por la tarde.
- **Postergado por el usuario:** probar en la jaula las opciones 2, 3 y 4 del menú.
- ~~`stop.sh` no detenía el contenedor `sip`~~: ahora lo detiene (commit `ac7d3a4`), y `start.sh` pregunta si levantarlo (por defecto, no).
- Medir la calidad de la llamada (retardo y pérdida de RTP, por ejemplo con `rtp set debug` o una captura en el contenedor `sip`).
- El panel muestra el nombre de la SIM (SIM 3, SIM 4) en lugar del modelo de teléfono (commit `6446d5c`).
- Pendientes de antes: cita E.212, tabla EDGE/LTE y la hipótesis de `zeroCorrelationZoneConfig`.
