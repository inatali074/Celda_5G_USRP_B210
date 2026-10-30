# Verificación de las respuestas de Gemini (2026-10-30, Claude)

Revisa `2026-10-30_sim-usim-lte.md` y `2026-10-30_versiones-docker.md`. Gemini marca como "verificado" datos que resultaron falsos, así que nada de esos archivos se usa sin contrastar.

## Comprobado
- Tags oficiales en `gitlab.com/ocudu/ocudu`: `release_26_10` (`e0db566`) y `release_26_04` existen.
- Open5GS `v2.8.0` existe (commit `157f611`; `f2808a2` es el objeto del tag anotado).
- `docker/Dockerfile` de `release_26_10`: `OS_VERSION=26.04`, `UHD_VERSION=4.9.0.1`, `MARCH=native`.
- `docker/docker-compose.yml` de `release_26_10`: `privileged: true` en el gNB ("solo para acceder a USB"), `SYS_NICE`, monta `/dev/bus/usb/`.
- La B210 enumera como `Cypress WestBridge` en USB 2.0 y pasa a USB 3.0 al cargar firmware (observado en esta placa).
- Guía COTS de srsRAN: pide SIM de prueba o programable con claves conocidas y usa PLMN 00101; la compatibilidad depende del modelo (OnePlus 8T necesita "roaming hack"; Telit + SIM sysmocom debe desactivar el servicio 124).

## Errores de Gemini
| Dijo | Realidad |
| :--- | :--- |
| Imagen base del gNB `ubuntu:24.04` | `ubuntu:26.04` por defecto |
| Open5GS v2.8.0 en los Dockerfile de OCUDU | El compose oficial usa `v2.7.6` sobre Ubuntu 22.04; hay que fijar v2.8.0 aparte |
| Sin `--privileged` como opción oficial | El oficial usa `privileged: true`; `device_cgroup_rules` queda por probar |
| URL `.../user_manuals/source/cots_ues.html` | Devuelve 404. La guía real es `.../knowledge_base/source/cots_ues/source/index.html` |
| FDD μ=0 y TDD μ=1 con 14 000 símbolos/s | μ=1 tiene 28 000 símbolos/s (TS 38.211 §4.3.2) |
| Bit NG-RAN `0x0800` en el segundo byte | Va en el primer byte, b4; GSM está en el segundo (tabla del docx, con TS 31.102) |

## Sin verificar
- Texto normativo de TS 31.102, TS 33.501 y TS 24.501: no están en la carpeta. Pendiente de leerlos, porque contradice la causa raíz del docx.
- Mínimo de 4 núcleos: no encontré la página de requisitos de OCUDU.
- Perfil de módem o `CarrierConfig` como causa, y que 001/01 lo destrabe en estos modelos: mecanismo plausible, sin fuente primaria leída.
- Compatibilidad de MongoDB 8.0 con Open5GS v2.8.0: el Dockerfile oficial de OCUDU instala MongoDB 6.

## Fuentes
- https://gitlab.com/ocudu/ocudu/-/tree/release_26_10/docker
- https://docs.srsran.com/projects/project/en/latest/knowledge_base/source/cots_ues/source/index.html
- https://docs.srsran.com/projects/project/en/latest/tutorials/source/cotsUE/source/index.html
