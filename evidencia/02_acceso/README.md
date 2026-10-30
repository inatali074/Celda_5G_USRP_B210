# Etapa: acceso (2026-10-30)

Celda n78 TDD, 3525 MHz, TX 70, dentro de la jaula; UE: Redmi Note 14 5G con la SIM 1 en selección automática de red. El Motorola Edge 30 Neo solo vio la red con un chip comercial (intento `722-34` a las 14:26, anonimizado); con la SIM de laboratorio nunca la vio.

`2026-10-30_gnb_b210_chip_operadora.log` confirma el RACH de 4 pasos (TS 38.321 §5.1): Msg1 con PRACH detectado (`detection_metric` 39,2; TA estable de unos 7,9 µs, lo que lo distingue de una falsa alarma), Msg2 RAR por PDCCH con RA-RNTI, Msg3 por PUSCH con CRC OK (CCCH) y `rrcSetupComplete` con el NAS.

Los IMSI ajenos están anonimizados.
