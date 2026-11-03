Creado `config/gnb/gnb_b210_00101_csiaper_ppm0.yml`. YAML validado con PyYAML: único cambio funcional, `ru_sdr.clock_ppm: 0`. No modifiqué otros archivos ni ejecuté Docker o el gNB.

Diff contra el original (`diff -u`):

```diff
@@ -1,5 +1,6 @@
 # SPDX-FileCopyrightText: Copyright (C) 2021-2026 Software Radio Systems Limited
 # SPDX-License-Identifier: BSD-3-Clause-Open-MPI
+# Variante de gnb_b210_00101_csiaper.yml con clock_ppm 0.
 # Solo prueba de PLMN 001/01 con CSI aperiódico (TS 31.102 no lo exige: es para ver si el módem trata distinto un PLMN de prueba). El resto es igual a gnb_b210.yml.
 
 
@@ -33,8 +34,8 @@
   # Jaula de Faraday a corta distancia; ajustar según medición.
   tx_gain: 80
   rx_gain: 40
-  # Antecedente a remedir en esta placa y condiciones de prueba.
-  clock_ppm: -1.87
+  # Prueba 2026-11-03: sin correccion. En OCUDU clock_ppm solo corrige la portadora, no el muestreo (ru_sdr_config_translator.cpp); ver investigacion/2026-11-03_analisis-cortes-claude.md
+  clock_ppm: 0
 
 cell_cfg:
   dl_arfcn: 635000  # 3525 MHz; n78, raster de 30 kHz.
```
