# Revisión de Claude: Dockerfile y compose de Codex (2026-10-30)

Contrastado con el código de `release_26_10` (OCUDU), `v2.8.0` (Open5GS) y `release_25_10` (srsRAN_4G). Nada se construyó ni se levantó.

## Corregido
| Severidad | Archivo | Problema | Corrección |
| :--- | :--- | :--- | :--- |
| Bloqueante | `docker/open5gs/Dockerfile`, compose | `f2808a2` es el objeto del tag anotado, no el commit: la comprobación de HEAD fallaba siempre. El error vino del pedido de Claude | Commit `157f611` |
| Importante | `docker/srsue/Dockerfile` | `DISABLE_SIMD=ON` sin pedido: el UE por software podía ir demasiado lento | Quitado |
| Importante | compose, `gnb-zmq` | Sin `SYS_NICE`, que el compose oficial marca como siempre necesario | Agregado, con `ulimits` |
| Importante | compose | gNB iniciado sin esperar al núcleo | Healthcheck de `:7777` y `service_healthy` |
| Menor | `docker/gnb/Dockerfile` | Descargaba las imágenes de todas las USRP | `-t b2xx` |

## Confirmado en fuente
Rutas de los scripts de OCUDU, `ENABLE_ZEROMQ`, ruta `build/apps/gnb/gnb`, opciones de cmake de srsRAN_4G, commits de OCUDU y srsRAN_4G. Sin perfiles, el compose solo incluye `mongodb` y `open5gs`; no publica puertos ni usa `privileged`.

## Pendiente
- El módulo `sctp` no está cargado en el host. Puede hacer falta `sudo modprobe sctp` (requiere aprobación).
- Las Dockerfile no se construyeron: el binario `5gc` y el camino de `uhd_images_downloader` recién se comprueban al construir.
- `MARCH=x86-64-v3` puede dejar sin AVX-512 al gNB; medir, porque la CPU está justa.
- `docker compose` falla hasta crear `config/open5gs/network.env` y demás configuraciones.
- Acceso USB sin `privileged`: sin probar.
- Levantar el compose crea reglas de iptables de Docker en el host: requiere aprobación.

## Configuraciones sin radio (revisión de Claude)
`gnb_zmq.yml` coincide con el ejemplo oficial `gnb_rf_b210_fdd_srsUE.yml` en celda, PDCCH y PRACH. Las opciones `no_*` de `open5gs-5gc.yml` existen en v2.8.0.

**Corregido (importante):** srsUE fija MNC de 2 dígitos salvo para MCC de EE. UU. (`usim.cc`, `get_mnc_str`), así que su SUCI llega como 722/99 y el NRF solo servía 722/999. Se agregó 722/99 a `nrf.serving`, solo para esta prueba. Falta comprobar en la ejecución que alcance.

Claude creó `config/secretos/usim.env` (permisos 600, excluido de git). Sigue faltando cargar el abonado en MongoDB.
