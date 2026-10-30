Implementado en [gnb_b210.yml](config/gnb/gnb_b210.yml) y [docker-compose.yml](docker-compose.yml:53).

Respecto del ejemplo:

- AMF y binds N2/N3 adaptados a `10.53.1.2` / `10.53.1.3`; PLMN `'722999'`. TAC 7 y SST 1 conservados.
- ARFCN cambiado a `635000` (3525 MHz); conserva n78, 20 MHz, SCS 30 kHz y PCI 1.
- `device_args: type=b200`, sin los ajustes de frames del ejemplo. Conserva 23,04 MS/s, `sc12` y reloj interno.
- Ganancias TX/RX 50/40, con comentario para jaula de Faraday y ajuste según medición.
- `clock_ppm: -1.87`, marcado como antecedente a remedir. La opción existe en `apps/units/flexible_o_du/split_8/helpers/ru_sdr_config_cli11_schema.cpp:74`.
- UL CP-OFDM explícito con `enable_transform_precoding: false`.
- Log `/tmp/gnb.log` en `info`; PCAP MAC/NGAP desactivados, conservando sus rutas en `/tmp`.
- En Compose, únicamente agregué `tty: true` y `stdin_open: true` a `gnb-radio`.

**Evidencia de frecuencia**, relativa al checkout indicado, cuyo commit confirmé como `e0db566aac6e6376ddd60e83c84f58698fcc4d70`:

- `lib/ran/band_helper.cpp:96`: n78 admite 620000–653332 con paso 2 a 30 kHz; 635000 cumple. La validación está en líneas 872–888.
- `lib/ran/band_helper.cpp:308`: SSB de n78 a 30 kHz, caso C.
- Calculando con las fórmulas de `lib/ran/ssb/ssb_freq_position_generator.cpp`, existe este candidato: **GSCN 7860, SSB ARFCN 634656, 3519,84 MHz, offsetToPointA 2 y k_SSB 4**.
- `lib/ran/pdcch/pdcch_type0_css_coreset_config.cpp:86`: CORESET#0 índice 6, 24 PRB, 3 símbolos y offset 1. Para ese SSB ocupa CRB `[0,24)`, dentro de los 51 PRB; cumple las condiciones de `band_helper.cpp:1688–1698`. Dejé la selección automática.

Validación estática: YAML legible, coherencia con núcleo/Compose y `git diff --check` correctos. Sin problemas encontrados en ese alcance.

**Sin confirmar:** aceptación por el binario en ejecución, selección automática efectiva de SSB/CORESET, calibración de frecuencia, ganancias y funcionamiento con celular/SIM. No ejecuté Docker, sudo, gNB ni accedí a la USRP.
