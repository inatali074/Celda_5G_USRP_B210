Creé únicamente [gnb_b210_00101_n3_ppm0_kos.yml](config/gnb/gnb_b210_00101_n3_ppm0_kos.yml). El base quedó intacto; el `diff -u` completo se mostró en la salida.

**Verificado:**

- YAML parsea con PyYAML; comparación estructural confirma únicamente los cambios pedidos. Comentarios sin tildes.
- n3 FDD: ARFCN 368500 → DL 1842,5 MHz; UL 1747,5 MHz, separación 95 MHz. Cumple raster de 100 kHz; 20 MHz/15 kHz corresponde a 106 PRB. [TS 38.104](https://www.etsi.org/deliver/etsi_ts/138100_138199/138104/15.03.00_60/ts_138104v150300p.pdf).
- CORESET#0 índice 12: 96 RB, un símbolo, offset 38; válido para SSB/PDCCH 15/15 kHz y compatible en tamaño con 106 PRB. SS0 índice 0: O=0, M=1, primer símbolo 0. [TS 38.213, tablas 13-1/13-11](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/15.03.00_60/ts_138213v150300p.pdf).
- PRACH índice 1 válido en FR1 FDD: formato 0, SFN mod 16=1, subtrama 4. [TS 38.211, tabla 6.3.3.2-2](https://www.etsi.org/deliver/etsi_ts/138200_138299/138211/15.02.00_60/ts_138211v150200p.pdf).

**No verificado:** ejemplo remoto `release_26_10` y `band_helper.cpp`, por fallas de acceso. Los valores coinciden con `gnb_zmq.yml`. No ejecuté Docker, gNB ni pruebas con celulares.
