# Proyecto: celda 5G NR SA con USRP B210

*Memoria entre sesiones. Solo la edita Claude. Última actualización: 2026-10-30.*

## Objetivo
Desplegar desde cero una celda 5G NR Standalone (Opción 2, Release 15) en un entorno de RF autorizado o controlado, y lograr que un celular con SIM de laboratorio se registre, obtenga IP y navegue. Después, medir throughput, latencia y jitter y compararlos con 2G (EDGE) y 4G (LTE) del mismo grupo.

## Alcance
- Radio USRP B210 por USB 3.0, gNB OCUDU/srsRAN Project, núcleo Open5GS v2.8.0 + MongoDB, NAT del kernel Linux, PLMN 722/999.
- Cada decisión se justifica con teoría y especificaciones (TS 38.211, 38.213, 38.321, 38.331).
- Cada etapa se cierra con evidencia: sincronización, acceso, registro, sesión PDU, tráfico IP y mediciones.
- Nada de `~/red5g` se reutiliza: sus resultados son solo antecedente.

## Entorno (relevado 2026-10-30, `tachoPC`)
| Ítem | Valor |
| :--- | :--- |
| Sistema | Debian 13 (trixie), kernel 6.12.113 |
| CPU / RAM / disco | Intel i3-1005G1 (2C/4T, AVX2 y AVX-512) / 7,3 GiB / 86 GB libres |
| USRP B210 | **No conectada** al relevar (`No UHD Devices Found`). Hay bus USB 3 libre |
| UHD | 4.8.0 instalado (`uhd-host`, paquete Debian) |
| Instalados | docker, git, pcscd, pcsc-tools |
| No instalados | Open5GS, MongoDB, gNB, tmux, iperf3, tshark |
| Ajustes del host | governor `powersave`; `wmem_max` 1 MB y `rmem_max` 50 MB; `ip_forward` = 1 |
| Docker | Contenedores 4G detenidos (`srsran-4g`, `srsran_4g`) |
| `~/red5g` | **No existe en esta PC**: está en la PC de un compañero |

## A definir (lo decide el usuario)
1. **Entorno de RF:** jaula de Faraday, cable con atenuadores o permiso ENACOM. Bloquea toda transmisión.
2. **Celulares:** modelos que se usarán y sus bandas NR SA. Antecedentes: OnePlus 13, Motorola Edge 30, Xiaomi Redmi Note 14 5G.
3. **Entregable:** informe, formato y fecha.
4. **SIM:** ¿se puede conseguir una tarjeta programable 5G? (ver Riesgos)
5. **Acceso a `~/red5g`:** copia de solo lectura, si se quiere consultar más allá del docx.

## Versiones
| Componente | Versión | Estado |
| :--- | :--- | :--- |
| Open5GS | v2.8.0 | Fijada por el proyecto |
| UHD | 4.8.0 (Debian) | Propuesta: ya instalada; confirmar soporte de B210 e imágenes de FPGA |
| OCUDU/srsRAN | Sin definir | Las fuentes dicen "OCUDU 2.10", "OCUDU 26.10" y `release_25_10`. Propuesta: fijar un commit tras verificar el repositorio oficial, antes de instalar |

## Decisiones
| ID | Fecha | Decisión | Justificación | Aportó |
| :--- | :--- | :--- | :--- | :--- |
| D-001 | 2026-10-30 | El repo git es solo local y versiona lo nuevo más los documentos propios sin claves de la raíz (`Diagramas_UL_DL_Paging_5G.{md,html}`, `DFT-s-OFDM_explicacion.html`, `generar_html.py`). El resto del material previo, `.env` y `CONTEXTO_ANTECEDENTES.local.md` quedan excluidos | Varios contienen claves de SIM; también son pesados o de terceros. Sin referencia a TS: decisión de organización | Claude |

## Propuestas pendientes de decisión
| ID | Propuesta | Justificación | Falta verificar |
| :--- | :--- | :--- | :--- |
| P-001 | Empezar por **n78 TDD, 20 MHz, μ=1, 51 PRB**, con UL DFT-s-OFDM como objetivo a validar | Es la única configuración con la que un celular comercial llegó al AMF. Numerología: TS 38.211 §4.2-4.3; SSB: TS 38.213 §4.1; precodificación: TS 38.211 §6.3.1.4 | Bandas SA de los celulares. Contradice el diseño n3 FDD del diagrama: cambia lo que se defiende ante el profesor |
| P-002 | Definir la **frecuencia** recién con el entorno de RF elegido | 3489,42 MHz cae en el bloque de Personal y atrajo celulares ajenos | Bloques adjudicados, barrido en recepción |

## Riesgos
- **RF:** ambas bandas están licenciadas. En pruebas previas, celulares de Personal intentaron registrarse en la celda, así que la señal salía del laboratorio. No se transmite hasta definir el entorno.
- **SIM:** las tarjetas LY14 del laboratorio no tienen DF_5GS ni servicios 5G en EF_UST, y con ellas los celulares no buscaron la celda. El docx de antecedente lo da por causa raíz, pero también sigue abierto el perfil del módem para un PLMN desconocido. Hay que verificar en TS 31.102 y TS 33.501 si esos servicios son realmente obligatorios.
- **CPU:** 2 núcleos a 20 MHz pueden no alcanzar. El host tiene el governor en `powersave` y buffers bajos, y cambiarlos requiere aprobación.

## Antecedentes (no reutilizados, a reverificar)
Según `Prueba_configuracion_Drive_5G.docx` (29/10): ZMQ + srsUE funcionó de punta a punta; por aire en n78 un celular de Personal llegó al AMF; n3 no tuvo ningún PRACH real; DFT-s-OFDM y NEA2 quedaron sin validar con celular; B210 serie 31677B2 con `clock_ppm` −1,87 medido.

## Estado actual
Configuración inicial terminada (sesión 0). Sin nada instalado ni transmitido. Codex y agy verificados.

## Próximos pasos
Ver el plan propuesto en `sesiones/2026-10-30_configuracion-inicial.md`.
