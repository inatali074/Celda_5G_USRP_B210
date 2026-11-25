# 2026-11-24 y 2026-11-25: escenario iperf de saturación

Escenario pedido por los docentes: cargar la celda con iperf3 desde el Redmi (SIM 3) y observar los métodos de acceso de NR. Celda en la PC de Santi, iniciada y frenada por las personas desde el panel; Claude solo leyó por SSH.

## Qué se hizo
- **Herramientas** (`Escenario IPERF/`):
  - `monitorear.sh` graba el estado del panel cada 1 s (`datos/*.jsonl`) y la consola del gNB;
  - `analizar.py` hace una gráfica por caso y `resumen.csv`;
  - `rampa.py` arma la curva de saturación de una rampa UDP (5.º argumento opcional: sufijo de archivo, por ejemplo `_cpofdm`);
  - `contar_gnb.sh` cuenta en el log del gNB los paquetes GTP-U recibidos, enviados por PDCP y descartados, y los "UL processor is busy";
  - `comparar.py` compara n78 con n3, y `comparar_formas.py` compara CP-OFDM con DFT-s-OFDM.
  - El usuario e IP de la PC de la celda salen de la variable `REMOTO` o de `remoto.local.txt` (fuera de git).
  - `casos.csv` tiene cada caso con su horario.
- **Datos crudos** (~500 MB, `datos/`) fuera del repo. Van comprimidos en el zip del Drive.
- **Casos:**
  - 0: ping sin carga;
  - 1: TCP de bajada;
  - 2/2b: TCP de subida;
  - 3/3b: bajada con `-P 4`;
  - 4: `--bidir`;
  - 5: rampa UDP de bajada;
  - 6: rampa UDP de subida.
  - El 24/11 se hicieron en n78 y n3 con DFT-s-OFDM. El 25/11 se agregaron los casos 3, 3b y 4 en n3, y la subida con CP-OFDM en las dos bandas (casos 2c y 6c).
- **Informe** en el Google Doc «Escenario iperf – celda 5G» (carpeta del Drive del escenario), con 17 gráficas y 7 tablas. Santi escribió aparte una guía de estudio («Por qué de cada escenario»), que se revisó sin editarla.

## Resultados principales
| | n78 TDD | n3 FDD |
|---|---|---|
| Bajada máxima | ≈ 50 Mbit/s (70 % de 71,7) | 95 Mbit/s (84 % de 113,4) |
| Subida máxima | ≈ 15 Mbit/s (PHR < 0) | ≥ 59 Mbit/s, sin saturar |
| RTT sin carga | diente de sierra de 16–36 ms (SR de 20 ms) | igual, 17–38 ms |

- **Bufferbloat:** la cola RLC AM del gNB llega a su tope (6 172 672 B) y el RTT sube a 1–2 s.
- **Cuatro flujos TCP rinden menos** en las dos bandas: el límite es el PUCCH (CQI y HARQ-ACK), no TCP.
  - Hay RLF por "100 consecutive HARQ-ACK KOs" y "RLC max ReTxs", aun con `pucch.max_consecutive_kos 100000`.
  - Después de un corte de radio, TCP queda en cero hasta 40 s por el backoff del RTO (RFC 6298 §5.5). El ping distingue los dos casos.
- **`csi1=2222` verificado en el código de OCUDU** (`release_26_10`):
  - el 2 es el relleno del log para un UCI inválido (`pucch/formatters.h`);
  - el CSI part 1 de 4 bits no lleva CRC: se descarta si la métrica GLRT no supera 14 (`short_block_detector_impl.cpp`);
  - en n3, más del 99 % de los PUCCH F2 se descartan, con SNR de −4 a −6 dB.
  - Falta ver qué hace el scheduler con un CSI inválido.
- **CP-OFDM contra DFT-s-OFDM:**
  - en la rampa UDP, mismo techo;
  - con TCP de subida en n78, DFT-s-OFDM da 13,6 contra 8,7 Mbit/s (+57 %), con 4–5 dB más de SINR y BLER de 32 contra 53 %;
  - en n3, SINR 5–8 dB menor con CP-OFDM y la misma tasa;
  - CP-OFDM no reduce los UL busy.
  - Limitación: cada forma de onda se midió en un día distinto.
- **P-004:** el 24/11 n3 colapsó dos veces por tiempo real. Desde las 20:11 la CPU quedó en "powersave" (≈ 3,5 GHz); dato de Santi. El 25/11, con la celda recién arrancada, hubo ~18–24 UL busy/s en n3 y ~4/s en n78.

## Para retomar
- Revisar en el scheduler de OCUDU cómo trata un CSI inválido o un CQI 0, y probar `p0_nominal` del PUCCH o más PRB en el F2.
- Alternar CP-OFDM y DFT-s-OFDM en la misma sesión para cuantificar la diferencia.
- El gNB tarda en frenar ("Could not stop application after 5 seconds. Forcing exit."): investigarlo.
- Pasarle a Santi seis observaciones sobre su guía (RLC max ReTxs, fuente de t310, picos con 51/106 PRB para CP-OFDM, entre otras).
