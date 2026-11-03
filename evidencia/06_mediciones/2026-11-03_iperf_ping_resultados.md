# Resultados de iperf3 y ping, 2026-11-03 (tachoPC, n78 TDD)

**Entorno:**
- tachoPC: 4 hilos, 7 GiB de RAM y governor `performance`, puesto por el usuario antes del tramo A1.
- B210 por USB 3.0.
- Celda n78, ARFCN 635000, 20 MHz, μ=1, 51 PRB.
- Configuraciones sin métricas JSON.
- Teléfono: Redmi Note 14 5G (SIM …003, IP 10.45.0.2), con VoLTE activado y `NR only`.
- El OnePlus (SIM …004) estuvo en la celda pero no se midió.

**Cómo se midió:**
- **iperf3:** servidor del dashboard en `10.45.0.1:5201` (`iperf3 -s -1 -J`). Cliente: la app del teléfono, en TCP, con 10 s por prueba (la app no usó `-t 30`). Los valores son los de `sum_received` (subida) o `sum_sent` (bajada) del JSON del servidor. En la bajada, el servidor es el emisor, así que el valor es la **tasa del emisor**, no el *goodput* recibido.
- **Transcripción sin original:** los resultados se copiaron de `/api/metrics` durante la sesión. El dashboard no guarda en disco ni el JSON de iperf3 ni la salida del ping. Los logs del gNB permiten verificar el tráfico y las fallas, pero no estos valores TCP e ICMP.
- **La columna "Hora" es la de fin de cada prueba**, porque el backend la registra al terminar iperf3. En la bajada, el inicio y el fin se deducen de las ráfagas de PDSCH del log del gNB.
- **Las listas por segundo** tienen 11-12 intervalos porque iperf3 incluye el tramo final, de menos de 1 s.
- **Ping:** desde el contenedor del dashboard, que comparte la red con Open5GS, hacia 10.45.0.2, cada 0,5 s durante 30 s.

Horas en UTC.

## Subida (UE → núcleo), TCP 10 s
| Tramo | Configuración | Hora | Mbit/s | Por segundo (Mbit/s) |
| :--- | :--- | :--- | :--- | :--- |
| A1 | `gnb_b210_00101_csiper_ppm0_kos_sinmetricas.yml` (CP-OFDM) | 22:39:41 | 8,38 | 9,4 13,6 10,5 4,2 5,2 19,9 4,2 0,0 0,0 14,7 11,0 |
| A1 | ídem | 22:41:00 | 8,94 | 2,1 11,5 14,7 11,5 11,5 11,5 1,0 0,0 0,0 25,1 10,1 |
| B | `gnb_b210_00101_csiper_ppm0_kos_sinmetricas_dfts.yml` (DFT-s-OFDM) | 22:50:03 | 14,72 | 12,6 16,8 14,7 15,7 13,6 12,6 15,7 14,7 15,7 13,6 15,7 15,8 |
| B | ídem | 22:50:17 | 12,22 | 11,5 13,6 13,6 12,6 10,5 0,0 15,7 13,6 13,6 14,7 15,0 |
| B | ídem | 22:50:33 | 11,90 | 10,5 12,6 9,4 12,6 11,5 13,6 13,6 13,6 14,7 13,6 11,5 0,0 |
| B | ídem | 22:50:48 | 11,97 | 11,5 15,7 13,6 10,5 10,5 1,0 12,6 18,9 12,6 11,5 12,6 31,5 |
| A2 | `gnb_b210_00101_csiper_ppm0_kos_sinmetricas.yml` (CP-OFDM) | 22:54:04 | 14,55 | 10,5 16,8 16,8 15,7 15,7 14,7 13,6 5,2 4,2 31,5 15,9 |
| A2 | ídem | 22:54:19 | 14,52 | 9,4 15,7 14,7 13,6 11,5 14,7 17,8 16,8 13,6 13,6 16,8 19,8 |
| A2 | ídem | 22:54:34 | 13,76 | 9,4 14,7 12,6 10,5 11,5 14,7 15,7 15,7 14,7 14,7 15,7 18,8 |
| A2 | ídem | 22:54:49 | 16,53 | 11,5 17,8 17,8 18,9 16,8 16,8 17,8 8,4 23,1 14,7 18,5 |

**Promedios por tramo (el desvío es el muestral):**

| Tramo | Promedio (Mbit/s) | Desvío (Mbit/s) | Pruebas |
| :--- | :--- | :--- | :--- |
| A1 | 8,66 | 0,40 | 2 |
| B | 12,70 | 1,35 | 4 |
| A2 | 14,84 | 1,18 | 4 |

Ninguna prueba de subida coincidió con fallas "UL processor is busy". En A1, la primera de esas fallas fue a las 22:41:21, después de las dos pruebas.

## Bajada (núcleo → UE), TCP 10 s con `-R`, tramo A2
| Ventana aproximada (por el PDSCH) | Mbit/s (emisor) | Retransmisiones | Por segundo (Mbit/s) | Estado de la celda |
| :--- | :--- | :--- | :--- | :--- |
| 22:56:27-22:56:38 | 55,16 | 311 | 57,6 61,9 60,8 46,1 46,1 58,7 58,7 46,1 46,1 57,7 | Sin "UL busy" |
| 22:56:41-22:56:51 | 52,66 | 172 | 51,3 64,0 58,7 50,3 33,6 57,7 54,5 45,1 55,6 56,6 | Sin "UL busy": terminó antes de la primera |
| 22:56:54-22:57:04 | 42,18 | 56 | 44,0 56,6 52,4 53,5 53,5 46,1 26,2 28,3 26,2 35,7 | La primera "UL busy" (22:56:58,59) cayó en medio de esta prueba; en parte de ella hubo ~30 por segundo |

La caída de la tercera prueba coincide en parte con la aparición de las fallas. Esa coincidencia sola no demuestra causalidad.

## Ping a 10.45.0.2, tramo A2, ~22:58 (con ~13 "UL busy" por segundo: medición degradada)
| Medida | Valor |
| :--- | :--- |
| Enviados / recibidos | 60 / 47 (21,7 % de pérdida) |
| RTT mínimo | 16,7 ms |
| RTT mediano | 27,7 ms |
| RTT p90 | 44,9 ms |
| RTT máximo | 1052 ms |
| RTT promedio | 62,5 ms |
| mdev | 164,0 ms |
| Jitter (diferencias entre muestras sucesivas) | 52,3 ms |

Hay que repetirlo con la celda limpia.
