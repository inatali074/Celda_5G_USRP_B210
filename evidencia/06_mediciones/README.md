# Etapa 06: mediciones

## 2026-11-03: prueba A/B/A de CP-OFDM contra DFT-s-OFDM en la subida (tachoPC)
- **Detalle de la prueba:** `sesiones/2026-11-03_dashboard-dfts.md`.
- **Logs completos:** en `logs/`, fuera de git.

| Tramo | Corrida | Configuración |
| :--- | :--- | :--- |
| A1 | `2026-11-03_194454` | CP-OFDM |
| B | `2026-11-03_195149` | DFT-s-OFDM |
| A2 | `2026-11-03_195841` | CP-OFDM |

| Archivo | Contenido |
| :--- | :--- |
| `2026-11-03_iperf_ping_resultados.md` | Resultados de iperf3 (subida y bajada) y del ping, con la configuración y el estado de la celda en cada prueba. Son una transcripción: los JSON originales no se conservaron |
| `2026-11-03_gnb_por_segundo_{A1,B,A2}.csv` | Por segundo y desde el log del gNB: PUSCH OK y KO, Mbit/s decodificados en la subida (suma de TBS de los PUSCH OK), modulaciones, cantidad de PDSCH, fallas de tiempo real y "UL processor is busy" |
| `2026-11-03_gnb_eventos_{A1,B,A2}.log` | Arranque del gNB, creación de UE, `rrcRelease` y RLF |
| `2026-11-03_nucleo_eventos_{A1,B,A2}.log` | Registros, IP asignadas y liberaciones en Open5GS, filtrados a la ventana de cada corrida del gNB |

En los logs solo aparecen las SIM de laboratorio (…003 y …004): no hay identificadores de terceros.

### Cómo confirma o no la teoría
- **Precodificación por transformada (TS 38.211 §6.3.1.4):** la norma define la transformada y la restricción de PRB 2^a·3^b·5^c de la asignación del PUSCH. Que la reducción de PAPR solo aporte con el UE limitado en potencia es una **hipótesis**: falta el PHR, o una medición equivalente, para afirmar que el Redmi tenía margen.
  - **Resultado A/B/A (una corrida por tramo, 2/4/4 pruebas consecutivas):** B quedó entre A1 y A2. **No hay evidencia suficiente para adoptar DFT-s-OFDM por rendimiento:** se mantiene CP-OFDM de forma provisoria (D-017).
  - **A1 tuvo menor rendimiento y otras condiciones de enlace:** la SINR media del PUSCH en sus ventanas de subida fue de ~19 dB, contra ~27 dB en B y A2, y el MCS osciló. La causa está pendiente. **No hubo fallas de tiempo real dentro de esas ventanas.**
  - **Variables no controladas:** posición y orientación del teléfono, actividad del OnePlus, tiempo desde el arranque y asignación de PRB (51 en A, 50 en B, entre otras).
  - **256QAM es compatible con transform precoding:** TS 38.214 §6.1.4.1 incluye `mcs-TableTransformPrecoder = qam256`.
- **Bajada contra subida:** ~54 Mbit/s contra ~14,8 Mbit/s. El patrón TDD que difunde el gNB en `tdd-UL-DL-ConfigurationCommon` (TS 38.331; uso en TS 38.213 §11.1) tiene un período de 5 ms: 6 slots de bajada, un slot especial con 8 símbolos de bajada y 3 slots de subida. Ese patrón explica parte de la asimetría, aunque no fija una relación entre las tasas TCP. En el log, los PUSCH caen en los slots 7, 8, 9, 17, 18 y 19. Además, el PUSCH tiene más KO en la primera transmisión.
