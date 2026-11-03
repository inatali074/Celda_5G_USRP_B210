# Análisis de los cortes (2026-11-03, Claude; corregido según la revisión de Codex)

Fuentes:
- logs `info` del gNB del 2026-11-02 en tachoPC (`logs/*_gnb.log.gz`, `evidencia/04_sesion_pdu/*.gz`);
- logs del 2026-11-03 de la PC de Santi (4 corridas, solo el Redmi con SIM 3), copiados con `scp`;
- código de OCUDU `release_26_10`.

Revisión de Codex: `revisiones/2026-11-03_codex-analisis-cortes.md`. No encontró nada bloqueante. Sus correcciones están incorporadas.

Notación: `ack=2` en PUCCH es compatible con DTX, pero la codificación no se verificó en el código. "PUSCH no decodificado con SINR negativa" quiere decir CRC KO con SINR estimada < 0. Es compatible con que el UE no transmitió, pero no lo prueba: también pueden fallar el grant, la temporización, los DM-RS o el estimador.

## Hallazgo 1: con `clock_ppm −1,87` el gNB pide TA positivos todo el tiempo; con 0, no
- **Verificado en el código (Claude, con WebFetch al tag `release_26_10`):** `ru_sdr_config_translator.cpp` aplica `clock_ppm` solo a las frecuencias centrales, `(f + freq_offset) * (1 + ppm*1e-6)`. `sampling_rate_Hz` se toma de `srate_MHz` sin corregir. Codex no pudo acceder a GitLab para confirmarlo.
- **Métrica:** TA solicitado = Σ(`ta_cmd` − 31) dividido por los segundos con algún PUSCH CRC OK. Paso de TA a μ=1: 16·64·Tc/2 = 0,2604 µs (TS 38.213 §4.2). Son comandos enviados, no ajustes confirmados en el UE.

| Corrida | PC | Teléfonos | clock_ppm | tx_gain | TA solicitado (pasos/s) | µs/s |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 18:18 (11-02) | tachoPC | Redmi | −1,87 | 70 | +3,84 | +1,00 |
| 18:38 (11-02) | tachoPC | Redmi | −1,87 | 80 | +2,76 | +0,72 |
| 19:45 (11-02) | tachoPC | Redmi + OnePlus | −1,87 | 60 | +2,82 | +0,74 |
| 19:49 (11-02) | tachoPC | Redmi | **0** | 80 | **−0,12** | −0,03 |
| 18:26 (11-03) | Santi | Redmi | −1,87 | 80 | +2,43 | +0,63 |
| 18:32 (11-03) | Santi | Redmi | −1,87 | 80 | +2,19 | +0,57 |
| 18:36 (11-03) | Santi | Redmi | −1,87 | 80 | +3,33 | +0,87 |
| 18:38 (11-03) | Santi | Redmi | −1,87 | 80 | +3,73 | +0,97 |

- **Mecanismo, plausible pero no demostrado:** el teléfono sigue la portadora corregida mientras el muestreo del gNB no se corrige. Una deriva libre de 1,87 ppm daría 1,87 µs/s, y lo observado es 0,6 a 1,0 µs/s: el UE también ajusta su tiempo con la bajada, así que la cifra no tiene por qué coincidir.
- **Lo que limita la conclusión:** hay una sola corrida con `clock_ppm 0`, corta (~2 min), con un teléfono y poco tráfico. Las corridas también difieren en duración, tráfico y `tx_gain`.

## Hallazgo 2: con pedido de CSI aperiódico, el PUSCH del Redmi nunca se decodifica
| Corrida | Con CSI: OK / KO con SINR<0 / KO con SINR≥0 | Sin CSI: OK / KO con SINR<0 / KO con SINR≥0 |
| :--- | :--- | :--- |
| 18:38 (11-02), archivo completo (cuenta de Codex) | 3 / 7136 / 0 | 4993 / 5317 / 832 |
| 4 corridas de Santi (11-03), archivos completos | **0 / 4896 / 0** | 2680 / 1870 / 349 |
| 19:49 (11-02), `clock_ppm 0` | 0 / 165 / 0 | 144 / 9 / 19 |

- La anomalía **sigue con `clock_ppm 0`**: es independiente del hallazgo 1.
- El OnePlus 13 (RNTI 0x4602 → `ue=1` → IMSI …004, verificado por Codex en el gNB y el AMF) sí decodifica con CSI: 384 OK, 50 KO con SINR ≥ 0 y 16 KO con SINR < 0. Que la SIM …004 esté en el OnePlus sale del inventario, no del AMF.
- Esos PUSCH llevan también HARQ-ACK de bajada. Si se pierden, el gNB los cuenta como KO de bajada.
- **Causa todavía abierta:** puede ser incompatibilidad del módem del Redmi con la configuración de CSI de OCUDU, grants perdidos, la configuración de UCI/DM-RS o la potencia de UL.

## Hallazgo 3: la RLF por HARQ-ACK se dispara con huecos cortos
- En `164854_gnb`: 100 HARQ-ACK KOs a las 19:45:55,745; vuelve `ack=1` a las 55,755; se pide la liberación a las 59,745. El UE se había recuperado y aun así lo liberaron.
- 100 KOs no son 100 slots: un reporte puede llevar varios bits HARQ, y KO incluye NACK y DTX.
- `pdsch.max_consecutive_kos` y `pusch.max_consecutive_kos` valen 100 por defecto. `pucch.max_consecutive_kos` cuenta CSI sin decodificar en PUCCH formato 2. Falta confirmar en el código cómo se reinicia el contador.

## Hallazgo 4: coincidencia RLF / tiempo real
- Avisos MAC de RLF: 38 + 14; precedidos en ≤ 3 s por un `late` o `underflow`: 5 + 7.
- Liberaciones iniciadas (`DU-MNG … Timer`): 31 + 9; con coincidencia: 1 + 5.
- La coincidencia inmediata es baja, pero eso no alcanza para descartar el tiempo real: falta comparar contra períodos sin corte.

## Otros, sin conclusión
- PUSCH en 256QAM, con KO a SINR 15-25 dB. Para decir que el MCS es demasiado alto faltan el MCS, la tasa de código y la BLER de primera transmisión.
- PDCCH del UE casi siempre en AL2 (`al_cqi_offset` existe).
- TA del PRACH ≈ 7,5 µs a 2 m. Puede ser el desalineamiento TX/RX de la B210 (`time_alignment_calibration`).

## Próximas pruebas (una variable por vez)
1. `gnb_b210_00101_csiaper_ppm0.yml`, 3 min, con tráfico continuo. Primero el Redmi, para comparar con las 4 corridas de Santi, y después el OnePlus.
2. Según el resultado: CSI periódico con `clock_ppm 0`, `max_consecutive_kos` más alto, PUSCH en `qam64`.

## Fuentes
- https://gitlab.com/ocudu/ocudu/-/raw/release_26_10/apps/units/flexible_o_du/split_8/helpers/ru_sdr_config_translator.cpp
- https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html
- https://docs.srsran.com/projects/project/en/latest/tutorials/source/cotsUE/source/index.html (recomienda reloj externo)
- TS 38.213 §4.2 (paso de TA)
