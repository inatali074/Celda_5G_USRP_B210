# Celda 5G NR SA con USRP B210

Trabajo práctico de **Comunicaciones Móviles (UNRC)**: implementación desde cero de una celda **5G NR Standalone** (opción 2, Release 15) con una **USRP B210**, en una jaula de Faraday. Un celular comercial con una SIM de laboratorio se registra, obtiene una IP y navega. Toda la red corre en **Docker**.

📄 **Informe final:** [`informe/informe_final.pdf`](informe/informe_final.pdf)

## Resultados principales

| Magnitud | Valor |
| --- | --- |
| Celda principal | n78 TDD, 3525 MHz, 20 MHz, μ = 1 (30 kHz), 51 PRB, patrón `DDDDDDSUUU` |
| Celda secundaria | n3 FDD, 1842,5 / 1747,5 MHz, 15 kHz, 106 PRB |
| Muestreo | 23,04 MS/s (1536 × 15 kHz = 768 × 30 kHz) |
| Bajada TCP | ≈ 54 Mbit/s (≈ 75 % de la referencia teórica de 71,7 Mbit/s) |
| Subida TCP | 14,8 Mbit/s (referencia teórica: ≈ 35 Mbit/s) |
| RTT mínimo / mediano | 16,7 / 27,7 ms (medido con la celda degradada) |

## Componentes

- **Radio:** USRP B210 por USB 3.0, sin GPSDO.
- **gNB:** OCUDU (ex srsRAN Project) `release_26_10`.
- **Núcleo:** Open5GS v2.8.0 con MongoDB.
- **Monitoreo:** panel web propio (métricas y logs del gNB, ping e iperf3) en `http://localhost:8080`.
- **Salida a Internet:** NAT del kernel Linux.

## Estructura

| Carpeta / archivo | Contenido |
| --- | --- |
| `informe/` | Informe final en LaTeX (`secciones/`), PDF y figuras (`figuras/generar_figuras.py`) |
| `config/gnb/` | Configuraciones del gNB (n78 TDD, n3 FDD, variantes de CSI, DFT-s-OFDM y ZMQ) |
| `config/open5gs/` | Configuración del núcleo |
| `docker/`, `docker-compose.yml` | Imágenes y servicios: `mongodb`, `open5gs`, `dashboard`, `gnb-radio` (perfil `radio`), `gnb-zmq` y `srsue` (perfil `zmq`) |
| `start.sh`, `stop.sh` | Levantan y detienen la red, con una consola de control en GNU screen |
| `scripts/` | Lectura y grabación de SIM por APDU, carga de abonados, prueba de autenticación Milenage, barrido de RX y empaquetado para otra PC |
| `evidencia/` | Evidencia de cada etapa: sincronización, acceso, registro, sesión PDU y mediciones |
| `docs/LEVANTAR_EN_OTRA_PC.md` | Cómo instalar el proyecto en otra PC |
| `PROYECTO.md`, `sesiones/` | Estado del proyecto, decisiones y resúmenes de cada sesión |
| `revisiones/`, `investigacion/` | Revisiones técnicas y consultas de especificaciones hechas durante el trabajo |

## Uso

> ⚠️ **`start.sh` transmite por la B210 apenas se ejecuta.** Usarlo solo dentro de la jaula de Faraday o en un entorno de RF autorizado, y con la B210 conectada por USB 3.0.

```bash
# Levantar la red con la configuración n78 TDD recomendada
./start.sh gnb_b210_00101_csiper_ppm0_kos.yml

# Detenerla
./stop.sh
```

Antes de transmitir hacen falta algunos ajustes del host (governor de CPU y buffers de red), que requieren `sudo` y se describen en [`docs/LEVANTAR_EN_OTRA_PC.md`](docs/LEVANTAR_EN_OTRA_PC.md).

Para recompilar el informe:

```bash
cd informe
python3 figuras/generar_figuras.py
pdflatex informe_final.tex && pdflatex informe_final.tex
```

## Datos sensibles

Las claves de las SIM (K, OPc, ADM) **no están en el repositorio**: viven en `config/secretos/` y en archivos `*.local.*`, que `.gitignore` excluye. Para cargar los abonados en otra PC hay que copiarlos aparte. Los identificadores de teléfonos de terceros que aparecen en la evidencia están anonimizados.
